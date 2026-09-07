"""Saved QuReed topology is the single source of truth for model configuration."""
from __future__ import annotations

import copy
import importlib
import json
import math
import os
import tempfile
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = {
    "fm_generator": "FmGenerator", "cw_laser": "CwLaser", "splitter": "Splitter",
    "pump_reference": "PumpReference", "pump_eom": "PumpEom", "edfa": "Edfa",
    "probe_rf_generator": "ProbeRfGenerator", "probe_eom": "ProbeEom",
    "polarization_controller": "PolarizationController", "optical_isolator": "OpticalIsolator",
    "circulator": "Circulator", "fiber_segment": "FiberSegment",
    "pump_terminator": "PumpTerminator", "photodetector": "Photodetector",
    "lock_in": "LockIn", "scan_controller": "ScanController",
    "local_oscillator": "LocalOscillator", "homodyne_receiver": "HomodyneReceiver",
}
ALLOWED = {f"{module}.{name}" for module, name in COMPONENTS.items()}
SIGNALS = {"bocda_model.devices.OpticalSignal", "bocda_model.devices.ElectricalSignal"}


def device_class(path):
    if path not in ALLOWED:
        raise ValueError(f"Unsupported device {path!r}. Choose a BOCDA project component.")
    module, name = path.rsplit(".", 1)
    return getattr(importlib.import_module(module), name)


def uid(name):
    return str(uuid5(NAMESPACE_URL, "qureed:bocda:demo:" + name))


def default_scheme():
    scheme = dict(schema_version=1, name="Marquadt BOCDA segmented fiber",
                  model="classical weak-gain delayed-FM SBS", devices=[], connections=[],
                  provenance={
                      "paper_values": ["699 kHz FM", "47 GHz reported bandwidth (convention caveat)",
                                       "27 MHz intrinsic gain FWHM", "100 kHz pump intensity tag"],
                      "assumptions": ["Four 10 cm regions; third shifted from 10.85 to 10.90 GHz",
                                      "Demonstration powers, receiver gains, and SBS coefficient",
                                      "External delay 1/fm, correlation order 1; not the paper path"],
                      "excursion_note": "Default total span 47 GHz. See docs/source-audit.md. "
                                        "Reported nominal 3 cm is not imposed on computed PSF.",
                      "status": "Exploratory numerical model, not calibrated experimental prediction"})
    def node(key, module, name, x, y, **values):
        cls = device_class(f"{module}.{COMPONENTS[module]}")
        settings = copy.deepcopy(cls.values)
        settings.update(values)
        scheme["devices"].append(dict(uuid=uid(key), device=f"{module}.{COMPONENTS[module]}",
                                      name=name, location=[x, y], values=settings))
    node("fm", "fm_generator", "Laser FM", 90, 100)
    node("laser", "cw_laser", "Shared CW laser", 90, 300)
    node("splitter", "splitter", "50:50 splitter", 270, 300)
    node("probe_rf", "probe_rf_generator", "Probe RF sweep", 460, 80)
    node("probe_eom", "probe_eom", "Probe EOM", 460, 240)
    node("pc", "polarization_controller", "Probe PC", 650, 240)
    node("isolator", "optical_isolator", "Probe isolator", 840, 240)
    node("pump_eom", "pump_eom", "Pump EOM", 460, 480)
    node("edfa", "edfa", "Pump EDFA", 650, 480)
    node("circulator", "circulator", "Circulator", 840, 480)
    for i in range(4):
        node(f"fiber{i+1}", "fiber_segment", f"Fiber {i+1}" + (" (shifted)" if i == 2 else ""),
             1030 + 185*i, 480, resonance_hz=10.90e9 if i == 2 else 10.85e9)
    node("termination", "pump_terminator", "Pump output", 1770, 480)
    node("pump_reference", "pump_reference", "Pump AM + ref", 460, 690)
    node("pd", "photodetector", "Probe detector", 840, 690)
    node("lia", "lock_in", "Lock-in X / Y", 1090, 690)
    node("scan", "scan_controller", "Position scan", 1310, 860)
    def edge(a, p, b, q, optical=True):
        scheme["connections"].append(
            dict(signal="bocda_model.devices." + ("OpticalSignal" if optical else "ElectricalSignal"),
                 conn=[dict(device_uuid=uid(a), port=p), dict(device_uuid=uid(b), port=q)]))
    for a,p,b,q in [
        ("laser","optical","splitter","optical"), ("splitter","pump","pump_eom","optical"),
        ("splitter","probe","probe_eom","optical"), ("pump_eom","pump","edfa","pump_in"),
        ("edfa","pump_out","circulator","pump_in"), ("circulator","pump_out","fiber1","pump_in"),
        ("probe_eom","probe","pc","probe_in"), ("pc","probe_out","isolator","probe_in"),
        ("isolator","probe_out","fiber4","probe_in"),
        ("fiber1","probe_out","circulator","probe_in"),
        ("circulator","detector_out","pd","probe"), ("fiber4","pump_out","termination","pump")
    ]:
        edge(a,p,b,q)
    for i in range(1,4):
        edge(f"fiber{i}","pump_out",f"fiber{i+1}","pump_in")
        edge(f"fiber{i+1}","probe_out",f"fiber{i}","probe_in")
    for a,p,b,q in [
        ("fm","fm","laser","fm"), ("scan","fm_control","fm","control"),
        ("scan","rf_control","probe_rf","control"), ("probe_rf","rf","probe_eom","rf"),
        ("pump_reference","modulation","pump_eom","modulation"),
        ("pump_reference","reference","lia","reference"), ("pd","voltage","lia","voltage"),
        ("lia","measurement","scan","measurement")
    ]:
        edge(a,p,b,q,False)
    from .layout import tidy_scheme
    return tidy_scheme(scheme)


