"""Native QuReed board with BOCDA parameter editing and asynchronous results.

Run python -m bocda_model.gui in this project. --web exposes the same native
QuReed/Flet canvas at localhost for browser operation and verification.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import copy
import json
import threading
import traceback
from datetime import datetime
from pathlib import Path

import flet as ft

from .integration import (SnapshotSession, execute_snapshot, fingerprint,
                          install_hooks, parse_parameter)


def _format_number(value, scale=1.0, digits=5):
    try:
        return f"{float(value) * scale:.{digits}g}"
    except (ValueError, TypeError):
        return "unavailable"


def _path_values(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from _path_values(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            yield from _path_values(child)
    elif isinstance(value, (str, Path)):
        yield Path(value)


class BocdaGui:
    def __init__(self, page: ft.Page, project_directory: Path, scheme="experiment.json"):
        self.page = page
        self.root = project_directory.resolve()
        self.session = SnapshotSession(self.root / scheme)
        self.loading = True
        self.fields = {}
        self.selected = None
        self.field_dirty = False
        self.ui_lock = threading.RLock()
        self.page.title = "QuReed | BOCDA Fiber Sensing"
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 1550
        self.page.window_height = 980
        self.page.bgcolor = "#f5f6f8"
        # Native QuReed assumes one desktop page. A browser reload creates a
        # new Flet page; controls carrying old page IDs must never be reused.
        from qureed.gui.board.info_bar import InfoBar
        from qureed.gui.board.ports import BoardConnector
        from qureed.gui.project import ProjectManager
        from qureed.gui.simulation import SimulationWrapper
        InfoBar._InfoBar__instance = None
        InfoBar._InfoBar__initialized = False
        ProjectManager._instance = None
        SimulationWrapper._SimulationWrapper__instance = None
        if hasattr(BoardConnector, "instance"):
            delattr(BoardConnector, "instance")
        install_hooks(self.root, changed=self.on_board_changed,
                      select=self.select_device, run=self.run, save=self.save)
        from qureed.gui.board.board import Board
        from qureed.gui.board.info_bar import InfoBar
        from qureed.gui.panels.device_settings import DeviceSettings
        from qureed.gui.project import ProjectManager

        self.pm = ProjectManager()
        self.pm.configure(path=self.root, venv=self.root.parent / ".venv")
        self.pm.current_scheme = None
        self.pm.modified_schemes = {}
        DeviceSettings()  # Native Board uses this singleton for header selection.
        self.info_bar = InfoBar()
        self.info_bar.set_page(page)
        self.board = Board(page)
        self.board.scheme_name.top = 8
        self.board.scheme_name.left = 12
        self.board.board_wrapper.content.content.bgcolor = "#f2f5f9"

        self.status = ft.Text("Opening experiment...", size=12, selectable=True)
        self.progress = ft.ProgressBar(visible=False, height=3)
        self.selection = ft.Dropdown(label="Apparatus block", width=298,
                                     on_change=self.dropdown_select)
        self.editor_title = ft.Text("Input parameters", weight=ft.FontWeight.BOLD)
        self.editor_note = ft.Text("Select a block's header or use the list above.", size=12)
        self.editor_fields = ft.Column(spacing=10)
        self.apply_button = ft.ElevatedButton("Apply parameters", icon=ft.icons.CHECK,
                                            on_click=lambda e: self.apply_fields())
        self.save_button = ft.ElevatedButton("Save", icon=ft.icons.SAVE,
                                           on_click=lambda e: self.save())
        self.local_button = ft.ElevatedButton("Run local spectrum", icon=ft.icons.PLAY_ARROW,
                                            on_click=lambda e: self.run("local"))
        self.scan_button = ft.ElevatedButton("Run position scan", icon=ft.icons.TIMELINE,
                                           on_click=lambda e: self.run("scan"))
        self.reload_button = ft.TextButton("Reload from disk", icon=ft.icons.REFRESH,
                                           on_click=self.request_reload)
        self.experiment_selector = ft.Dropdown(label="Experiment",width=320,
            value=self.session.path.name,on_change=self.request_experiment)
        self.result_notice = ft.Text("No measurements yet. Run a local spectrum or position scan.",
                                      size=14, color="#344b67")
        self.result_body = ft.Column(spacing=15, visible=False)
        self.results_view = ft.Column([self.result_notice, self.result_body],
                                      scroll=ft.ScrollMode.AUTO, expand=True)
        self.palette = ft.Column(spacing=6)
        self.side = ft.Container(width=330, bgcolor="#ffffff", padding=16, visible=False,
            border=ft.border.only(right=ft.BorderSide(1, "#d7dde5")),
            content=ft.Column([self.selection, self.editor_title, self.editor_note,
                              self.editor_fields, self.apply_button, ft.Divider(),
                              ft.Text("Add apparatus blocks", weight=ft.FontWeight.BOLD),
                              ft.Text("Drag a device onto the native QuReed board.", size=11),
                              self.palette], scroll=ft.ScrollMode.AUTO))
        # Native Board draws at its saved pixel coordinates. Scroll containers
        # preserve the coordinate contract for port dragging and wire updates.
        self.board_surface = ft.Container(width=1380, height=840,
                                         content=ft.Stack([self.board]))
        self.board_scroll = ft.Column([
            ft.Row([self.board_surface], scroll=ft.ScrollMode.ALWAYS)
        ], scroll=ft.ScrollMode.ALWAYS, expand=True)
        board_page = ft.Column([
            ft.Container(padding=ft.padding.symmetric(horizontal=16,vertical=8),
                content=ft.Row([ft.Text("Pump / shared light",color="#a66d00",size=12),
                    ft.Text("Probe (counterpropagating)",color="#178578",size=12),
                    ft.Text("Dashed blue: RF / control",color="#526f9b",size=12),
                    ft.Text("Click a block header to edit. Crossings are not junctions.",size=12,color="#576577")],spacing=25,wrap=True)),
            ft.Row([self.side,ft.Container(expand=True,content=self.board_scroll)],
                   spacing=0,expand=True,vertical_alignment=ft.CrossAxisAlignment.STRETCH)],spacing=0,expand=True)
        from .advanced_gui import AdvancedPanel
        self.advanced = AdvancedPanel(self)
        self.tabs = ft.Tabs(selected_index=0, expand=True, tabs=[
            ft.Tab(text="Apparatus", icon=ft.icons.ACCOUNT_TREE, content=board_page),
            ft.Tab(text="Measurements", icon=ft.icons.INSERT_CHART,
                   content=ft.Container(padding=22, content=self.results_view)),
            ft.Tab(text="Advanced models",icon=ft.icons.SCIENCE,content=self.advanced),
            ft.Tab(text="How to use", icon=ft.icons.HELP_OUTLINE,
                   content=ft.Container(padding=22, content=self._help()))])
        toolbar = ft.Container(padding=ft.padding.symmetric(horizontal=14, vertical=8),
            bgcolor="#e9eef5", content=ft.Row([
                ft.Text("BOCDA / QuReed", size=19, weight=ft.FontWeight.BOLD),
                self.save_button, self.reload_button, self.local_button, self.scan_button,
                self.experiment_selector,
                ft.TextButton("Toggle editor", on_click=self.toggle_editor)
            ], wrap=True))
        footer = ft.Container(height=31, padding=ft.padding.symmetric(horizontal=12, vertical=4),
                              content=self.status, bgcolor="#e9eef5")
        # InfoBar is mounted so native port hover/selection methods remain usable.
        native_info = ft.Container(height=21, content=ft.Stack([self.info_bar]))
        page.add(ft.Column([toolbar, self.progress, self.tabs, footer, native_info],
                           spacing=0, expand=True))
        self.reload()
        self._disconnected=False
        if hasattr(page,"run_task"):
            page.on_disconnect=lambda event:setattr(self,"_disconnected",True)
            self._disk_watch=page.run_task(self._watch_disk)

    async def _watch_disk(self):
        """Lightweight file guard; never write or discard pending GUI edits."""
        noticed=False
        while not self._disconnected:
            await asyncio.sleep(2)
            changed=self.session.disk_changed()
            if changed and not noticed and not self.session.running and not self.loading:
                try:
                    with self.ui_lock:
                        self._refresh_freshness()
                        self._set_status("The experiment JSON changed outside this window. "
                                         "Reload from disk before saving or running.",True)
                except (RuntimeError,AssertionError):
                    return
            noticed=changed and not self.session.running

    def _help(self):
        return ft.Column([
            ft.Text("A shared laser, two optical arms, and a segmented fiber", size=22),
            ft.Text("This is QuReed's native optical board. Gold lines carry optical fields, "
                    "green lines identify probe routing, and blue lines carry electrical/control signals."),
            ft.Text("1. Click a block's black header, or choose it in Apparatus block. Edit values "
                    "with their displayed units, then Apply parameters. Save and Run also apply pending values."),
            ft.Text("2. In Scan controller, set the target, frequency sweep, and position scan. "
                    "The target maps to a physical modulation frequency or relative delay; it does not select a fiber label."),
            ft.Text("In frequency control mode, the target, external delay, and correlation order determine the actual "
                    "FM frequency. Editing nominal FM frequency alone does not move the peak in this mode. "
                    "Delay mode holds the nominal frequency and adjusts delay. Fixed mode holds both physical "
                    "controls and reports the resulting peak. Actual settings are listed with each measurement."),
            ft.Text("3. Run local spectrum measures one position. Run position scan measures a sequence. "
                    "Measurements shows fitted outputs, spatial response, profiles, and saved plot paths."),
            ft.Text("4. Drag a header to move a block. Left-click two compatible ports to connect them; "
                    "right-click a port to disconnect. Right-click a header for native remove options. "
                    "The model validates required connections before executing."),
            ft.Text("5. Scroll the board horizontally/vertically to see its full extent. Toggle editor "
                    "gives the board more room. The fiber carries pump left-to-right and probe right-to-left."),
            ft.Text("6. Save persists positions, topology, and physical parameters. Reload explicitly reads "
                    "external JSON edits. An external-change guard prevents cached GUI data overwriting newer disk edits."),
            ft.Text("Measurements are hidden and marked stale after edits. Every run saves its input snapshot, "
                    "data, and plots under results/. Source values and assumed settings are documented in the README."),
            ft.Text("7. Advanced models provides nonideal spectra, coupled optical/acoustic transients, "
                    "and selected-mode quantum analyses. Each is a separate model with explicit assumptions."),
            ft.Text("8. Choose experiment-homodyne.json in Experiment for a connected LO and balanced receiver. "
                    "Edit LO phase/power and receiver calibration on the Apparatus blocks, then run Gaussian / homodyne "
                    "from Advanced models. The output is measured before the drawn optional lock-in."),
            ft.Text("The baseline assumes weak probe and undepleted pump; the transient explicitly evolves depletion. "
                    "Quantum analysis is an effective selected-mode model, not a complete quantum SBS apparatus. "
                    "Numerical agreement is not laboratory calibration or evidence of quantum advantage.", color="#6b4d26")
        ], spacing=16, scroll=ft.ScrollMode.AUTO)

    def _set_status(self, message, error=False):
        self.status.value = str(message)
        self.status.color = "#ac2525" if error else "#31415a"
        self.page.update()

    def snapshot(self):
        return self.pm._capture_board_dict()

    def _populate_lists(self):
        from qureed.gui.panels.side_panel import DraggableDevice
        devices = [item.device_instance for item in self.board.content.controls
                   if hasattr(item, "device_instance")]
        self.selection.options = [ft.dropdown.Option(str(d.ref.uuid), d.name or d.gui_name)
                                  for d in devices]
        classes = {type(d): d.gui_name for d in devices}
        self.palette.controls = [DraggableDevice(
            d_cls={"class": cls}, group="device",
            content=ft.Container(padding=6, bgcolor="#eef2f8",
                                 content=ft.Text(label, size=12)),
            content_feedback=ft.Container(width=112, height=76, bgcolor="#dde5f0",
                                          content=ft.Text(label)))
            for cls, label in classes.items()]

    def reload(self):
        if self.session.running:
            self._set_status("Wait for the current run before reloading.", True)
            return
        self.loading = True
        try:
            scheme = self.session.open()
            self.pm.modified_schemes = {}
            self.pm.current_scheme = None
            self.pm._bocda_metadata = copy.deepcopy(scheme)
            self.pm.open_scheme(self.session.path.name)
            self._populate_lists()
            self.experiment_selector.options=[ft.dropdown.Option(p.name)
                for p in sorted(self.root.glob("*.json"))]
            self.experiment_selector.value=self.session.path.name
            self.selected = None
            self.fields = {}
            self.field_dirty = False
            self.editor_fields.controls = []
            self.selection.value = None
            self.editor_title.value = "Input parameters"
            self.editor_note.value = "Select a block's header or use the list above."
            if any(n["device"]=="homodyne_receiver.HomodyneReceiver" for n in scheme["devices"]):
                self.advanced.group="quantum"
                self.advanced.selector.value="quantum"
            self.advanced.reload()
            self._refresh_freshness()
            self._set_status(f"Loaded {self.session.path.name}. Select a block to edit its input parameters.")
        except Exception as exc:
            self._set_status(f"Cannot load project: {exc}", True)
            traceback.print_exc()
        finally:
            self.loading = False

    def request_experiment(self,event):
        name=event.control.value
        if self.session.running:
            self.experiment_selector.value=self.session.path.name
            return
        def switch():
            try:
                from .project import load
                path=self.root/name
                if Path(name).name!=name or path.suffix.lower()!=".json":
                    raise ValueError("Choose an experiment JSON in this project folder.")
                load(path)
                self.session=SnapshotSession(path)
                self.result_notice.value="No measurements for this experiment yet."
                self.result_body.controls=[]
                self.reload()
            except Exception as exc:
                self.experiment_selector.value=self.session.path.name
                self._set_status(f"Cannot open experiment: {exc}",True)
        if name==self.session.path.name:
            return
        if self.session.pending_edits or self.session.saved_fingerprint!=fingerprint(self.snapshot()):
            dialog=ft.AlertDialog(title=ft.Text("Open another experiment?"),
                content=ft.Text("This discards unsaved edits in this window. Saved files are preserved."),actions=[])
            def close(change):
                dialog.open=False
                if change:
                    switch()
                else:
                    self.experiment_selector.value=self.session.path.name
                self.page.update()
            dialog.actions=[ft.TextButton("Keep editing",on_click=lambda e:close(False)),
                            ft.TextButton("Open saved experiment",on_click=lambda e:close(True))]
            self.page.dialog=dialog
            dialog.open=True
            self.page.update()
        else:
            switch()

    def request_reload(self, event=None):
        if self.session.pending_edits or (self.session.saved_fingerprint != fingerprint(self.snapshot())):
            dialog = ft.AlertDialog(title=ft.Text("Reload saved experiment?"),
                content=ft.Text("This discards unsaved edits in this window and loads the current JSON from disk."),
                actions=[])
            def close(reload):
                dialog.open = False
                self.page.update()
                if reload:
                    self.reload()
            dialog.actions = [ft.TextButton("Keep editing", on_click=lambda e: close(False)),
                              ft.TextButton("Reload saved file", on_click=lambda e: close(True))]
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
        else:
            self.reload()

    def toggle_editor(self, event=None):
        self.side.visible = not self.side.visible
        self.page.update()

    def dropdown_select(self, event):
        self.board.handle_device_select(self.board.get_device(uuid=event.control.value))

    def select_device(self, device=None):
        if self.loading:
            return
        if self.field_dirty and not self.apply_fields(quiet=True):
            self._set_status("Correct the highlighted parameters before changing the selected block.", True)
            return
        self.selected = device
        self.fields = {}
        self.editor_fields.controls = []
        if device is None:
            self.editor_title.value = "Input parameters"
            self.editor_note.value = "Select a block's header or use the list above."
            self.selection.value = None
            self.page.update()
            return
        self.side.visible = True
        instance = device.device_instance
        self.selection.value = str(instance.ref.uuid)
        self.editor_title.value = instance.name or instance.gui_name
        self.editor_note.value = getattr(instance, "description", None) or instance.gui_name
        self.name_field = ft.TextField(label="Block name", value=instance.name,
                                      dense=True, on_change=self.pending_field)
        self.editor_fields.controls.append(self.name_field)
        values = getattr(instance, "values", {})
        schema = getattr(instance, "parameter_schema", {})
        for key, value in values.items():
            spec = schema.get(key, {"type": type(value).__name__, "label": key})
            label = spec.get("label", key)
            if spec.get("unit"):
                label += f" [{spec['unit']}]"
            kind = spec.get("type")
            choices = spec.get("choices", spec.get("options"))
            if kind in (bool, "bool", "boolean") or isinstance(value, bool):
                control = ft.Checkbox(label=label, value=bool(value), on_change=self.pending_field)
            elif choices:
                control = ft.Dropdown(label=label, value=str(value), dense=True,
                    options=[ft.dropdown.Option(str(option)) for option in choices],
                    on_change=self.pending_field)
            else:
                control = ft.TextField(label=label, value=str(value), dense=True,
                                       on_change=self.pending_field)
            control.tooltip = spec.get("description", spec.get("help", key))
            self.fields[key] = (control, spec)
            self.editor_fields.controls.append(control)
        self.page.update()

    def pending_field(self, event=None):
        self.field_dirty = True
        self.session.pending_edits = True
        self._refresh_freshness()
        self._set_status("Parameter edits pending. Apply, Save, or Run to use them.")

    def apply_fields(self, quiet=False):
        if not self.field_dirty or self.selected is None:
            return True
        parsed, errors = {}, []
        for key, (control, spec) in self.fields.items():
            try:
                parsed[key] = parse_parameter(control.value, spec)
                if hasattr(control, "error_text"):
                    control.error_text = None
            except (ValueError, TypeError) as exc:
                errors.append(f"{spec.get('label', key)}: {exc}")
                if hasattr(control, "error_text"):
                    control.error_text = str(exc)
        if errors:
            self._set_status("; ".join(errors), True)
            return False
        instance = self.selected.device_instance
        instance.values.update(parsed)
        instance.name = self.name_field.value.strip() or instance.gui_name
        instance.ref.name = instance.name
        self.selected.base_header.content.controls[1].content.value = instance.name
        self.field_dirty = False
        self.session.pending_edits = self.advanced.dirty
        self.advanced.sync_hardware()
        self._populate_lists()
        self._refresh_freshness()
        if not quiet:
            self._set_status("Parameters applied to the diagram. Save to persist them.")
        return True

    def on_board_changed(self):
        if self.loading:
            return
        self._populate_lists()
        self.advanced.sync_hardware()
        self._refresh_freshness()
        self._set_status("Diagram changed. Save to persist; run again for current measurements.")

    def _refresh_freshness(self):
        if self.session.last_result is None:
            self.result_body.visible = False
            return
        current = self.session.results_current(self.snapshot())
        self.result_body.visible = current
        self.result_notice.value = ("Measurements match the current diagram and parameters."
            if current else "STALE: the diagram or input values have changed. Run again to display current measurements. "
                               "Earlier files remain in the results folder.")
        if self.session.disk_changed():
            self.result_notice.value="STALE: the experiment JSON changed on disk. Reload from disk to review it; " \
                                     "unsaved edits in this window have not been discarded."
        self.result_notice.color = "#2a664b" if current else "#965b17"

    def save(self):
        try:
            if not self.apply_fields(quiet=True):
                return False
            if not self.advanced.apply(quiet=True):
                return False
            self.advanced.canonicalize_hardware()
            snapshot = self.snapshot()
            self.session.save(snapshot)
            self.pm._bocda_metadata = copy.deepcopy(snapshot)
            self.pm.modified_schemes = {self.pm.current_scheme: copy.deepcopy(snapshot)}
            self._refresh_freshness()
            self._set_status(f"Saved positions, wiring, and input values to {self.session.path.name}.")
            return True
        except Exception as exc:
            self._set_status(str(exc), True)
            return False

    def run(self, mode="local"):
        if self.session.running:
            self._set_status("A simulation is already running.")
            return
        if not self.apply_fields(quiet=True) or not self.advanced.apply(quiet=True):
            return
        try:
            self.advanced.prepare_run(mode)
        except Exception as exc:
            self._set_status(f"Cannot prepare run: {exc}",True)
            return
        if not self.save():
            return
        snapshot = copy.deepcopy(self.snapshot())
        try:
            from .project import validate_scheme, config_from_scheme
            validate_scheme(snapshot)
            from .extensions import validate_run
            validate_run(config_from_scheme(snapshot),snapshot,mode)
        except Exception as exc:
            self._set_status(f"Cannot run: {exc}", True)
            return
        self.session.running = True
        self.session.result_fingerprint = None
        self.local_button.disabled = True
        self.scan_button.disabled = True
        self.reload_button.disabled = True
        self.save_button.disabled = True
        self.side.disabled = True
        self.board_surface.disabled = True
        self.advanced.disabled = True
        self.experiment_selector.disabled = True
        self.progress.visible = True
        self.result_body.visible = False
        self.result_notice.value = "Running the saved input snapshot..."
        self._set_status(f"Running {mode} measurement...")
        outdir = self.root / "results" / f"gui_{mode}_{datetime.now():%Y%m%d_%H%M%S_%f}"
        self.page.run_thread(self._worker, snapshot, mode, outdir)

    def _worker(self, snapshot, mode, outdir):
        def progress(*args, **kwargs):
            with self.ui_lock:
                message = " / ".join(str(arg) for arg in args)
                self.status.value = f"Running {mode}: {message}"
                self.page.update()
        try:
            result, paths = execute_snapshot(snapshot, mode=mode, outdir=outdir, progress=progress)
            with self.ui_lock:
                self.session.complete(snapshot, result, paths)
                self._show_results(result, paths, outdir)
                self._refresh_freshness()
                self.tabs.selected_index = 1
                self._set_status(f"Completed {mode}. Input snapshot, data, and figures: {outdir}")
        except Exception as exc:
            traceback.print_exc()
            with self.ui_lock:
                self.session.last_result=None
                self.session.result_fingerprint=None
                self.session.output_paths={}
                self.result_notice.value = f"Run failed: {exc}"
                self.result_notice.color = "#ac2525"
                self.result_body.visible = False
                self._set_status(f"Run failed: {exc}", True)
        finally:
            with self.ui_lock:
                self.session.running = False
                self.local_button.disabled = False
                self.scan_button.disabled = False
                self.reload_button.disabled = False
                self.save_button.disabled = False
                self.side.disabled = False
                self.board_surface.disabled = False
                self.advanced.disabled = False
                self.experiment_selector.disabled = False
                self.progress.visible = False
                self.page.update()

    def _show_results(self, result, paths, outdir):
        if result.get("extension_kind") in ("quantum","dynamics"):
            self._show_advanced_results(result,paths,outdir)
            return
        spatial = result.get("spatial", {})
        controls = [ft.Text("Measured / reconstructed outputs", size=23, weight=ft.FontWeight.BOLD),
            ft.Text(f"Output directory: {outdir}", selectable=True, size=12),
            ft.Text("Model outputs use the configured optical/receiver gain and lock-in convention. "
                    "Assigned fiber resonances in profile plots are ground-truth inputs, not measurements. "
                    "For nonideal runs the spatial curve below remains the clean FM reference, not the noisy PSF.", size=12),
            ft.Text(f"Spatial response peak: {_format_number(spatial.get('peak_m'),100)} cm; "
                    f"measured FWHM: {_format_number(spatial.get('fwhm_m'),100)} cm; "
                    f"approximate resolution formula: {_format_number(spatial.get('approx_resolution_m'),100)} cm.")]
        warnings = result.get("warnings", [])
        if warnings:
            controls.append(ft.Text("Model notices: " + "; ".join(map(str, warnings)), color="#8c5919"))
        positions = result.get("positions_m", [])
        fitted = result.get("fitted_resonance_hz", [])
        fits = result.get("fits", [])
        physical_controls = result.get("controls", [])
        rows = []
        for index, (position, resonance) in enumerate(zip(positions, fitted)):
            fit = fits[index] if index < len(fits) else {}
            flag = fit.get("status", fit.get("quality", fit.get("flags", fit.get("flag", "none"))))
            if isinstance(flag, (list, tuple)):
                flag = ", ".join(map(str, flag)) or "none"
            physical = physical_controls[index] if index < len(physical_controls) else {}
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(_format_number(position, 100))),
                ft.DataCell(ft.Text(_format_number(physical.get("frequency_hz"), 1e-3, 9))),
                ft.DataCell(ft.Text(_format_number(physical.get("delay_s"), 1e9, 9))),
                ft.DataCell(ft.Text(_format_number(resonance, 1e-9, 7))),
                ft.DataCell(ft.Text(str(flag)))]))
        if rows:
            controls.append(ft.DataTable(columns=[ft.DataColumn(ft.Text("Position [cm]")),
                ft.DataColumn(ft.Text("Actual FM [kHz]")),
                ft.DataColumn(ft.Text("Relative delay [ns]")),
                ft.DataColumn(ft.Text("Fitted resonance [GHz]")),
                ft.DataColumn(ft.Text("Fit quality"))], rows=rows))
        png_paths = sorted({path.resolve() for path in _path_values(paths)
                            if path.suffix.lower() == ".png" and path.exists()})
        # The exporter may return a directory rather than individual figure paths.
        if not png_paths:
            png_paths = sorted(Path(outdir).glob("*.png"))
        for path in png_paths:
            controls.extend([ft.Text(path.stem.replace("_", " "), size=17),
                ft.Image(src_base64=base64.b64encode(path.read_bytes()).decode(),
                         width=1050, fit=ft.ImageFit.CONTAIN)])
        controls.append(ft.Text(json.dumps(result.get("diagnostics", {}), indent=2,
                                            default=str), selectable=True, size=11))
        self.result_body.controls = controls
        self.result_body.visible = True

    def _show_advanced_results(self,result,paths,outdir):
        kind=result["extension_kind"]
        controls=[ft.Text("Coupled optical/acoustic transient" if kind=="dynamics" else
                         "Selected-mode states and balanced homodyne",size=23,weight=ft.FontWeight.BOLD),
                  ft.Text(f"Output directory: {outdir}",selectable=True,size=12)]
        if kind=="quantum":
            q=result["quantum"]; selected=q["selected"]; measurement=selected["measurement"]
            controls.extend([
                ft.Text("Balanced difference voltage averaged over the selected mode duration; "
                        "not the original photodiode/lock-in voltage. LO locking is an explicit ideal assumption."),
                ft.Text(f"Selected position {_format_number(selected['position_m'],100)} cm, "
                        f"offset {_format_number(selected['frequency_hz'],1e-9,8)} GHz; "
                        f"effective gain {_format_number(selected['effective_amplifier_gain'],1,8)}."),
                ft.Text(f"Mean difference {_format_number(measurement['difference_voltage_v'])} V; "
                        f"variance {_format_number(measurement['difference_voltage_variance_v2'])} V². "
                        f"Displaced thermal: {selected['is_displaced_thermal']}; "
                        f"exact Gaussian under model: {selected['is_exact_gaussian_under_model']}."),
                ft.Text(q['multimode']['fisher_status']),
                ft.Text("Multimode comparisons use the same total signal photons, LO photons and observation time. "
                        "Additional covariance information is not automatically quantum advantage.",color="#6b4d26")])
            diagnostics={"selected_channel":selected['channel_checks_before_phase_mixture'],
                         "measurement":measurement,"multimode":q['multimode']}
        else:
            d=result["diagnostics"]
            controls.extend([
                ft.Text(f"{d['cells']} cells; dt {_format_number(d['dt_s'],1e12)} ps; "
                        f"simulated {_format_number(d['fm_periods_simulated'])} FM periods."),
                ft.Text(f"Duration {_format_number(d.get('duration_s'),1e9)} ns; "
                        f"{_format_number(d.get('propagation_transits_simulated'))} fiber transits; "
                        f"{_format_number(d.get('minimum_acoustic_lifetimes_simulated'))} longest acoustic amplitude lifetimes."),
                ft.Text(f"Refinement: {d.get('refinement_status','not_checked')}. "
                        "Acceptance compares each boundary trace using the saved absolute and relative RMS tolerances."),
                ft.Text(f"Final pump depletion {_format_number(d.get('pump_depletion_fraction_final'),100)}%; "
                        f"probe amplification {_format_number(d['probe_amplification_final'])}; "
                        f"photon balance residual {_format_number(d['photon_balance_relative'])}."),
                ft.Text("The acoustic field uses an explicitly defined envelope normalization, not acoustic energy. "
                        "Gain/probe multipliers are assumed demonstration settings.",color="#6b4d26")])
            diagnostics=d
        for warning in result.get("warnings",[]):
            controls.append(ft.Text(str(warning),size=12,color="#8c5919"))
        for path in sorted({p.resolve() for p in _path_values(paths)
                            if p.suffix.lower()==".png" and p.exists()}):
            controls.extend([ft.Text(path.stem.replace("_"," "),size=17),
                ft.Image(src_base64=base64.b64encode(path.read_bytes()).decode(),width=1050,fit=ft.ImageFit.CONTAIN)])
        controls.append(ft.Text(json.dumps(diagnostics,indent=2,default=str),selectable=True,size=11))
        self.result_body.controls=controls
        self.result_body.visible=True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web", action="store_true", help="Serve the native QuReed UI on localhost")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--scheme", default="experiment.json")
    args = parser.parse_args(argv)
    ft.app(target=lambda page: BocdaGui(page, args.project, args.scheme),
           host="127.0.0.1", port=args.port if args.web else 0,
           view=None if args.web else ft.AppView.FLET_APP,
           web_renderer=ft.WebRenderer.HTML)


if __name__ == "__main__":
    main()
