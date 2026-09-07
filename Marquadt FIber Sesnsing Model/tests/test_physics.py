"""Reproducible physics consistency checks; these are not experimental validation."""
import copy
import unittest
from unittest.mock import patch

import numpy as np

from bocda_model.physics import (ModelError, controls_for_target, fiber_grid,
    floquet_response, floquet_weights, fm_difference_amplitude, lockin_filter,
    power_budget, quasistatic_response, simulate, spatial_diagnostic,
    susceptibilities, validate_config)
from bocda_model.physics import _sample_count


def example_config():
    return {
        'fm': {'frequency_hz': 699e3, 'excursion_hz': 47e9,
               'excursion_convention': 'peak-to-peak', 'group_velocity_m_s': 2.04e8,
               'delay_s': 1/699e3, 'correlation_order': 1, 'phase_rad': 0},
        'laser': {'power_w': .02, 'wavelength_nm': 1550},
        'splitter': {'pump_fraction': .5, 'loss_db': 0},
        'pump': {'eom_loss_db': 3, 'modulation_hz': 1e5, 'modulation_depth': .2,
                 'phase_deg': 0, 'edfa_gain_db': 13, 'edfa_max_w': .2,
                 'circulator_loss_db': .5},
        'probe': {'eom_loss_db': 20, 'pc_overlap': 1, 'isolator_loss_db': .5},
        'segments': [{'name': f'Fiber {i+1}', 'length_m': .1,
                      'resonance_hz': 10.90e9 if i == 2 else 10.85e9,
                      'linewidth_hz': 27e6, 'gain_per_w_m': .5,
                      'attenuation_db_km': .2} for i in range(4)],
        'receiver': {'responsivity_a_w': .9, 'transimpedance_v_a': 1e4,
                     'bandwidth_hz': 1.1e6, 'max_voltage_v': 10,
                     'reference_phase_deg': 0, 'time_constant_s': .001,
                     'filter_order': 1, 'dwell_s': .01},
        'scan': {'target_m': .25, 'start_m': .05, 'stop_m': .35, 'step_m': .1,
                 'frequency_start_hz': 10.6e9, 'frequency_stop_hz': 11.1e9,
                 'frequency_step_hz': 2e6, 'cell_m': .004,
                 'position_control': 'frequency', 'background_subtraction': False}}


