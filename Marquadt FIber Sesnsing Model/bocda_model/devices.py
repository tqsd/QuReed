"""Native QuReed components for a steady-state BOCDA boundary-value experiment.

Ports are real QuReed ports. They define the topology consumed by the global
two-direction solver, not a claim that independent feed-forward devices solve SBS.
"""
from qureed.devices import GenericDevice
from qureed.devices.port import Port
from qureed.signals.generic_signal import GenericSignal


class OpticalSignal(GenericSignal):
    """Classical optical envelope boundary, shared modulation provenance retained."""


class ElectricalSignal(GenericSignal):
    """Control/reference/readout connection, never an optical quantum state."""


def ports(**entries):
    return {name: Port(name, direction, None,
                       OpticalSignal if kind == "optical" else ElectricalSignal, None)
            for name, (direction, kind) in entries.items()}


def spec(label, unit="", kind="float", **limits):
    return dict(label=label, unit=unit, type=kind, **limits)


class ModelDevice(GenericDevice):
    ports = {}
    gui_name = "BOCDA device"
    gui_icon = "fiber.png"
    gui_tags = ["BOCDA"]
    reference = None
    values = {}
    parameter_schema = {}
    model_role = ""
    optional_ports = ()

    def des_action(self, time, **kwargs):
        raise RuntimeError("This component participates in the coupled BOCDA solver. "
                           "Run the project Scan controller through the project launcher.")


class FmGenerator(ModelDevice):
    gui_name = "Laser FM generator"
    gui_icon = "clock_trigger.png"
    model_role = "fm"
    ports = ports(control=("input", "electrical"), fm=("output", "electrical"),
                  lo_fm=("output", "electrical"))
    optional_ports = ("lo_fm",)
    values = dict(frequency_hz=699e3, excursion_hz=47e9,
                  excursion_convention="peak-to-peak", group_velocity_m_s=2.04e8,
                  delay_s=1/699e3, correlation_order=1, phase_rad=0)
    parameter_schema = dict(
        frequency_hz=spec("Nominal FM (delay/fixed control mode)", "Hz", min=1),
        excursion_hz=spec("Optical excursion (selected convention)", "Hz", min=0),
        excursion_convention=spec("Excursion convention", kind="enum", choices=["peak-to-peak", "peak"]),
        group_velocity_m_s=spec("Fiber group velocity", "m/s", min=1),
        delay_s=spec("External pump minus probe delay", "s"),
        correlation_order=spec("Correlation order", kind="int"),
        phase_rad=spec("Common modulation phase", "rad"))


class CwLaser(ModelDevice):
    gui_name = "Shared FM CW laser"
    gui_icon = "laser.png"
    model_role = "laser"
    ports = ports(fm=("input", "electrical"), optical=("output", "optical"))
    values = dict(power_w=.02, wavelength_nm=1550)
    parameter_schema = dict(power_w=spec("Source optical power", "W", min=0),
                            wavelength_nm=spec("Optical wavelength", "nm", min=1))


class Splitter(ModelDevice):
    gui_name = "50:50 power splitter"
    gui_icon = "beam_splitter.png"
    model_role = "splitter"
    ports = ports(optical=("input", "optical"), pump=("output", "optical"),
                  probe=("output", "optical"))
    values = dict(pump_fraction=.5, loss_db=0)
    parameter_schema = dict(pump_fraction=spec("Pump power fraction", min=0, max=1),
                            loss_db=spec("Insertion loss", "dB", min=0))


class PumpReference(ModelDevice):
    gui_name = "Pump AM / lock-in reference"
    gui_icon = "clock_trigger.png"
    model_role = "pump_reference"
    ports = ports(modulation=("output", "electrical"), reference=("output", "electrical"))
    values = dict(modulation_hz=100e3, phase_deg=0)
    parameter_schema = dict(modulation_hz=spec("Pump tag frequency", "Hz", min=1),
                            phase_deg=spec("Pump tag phase", "deg"))


class PumpEom(ModelDevice):
    gui_name = "Pump intensity EOM"
    gui_icon = "phase_shift.png"
    model_role = "pump_eom"
    ports = ports(optical=("input", "optical"), modulation=("input", "electrical"),
                  pump=("output", "optical"))
    values = dict(eom_loss_db=3, modulation_depth=.2)
    parameter_schema = dict(eom_loss_db=spec("Mean insertion loss", "dB", min=0),
                            modulation_depth=spec("Intensity AM depth (linear model)", min=0, max=.3))


