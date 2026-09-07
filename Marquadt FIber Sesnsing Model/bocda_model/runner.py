"""CLI and GUI execution through native QuReed assembly and DES scheduling."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import sys
import threading
import time
from pathlib import Path

from . import project

_ASSEMBLY_LOCK = threading.RLock()


class _NativeRegistry:
    """Small headless equivalent of GUI SimulationWrapper; no GUI singleton edits."""
    def __init__(self, simulation):
        self.simulation, self.devices, self.signals = simulation, {}, []

    def add_device(self, device):
        self.devices[device.ref.uuid] = device

    def get_device(self, uid):
        return self.devices[uid]

    def create_connection(self, sig, dev1, port_label_1, dev2, port_label_2):
        dev1.register_signal(sig, port_label_1)
        dev2.register_signal(sig, port_label_2)
        self.signals.append(sig)


def _assemble(snapshot):
    from qureed.simulation import Simulation
    from qureed.simulation.simulate_from_json import JsonExecution

    class MemoryExecution(JsonExecution):
        def __init__(self, scheme, simulation):
            self.main_scheme = "snapshot.json"
            self.schemes = {self.main_scheme: scheme}
            self.sw = _NativeRegistry(simulation)
        def _get_scheme_dict(self, path):
            pass

    # Device constructors use a singleton. Swap only while constructing, and
    # restore the GUI's live simulation immediately, including on any exception.
    with _ASSEMBLY_LOCK:
        previous = Simulation._Simulation__instance
        Simulation._Simulation__instance = None
        try:
            simulation = Simulation.get_instance()
            executor = MemoryExecution(snapshot, simulation)
            executor.assemble_simulation()
        finally:
            Simulation._Simulation__instance = previous
    return executor.sw


def _assembled_snapshot(original, registry):
    rebuilt = copy.deepcopy(original)
    for node in rebuilt["devices"]:
        instance = registry.devices[node["uuid"]]
        node["values"] = copy.deepcopy(instance.values)
        node["name"] = instance.name
    rebuilt["connections"] = []
    for signal in registry.signals:
        rebuilt["connections"].append(dict(
            signal=f"{type(signal).__module__}.{type(signal).__name__}",
            conn=[dict(device_uuid=p.device.ref.uuid, port=p.label) for p in signal.ports]))
    return rebuilt


def execute_snapshot(scheme, mode="local", outdir=None, progress=None):
    """Run an isolated snapshot, returning (result, exported paths); errors propagate."""
    from .extensions import run_model, validate_run
    project.validate_scheme(scheme)
    snapshot = copy.deepcopy(scheme)
    # Fill schema defaults once before native JsonExecution assigns .values.
    for node in snapshot["devices"]:
        node["values"] = copy.deepcopy(project.device_class(node["device"]).values) | node.get("values", {})
    registry = _assemble(snapshot)
    config = project.config_from_scheme(_assembled_snapshot(snapshot, registry))
    validate_run(config,snapshot,mode)
    controller = next(d for d in registry.devices.values() if d.model_role == "scan")
    controller.execute = lambda: run_model(config, snapshot, mode=mode, progress=progress)
    started = time.perf_counter()
    registry.simulation.schedule_event(0, controller)
    # Do not call JsonExecution.run: the upstream method swallows exceptions.
    registry.simulation.run_des(0)
    result = controller.result
    result["execution"] = dict(
        adapter="QuReed JsonExecution assembly + native DES ScanController event",
        device_count=len(registry.devices), connection_count=len(registry.signals),
        remaining_events=len(registry.simulation.event_queue),
        elapsed_s=time.perf_counter()-started,
        scheme_sha256=hashlib.sha256(json.dumps(scheme, sort_keys=True,
                                                allow_nan=False).encode()).hexdigest(),
        versions={name: importlib.metadata.version(name)
                  for name in ("qureed","numpy","scipy","flet","photon-weave")})
    paths = {}
    if outdir is not None:
        if result.get("extension_kind") in ("quantum","dynamics"):
            from .advanced_results import save_advanced_results as save_results
        else:
            from .results import save_results
        paths = save_results(result, outdir, config)
        project.save(Path(outdir)/"experiment-used.json", snapshot)
        paths["experiment"] = str((Path(outdir)/"experiment-used.json").resolve())
        if "manifest" in paths:
            Path(paths["manifest"]).write_text(json.dumps(paths,indent=2)+"\n",encoding="utf-8")
    return result, paths


def main(argv=None):
    from .extensions import RUN_MODES
    parser = argparse.ArgumentParser(description="Run the saved QuReed BOCDA experiment.")
    parser.add_argument("--scheme", type=Path, default=project.ROOT/"experiment.json")
    parser.add_argument("--mode", choices=RUN_MODES, default="local")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args(argv)
    try:
        scheme = project.load(args.scheme)
        config = project.config_from_scheme(scheme)
        if args.validate:
            print(json.dumps({"valid": True, "devices": len(scheme["devices"]),
                              "segments": len(config["segments"]),
                              "length_m": sum(s["length_m"] for s in config["segments"])}, indent=2))
            return 0
        out = args.out or project.ROOT/"results"/args.mode
        def progress(*items, **kw):
            print("Progress:", *items, flush=True)
        result, paths = execute_snapshot(scheme,args.mode,out,progress)
        print(json.dumps({"completed": True, "mode": args.mode,
                          "positions": len(result.get("positions_m",result.get("z_m",[]))),
                          "frequency_points": len(result.get("frequency_hz",[])),
                          "time_frames": len(result.get("time_s",[])),
                          "warnings": result.get("warnings", []),
                          "files": paths}, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        print(f"BOCDA error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