class KernelChecks(unittest.TestCase):
    def test_sample_preflight_preserves_endpoint_convention(self):
        for start, stop, step in [(0,.3,.1),(.05,.35,.1),(0,.305,.1),
                                   (10.6e9,11.1e9,2e6),(1,1,.1),
                                   (0,5000,1)]:
            expected=len(np.arange(start,stop+.01*step,step))
            self.assertEqual(_sample_count(start,stop,step,5001,'Test'),expected)

    def test_zero_fm_reduces_to_lorentzian(self):
        d = np.linspace(-50e6, 50e6, 51)
        actual = floquet_response([0], d, 699e3, 27e6)[0]
        np.testing.assert_allclose(actual, 1/(1+(2*d/27e6)**2), atol=1e-14)

    def test_sideband_sum_converges(self):
        beta = np.array([0, .1, 5, 30, 100])
        n, weights = floquet_weights(beta)
        np.testing.assert_allclose(weights[:,0]+2*weights[:,1:].sum(1), 1, atol=1e-12)
        d = [-30e6, 0, 30e6]
        np.testing.assert_allclose(floquet_response(beta,d,699e3,27e6),
                                   floquet_response(beta,d,699e3,27e6,padding=80), atol=1e-12)

    def test_static_limit_and_high_rate_difference(self):
        a = np.array([0,10e6,50e6])
        d = np.linspace(-40e6,40e6,21)
        static = quasistatic_response(a,d,27e6)
        slow = floquet_response(a/699e3,d,699e3,27e6)
        self.assertLess(np.max(np.abs(slow-static)), .001)
        fast = floquet_response(a/27e6,d,27e6,27e6)
        self.assertGreater(np.max(np.abs(fast-static)), .02)

    def test_resonant_tag_susceptibility(self):
        dc, ac = susceptibilities([0], np.array([0]), 699e3, 27e6, 1e5)
        self.assertEqual(dc[0,0], 1)
        expected = .5*(1+1/(1+2j*1e5/27e6))
        self.assertAlmostEqual(abs(ac[0,0]-expected), 0, places=14)

    def test_target_mapping_and_periodic_peaks(self):
        c=example_config()
        for z in [0,.05,.2,.399]:
            p=controls_for_target(c,z)
            self.assertAlmostEqual(p['peak_m'],z,places=10)
            spacing=c['fm']['group_velocity_m_s']/(2*p['frequency_hz'])
            a=fm_difference_amplitude([z,z+spacing],.4,p,c)
            np.testing.assert_allclose(a,0,atol=1e-3)
        c['fm']['correlation_order']=0
        with self.assertRaisesRegex(ModelError,'order-zero'):
            controls_for_target(c,.2)

    def test_dwell_and_cascaded_filter(self):
        actual=lockin_filter(np.ones(2),.001,.001,1)
        np.testing.assert_allclose(actual.real,1-np.exp(-np.array([1,2])))
        actual=lockin_filter(np.ones(1),.001,.001,2)
        self.assertAlmostEqual(actual[0].real,1-2*np.exp(-1))

    def test_resolution_convention_and_range_tradeoff(self):
        c=example_config(); control=controls_for_target(c,.2)
        baseline=spatial_diagnostic(c,control,27e6,301)
        self.assertAlmostEqual(baseline['peak_spacing_m'],145.9227468,places=6)
        self.assertGreater(baseline['fwhm_m'],.04)
        self.assertLess(baseline['fwhm_m'],.05)
        c['fm']['excursion_convention']='peak'
        narrow=spatial_diagnostic(c,control,27e6,301)
        self.assertAlmostEqual(baseline['fwhm_m']/narrow['fwhm_m'],2,places=3)
        control['frequency_hz']/=2
        wider=spatial_diagnostic(c,control,27e6,301)
        self.assertAlmostEqual(wider['peak_spacing_m']/narrow['peak_spacing_m'],2)
        self.assertAlmostEqual(wider['fwhm_m']/narrow['fwhm_m'],2,places=2)


