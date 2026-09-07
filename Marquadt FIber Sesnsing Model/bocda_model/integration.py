"""Project-local QuReed integration; no changes to the installed GUI are required.

The native canvas remains the editor.  Its live devices and ports are serialized
before execution; both the CLI and GUI call ``execute_snapshot`` on that scheme.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import inspect
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


def fingerprint(scheme: dict) -> str:
    def canonical(value):
        if isinstance(value, dict):
            return {key: canonical(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [canonical(item) for item in value]
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value
    return hashlib.sha256(json.dumps(canonical(scheme), sort_keys=True, allow_nan=False,
                                    separators=(",", ":")).encode()).hexdigest()


def parse_parameter(raw: Any, spec: dict) -> Any:
    """Parse finite values and respect an optional schema range/choice contract."""
    kind = spec.get("type", "float")
    if kind in (bool, "bool", "boolean"):
        if isinstance(raw, bool):
            value = raw
        elif str(raw).lower() in ("true", "false"):
            value = str(raw).lower() == "true"
        else:
            raise ValueError("Enter true or false")
    elif kind in (int, "int", "integer"):
        if isinstance(raw,bool):
            raise ValueError("Enter an integer, not a boolean")
        numeric = float(raw)
        if not math.isfinite(numeric) or not numeric.is_integer():
            raise ValueError("Enter a finite integer")
        value = int(numeric)
    elif kind in (str, "str", "string", "enum"):
        value = str(raw)
    else:
        if isinstance(raw,bool):
            raise ValueError("Enter a number, not a boolean")
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError("Enter a finite number")
    choices = spec.get("choices", spec.get("options"))
    if choices and value not in choices:
        raise ValueError(f"Choose one of: {', '.join(map(str, choices))}")
    if "min" in spec and value < spec["min"]:
        raise ValueError(f"Minimum is {spec['min']}")
    if "max" in spec and value > spec["max"]:
        raise ValueError(f"Maximum is {spec['max']}")
    return value


@dataclass
class SnapshotSession:
    """Keep edits, disk state, and result freshness distinct and testable."""
    path: Path
    saved_fingerprint: str | None = None
    result_fingerprint: str | None = None
    disk_digest: str | None = None
    pending_edits: bool = False
    running: bool = False
    last_result: dict | None = None
    output_paths: dict = field(default_factory=dict)

    def open(self) -> dict:
        from .project import load
        scheme = load(self.path)
        self.disk_digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.saved_fingerprint = fingerprint(scheme)
        self.pending_edits = False
        return scheme

    def save(self, scheme: dict) -> None:
        from .project import save
        if self.path.exists() and self.disk_digest is not None:
            current = hashlib.sha256(self.path.read_bytes()).hexdigest()
            if current != self.disk_digest:
                raise RuntimeError("The JSON changed outside this window. Reload from disk "
                                   "before saving; your cached diagram was not written.")
        save(self.path, scheme)
        self.disk_digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.saved_fingerprint = fingerprint(scheme)
        self.pending_edits = False

    def disk_changed(self) -> bool:
        if self.disk_digest is None:
            return False
        try:
            return hashlib.sha256(self.path.read_bytes()).hexdigest()!=self.disk_digest
        except OSError:
            return True

    def results_current(self, scheme: dict) -> bool:
        return (not self.pending_edits and self.result_fingerprint is not None
                and self.result_fingerprint == fingerprint(scheme) and not self.disk_changed())

    def complete(self, scheme: dict, result: dict, paths: dict) -> None:
        self.last_result = result
        self.output_paths = paths
        self.result_fingerprint = fingerprint(scheme)


def execute_snapshot(scheme: dict, mode: str = "local", outdir=None,
                     progress: Callable | None = None):
    """Validate the exact saved topology/parameters and run the shared engine."""
    from .runner import execute_snapshot as execute
    return execute(scheme, mode=mode, outdir=outdir, progress=progress)


def discover_device(project_path: Path, relative_path: str):
    """Return a compatible device class, or None for ordinary project Python.

    Utility and test files are displayed as files instead of being instantiated
    as device classes.  Locally authored custom devices remain discoverable.
    """
    path = (Path(project_path) / relative_path).resolve()
    if not path.is_relative_to(Path(project_path).resolve()):
        raise ValueError("Device module must be inside the project")
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    declarations = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    if not declarations:
        return None
    module_name = ".".join(path.relative_to(project_path).with_suffix("").parts)
    module = importlib.import_module(module_name)
    from qureed.devices import GenericDevice
    candidates = [getattr(module, name) for name in declarations
                  if inspect.isclass(getattr(module, name, None))]
    candidates = [cls for cls in candidates if issubclass(cls, GenericDevice)
                  and cls is not GenericDevice and getattr(cls, "gui_name", None)]
    preferred = "".join(part.capitalize() for part in path.stem.split("_"))
    return next((cls for cls in candidates if cls.__name__ == preferred),
                candidates[0] if len(candidates) == 1 else None)


_HOOKS_INSTALLED = False
_ACTIVE_ROOT = None
_CALLBACKS = {}


def install_hooks(project_path, *, changed=None, select=None, run=None, save=None):
    """Install narrowly scoped, process-only compatibility fixes for this project."""
    global _HOOKS_INSTALLED, _ACTIVE_ROOT, _CALLBACKS
    _ACTIVE_ROOT = Path(project_path).resolve()
    _CALLBACKS = {"changed": changed, "select": select, "run": run, "save": save}
    if _HOOKS_INSTALLED:
        return
    _HOOKS_INSTALLED = True
    import flet as ft
    from qureed.gui.board.board import Board
    from qureed.gui.board.device import Device
    from qureed.gui.board.base_device_component import BaseDeviceComponent
    from qureed.gui.board.connections import Connection
    from qureed.gui.board.ports import BoardConnector, Ports
    from qureed.gui.panels.device_settings import DeviceSettings
    from qureed.gui.panels.project_panel import File
    from qureed.gui.project import ProjectManager
    from qureed.gui.simulation import SimulationWrapper

    def active():
        path = ProjectManager().path
        return path is not None and Path(path).resolve() == _ACTIVE_ROOT

    def changed():
        if active() and _CALLBACKS.get("changed"):
            _CALLBACKS["changed"]()

    original_capture = ProjectManager._capture_board_dict
    def capture(pm):
        current = original_capture(pm)
        if not active():
            return current
        base = copy.deepcopy(getattr(pm, "_bocda_metadata", {}))
        nodes = {node["uuid"]: node for node in base.get("devices", [])}
        for node in current["devices"]:
            node["location"] = list(node["location"])
            device = Board.get_board().get_device(uuid=node["uuid"]).device_instance
            extras = nodes.get(node["uuid"], {}).copy()
            extras.update(node)
            extras["values"] = copy.deepcopy(getattr(device, "values", {}))
            node.clear()
            node.update(extras)
        base.update(current)
        return base
    ProjectManager._capture_board_dict = capture

    original_load = Board.load_device
    def load_device(board, dev_class, position, uid, values, name=None):
        original_load(board, dev_class, position, uid, values, name)
        if active():
            gui_device = board.get_device(uuid=uid)
            if values is not None:
                gui_device.device_instance.values.update(copy.deepcopy(values))
    Board.load_device = load_device

    original_ports = Device._compute_ports
    def compute_ports(device):
        original_ports(device)
        mapping = getattr(device.device_instance, "gui_port_sides", {})
        if active() and mapping:
            all_ports = list(device.device_instance.ports.values())
            for widget, side, default_dir in ((device.ports_in, "left", "input"),
                                              (device.ports_out, "right", "output")):
                widget.ports = [port for port in all_ports
                                if mapping.get(port.label,
                                  "left" if port.direction == "input" else "right") == side]
                widget.create_ports(Ports.left_side if side == "left" else Ports.right_side)
    Device._compute_ports = compute_ports

    original_device_init = Device.__init__
    def init_device(device, *args, **kwargs):
        original_device_init(device, *args, **kwargs)
        if active():
            instance = device.device_instance
            device.base_wrapper_width = 112
            device.base_wrapper.width = 112
            device.base_wrapper_height = max(86, device.base_wrapper_height)
            device.base_wrapper.height = device.base_wrapper_height
            device.header_height = 22
            device.base_header.height = 22
            device.content_wrapper.top = 22
            device.base_header.bgcolor = "#24364b"
            device.base_header.content.controls[1].content.value = instance.name or instance.gui_name
            device.base_header.content.controls[1].content.size = 11
            device.base_header.content.controls[1].content.max_lines = 1
            device.base_wrapper.tooltip = f"{instance.name}\n{instance.gui_name}\nClick header to edit; drag header to move"
            # Absolute local image paths cannot be served to a browser.  Read the
            # same installed icon and embed it, preserving native visual assets.
            icon_path = Path(device.image.src)
            if icon_path.exists():
                import base64
                device.image.src_base64 = base64.b64encode(icon_path.read_bytes()).decode()
                device.image.src = None
            device.image.width = 90
            device.image.height = 45
    Device.__init__ = init_device

    original_settings = DeviceSettings.show_device_settings
    def settings(panel, device=None):
        if active() and _CALLBACKS.get("select"):
            _CALLBACKS["select"](device)
        else:
            original_settings(panel, device)
    DeviceSettings.show_device_settings = settings

    original_file = File.__init__
    def init_file(item, path):
        if not active() or not str(path).endswith(".py"):
            original_file(item, path)
            return
        cls = discover_device(_ACTIVE_ROOT, path)
        if cls is not None:
            original_file(item, path)
            return
        ft.TextButton.__init__(item, content=ft.Text(Path(path).name, size=12), disabled=True)
        item.path, item.name, item.cls = path, Path(path).name, None
    File.__init__ = init_file
    original_discover = ProjectManager.load_class_from_file
    ProjectManager.load_class_from_file = lambda pm, path: (
        discover_device(_ACTIVE_ROOT, path) if active() else original_discover(pm, path))

    original_clear = SimulationWrapper.clear
    def clear(wrapper):
        original_clear(wrapper)
        if active():
            wrapper.simulation.event_queue.clear()
            wrapper.simulation.event_map.clear()
            wrapper.simulation.current_time = 0
            wrapper.simulation.end_time = 0
            connector = BoardConnector()
            connector.first_click = None
    SimulationWrapper.clear = clear

    original_execute = SimulationWrapper.execute
    def execute(wrapper):
        if active() and _CALLBACKS.get("run"):
            return _CALLBACKS["run"]("local")
        return original_execute(wrapper)
    SimulationWrapper.execute = execute

    original_save = ProjectManager.save
    def save_project(pm):
        if active() and _CALLBACKS.get("save"):
            return _CALLBACKS["save"]()
        return original_save(pm)
    ProjectManager.save = save_project

    original_open = ProjectManager.open_project
    def open_project(pm, project_path):
        if Path(project_path).resolve() == _ACTIVE_ROOT:
            pm.configure(path=_ACTIVE_ROOT, venv=Path(sys.prefix))
            from qureed.gui.panels.project_panel import ProjectPanel
            panel = ProjectPanel.get_instance()
            if panel is not None:
                panel.update_project(_ACTIVE_ROOT)
            return
        return original_open(pm, project_path)
    ProjectManager.open_project = open_project

    for cls, method_name in ((BaseDeviceComponent, "handle_device_move"),
                             (Board, "remove_device"), (Board, "drag_accept"),
                             (BoardConnector, "handle_disconnect"),
                             (BoardConnector, "handle_connect")):
        original = getattr(cls, method_name)
        def wrap(self, *args, _original=original, **kwargs):
            answer = _original(self, *args, **kwargs)
            changed()
            return answer
        setattr(cls, method_name, wrap)

    original_draw = Connection.draw
    def draw(connection):
        if not active():
            return original_draw(connection)
        import flet.canvas as cv
        from .layout import route_wire
        board = Board.get_board()
        blocks = [d for d in board.content.controls if hasattr(d,"device_instance")]
        rectangles = [(2*d.left,2*d.top,2*d.left+d.base_wrapper_width,
                       2*d.top+d.base_wrapper_height) for d in blocks]
        existing = {}
        for d in blocks:
            for side in (d.ports_in,d.ports_out):
                for widget in side.ports_controls:
                    item = widget.connection
                    if item is not None and item is not connection:
                        existing[id(item)] = getattr(item,"_route_points",[])
        points = route_wire(connection._start_point,connection._end_point,rectangles,
                            connection.port_a.side.lower(),connection.port_b.side.lower(),existing.values())
        connection._route_points = points
        signal = type(connection.port_a.port_instance.signal).__name__.lower()
        optical = "optical" in signal
        probe = any("probe" in p.port_instance.label.lower() for p in (connection.port_a,connection.port_b))
        color = ("#178578" if probe else "#c68a08") if optical else "#6a85b2"
        connection.connection = cv.Path([cv.Path.MoveTo(*points[0])]+
            [cv.Path.LineTo(*p) for p in points[1:]],paint=ft.Paint(color=color,
            stroke_width=2.6 if optical else 1.5,stroke_dash_pattern=None if optical else [6,4],
            style=ft.PaintingStyle.STROKE))
        connection.canvas.shapes.append(connection.connection)
        connection.canvas.update()
    Connection.draw = draw

    original_move = BaseDeviceComponent.handle_device_move
    def move_and_route(device,event):
        original_move(device,event)
        if active():
            # Moving even an unconnected block can obstruct another wire.
            all_connections = {}
            for block in Board.get_board().content.controls:
                if not hasattr(block,"ports_in"): continue
                for side in (block.ports_in,block.ports_out):
                    for port in side.ports_controls:
                        if port.connection is not None:
                            all_connections[id(port.connection)] = port.connection
            for wire in all_connections.values():
                wire._start_point = wire.port_a.get_location_on_board()
                wire._end_point = wire.port_b.get_location_on_board()
                wire.redraw()
    BaseDeviceComponent.handle_device_move = move_and_route