class Edfa(ModelDevice):
    gui_name = "Pump EDFA"
    gui_icon = "excitation.png"
    model_role = "edfa"
    ports = ports(pump_in=("input", "optical"), pump_out=("output", "optical"))
    values = dict(edfa_gain_db=13, edfa_max_w=.2)
    parameter_schema = dict(edfa_gain_db=spec("Power gain", "dB"),
                            edfa_max_w=spec("Maximum output power", "W", min=1e-9))


class ProbeRfGenerator(ModelDevice):
    gui_name = "Probe microwave sweep"
    gui_icon = "clock_trigger.png"
    model_role = "probe_rf"
    ports = ports(control=("input", "electrical"), rf=("output", "electrical"),
                  lo_rf=("output", "electrical"))
    optional_ports = ("lo_rf",)
    values = dict(frequency_start_hz=10.6e9, frequency_stop_hz=11.1e9, frequency_step_hz=2e6)
    parameter_schema = dict(frequency_start_hz=spec("Offset sweep start", "Hz", min=1),
                            frequency_stop_hz=spec("Offset sweep stop", "Hz", min=1),
                            frequency_step_hz=spec("Offset sweep step", "Hz", min=1))


class ProbeEom(ModelDevice):
    gui_name = "Probe selected-sideband EOM"
    gui_icon = "phase_shift.png"
    model_role = "probe_eom"
    ports = ports(optical=("input", "optical"), rf=("input", "electrical"),
                  probe=("output", "optical"))
    values = dict(eom_loss_db=20)
    parameter_schema = dict(eom_loss_db=spec("Selected sideband effective loss", "dB", min=0))


class PolarizationController(ModelDevice):
    gui_name = "Polarization controller"
    gui_icon = "fiber.png"
    model_role = "pc"
    ports = ports(probe_in=("input", "optical"), probe_out=("output", "optical"))
    values = dict(pc_overlap=1)
    parameter_schema = dict(pc_overlap=spec("SBS polarization overlap", min=0, max=1))


class OpticalIsolator(ModelDevice):
    gui_name = "Probe isolator"
    gui_icon = "sorter.png"
    model_role = "isolator"
    ports = ports(probe_in=("input", "optical"), probe_out=("output", "optical"))
    values = dict(isolator_loss_db=.5)
    parameter_schema = dict(isolator_loss_db=spec("Forward loss; ideal reverse blocking", "dB", min=0))


class Circulator(ModelDevice):
    gui_name = "Circulator (1 to 2, 2 to 3)"
    gui_icon = "reverse_switch.png"
    model_role = "circulator"
    ports = ports(pump_in=("input", "optical"), pump_out=("output", "optical"),
                  probe_in=("input", "optical"), detector_out=("output", "optical"))
    gui_port_sides = dict(pump_in="left", pump_out="right", probe_in="right", detector_out="left")
    values = dict(circulator_loss_db=.5)
    parameter_schema = dict(circulator_loss_db=spec("Loss for each routed pass", "dB", min=0))


class FiberSegment(ModelDevice):
    gui_name = "Bidirectional SBS fiber"
    gui_icon = "fiber.png"
    model_role = "segment"
    ports = ports(pump_in=("input", "optical"), pump_out=("output", "optical"),
                  probe_in=("input", "optical"), probe_out=("output", "optical"))
    gui_port_sides = dict(pump_in="left", pump_out="right", probe_in="right", probe_out="left")
    values = dict(length_m=.1, resonance_hz=10.85e9, linewidth_hz=27e6,
                  gain_per_w_m=.5, attenuation_db_km=.2)
    parameter_schema = dict(length_m=spec("Physical segment length", "m", min=1e-6),
                            resonance_hz=spec("Local Brillouin resonance", "Hz", min=1),
                            linewidth_hz=spec("Intrinsic gain FWHM", "Hz", min=1),
                            gain_per_w_m=spec("Effective SBS gain coefficient", "1/(W m)", min=0),
                            attenuation_db_km=spec("Power attenuation", "dB/km", min=0))


class PumpTerminator(ModelDevice):
    gui_name = "Pump output monitor / termination"
    gui_icon = "detector.png"
    model_role = "termination"
    ports = ports(pump=("input", "optical"))