def homodyne_scheme():
    """A separate, fully connected receiver variant; baseline remains unchanged."""
    scheme = default_scheme()
    scheme["name"] = "Marquadt BOCDA with explicit balanced homodyne"
    scheme["model"] = "effective selected-mode Gaussian channel and balanced homodyne"
    receiver = next(n for n in scheme["devices"] if n["uuid"] == uid("pd"))
    receiver.update(device="homodyne_receiver.HomodyneReceiver", name="Balanced receiver",
                    values=copy.deepcopy(device_class("homodyne_receiver.HomodyneReceiver").values))
    lo_cls = device_class("local_oscillator.LocalOscillator")
    scheme["devices"].append(dict(uuid=uid("lo"), device="local_oscillator.LocalOscillator",
        name="Matched local oscillator", location=[650,860], values=copy.deepcopy(lo_cls.values)))
    for a,p,b,q,optical in [("fm","lo_fm","lo","fm",False),
                            ("probe_rf","lo_rf","lo","rf",False),
                            ("lo","optical","pd","lo",True)]:
        scheme["connections"].append(dict(
            signal="bocda_model.devices."+("OpticalSignal" if optical else "ElectricalSignal"),
            conn=[dict(device_uuid=uid(a),port=p),dict(device_uuid=uid(b),port=q)]))
    from .extensions import defaults, hardware_options
    hardware = hardware_options(scheme)
    scheme["extensions"] = {"quantum": {k:v for k,v in
        (defaults("quantum") | {"enabled": True}).items() if k not in hardware}}
    scheme["provenance"]["assumptions"].extend([
        "Ideal coherent LO follows the complete probe optical phase history; no lock feedback dynamics",
        "Balanced mixer and two photodiodes are one explicit composite receiver block",
        "Quantum statistics are read before the drawn optional lock-in; no quantum LIA processing is inferred"])
    validate_scheme(scheme)
    from .layout import tidy_scheme
    return tidy_scheme(scheme)


