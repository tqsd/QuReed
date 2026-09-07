"""Real nonideal result exports: serialization, units, row counts, figures and links."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image
from test_physics import example_config
from bocda_model.nonideal import simulate_nonideal
from bocda_model.physics import simulate
from bocda_model.results import save_results
from bocda_model.nonideal_results import save_nonideal_diagnostics


class NonidealResultExports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=example_config()
        cls.config['scan'].update(start_m=.15,stop_m=.25,step_m=.1,cell_m=.01,
                                  frequency_start_hz=10.8e9,frequency_stop_hz=10.95e9,frequency_step_hz=10e6)
        cls.result=simulate_nonideal(cls.config,{'trace_samples':256,'seed':1337},'scan')
        cls.result['extension_kind']='nonideal'
        cls.temp=tempfile.TemporaryDirectory(prefix='bocda-nonideal-export-')
        cls.paths=save_results(cls.result,Path(cls.temp.name)/'nonideal')

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def rows(self,key):
        with open(self.paths[key],newline='',encoding='utf-8') as stream:
            return list(csv.DictReader(stream))

    def test_full_result_is_strict_json_safe(self):
        # Regression: gain_spectra previously retained an ndarray per position.
        snapshot=json.loads(json.dumps(self.result,allow_nan=False))
        self.assertIsInstance(snapshot['gain_spectra'][0],list)
        saved=json.loads(Path(self.paths['json']).read_text(encoding='utf-8'))
        self.assertEqual(saved['gain_spectra'],snapshot['gain_spectra'])

    def test_settings_and_manifest_preserve_options_and_paths(self):
        settings=json.loads(Path(self.paths['config']).read_text(encoding='utf-8'))
        self.assertEqual(settings['extensions']['nonideal']['seed'],1337)
        self.assertEqual(settings['extensions']['nonideal']['trace_samples'],256)
        self.assertEqual(settings['laser'],self.config['laser'])
        self.assertNotIn('extensions',self.config)
        manifest=json.loads(Path(self.paths['manifest']).read_text(encoding='utf-8'))
        self.assertEqual(manifest,self.paths)
        for path in manifest.values():
            self.assertTrue(Path(path).is_absolute())
            self.assertTrue(Path(path).is_file())

    def test_csv_rows_units_and_signed_sidebands(self):
        details=self.result['nonideal']
        expected={'nonideal_pump_eom_csv':len(details['pump_eom']['phase_rad']),
                  'nonideal_probe_sidebands_csv':len(details['probe_eom']['components']),
                  'nonideal_edfa_csv':len(details['edfa_trace']['time_s']),
                  'nonideal_source_noise_csv':256,
                  'nonideal_polarization_csv':len(details['polarization']['z_m']),
                  'nonideal_polarization_scan_csv':len(self.result['positions_m'])*len(details['polarization']['z_m']),
                  'nonideal_detector_noise_csv':len(self.result['positions_m'])*len(self.result['frequency_hz']),
                  'nonideal_interaction_csv':len(self.result['positions_m'])*len(self.result['frequency_hz'])}
        for key,count in expected.items(): self.assertEqual(len(self.rows(key)),count,key)
        self.assertIn('pump_phase_rad',self.rows('nonideal_source_noise_csv')[0])
        self.assertIn('input_power_w',self.rows('nonideal_edfa_csv')[0])
        for row in self.rows('nonideal_probe_sidebands_csv'):
            n=int(row['optical_sideband_order']); fraction=float(row['power_fraction']); signed=float(row['signed_sbs_power_fraction'])
            self.assertGreaterEqual(fraction,0)
            self.assertAlmostEqual(signed,-np.sign(n)*fraction)

    def test_noise_csv_contributions_sum_and_statistics_units(self):
        for row in self.rows('nonideal_detector_noise_csv'):
            total=float(row['total_one_sided_voltage_psd_v2_hz'])
            parts=sum(float(row[name+'_one_sided_voltage_psd_v2_hz']) for name in ['shot','shared_rin','electronic','signal_ase','ase_ase'])
            self.assertAlmostEqual(parts/total,1,places=12)
            sigma=float(row['stationary_iq_sigma_peak_v'])
            factor=self.result['nonideal']['detector']['stationary_IQ_variance_per_psd_hz']
            self.assertAlmostEqual(sigma*sigma/(total*factor),1,places=12)

    def test_pngs_are_decodable_nonempty_and_linked(self):
        report=Path(self.paths['report']).read_text(encoding='utf-8')
        keys=[key for key in self.paths if key.startswith('nonideal_') and key.endswith('_plot')]
        self.assertEqual(len(keys),5)
        for key in keys:
            path=Path(self.paths[key])
            self.assertGreater(path.stat().st_size,10000)
            with Image.open(path) as picture:
                self.assertEqual(picture.format,'PNG')
                self.assertGreater(picture.width,900)
                low,high=picture.convert('L').getextrema()
                self.assertGreater(high-low,100)
            self.assertIn(path.name,report)
        for key,path in self.paths.items():
            if key.startswith('nonideal_') and str(path).endswith('.csv'):
                self.assertIn(Path(path).name,report)
        self.assertIn('clean FM reference',report)
        self.assertIn('not the nonideal point-spread function',report)
        self.assertIn('anti-Stokes',report)
        self.assertIn('clipping',report)
        self.assertIn('Fit flags',report)

    def test_baseline_exports_unchanged_and_disabled_supplement_is_empty(self):
        baseline=simulate(self.config)
        paths=save_results(baseline,Path(self.temp.name)/'baseline')
        self.assertEqual(len(paths),10)
        self.assertFalse(any(k.startswith('nonideal_') for k in paths))
        self.assertEqual(json.loads(Path(paths['config']).read_text(encoding='utf-8')),self.config)
        self.assertEqual(save_nonideal_diagnostics({'nonideal':{'enabled':False}},Path(self.temp.name)/'disabled'),{})

    def test_real_drift_ram_histories_csv_pngs_and_settings(self):
        options={'trace_samples':256,'seed':1337,'source_ram_depth':.08,'source_ram_phase_deg':43.,
                 'pump_bias_drift_deg_s':1.,'probe_bias_drift_deg_s':-.5}
        result=simulate_nonideal(self.config,options,'scan');result['extension_kind']='nonideal'
        json.dumps(result,allow_nan=False)
        paths=save_results(result,Path(self.temp.name)/'drift-ram')
        settings=json.loads(Path(paths['config']).read_text(encoding='utf-8'))
        for key,value in options.items():self.assertEqual(settings['extensions']['nonideal'][key],value)
        for key in ['nonideal_bias_drift_plot','nonideal_ram_plot']:
            path=Path(paths[key]);self.assertGreater(path.stat().st_size,10000)
            with Image.open(path) as picture:
                self.assertGreater(picture.width,900);self.assertEqual(picture.format,'PNG')
        history=result['nonideal']['bias_history'];ram=result['nonideal']['ram']
        expectations={'nonideal_bias_drift_csv':(len(history['time_s']),'pump_bias_deg'),
                      'nonideal_ram_csv':(len(ram['source_trace']['time_s']),'pump_intensity_multiplier'),
                      'nonideal_ram_floquet_csv':(len(result['positions_m'])*len(ram['z_m']),'mean_intensity_product')}
        for key,(count,column) in expectations.items():
            with open(paths[key],newline='',encoding='utf-8') as stream:rows=list(csv.DictReader(stream))
            self.assertEqual(len(rows),count);self.assertIn(column,rows[0])
            if key=='nonideal_bias_drift_csv':
                self.assertEqual(float(rows[-1]['time_s']),history['time_s'][-1])
                self.assertEqual(float(rows[-1]['probe_bias_deg']),history['probe_bias_deg'][-1])
            if key=='nonideal_ram_floquet_csv':
                for row in rows:
                    self.assertAlmostEqual(float(row['mean_intensity_product']),float(row['summed_fourier_power']),places=12)
        report=Path(paths['report']).read_text(encoding='utf-8')
        for key in ['nonideal_bias_drift_plot','nonideal_ram_plot',*expectations]:
            self.assertIn(Path(paths[key]).name,report)
        self.assertIn('not full cyclostationary',report)


if __name__=='__main__': unittest.main()
