"""Shared optional-model dispatch; the saved scheme remains authoritative."""
from __future__ import annotations
import copy
import importlib

GROUPS = ("nonideal", "dynamics", "quantum")
RUN_MODES = ("local", "scan", "nonideal-local", "nonideal-scan", "dynamics", "quantum", "quantum-scan")


def module_for(group):
    if group not in GROUPS:
        raise ValueError(f"Unknown advanced model: {group}")
    return importlib.import_module(f"bocda_model.{group}")


def group_for_mode(mode):
    if mode.startswith("nonideal-"):
        return "nonideal"
    if mode.startswith("quantum"):
        return "quantum"
    return "dynamics" if mode == "dynamics" else None


def defaults(group):
    return copy.deepcopy(module_for(group).default_options())


def schema(group):
    fields=copy.deepcopy(module_for(group).schema())
    suffixes={"_deg_s":"deg/s","_db_hz":"dB/Hz","_mhz":"MHz","_ghz":"GHz","_hz":"Hz",
              "_ns":"ns","_us":"us","_s":"s","_deg":"deg","_rad":"rad",
              "_db":"dB","_w":"W","_m":"m"}
    for key,spec in fields.items():
        spec.setdefault("label",key.replace("_"," ").capitalize())
        if "unit" not in spec:
            spec["unit"]=next((unit for suffix,unit in suffixes.items() if key.endswith(suffix)),"")
    return fields


def options_for(scheme, group):
    from .integration import parse_parameter
    value = scheme.get("extensions", {})
    if not isinstance(value, dict):
        raise ValueError("extensions must be an object with nonideal, dynamics or quantum groups.")
    raw = value.get(group, {})
    if not isinstance(raw, dict):
        raise ValueError(f"extensions.{group} must be an object.")
    fields = schema(group)
    unknown = set(raw)-set(fields)
    if unknown:
        raise ValueError(f"Unknown {group} options: {', '.join(sorted(unknown))}")
    merged = defaults(group) | copy.deepcopy(raw)
    parsed = {key: parse_parameter(value, fields[key]) for key,value in merged.items()}
    if group == "quantum":
        parsed.update(hardware_options(scheme))
    return parsed


def validate_options(scheme):
    raw = scheme.get("extensions", {})
    if not isinstance(raw, dict) or set(raw)-set(GROUPS):
        raise ValueError("Only nonideal, dynamics and quantum extension groups are supported.")
    for group in raw:
        options_for(scheme, group)


def hardware_options(scheme):
    """Read displayable quantum settings from native blocks, even while rewiring."""
    from .project import device_class
    result = {}
    for node in scheme.get("devices", []):
        cls = device_class(node["device"])
        if cls.model_role == "lo" or getattr(cls,"is_homodyne",False):
            result.update(copy.deepcopy(cls.values) | copy.deepcopy(node.get("values",{})))
    return {key:value for key,value in result.items() if key in schema("quantum")}


def validate_run(config, scheme, mode):
    if mode not in RUN_MODES:
        raise ValueError(f"Run mode must be one of {RUN_MODES}.")
    group = group_for_mode(mode)
    homodyne = "quantum_hardware" in config
    if group == "quantum":
        if not homodyne:
            raise ValueError("Quantum/homodyne requires the connected LO and balanced receiver. "
                             "Open experiment-homodyne.json using the Experiment selector.")
        if not options_for(scheme,"quantum")["enabled"]:
            raise ValueError("Enable selected-mode quantum/homodyne analysis in Advanced models before running.")
    elif homodyne and group != "dynamics":
        raise ValueError("This apparatus has a homodyne receiver, not the original direct detector. "
                         "Run Gaussian / homodyne, or open experiment.json for direct-detection spectra.")
    if group is not None:
        options_for(scheme,group)


def run_model(config, scheme, mode, progress=None):
    from .physics import simulate
    validate_run(config,scheme,mode)
    group = group_for_mode(mode)
    if group is None:
        return simulate(config, mode=mode, progress=progress)
    options = options_for(scheme,group)
    if group == "nonideal":
        result = module_for(group).simulate_nonideal(
            config,options,mode="scan" if mode.endswith("scan") else "local",progress=progress)
        result["mode"] = mode
        result["extension_kind"] = "nonideal"
    elif group == "dynamics":
        result = module_for(group).simulate_dynamics(config,options,progress=progress)
        result["mode"] = "dynamics"
        result["extension_kind"] = "dynamics"
        result.setdefault("config",copy.deepcopy(config))
    else:
        # Quantum hardware overrides are derived from the connected optional
        # LO/receiver, when present, never from an unsaved GUI cache.
        options.update(copy.deepcopy(config.get("quantum_hardware", {})))
        classical = simulate(config,mode="scan" if mode.endswith("scan") else "local",progress=progress)
        quantum = module_for(group).analyze_quantum(classical,options)
        result = dict(mode=mode,extension_kind="quantum",quantum=quantum,
                      classical_reference=classical,config=copy.deepcopy(config),
                      positions_m=classical["positions_m"],frequency_hz=classical["frequency_hz"],
                      warnings=list(quantum.get("warnings",[])),
                      diagnostics=quantum.get("diagnostics",{}))
    result["extension_options"] = copy.deepcopy(options)
    return result
