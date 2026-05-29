from __future__ import annotations

import importlib
import inspect
import re
from dataclasses import dataclass
from typing import Any, Iterable

from qureed.interface.project import QureedProject, add_project_to_import_path


def camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


@dataclass(frozen=True)
class DeviceRecord:
    id: str
    class_path: str
    display_name: str
    category: str
    source: str
    device_class: type | None = None
    import_error: str | None = None


BUILTIN_DEVICE_SPECS = (
    (
        "qureed.devices.beam_splittters.perfect_overlap_beamsplitter."
        "PerfectOverlapBeamSplitter",
        "BeamSplitters",
        "Perfect Overlap Beam Splitter",
    ),
    (
        "qureed.devices.clocks.constant_clock.ConstantClock",
        "Clocks",
        "Constant Clock",
    ),
    (
        "qureed.devices.detectors.ideal_detector.IdealDetector",
        "Detectors",
        "Ideal Detector",
    ),
    (
        "qureed.devices.detectors.imperfect_detector.ImperfectDetector",
        "Detectors",
        "Imperfect Detector",
    ),
    (
        "qureed.devices.fibers.lossy_fiber.LossyFiber",
        "Fibers",
        "Lossy Fiber",
    ),
    (
        "qureed.devices.optical_sources.ideal_n_photon_source."
        "IdealNPhotonSource",
        "OpticalSources",
        "Ideal n-photon source",
    ),
    (
        "qureed.devices.optical_sources.qd_entangled_photon_source."
        "QDEntangledPhotonSource",
        "OpticalSources",
        "QD Entangled Photon Source",
    ),
    (
        "qureed.devices.phase_shifters.ideal_phase_shifter.IdealPhaseShifter",
        "PhaseShifters",
        "Ideal Phase Shifter",
    ),
    (
        "qureed.devices.waveplates.ideal_tunable_waveplate."
        "IdealTunableWaveplate",
        "Waveplates",
        "Ideal Tunable Waveplate",
    ),
)


class DeviceDiscoveryError(RuntimeError):
    pass


class DeviceProvider:
    source: str

    def discover(self) -> Iterable[DeviceRecord]:
        raise NotImplementedError


class BuiltinDeviceProvider(DeviceProvider):
    source = "builtin"

    def discover(self) -> Iterable[DeviceRecord]:
        for class_path, category, display_name in BUILTIN_DEVICE_SPECS:
            device_class, import_error = try_import_class(class_path)
            yield build_device_record(
                device_class=device_class,
                category=category,
                source=self.source,
                class_path=class_path,
                display_name=display_name,
                import_error=import_error,
            )


class ProjectDeviceProvider(DeviceProvider):
    source = "project"

    def __init__(self, project: QureedProject | None):
        self.project = project

    def discover(self) -> Iterable[DeviceRecord]:
        if self.project is None:
            return

        add_project_to_import_path(self.project)
        for class_path in self.project.device_class_paths:
            device_class, import_error = try_import_class(class_path)
            yield build_device_record(
                device_class=device_class,
                category="Project",
                source=self.source,
                class_path=class_path,
                import_error=import_error,
            )


class DeviceRegistry:
    def __init__(self, providers: Iterable[DeviceProvider]):
        self.providers = tuple(providers)
        self._records: list[DeviceRecord] | None = None

    def all(self) -> list[DeviceRecord]:
        if self._records is None:
            records: list[DeviceRecord] = []
            for provider in self.providers:
                records.extend(provider.discover())
            self._records = sorted(records, key=lambda item: item.class_path)
        return list(self._records)

    def find(self, identifier: str) -> DeviceRecord:
        matches = [
            record
            for record in self.all()
            if identifier
            in {
                record.id,
                record.class_path,
                f"{record.source}:{record.id}",
                f"{record.source}:{record.class_path}",
            }
        ]
        if not matches:
            raise KeyError(identifier)
        if len(matches) > 1:
            options = ", ".join(record.class_path for record in matches)
            raise DeviceDiscoveryError(
                f"Device identifier '{identifier}' is ambiguous: {options}"
            )
        return matches[0]


def build_registry(project: QureedProject | None = None) -> DeviceRegistry:
    return DeviceRegistry(
        [BuiltinDeviceProvider(), ProjectDeviceProvider(project)]
    )


def import_class(class_path: str) -> type:
    module_name, separator, class_name = class_path.rpartition(".")
    if not separator:
        raise DeviceDiscoveryError(
            f"Device class path must include a module: {class_path}"
        )
    module = importlib.import_module(module_name)
    obj = getattr(module, class_name)
    if not inspect.isclass(obj):
        raise DeviceDiscoveryError(f"{class_path} is not a class")
    return obj


def try_import_class(class_path: str) -> tuple[type | None, str | None]:
    try:
        return import_class(class_path), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def build_device_record(
    device_class: type | None,
    category: str,
    source: str,
    class_path: str | None = None,
    display_name: str | None = None,
    import_error: str | None = None,
) -> DeviceRecord:
    if device_class is None and class_path is None:
        raise DeviceDiscoveryError("Device records need a class or class path")
    resolved_class_path = class_path or class_path_for(device_class)
    class_name = resolved_class_path.rsplit(".", 1)[-1]
    return DeviceRecord(
        id=camel_to_snake(class_name),
        class_path=resolved_class_path,
        display_name=display_name
        or (
            read_device_display_name(device_class)
            if device_class is not None
            else None
        )
        or class_name,
        category=category,
        source=source,
        device_class=device_class,
        import_error=import_error,
    )


def class_path_for(device_class: type) -> str:
    return f"{device_class.__module__}.{device_class.__name__}"


def read_device_display_name(device_class: type) -> str:
    value = read_property_without_instance(device_class, "gui_name")
    if isinstance(value, str):
        return value
    return device_class.__name__


def read_property_without_instance(device_class: type, name: str) -> Any:
    for cls in device_class.__mro__:
        attr = cls.__dict__.get(name)
        if isinstance(attr, property) and attr.fget is not None:
            try:
                return attr.fget(None)
            except Exception:
                return None
    return None


def describe_device(record: DeviceRecord) -> dict[str, Any]:
    device_class = record.device_class
    import_error = record.import_error
    if device_class is None:
        device_class, import_error = try_import_class(record.class_path)
    return {
        "id": record.id,
        "source": record.source,
        "class_path": record.class_path,
        "display_name": record.display_name,
        "category": record.category,
        "properties": describe_properties(
            getattr(device_class, "properties", {}) if device_class else {}
        ),
        "ports": describe_ports(
            getattr(device_class, "port_definitions", {})
            if device_class
            else {}
        ),
        "doc": inspect.getdoc(device_class) if device_class else "",
        "warnings": [import_error] if import_error else [],
    }


def describe_properties(properties: dict[str, dict[str, Any]]) -> list[dict]:
    described = []
    for name, metadata in properties.items():
        value_type = metadata.get("type")
        described.append(
            {
                "name": name,
                "type": getattr(value_type, "__name__", str(value_type)),
                "default": metadata.get("value"),
            }
        )
    return described


def describe_ports(ports: dict[str, Any]) -> list[dict]:
    described = []
    for name, port in ports.items():
        signal_type = getattr(port, "signal_type", None)
        described.append(
            {
                "name": name,
                "direction": getattr(port, "direction", None),
                "signal_type": (
                    class_path_for(signal_type)
                    if inspect.isclass(signal_type)
                    else str(signal_type)
                ),
            }
        )
    return described