class Photodetector(ModelDevice):
    gui_name = "Probe photodetector"
    gui_icon = "detector.png"
    model_role = "pd"
    ports = ports(probe=("input", "optical"), voltage=("output", "electrical"))
    values = dict(responsivity_a_w=.9, transimpedance_v_a=1e4,
                  bandwidth_hz=1.1e6, max_voltage_v=10)
    parameter_schema = dict(responsivity_a_w=spec("Responsivity", "A/W", min=1e-9),
                            transimpedance_v_a=spec("Transimpedance", "V/A", min=1e-9),
                            bandwidth_hz=spec("Single-pole detector bandwidth", "Hz", min=1),
                            max_voltage_v=spec("Voltage limit", "V", min=1e-9))


class LockIn(ModelDevice):
    gui_name = "Dual-phase lock-in"
    gui_icon = "histogram.png"
    model_role = "lia"
    ports = ports(voltage=("input", "electrical"), reference=("input", "electrical"),
                  measurement=("output", "electrical"))
    values = dict(reference_phase_deg=0, time_constant_s=.001, filter_order=1, dwell_s=.01)
    parameter_schema = dict(reference_phase_deg=spec("Reference phase", "deg"),
                            time_constant_s=spec("RC time constant", "s", min=1e-9),
                            filter_order=spec("Cascaded RC stages", kind="int", min=1, max=4),
                            dwell_s=spec("Dwell per spectral point", "s", min=1e-9))


class ScanController(ModelDevice):
    gui_name = "BOCDA scan and result controller"
    gui_icon = "optical_memory_decoder.png"
    model_role = "scan"
    ports = ports(fm_control=("output", "electrical"), rf_control=("output", "electrical"),
                  measurement=("input", "electrical"))
    values = dict(target_m=.25, start_m=.025, stop_m=.375, step_m=.01,
                  cell_m=.002, position_control="frequency", background_subtraction=False)
    parameter_schema = dict(target_m=spec("Local target position", "m", min=0),
                            start_m=spec("Spatial scan start", "m", min=0),
                            stop_m=spec("Spatial scan stop", "m", min=0),
                            step_m=spec("Spatial scan step", "m", min=1e-6),
                            cell_m=spec("Numerical cell size (not resolution)", "m", min=1e-6),
                            position_control=spec("Position control", kind="enum", choices=["frequency", "delay", "fixed"]),
                            background_subtraction=spec("Background subtraction (unsupported)", kind="bool"))

    def des_action(self, time, **kwargs):
        if not hasattr(self, "execute"):
            raise RuntimeError("Launch through launch_gui.ps1 or python -m bocda_model.runner.")
        self.result = self.execute()


class LocalOscillator(ModelDevice):
    gui_name = "Phase-locked local oscillator"
    gui_icon = "laser.png"
    model_role = "lo"
    description = ("Ideal coherent LO locked to the same FM and probe offset. "
                   "Residual detuning, phase and power-mode overlap are explicit controls.")
    ports = ports(fm=("input", "electrical"), rf=("input", "electrical"),
                  optical=("output", "optical"))
    values = dict(lo_power_w=.01, lo_phase_deg=0, lo_detuning_hz=0, lo_mode_overlap=1)
    parameter_schema = dict(
        lo_power_w=spec("LO optical power at balanced mixer", "W", min=1e-12),
        lo_phase_deg=spec("LO phase relative to selected probe mode", "deg"),
        lo_detuning_hz=spec("Residual LO frequency mismatch", "Hz"),
        lo_mode_overlap=spec("Signal/LO power-mode overlap", min=0, max=1))


class HomodyneReceiver(ModelDevice):
    gui_name = "Balanced homodyne receiver"
    gui_icon = "beam_splitter.png"
    model_role = "pd"
    is_homodyne = True
    description = ("50:50 signal/LO mixing, two photodiodes and subtraction. "
                   "Gaussian mode readout is before optional lock-in filtering.")
    ports = ports(probe=("input", "optical"), lo=("input", "optical"),
                  voltage=("output", "electrical"))
    values = dict(quantum_efficiency=.8, homodyne_transimpedance_v_a=1000,
                  homodyne_max_voltage_v=10, bandwidth_hz=1.1e6)
    parameter_schema = dict(
        quantum_efficiency=spec("Balanced detector quantum efficiency", min=1e-9, max=1),
        homodyne_transimpedance_v_a=spec("Balanced transimpedance", "V/A", min=1e-9),
        homodyne_max_voltage_v=spec("Per-diode and difference voltage limit", "V", min=1e-9),
        bandwidth_hz=spec("Reference photodetector bandwidth", "Hz", min=1))