def _structure(scheme):
    if not isinstance(scheme, dict) or not isinstance(scheme.get("devices"), list):
        raise ValueError("Scheme must have a devices array.")
    if not isinstance(scheme.get("connections"), list):
        raise ValueError("Scheme must have a connections array.")
    if "extensions" in scheme:
        from .extensions import validate_options
        validate_options(scheme)
    nodes, classes, used, links = {}, {}, set(), {}
    for item in scheme["devices"]:
        key = item.get("uuid")
        if not isinstance(key, str) or not key or key in nodes:
            raise ValueError("Every device needs a unique nonempty UUID.")
        cls = device_class(item.get("device"))
        nodes[key], classes[key] = item, cls
        if not isinstance(item.get("values", {}), dict):
            raise ValueError(f"{item.get('name')}: values must be an object.")
        location = item.get("location", [0,0])
        if len(location) != 2 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in location):
            raise ValueError(f"{item.get('name')}: location must contain two finite coordinates.")
        for key_, value in item.get("values", {}).items():
            if key_ not in cls.values:
                raise ValueError(f"{item.get('name')}: unknown parameter {key_}.")
            spec = cls.parameter_schema[key_]
            kind = spec.get("type", "float")
            if kind == "bool":
                valid = isinstance(value, bool)
            elif kind in ("enum", "str"):
                valid = isinstance(value, str) and (not spec.get("choices") or value in spec["choices"])
            else:
                valid = not isinstance(value,bool) and isinstance(value,(int,float)) and math.isfinite(value)
                valid = valid and (kind != "int" or int(value) == value)
                valid = valid and ("min" not in spec or value >= spec["min"])
                valid = valid and ("max" not in spec or value <= spec["max"])
            if not valid:
                raise ValueError(f"{item.get('name')}: invalid {key_}={value!r}. Check units/range.")
    for connection in scheme["connections"]:
        signal = connection.get("signal")
        endpoints = connection.get("conn", [])
        if signal not in SIGNALS or len(endpoints) != 2:
            raise ValueError("Every connection must use a supported signal and two endpoints.")
        resolved = []
        for end in endpoints:
            key, label = end.get("device_uuid"), end.get("port")
            if key not in nodes or label not in classes[key].ports:
                raise ValueError(f"Connection references an unknown device/port: {key}:{label}.")
            point = (key,label)
            if point in used:
                raise ValueError(f"{nodes[key].get('name')}:{label} is connected more than once.")
            used.add(point)
            port = classes[key].ports[label]
            expected = f"{port.signal_type.__module__}.{port.signal_type.__name__}"
            if signal != expected:
                raise ValueError(f"{nodes[key].get('name')}:{label} requires {expected}.")
            resolved.append((point,port.direction))
        if resolved[0][1] == resolved[1][1]:
            raise ValueError("Connections must join an output to an input.")
        origin, target = (resolved if resolved[0][1] == "output" else resolved[::-1])
        links[origin[0]] = target[0]
    return nodes, classes, used, links