class SimulationChecks(unittest.TestCase):
    def test_huge_sweeps_rejected_before_array_allocation(self):
        cases=[('local',{'frequency_step_hz':1e-300}),
               ('local',{'frequency_stop_hz':1e300,'frequency_step_hz':1e-300}),
               ('scan',{'step_m':1e-300})]
        for mode, fields in cases:
            with self.subTest(mode=mode,fields=fields):
                c=example_config(); c['scan'].update(fields)
                with patch('bocda_model.physics.np.arange',side_effect=AssertionError('Array allocated before preflight')):
                    with self.assertRaisesRegex(ModelError,'samples'):
                        simulate(c,mode)

    def test_huge_fiber_grids_rejected_before_array_allocation(self):
        for length, cell in [(1e300,1e-300),(.1,1e-300),(.1,.4/30001)]:
            with self.subTest(length=length,cell=cell):
                c=example_config(); c['segments'][0]['length_m']=length
                c['scan']['cell_m']=cell
                with patch('bocda_model.physics.np.arange',side_effect=AssertionError('Array allocated before preflight')):
                    with self.assertRaisesRegex(ModelError,'30000 cells'):
                        simulate(c)

    def test_power_budget_and_segment_alignment(self):
        c=example_config(); z,dz,l,b=fiber_grid(c)
        budget,power=power_budget(c,z,dz,l)
        self.assertAlmostEqual(budget['splitter_output_sum_w'],c['laser']['power_w'])
        self.assertAlmostEqual(budget['splitter_pump_w']+budget['splitter_probe_w'],.02)
        np.testing.assert_allclose(b,[0,.1,.2,.3,.4])
        self.assertTrue(np.all(np.diff(power)<=0))
        self.assertAlmostEqual(budget['pump_fiber_input_w'],.1*10**(-.05))

    def test_uniform_fiber_and_altered_segment(self):
        c=example_config()
        changed=simulate(c)
        self.assertLess(abs(changed['fitted_resonance_hz'][0]-10.90e9),4e6)
        for seg in c['segments']: seg['resonance_hz']=10.85e9
        uniform=simulate(c)
        self.assertLess(abs(uniform['fitted_resonance_hz'][0]-10.85e9),1e6)
        self.assertLess(uniform['diagnostics']['estimated_pump_depletion_fraction'],.01)

    def test_zero_gain_and_zero_tag(self):
        c=example_config()
        for seg in c['segments']: seg['gain_per_w_m']=0
        zero=simulate(c)
        np.testing.assert_allclose(zero['spectra_r_v'],0,atol=0)
        self.assertEqual(zero['fits'][0]['flags'],['no_signal'])
        c=example_config(); c['pump']['modulation_depth']=0
        zero=simulate(c)
        np.testing.assert_allclose(zero['spectra_r_v'],0,atol=0)

    def test_phase_rotation_and_repeat_isolation(self):
        c=example_config(); original=simulate(c)
        c['receiver']['reference_phase_deg']=90
        rotated=simulate(c)
        np.testing.assert_allclose(rotated['spectra_x_v'], original['spectra_y_v'],atol=1e-14)
        np.testing.assert_allclose(rotated['spectra_y_v'], -np.array(original['spectra_x_v']),atol=1e-14)
        c['receiver']['reference_phase_deg']=0
        np.testing.assert_allclose(simulate(c)['spectra_r_v'], original['spectra_r_v'],atol=0)

    def test_grid_refinement_and_position_scan(self):
        c=example_config(); coarse=simulate(c,'scan')
        c['scan']['cell_m']/=2
        fine=simulate(c,'scan')
        a,b=np.array(coarse['spectra_r_v']),np.array(fine['spectra_r_v'])
        self.assertLess(np.max(np.abs(a-b))/np.max(b),.005)
        np.testing.assert_allclose(fine['fitted_resonance_hz'],[10.85e9,10.85e9,10.90e9,10.85e9],atol=4e6)

    def test_boundary_mixing_not_truth_lookup(self):
        c=example_config(); c['scan']['target_m']=.2
        result=simulate(c)
        fit=result['fits'][0]
        self.assertTrue(fit['flags'])
        contrib=np.array(result['segment_gain_contributions'][0])
        self.assertGreater(contrib[1].max(),0)
        self.assertGreater(contrib[2].max(),0)

    def test_limits_report_actionable_errors(self):
        c=example_config(); c['pump']['edfa_gain_db']=40
        with self.assertRaisesRegex(ModelError,'EDFA'):
            simulate(c)
        c=example_config(); c['receiver']['max_voltage_v']=.01
        with self.assertRaisesRegex(ModelError,'saturate'):
            simulate(c)
        c=example_config(); c['segments'][0]['length_m']=-1
        with self.assertRaisesRegex(ModelError,'length_m'):
            validate_config(c)

    def test_frequency_refinement_and_receiver_alias_guard(self):
        c=example_config(); coarse=simulate(c)
        c['scan']['frequency_step_hz']/=2
        fine=simulate(c)
        self.assertLess(abs(coarse['fitted_resonance_hz'][0]-fine['fitted_resonance_hz'][0]),.5e6)
        np.testing.assert_allclose(np.array(coarse['spectra_r_v']),np.array(fine['spectra_r_v'])[:,::2],rtol=.001,atol=1e-12)
        c=example_config(); c['scan']['position_control']='fixed'
        c['fm']['frequency_hz']=2*c['pump']['modulation_hz']
        with self.assertRaisesRegex(ModelError,'overlaps an FM harmonic'):
            simulate(c)

    def test_multiple_periodic_peaks_with_reduced_excursion(self):
        c=example_config(); c['fm']['excursion_hz']=200e6
        c['scan'].update(target_m=160,start_m=100,stop_m=200,step_m=100,cell_m=2,
                         frequency_step_hz=10e6)
        for seg in c['segments']:
            seg.update(length_m=80,gain_per_w_m=1e-5,resonance_hz=10.85e9)
        r=simulate(c)
        peaks=r['spatial']['correlation_peaks_m']
        self.assertEqual(len(peaks),3)
        np.testing.assert_allclose(np.diff(peaks),r['spatial']['peak_spacing_m'])
        self.assertTrue(any('Multiple correlation peaks' in w for w in r['warnings']))


if __name__=='__main__':
    unittest.main()
