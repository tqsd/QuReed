"""Artifact tests use real small classical/quantum and transient solver results."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from bocda_model.advanced_results import save_advanced_results
from bocda_model.extensions import run_model
from bocda_model.project import default_scheme, homodyne_scheme, config_from_scheme


def small_quantum():
    scheme=homodyne_scheme()
    config=config_from_scheme(scheme)
    config["scan"].update(start_m=.15,stop_m=.25,step_m=.1,
                          frequency_start_hz=10.84e9,frequency_stop_hz=10.89e9,
                          frequency_step_hz=5e6,cell_m=.01)
    return run_model(config,scheme,"quantum-scan")


def small_dynamics(convergence=True):
    scheme=default_scheme()
    scheme["extensions"]={"dynamics":{"cells":16,"duration_ns":15.,
        "output_frames":16,"gain_scale":2.,"probe_scale":10.,"fm_enabled":False,
        "convergence_check":convergence}}
    return run_model(config_from_scheme(scheme),scheme,"dynamics")


class AdvancedResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.quantum=small_quantum()
        cls.dynamics=small_dynamics()

    def inspect_pngs(self,paths):
        plots={key:Path(value) for key,value in paths.items() if key.endswith("_plot")}
        self.assertTrue(plots)
        for name,path in plots.items():
            self.assertGreater(path.stat().st_size,10000,name)
            with Image.open(path) as image:
                self.assertGreater(image.width,500)
                self.assertGreater(image.height,300)
                self.assertIn("Description",image.info)
                array=np.asarray(image.convert("RGB"))
                self.assertGreater(float(np.std(array)),10,name)
        return plots

    def test_quantum_exports_real_scan_data_and_units(self):
        with tempfile.TemporaryDirectory(prefix="bocda-quantum-export-") as tmp:
            paths=save_advanced_results(self.quantum,tmp)
            self.assertTrue(all(Path(value).is_absolute() for value in paths.values()))
            data=json.loads(Path(paths["data"]).read_text(encoding="utf-8"))
            settings=json.loads(Path(paths["config"]).read_text(encoding="utf-8"))
            self.assertEqual(data,self.quantum)
            self.assertEqual(settings["configuration"],self.quantum["config"])
            self.assertEqual(settings["extension_options"],self.quantum["extension_options"])
            self.assertEqual(json.loads(Path(paths["manifest"]).read_text(encoding="utf-8")),paths)
            with Path(paths["quantum_spectra_csv"]).open(encoding="utf-8",newline="") as stream:
                rows=list(csv.DictReader(stream))
            q=self.quantum["quantum"]
            self.assertEqual(len(rows),len(q["positions_m"])*len(q["frequency_hz"]))
            self.assertIn("difference_variance_v2",rows[0])
            self.assertAlmostEqual(float(rows[0]["difference_mean_v"]),q["difference_voltage_v"][0][0])
            with Path(paths["quantum_modes_csv"]).open(encoding="utf-8",newline="") as stream:
                modes=list(csv.DictReader(stream))
            self.assertAlmostEqual(sum(float(m["input_photons"]) for m in modes),q["input_total_photons"],places=5)
            plots=self.inspect_pngs(paths)
            self.assertIn("quantum_map_plot",plots)
            html=Path(paths["report"]).read_text(encoding="utf-8")
            for text in ["not quantum Fisher information","not a global optimum","phase","Variance"]:
                # Wording can differ in case between captions and descriptions.
                self.assertIn(text.lower(),html.lower())
            self.assertNotIn('src="C:',html)
            self.assertIn('src="quantum_spectrum.png"',html)

    def test_suppressed_fisher_stays_unavailable_not_zero(self):
        scheme=homodyne_scheme()
        scheme["extensions"]["quantum"]["phase_jitter_std_rad"]=.01
        config=config_from_scheme(scheme)
        config["scan"].update(frequency_start_hz=10.85e9,frequency_stop_hz=10.89e9,frequency_step_hz=1e7,cell_m=.01)
        result=run_model(config,scheme,"quantum")
        self.assertIsNone(result["quantum"]["multimode"]["fisher_information"])
        with tempfile.TemporaryDirectory(prefix="bocda-fi-gated-export-") as tmp:
            paths=save_advanced_results(result,tmp)
            with Path(paths["quantum_fisher_csv"]).open(encoding="utf-8",newline="") as stream:
                rows=list(csv.DictReader(stream))
            self.assertEqual(rows[0]["readout"],"not computed")
            self.assertEqual(rows[0]["total_fi_hz_minus2"],"")
            text=Path(paths["report"]).read_text(encoding="utf-8")
            self.assertIn("non-Gaussian",text)
            self.assertIn("Not evaluated",text)
            self.inspect_pngs(paths)

    def test_dynamics_exports_real_fields_boundary_and_refinement(self):
        with tempfile.TemporaryDirectory(prefix="bocda-dynamics-export-") as tmp:
            paths=save_advanced_results(self.dynamics,tmp)
            data=json.loads(Path(paths["data"]).read_text(encoding="utf-8"))
            self.assertEqual(data,self.dynamics)
            with Path(paths["dynamics_fields_csv"]).open(encoding="utf-8",newline="") as stream:
                rows=list(csv.DictReader(stream))
            self.assertEqual(len(rows),len(data["time_s"])*len(data["z_m"]))
            self.assertIn("normalized_acoustic_real_w",rows[0])
            self.assertAlmostEqual(float(rows[-1]["pump_power_w"]),data["pump_power_w"][-1][-1])
            with Path(paths["dynamics_boundary_csv"]).open(encoding="utf-8",newline="") as stream:
                boundary=list(csv.DictReader(stream))
            self.assertEqual(len(boundary),len(data["boundary_time_s"]))
            self.assertIn("photon_balance_trace_relative",boundary[0])
            text=Path(paths["report"]).read_text(encoding="utf-8")
            for expected in ["not acoustic power","not prove continuum accuracy","retarded no-SBS","refinement"]:
                self.assertIn(expected,text)
            self.inspect_pngs(paths)

    def test_html_escapes_warning_and_configuration_text(self):
        result=small_dynamics(False)
        result["warnings"].append('<script>alert("untrusted")</script>')
        with tempfile.TemporaryDirectory(prefix="bocda-safe-report-") as tmp:
            paths=save_advanced_results(result,tmp)
            text=Path(paths["report"]).read_text(encoding="utf-8")
            self.assertNotIn('<script>alert("untrusted")</script>',text)
            self.assertIn("&lt;script&gt;",text)
            with Image.open(paths["dynamics_refinement_plot"]) as image:
                self.assertIn("refinement",image.info["Description"])
            self.assertNotIn("fine_cells",result["diagnostics"])

    def test_unsupported_kind_fails_before_writing(self):
        with tempfile.TemporaryDirectory(prefix="bocda-invalid-export-") as tmp:
            with self.assertRaises(ValueError):
                save_advanced_results({"extension_kind":"other"},tmp)
            self.assertEqual(list(Path(tmp).iterdir()),[])


if __name__=="__main__":
    unittest.main()