def validate_scheme(scheme, complete=True):
    nodes, classes, used, links = _structure(scheme)
    if not complete:
        return True
    roles = {}
    for key, cls in classes.items():
        roles.setdefault(cls.model_role, []).append(key)
        for label in cls.ports:
            if (key,label) not in used and label not in cls.optional_ports:
                raise ValueError(f"Connect {nodes[key].get('name') or cls.gui_name}:{label} before running.")
    required = ["fm","laser","splitter","probe_rf","probe_eom","pc","isolator","pump_eom",
                "edfa","circulator","termination","pump_reference","pd","lia","scan"]
    for role in required:
        if len(roles.get(role,[])) != 1:
            raise ValueError(f"Expected exactly one {role} device; found {len(roles.get(role,[]))}.")
    if not roles.get("segment"):
        raise ValueError("Add at least one bidirectional fiber segment.")
    def expect(a,p,b,q):
        origin, wanted = (roles[a][0],p), (roles[b][0],q)
        if links.get(origin) != wanted:
            raise ValueError(f"Required route: {nodes[origin[0]]['name']}:{p} to "
                             f"{nodes[wanted[0]]['name']}:{q}.")
    for a,p,b,q in [
        ("fm","fm","laser","fm"), ("laser","optical","splitter","optical"),
        ("splitter","pump","pump_eom","optical"), ("splitter","probe","probe_eom","optical"),
        ("pump_eom","pump","edfa","pump_in"), ("edfa","pump_out","circulator","pump_in"),
        ("probe_eom","probe","pc","probe_in"), ("pc","probe_out","isolator","probe_in"),
        ("circulator","detector_out","pd","probe"), ("pd","voltage","lia","voltage"),
        ("pump_reference","modulation","pump_eom","modulation"),
        ("pump_reference","reference","lia","reference"), ("probe_rf","rf","probe_eom","rf"),
        ("scan","fm_control","fm","control"), ("scan","rf_control","probe_rf","control"),
        ("lia","measurement","scan","measurement")
    ]:
        expect(a,p,b,q)
    receiver_cls = classes[roles["pd"][0]]
    if getattr(receiver_cls, "is_homodyne", False):
        if len(roles.get("lo", [])) != 1:
            raise ValueError("Balanced homodyne requires exactly one connected local oscillator.")
        expect("lo","optical","pd","lo")
        expect("fm","lo_fm","lo","fm")
        expect("probe_rf","lo_rf","lo","rf")
    elif roles.get("lo"):
        raise ValueError("A local oscillator must feed a balanced homodyne receiver.")
    chain = []
    cursor = links[(roles["circulator"][0],"pump_out")]
    previous = (roles["circulator"][0],"probe_in")
    while cursor[0] in roles["segment"]:
        key, port = cursor
        if port != "pump_in" or key in chain:
            raise ValueError("Pump fiber chain has reversed ports or a cycle.")
        if links.get((key,"probe_out")) != previous:
            raise ValueError("Probe must traverse the same fiber chain in the reverse direction.")
        chain.append(key)
        previous = (key,"probe_in")
        cursor = links[(key,"pump_out")]
    if cursor != (roles["termination"][0],"pump") or set(chain) != set(roles["segment"]):
        raise ValueError("Every fiber must lie in one pump chain ending at Pump output.")
    if links[(roles["isolator"][0],"probe_out")] != (chain[-1],"probe_in"):
        raise ValueError("Probe isolator must feed the rightmost fiber's probe_in port.")
    return True


def config_from_scheme(scheme):
    validate_scheme(scheme)
    nodes, classes, used, links = _structure(scheme)
    grouped = {}
    for key, cls in classes.items():
        if cls.model_role != "segment":
            grouped[cls.model_role] = (key, copy.deepcopy(cls.values) | copy.deepcopy(nodes[key].get("values", {})))
    get = lambda role: grouped[role][1]
    chain, cursor = [], links[(grouped["circulator"][0],"pump_out")]
    while classes[cursor[0]].model_role == "segment":
        key = cursor[0]
        chain.append(copy.deepcopy(classes[key].values) | copy.deepcopy(nodes[key].get("values",{}))
                     | {"name": nodes[key].get("name") or "Fiber"})
        cursor = links[(key,"pump_out")]
    config = dict(fm=get("fm"), laser=get("laser"), splitter=get("splitter"),
                  pump=get("pump_eom") | get("pump_reference") | get("edfa") | get("circulator"),
                  probe=get("probe_eom") | get("pc") | get("isolator"), segments=chain,
                  receiver=get("pd") | get("lia"), scan=get("scan") | get("probe_rf"),
                  provenance=copy.deepcopy(scheme.get("provenance", {})))
    if "lo" in grouped:
        hardware = get("lo") | {k:v for k,v in get("pd").items() if k != "bandwidth_hz"}
        config["quantum_hardware"] = hardware
        receiver = config["receiver"]
        optical_hz = 299792458/(config["laser"]["wavelength_nm"]*1e-9)
        receiver["responsivity_a_w"] = hardware["quantum_efficiency"]*1.602176634e-19/(6.62607015e-34*optical_hz)
        receiver["transimpedance_v_a"] = hardware["homodyne_transimpedance_v_a"]
        receiver["max_voltage_v"] = hardware["homodyne_max_voltage_v"]
    from .physics import validate_config
    return validate_config(config)


def load(path):
    path = Path(path)
    if path.is_dir():
        path /= "experiment.json"
    scheme = json.loads(path.read_text(encoding="utf-8-sig"))
    validate_scheme(scheme, complete=False)
    return scheme


def save(path, scheme):
    """Atomic save; allow incomplete wiring during editing, validate fully at Run."""
    validate_scheme(scheme, complete=False)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(scheme, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=path.name+".", suffix=".tmp", delete=False) as stream:
            temp = Path(stream.name)
            stream.write(text)
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()
