"""Regression checks for native GUI values/topology, reload, and stale results."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bocda_model.integration import SnapshotSession, discover_device, parse_parameter
from bocda_model.project import ROOT, default_scheme, load, save


class FakePage:
    """No display server: exercise actual native GUI objects and callbacks."""
    def __init__(self):
        self.controls = []
        self.jobs = []

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        pass

    def run_thread(self, function, *args):
        self.jobs.append((function, args))


class GuiContractTests(unittest.TestCase):
    def test_parameter_parser_rejects_nonfinite_fractional_integer_and_ranges(self):
        for raw in ("nan", "inf", "-inf"):
            with self.assertRaises(ValueError):
                parse_parameter(raw, {"type": "float"})
        with self.assertRaises(ValueError):
            parse_parameter("1.5", {"type": "int"})
        with self.assertRaises(ValueError):
            parse_parameter("2", {"type": "float", "max": 1})
        self.assertEqual(parse_parameter("3", {"type": "int"}), 3)
        self.assertFalse(parse_parameter("false", {"type": "bool"}))

    def test_discovery_keeps_wrapped_devices_and_skips_utilities(self):
        self.assertEqual(discover_device(ROOT, "fiber_segment.py").__name__, "FiberSegment")
        self.assertIsNone(discover_device(ROOT, "bocda_model/gui.py"))
        self.assertIsNone(discover_device(ROOT, "bocda_model/integration.py"))

    def test_external_disk_edits_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experiment.json"
            scheme = default_scheme()
            save(path, scheme)
            session = SnapshotSession(path)
            session.open()
            external = copy.deepcopy(scheme)
            external["devices"][0]["values"]["frequency_hz"] = 700000.0
            save(path, external)
            with self.assertRaisesRegex(RuntimeError, "outside this window"):
                session.save(scheme)
            self.assertEqual(load(path), external)

    def test_measurements_become_stale_for_values_topology_or_pending_edits(self):
        scheme = default_scheme()
        session = SnapshotSession(Path("unused.json"))
        session.complete(scheme, {"mode": "local"}, {})
        self.assertTrue(session.results_current(scheme))
        altered = copy.deepcopy(scheme)
        altered["devices"][0]["values"]["frequency_hz"] += 50
        self.assertFalse(session.results_current(altered))
        altered = copy.deepcopy(scheme)
        altered["connections"].pop()
        self.assertFalse(session.results_current(altered))
        session.pending_edits = True
        self.assertFalse(session.results_current(scheme))

    @patch("flet.Control.update", lambda self: None)
    def test_native_board_parameter_save_reload_and_counterpropagating_ports(self):
        from bocda_model.gui import BocdaGui
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experiment.json"
            source = default_scheme()
            save(path, source)
            gui = BocdaGui(FakePage(), Path(directory))
            self.assertIn("Loaded", gui.status.value)
            captured = gui.snapshot()
            self.assertEqual(captured, source)
            fiber = next(item for item in gui.board.content.controls
                         if getattr(item.device_instance, "model_role", "") == "segment")
            # The native editor uses real input/output ports on physical sides.
            self.assertEqual(fiber.get_port("pump_in").side, "LEFT")
            self.assertEqual(fiber.get_port("probe_in").side, "RIGHT")
            gui.select_device(fiber)
            control, _ = gui.fields["resonance_hz"]
            control.value = "10870000000"
            gui.pending_field()
            self.assertTrue(gui.save())
            gui.reload()
            self.assertIn("Loaded", gui.status.value)
            reopened = next(item for item in gui.board.content.controls
                            if item.device_instance.ref.uuid == fiber.device_instance.ref.uuid)
            self.assertEqual(reopened.device_instance.values["resonance_hz"], 10.87e9)
            self.assertEqual(gui.snapshot()["connections"], source["connections"])
            self.assertEqual(gui.snapshot()["devices"][0]["location"], source["devices"][0]["location"])

    @patch("flet.Control.update", lambda self: None)
    def test_run_dispatches_saved_snapshot_and_rejects_broken_topology(self):
        from bocda_model.gui import BocdaGui
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experiment.json"
            save(path, default_scheme())
            page = FakePage()
            gui = BocdaGui(page, Path(directory))
            gui.run("local")
            self.assertEqual(len(page.jobs), 1)
            _, (executed, mode, _) = page.jobs[0]
            self.assertEqual(executed, load(path))
            self.assertEqual(mode, "local")
            self.assertTrue(gui.session.running)
            gui.session.running = False
            gui.board.sim_wrapper.signals.pop()
            gui.run("local")
            self.assertEqual(len(page.jobs), 1)
            self.assertIn("Cannot run", gui.status.value)

    @patch("flet.Control.update", lambda self: None)
    def test_gui_worker_matches_cli_pipeline_and_repeated_run_isolation(self):
        import numpy as np
        from bocda_model.gui import BocdaGui
        from bocda_model.runner import execute_snapshot
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experiment.json"
            save(path, default_scheme())
            gui = BocdaGui(FakePage(), Path(directory))
            gui.run("local")
            function, arguments = gui.page.jobs.pop()
            function(*arguments)
            self.assertIn("Completed", gui.status.value)
            self.assertTrue(gui.session.results_current(gui.snapshot()))
            self.assertTrue(gui.result_body.visible)
            self.assertFalse(gui.session.running)
            self.assertFalse(gui.board_surface.disabled)
            cli, _ = execute_snapshot(load(path), mode="local")
            np.testing.assert_allclose(gui.session.last_result["spectra_x_v"],
                                       cli["spectra_x_v"], rtol=0, atol=0)
            gui.run("local")
            function, arguments = gui.page.jobs.pop()
            function(*arguments)
            self.assertIn("Completed", gui.status.value)
            np.testing.assert_allclose(gui.session.last_result["spectra_x_v"],
                                       cli["spectra_x_v"], rtol=0, atol=0)
            self.assertEqual(gui.session.last_result["execution"]["remaining_events"], 0)


if __name__ == "__main__":
    unittest.main()
