import unittest
import numpy as np
from test_physics import example_config
from bocda_model.dynamics import simulate_dynamics
from bocda_model.physics import ModelError


class CoupledDynamics(unittest.TestCase):
    def uniform(self):
        c=example_config();c['pump']['modulation_depth']=0
        for seg in c['segments']:seg.update(resonance_hz=10.85e9,attenuation_db_km=0)
        return c

    def test_no_coupling_characteristics_and_conservation(self):
        c=self.uniform();r=simulate_dynamics(c,{'cells':20,'duration_ns':30,'fm_enabled':False,'offset_ghz':10.85,'gain_scale':0,'convergence_check':False})
        d=r['diagnostics']
        self.assertLess(abs(d['photon_balance_relative']),1e-11)
        self.assertLess(abs(d['pump_depletion_fraction_final']),1e-10)
        self.assertAlmostEqual(d['probe_amplification_final'],1,places=6)
        self.assertEqual(r['pump_power_w'][0],[0.]*20)

    def test_real_depletion_and_grid_time_refinement(self):
        c=self.uniform();r=simulate_dynamics(c,{'cells':20,'duration_ns':100,'fm_enabled':False,'offset_ghz':10.85,'convergence_check':True})
        d=r['diagnostics']
        self.assertGreater(d['pump_depletion_fraction_final'],.18)
        self.assertGreater(d['probe_amplification_final'],4.7)
        self.assertLess(abs(d['photon_balance_relative']),1e-8)
        self.assertLess(d['refinement']['probe_output_w_relative_l2'],.005)
        # Independently reviewed stationary BVP benchmark: 0.18933 depletion.
        self.assertLess(abs(d['pump_depletion_fraction_final']-.189331892),.001)

    def test_common_fm_transient_is_finite_and_shorter_than_cycle(self):
        r=simulate_dynamics(example_config(),{'duration_ns':50,'convergence_check':False})
        self.assertLess(r['diagnostics']['fm_periods_simulated'],1)
        self.assertTrue(np.all(np.isfinite(r['acoustic_real_w'])))
        self.assertGreater(np.max(abs(np.array(r['acoustic_imag_w']))),0)
        self.assertLess(abs(r['diagnostics']['photon_balance_relative']),1e-8)

    def test_workload_and_time_step_limits(self):
        c=example_config();c['segments']=[{**c['segments'][0],'length_m':1e-8}]
        c['scan'].update(target_m=0,start_m=0,stop_m=1e-8)
        with self.assertRaisesRegex(ModelError,'workload'):
            simulate_dynamics(c,{'duration_ns':2000,'convergence_check':False})
        with self.assertRaisesRegex(ModelError,'integer'):
            simulate_dynamics(example_config(),{'cells':10.5})

    def test_depletion_unavailable_before_pump_arrives(self):
        r=simulate_dynamics(example_config(),{'duration_ns':1.,'convergence_check':False})
        self.assertIsNone(r['diagnostics']['pump_depletion_fraction_final'])
        self.assertIn('No reference pump',r['diagnostics']['depletion_unavailable_reason'])

    def test_declared_refinement_tolerances_failure_and_characteristic_times(self):
        c=self.uniform()
        options={'cells':8,'duration_ns':10,'fm_enabled':False,'offset_ghz':10.85,
                 'gain_scale':0,'probe_scale':1,'refinement_rtol':1e-8,'refinement_atol_w':0.}
        with self.assertRaisesRegex(ModelError,'refinement failed'):
            simulate_dynamics(c,options)
        c['laser']['power_w']=0
        result=simulate_dynamics(c,options|{'refinement_atol_w':1e-9})
        d=result['diagnostics']
        self.assertEqual(d['refinement_status'],'passed')
        self.assertEqual(d['refinement']['pump_output_w_rms_error_w'],0)
        self.assertAlmostEqual(d['propagation_time_s'],.4/2.04e8)
        self.assertAlmostEqual(d['acoustic_amplitude_lifetime_max_s'],1/(np.pi*27e6))
        self.assertAlmostEqual(d['minimum_acoustic_lifetimes_simulated'],d['duration_s']*np.pi*27e6)


if __name__=='__main__':unittest.main()
