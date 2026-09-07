"""Editable advanced-model controls mounted inside the native QuReed GUI."""
from __future__ import annotations
import copy
import flet as ft
from . import extensions
from .integration import parse_parameter


class AdvancedPanel(ft.Container):
    def __init__(self, owner):
        super().__init__(padding=22)
        self.owner = owner
        self.group = "nonideal"
        self.fields = {}
        self.dirty = False
        self.selector = ft.Dropdown(label="Advanced model",width=390,value=self.group,
            options=[ft.dropdown.Option("nonideal","Nonideal optics and detector noise"),
                     ft.dropdown.Option("dynamics","Coupled optical/acoustic transient"),
                     ft.dropdown.Option("quantum","Gaussian modes and homodyne receiver")],
            on_change=self.switch_group)
        self.description = ft.Text("",selectable=True)
        self.form = ft.Column(spacing=12)
        self.action_row = ft.Row(wrap=True)
        self.content = ft.Column([
            ft.Text("Advanced physical models",size=24,weight=ft.FontWeight.BOLD),
            ft.Text("All controls are saved in this experiment JSON. These models expose their own "
                    "assumptions and validity limits; a stochastic optical ensemble is not silently "
                    "treated as an exact Gaussian quantum state.",selectable=True),
            self.selector,self.description,
            ft.Row([ft.ElevatedButton("Apply advanced parameters",on_click=lambda e:self.apply()),
                    ft.TextButton("Reset this model's defaults",on_click=self.reset_defaults)],wrap=True),
            self.action_row,ft.Divider(),self.form],
            scroll=ft.ScrollMode.AUTO,spacing=15,expand=True)

    def reload(self):
        self.dirty=False
        self._render()

    def _render(self):
        raw=self.owner.snapshot()
        try:
            options=extensions.options_for(raw,self.group)
            specs=extensions.schema(self.group)
        except (ImportError,AttributeError,ValueError) as exc:
            self.form.controls=[ft.Text(f"Model not available: {exc}",color="#ac2525")]
            self.action_row.controls=[]
            self.owner.page.update()
            return
        self.fields={}
        self.form.controls=[]
        hardware=extensions.hardware_options(raw) if self.group=="quantum" else {}
        if self.group=="quantum":
            self.form.controls.append(ft.Text(
                "LO/receiver fields below come from the native apparatus blocks and are read-only here. "
                "Edit those blocks in Apparatus. Load experiment-homodyne.json to use this receiver.",
                color="#546579",size=12))
        for key,value in options.items():
            spec=specs[key]
            label=spec.get("label",key)
            if spec.get("unit"): label+=f" [{spec['unit']}]"
            kind=spec.get("type","float")
            choices=spec.get("choices",spec.get("options"))
            if kind in ("bool","boolean",bool) or isinstance(value,bool):
                field=ft.Checkbox(label=label,value=value,on_change=self.changed)
            elif choices:
                field=ft.Dropdown(label=label,value=str(value),width=570,
                    options=[ft.dropdown.Option(str(v)) for v in choices],on_change=self.changed)
            else:
                field=ft.TextField(label=label,value=str(value),width=570,dense=True,on_change=self.changed)
            field.tooltip=spec.get("description",spec.get("help",key))
            if key in hardware:
                field.disabled=True
                field.tooltip="Controlled by the connected LO/receiver block in Apparatus."
            self.fields[key]=(field,spec)
            self.form.controls.append(field)
            if spec.get("description"):
                self.form.controls.append(ft.Text(spec["description"],size=11,color="#546579"))
        descriptions={
            "nonideal":"Weak-gain spectra with explicit device transfer functions, shared-source noise, "
                       "polarization variation and detector statistics. This does not invoke the depleted transient solver.",
            "dynamics":"Both optical directions and the acoustic envelope evolve in time. "
                       "Power/gain scales are explicit demonstration overrides. A short transient does not represent "
                       "an average over a complete 699 kHz FM cycle.",
            "quantum":"Finite selected optical modes, thermal amplifier noise, explicit LO and homodyne readout "
                      "before the optional drawn lock-in. This uses the clean single-Stokes baseline, not the "
                      "nonideal multi-sideband detector sum. Resource-matched comparisons do not imply quantum advantage."
        }
        self.description.value=descriptions[self.group]
        modes={"nonideal":[("Run nonideal local","nonideal-local"),("Run nonideal scan","nonideal-scan")],
               "dynamics":[("Run coupled transient","dynamics")],
               "quantum":[("Run Gaussian / homodyne","quantum"),("Run quantum position scan","quantum-scan")]}
        self.action_row.controls=[ft.ElevatedButton(label,on_click=lambda e,m=mode:self.owner.run(m))
                                  for label,mode in modes[self.group]]
        self.owner.page.update()

    def changed(self,event=None):
        self.dirty=True
        self.owner.session.pending_edits=True
        self.owner._refresh_freshness()
        self.owner._set_status("Advanced inputs changed. Apply, Save or Run to use them.")

    def apply(self,quiet=False):
        if not self.dirty:
            return True
        parsed={}
        errors=[]
        hardware=extensions.hardware_options(self.owner.snapshot()) if self.group=="quantum" else {}
        for key,(field,spec) in self.fields.items():
            if key in hardware:
                continue
            try:
                parsed[key]=parse_parameter(field.value,spec)
                if hasattr(field,"error_text"):field.error_text=None
            except (ValueError,TypeError) as exc:
                errors.append(f"{key}: {exc}")
                if hasattr(field,"error_text"):field.error_text=str(exc)
        if errors:
            self.owner._set_status("; ".join(errors),True)
            return False
        self.owner.pm._bocda_metadata.setdefault("extensions",{})[self.group]=parsed
        self.dirty=False
        self.owner.session.pending_edits=self.owner.field_dirty
        self.owner._refresh_freshness()
        if not quiet:self.owner._set_status("Advanced settings applied. Save to persist.")
        return True

    def switch_group(self,event):
        wanted=event.control.value
        if not self.apply(quiet=True):
            self.selector.value=self.group
            self.owner.page.update()
            return
        self.group=wanted
        self._render()

    def reset_defaults(self,event=None):
        self.owner.pm._bocda_metadata.setdefault("extensions",{})[self.group]=extensions.defaults(self.group)
        self.canonicalize_hardware()
        self.dirty=False
        self.owner.session.pending_edits=self.owner.field_dirty
        self._render()
        self.owner._refresh_freshness()
        self.owner._set_status("Advanced defaults restored in memory. Save to persist.")

    def prepare_run(self,mode):
        group=extensions.group_for_mode(mode)
        if group is not None:
            self.owner.pm._bocda_metadata.setdefault("extensions",{})[group]=extensions.options_for(
                self.owner.snapshot(),group)
        self.canonicalize_hardware()

    def canonicalize_hardware(self):
        options=self.owner.pm._bocda_metadata.get("extensions",{}).get("quantum")
        if isinstance(options,dict):
            for key in extensions.hardware_options(self.owner.snapshot()):
                options.pop(key,None)

    def sync_hardware(self):
        if self.group!="quantum":
            return
        hardware=extensions.hardware_options(self.owner.snapshot())
        for key,(field,spec) in self.fields.items():
            field.disabled=key in hardware
            if key in hardware:
                field.value=hardware[key] if spec.get("type")=="bool" else str(hardware[key])
