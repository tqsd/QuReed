"""Topology and native-scheduler regression checks independent of the GUI."""
import copy
import unittest

from bocda_model import project
from bocda_model.runner import _assemble, _assembled_snapshot


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.scheme = project.default_scheme()

    def test_default_dimensions_and_source_convention(self):
        c = project.config_from_scheme(self.scheme)
        self.assertEqual(len(self.scheme["devices"]), 19)
        self.assertEqual(len(c["segments"]), 4)
        self.assertAlmostEqual(sum(s["length_m"] for s in c["segments"]), .4)
        self.assertEqual(c["fm"]["excursion_convention"], "peak-to-peak")
        self.assertEqual(c["segments"][2]["resonance_hz"], 10.90e9)

    def test_rewiring_not_list_order_controls_fiber_order(self):
        before = project.config_from_scheme(self.scheme)
        fibers = [d for d in self.scheme["devices"] if d["device"] == "fiber_segment.FiberSegment"]
        a, b = fibers[0]["uuid"], fibers[2]["uuid"]
        for connection in self.scheme["connections"]:
            for end in connection["conn"]:
                end["device_uuid"] = {a:b,b:a}.get(end["device_uuid"],end["device_uuid"])
        after = project.config_from_scheme(self.scheme)
        self.assertEqual(before["segments"][2]["resonance_hz"], after["segments"][0]["resonance_hz"])
        self.scheme["devices"].reverse()
        self.assertEqual(project.config_from_scheme(self.scheme), after)

    def test_incomplete_edit_can_save_but_cannot_run(self):
        self.scheme["connections"].pop()
        self.assertTrue(project.validate_scheme(self.scheme, complete=False))
        with self.assertRaisesRegex(ValueError, "Connect"):
            project.config_from_scheme(self.scheme)

    def test_crossed_counterpropagation_rejected(self):
        conn = next(c for c in self.scheme["connections"] if
                    c["conn"][0]["port"] == "probe_out" and
                    c["conn"][1]["port"] == "probe_in" and
                    c["conn"][0]["device_uuid"] == project.uid("fiber3"))
        other = next(c for c in self.scheme["connections"] if
                     c["conn"][0]["port"] == "probe_out" and
                     c["conn"][0]["device_uuid"] == project.uid("fiber4"))
        conn["conn"][1], other["conn"][1] = other["conn"][1], conn["conn"][1]
        with self.assertRaisesRegex(ValueError, "Probe must traverse"):
            project.validate_scheme(self.scheme)

    def test_untrusted_device_imports_are_not_executed(self):
        self.scheme["devices"][0]["device"] = "os.system"
        with self.assertRaisesRegex(ValueError, "Unsupported device"):
            project.validate_scheme(self.scheme)

    def test_nonfinite_invalid_values_and_duplicate_ports_rejected(self):
        self.scheme["devices"][0]["values"]["frequency_hz"] = float("nan")
        with self.assertRaisesRegex(ValueError, "invalid frequency_hz"):
            project.validate_scheme(self.scheme)
        self.scheme = project.default_scheme()
        self.scheme["connections"].append(copy.deepcopy(self.scheme["connections"][0]))
        with self.assertRaisesRegex(ValueError, "more than once"):
            project.validate_scheme(self.scheme)

    def test_independent_native_registry_preserves_live_simulation(self):
        from qureed.simulation import Simulation
        from cw_laser import CwLaser
        live = Simulation.get_instance()
        marker = CwLaser(name="Existing user device")
        existing = list(live.devices)
        source = copy.deepcopy(self.scheme)
        first, second = _assemble(self.scheme), _assemble(self.scheme)
        self.assertIs(Simulation.get_instance(),live)
        self.assertEqual(live.devices, existing)
        self.assertEqual(self.scheme,source)
        self.assertIsNot(first.simulation, second.simulation)
        key = self.scheme["devices"][0]["uuid"]
        self.assertIsNot(first.devices[key],second.devices[key])
        self.assertIs(marker.simulation,live)
        for registry in (first,second):
            self.assertEqual(project.config_from_scheme(_assembled_snapshot(source,registry)),
                             project.config_from_scheme(source))
            self.assertFalse(registry.simulation.event_queue)
        live.devices.remove(marker.ref)

    def test_custom_parameters_survive_native_assembly(self):
        segment = next(d for d in self.scheme["devices"] if d["device"]=="fiber_segment.FiberSegment")
        segment["values"]["length_m"] = .12
        segment["values"]["resonance_hz"] = 10.87e9
        registry = _assemble(self.scheme)
        c = project.config_from_scheme(_assembled_snapshot(self.scheme,registry))
        self.assertEqual(c["segments"][0]["length_m"],.12)
        self.assertEqual(c["segments"][0]["resonance_hz"],10.87e9)

    def test_optical_and_receiver_scaling(self):
        import numpy as np
        from bocda_model.physics import simulate
        config = project.config_from_scheme(self.scheme)
        config["scan"].update(frequency_start_hz=10.80e9, frequency_stop_hz=10.95e9,
                              frequency_step_hz=5e6)
        base = np.asarray(simulate(config)["spectra_r_v"])
        more_pump = copy.deepcopy(config)
        more_pump["pump"]["edfa_gain_db"] += 10*np.log10(1.5)
        np.testing.assert_allclose(simulate(more_pump)["spectra_r_v"], 1.5*base, rtol=1e-12)
        more_probe = copy.deepcopy(config)
        more_probe["probe"]["eom_loss_db"] -= 10*np.log10(1.5)
        np.testing.assert_allclose(simulate(more_probe)["spectra_r_v"], 1.5*base, rtol=1e-12)
        more_receiver = copy.deepcopy(config)
        more_receiver["receiver"]["transimpedance_v_a"] *= 2
        np.testing.assert_allclose(simulate(more_receiver)["spectra_r_v"], 2*base, rtol=1e-12)


if __name__ == "__main__":
    unittest.main()
