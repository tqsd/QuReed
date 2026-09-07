import unittest
from copy import deepcopy
import numpy as np
from scipy.integrate import quad,solve_ivp
from test_physics import example_config
from bocda_model.physics import simulate,ModelError
from bocda_model.nonideal import (default_options,pump_eom_transfer,probe_eom_spectrum,
    edfa_trace,shared_source_trace,phase_susceptibility,receiver_noise,clip_fundamental,simulate_nonideal,polarization_overlap,
    ram_floquet_weights,_signed_response,_bias_history)
from scipy.special import jv


class NonidealComponents(unittest.TestCase):
    def test_pump_eom_extinction_and_rf_errors(self):
        a=pump_eom_transfer(.2,100)
        b=pump_eom_transfer(.2,10,5,.2,30)
        self.assertAlmostEqual(a['mean_transmission'],.5,places=8)
        self.assertLess(abs(a['relative_fundamental_real']-.2),.002)
        self.assertGreater(b['relative_fundamental_imag'],.05)
        self.assertGreater(min(b['transmission']),0)
        self.assertLessEqual(max(b['transmission']),1)

    def test_iq_sideband_power_and_leakage(self):
        o=default_options();o.update(probe_extinction_db=100.,probe_bias_error_deg=0.,probe_rf_amplitude_error_frac=0.,probe_rf_phase_error_deg=0.)
        ideal=probe_eom_spectrum(o)
        self.assertAlmostEqual(ideal['retained_fraction'],1,places=8)
        powers={x['order']:x['power_fraction'] for x in ideal['components']}
        self.assertGreater(powers[-1],.9999)
        o['probe_extinction_db']=20
        leaky=probe_eom_spectrum(o)
        self.assertGreater(next(x['power_fraction'] for x in leaky['components'] if x['order']==0),.1)

    def test_edfa_compression_and_relaxation(self):
        t=np.linspace(0,1e-3,1001);pin=np.full(len(t),.01)
        r=edfa_trace(t,pin,20,.1,1e-4)
        expected=20/(1+20*.01/.1)
        self.assertLess(abs(r['gain'][-1]-expected),.001)
        self.assertTrue(np.all(np.diff(r['gain'])<=0))
        self.assertLess(r['output_power_w'][-1],.1)

    def test_shared_phase_cancels_at_equal_delay(self):
        r=shared_source_trace(5e4,1e-15,5e6,1e-6,1e-6,4096,2e-9,12)
        np.testing.assert_equal(r['relative_phase_rad'],np.zeros(4096))
        np.testing.assert_equal(r['pump_intensity_multiplier'],r['probe_intensity_multiplier'])
        r=shared_source_trace(5e4,1e-15,5e6,128e-9,0,32768,2e-9,12)
        self.assertLess(abs(r['sample_relative_phase_variance_rad2']/r['expected_relative_phase_variance_rad2']-1),.12)

    def test_shared_phase_acoustic_kernel(self):
        d=np.array([-30e6,0,30e6]);linewidth=27e6;laser=2e6
        np.testing.assert_allclose(phase_susceptibility(d,linewidth,laser,0),1/(1+2j*d/linewidth),atol=1e-14)
        np.testing.assert_allclose(phase_susceptibility(d,linewidth,laser,np.inf),linewidth/(linewidth+2*laser+2j*d),atol=1e-14)
        gamma=np.pi*linewidth;delay=5e-9
        expected=quad(lambda u:np.exp(-u)*np.cos(2*np.pi*10e6*u/gamma)*np.exp(-2*np.pi*laser*min(u/gamma,delay)),0,40,points=[gamma*delay],epsabs=1e-11)[0]
        self.assertAlmostEqual(phase_susceptibility(10e6,linewidth,laser,delay).real,expected,places=10)

    def test_receiver_white_noise_variance_and_clipping(self):
        psd=1e-12;tau=.001
        noise,factor=receiver_noise(psd,tau,.01,1,30000,np.random.default_rng(3))
        self.assertAlmostEqual(factor,1/(2*tau),places=8)
        self.assertLess(abs(np.var(noise.real)/(psd/(2*tau))-1),.03)
        ac,dc,fraction=clip_fundamental([2.,.5],[.1+.2j,.1+.2j],1)
        self.assertLess(abs(ac[0]),1e-12)
        self.assertAlmostEqual(abs(ac[1]-(.1+.2j)),0,places=12)
        self.assertEqual(fraction,.5)

    def test_fast_scrambling_does_not_alias_fixed_dwell_samples(self):
        angle=np.array([0.,.2,1.]);amplitude=.7
        result=polarization_overlap(angle,[.005,.015],.01,3200.,amplitude)
        expected=.5+.5*np.cos(2*angle)*jv(0,2*amplitude)
        np.testing.assert_allclose(result,np.repeat(expected[:,None],2,axis=1),atol=1e-13)


class NonidealIntegration(unittest.TestCase):
    def config(self):
        c=example_config();c['scan'].update(cell_m=.01,frequency_step_hz=5e6)
        return c

    def test_disabled_mode_preserves_classical_result(self):
        c=self.config(); a=simulate(c);b=simulate_nonideal(c,{'enabled':False})
        np.testing.assert_equal(a['spectra_x_v'],b['spectra_x_v'])

    def test_full_components_are_reproducible_and_exported(self):
        c=self.config();a=simulate_nonideal(c);b=simulate_nonideal(c)
        np.testing.assert_equal(a['spectra_x_v'],b['spectra_x_v'])
        self.assertLess(abs(a['fitted_resonance_hz'][0]-10.90e9),4e6)
        n=a['nonideal']
        self.assertLess(n['edfa']['compressed_mean_gain'],n['edfa']['unsaturated_gain'])
        self.assertGreater(n['ase']['edfa_total_ase_w'],0)
        self.assertEqual(len(n['shared_source_trace']['time_s']),4096)
        self.assertTrue(np.all(np.array(n['polarization']['unscrambled_overlap'])<=1))
        self.assertTrue(np.all(np.array(n['detector']['one_sided_voltage_psd_v2_hz'])>0))
        components=n['detector']['one_sided_voltage_psd_components_v2_hz']
        np.testing.assert_allclose(sum(np.array(v) for v in components.values()),n['detector']['one_sided_voltage_psd_v2_hz'],rtol=1e-14)

    def test_saturated_detector_is_reported_not_baseline_rejected(self):
        c=self.config();c['receiver']['max_voltage_v']=.1
        r=simulate_nonideal(c)
        self.assertGreater(r['nonideal']['detector']['clipped_sample_fraction_by_position'][0],.99)
        self.assertTrue(any('clipping occurred' in w for w in r['warnings']))

    def test_symmetric_stokes_antistokes_sidebands_cancel_first_order_sbs(self):
        c=self.config()
        options={'probe_bias_error_deg':0.,'probe_rf_amplitude_error_frac':0.,
                 'probe_rf_phase_error_deg':90.,'probe_extinction_db':100.,
                 'laser_linewidth_hz':0.,'polarization_enabled':False}
        r=simulate_nonideal(c,options)
        np.testing.assert_allclose(r['gain_spectra'],0,atol=1e-13)

    def test_shot_noise_scaling_without_other_noise_sources(self):
        c=self.config()
        r=simulate_nonideal(c,{'edfa_ase_enabled':False,'laser_rin_db_hz':-300.,
                            'detector_electronic_asd_a':0.,'circulator_isolation_db':120.})
        p=r['power_budget']['probe_detector_no_sbs_w']*(1+np.array(r['gain_spectra'][0]))+r['nonideal']['ase']['receiver_pump_leakage_w']
        response=1/(1+(c['pump']['modulation_hz']/c['receiver']['bandwidth_hz'])**2)
        expected=2*1.602176634e-19*c['receiver']['responsivity_a_w']*p*c['receiver']['transimpedance_v_a']**2*response
        np.testing.assert_allclose(r['nonideal']['detector']['one_sided_voltage_psd_v2_hz'][0],expected,rtol=1e-10)

    def test_scrambling_restored_gain_has_its_own_guard(self):
        c=self.config();c['probe']['pc_overlap']=0.
        for seg in c['segments']:seg['gain_per_w_m']=50.
        with self.assertRaisesRegex(ModelError,'Actual nonideal gain'):
            simulate_nonideal(c,{'polarization_rms_rad':1.4,'probe_rf_phase_error_deg':90.,
                               'probe_bias_error_deg':0.,'probe_rf_amplitude_error_frac':0.})


class BiasDriftAndRAM(unittest.TestCase):
    def config(self):
        c=example_config()
        c['scan'].update(cell_m=.01,start_m=.15,stop_m=.25,step_m=.1,
                         frequency_start_hz=10.8e9,frequency_stop_hz=10.95e9,frequency_step_hz=10e6)
        return c

    def test_zero_ram_and_drift_preserve_default_branch_exactly(self):
        c=self.config();a=simulate_nonideal(c,{'trace_samples':256})
        b=simulate_nonideal(c,{'trace_samples':256,'pump_bias_drift_deg_s':0.,
                              'probe_bias_drift_deg_s':0.,'source_ram_depth':0.,'source_ram_phase_deg':72.})
        for key in ['spectra_x_v','spectra_y_v','gain_spectra']:
            np.testing.assert_equal(a[key],b[key])
        self.assertNotIn('bias_history',b['nonideal']);self.assertNotIn('ram',b['nonideal'])

    def test_actual_drift_transfer_chronology_and_nonzero_spectrum(self):
        c=self.config();options={'trace_samples':256,'pump_bias_drift_deg_s':2.,'probe_bias_drift_deg_s':-1.}
        r=simulate_nonideal(c,options,'scan');h=r['nonideal']['bias_history']
        t=np.asarray(h['time_s']);count=len(r['positions_m'])*len(r['frequency_hz'])
        np.testing.assert_allclose(t,(np.arange(count)+.5)*c['receiver']['dwell_s'],atol=1e-15)
        np.testing.assert_allclose(h['pump_bias_deg'],2+2*t)
        np.testing.assert_allclose(h['probe_bias_deg'],1-t)
        direct=pump_eom_transfer(c['pump']['modulation_depth'],30,h['pump_bias_deg'][-1],.02,1)
        self.assertAlmostEqual(h['pump_mean_transmission'][-1],direct['mean_transmission'],places=14)
        o=default_options();nominal=probe_eom_spectrum(o)['raw_mean_transmission']
        o['probe_bias_error_deg']=h['probe_bias_deg'][-1]
        self.assertAlmostEqual(h['probe_transmission_ratio'][-1],probe_eom_spectrum(o)['raw_mean_transmission']/nominal,places=14)
        self.assertGreater(np.ptp(h['pump_edfa_output_w']),1e-5)
        self.assertGreater(np.ptp(h['probe_transmission_ratio']),1e-4)
        clean=simulate_nonideal(c,{'trace_samples':256},'scan')
        self.assertGreater(np.max(abs(np.asarray(r['steady_x_v'])-clean['steady_x_v'])),1e-7)
        self.assertEqual(r['diagnostics']['estimated_pump_depletion_fraction'],max(r['nonideal']['estimated_depletion_by_position']))

    def test_quasistatic_bias_guards(self):
        c=self.config();o=default_options();c['receiver']['dwell_s']=.1;o['pump_bias_drift_deg_s']=2.
        with self.assertRaisesRegex(ModelError,'0.1degree'): _bias_history(c,o,10)
        c['receiver']['dwell_s']=.01;o['pump_bias_error_deg']=79.99
        with self.assertRaisesRegex(ModelError,'operating range'): _bias_history(c,o,10)
        o=default_options();o.update(probe_eom_enabled=False,probe_bias_drift_deg_s=.1)
        with self.assertRaisesRegex(ModelError,'requires its EOM'): _bias_history(c,o,10)

    def test_ram_equal_delay_no_fm_has_analytic_three_coefficients(self):
        c=self.config();c['fm']['excursion_hz']=0.;fm=1e6;length=.4;z=.2
        control={'frequency_hz':fm,'delay_s':0.}
        n,w,d=ram_floquet_weights([z],length,control,c,.1,53.)
        expected=np.zeros(len(n));expected[n==0]=1.;expected[abs(n)==1]=.1**2/4
        np.testing.assert_allclose(w[0],expected,atol=1e-14)
        self.assertAlmostEqual(d['summed_fourier_power'][0],1.005,places=13)
        kd,_=_signed_response([7e6],n,fm,27e6,0.,0.,1e5)
        lorentz=lambda v:1/(1+(2*v/27e6)**2)
        exact=lorentz(7e6)+.1**2/4*(lorentz(7e6+fm)+lorentz(7e6-fm))
        self.assertAlmostEqual(float(w[0]@kd[:,0]),exact,places=13)
        control['delay_s']=.5/fm
        _,w,d=ram_floquet_weights([z],length,control,c,.1,53.)
        self.assertAlmostEqual(d['summed_fourier_power'][0],.995,places=13)

    def test_asymmetric_ram_floquet_matches_independent_acoustic_ode(self):
        c=self.config();fm=1e6;length=.4;z=.17;vg=c['fm']['group_velocity_m_s']
        peak=10*fm/(2*np.sin(np.pi*.25));c['fm'].update(excursion_hz=2*peak,phase_rad=.7)
        control={'frequency_hz':fm,'delay_s':1.25/fm-(2*z-length)/vg}
        n,w,d=ram_floquet_weights([z],length,control,c,.1,37.)
        self.assertGreater(np.max(abs(w[0]-w[0,::-1])),1e-3)
        _,refined,_=ram_floquet_weights([z],length,control,c,.1,37.,oversampling=8)
        np.testing.assert_allclose(w,refined,atol=1e-13)
        taup=control['delay_s']+z/vg;taus=(length-z)/vg;omega=2*np.pi*fm
        def drive(theta):
            xp=theta-omega*taup;xs=theta-omega*taus
            ip=1+.1*np.cos(xp+np.deg2rad(37.));is_=1+.1*np.cos(xs+np.deg2rad(37.))
            phase=-peak/fm*(np.cos(xp+.7)-np.cos(xs+.7))
            return np.sqrt(ip*is_)*np.exp(1j*phase)
        gamma=np.pi*27e6;delta=7e6
        sol=solve_ivp(lambda theta,q:gamma/omega*drive(theta)-(gamma/omega+1j*delta/fm)*q,
                      (0,8*2*np.pi),[0j],rtol=2e-10,atol=2e-12,dense_output=True,max_step=.025)
        theta=7*2*np.pi+np.arange(8192)/8192*2*np.pi
        direct=np.mean(np.real(np.conj(drive(theta))*sol.sol(theta)[0]))
        kd,_=_signed_response([delta],n,fm,27e6,0.,0.,1e5)
        predicted=float(w[0]@kd[:,0])
        self.assertAlmostEqual(predicted,direct,places=8)
        self.assertGreater(abs(float(w[0,::-1]@kd[:,0])-direct),1e-3)

    def test_ram_resources_rejected_before_large_grid(self):
        c=self.config();c['fm']['excursion_hz']=0.
        with self.assertRaisesRegex(ModelError,'2million'):
            ram_floquet_weights(np.linspace(0,.4,10000),.4,{'frequency_hz':699e3,'delay_s':0.},c,.1)

    def test_combined_ram_and_drift_use_shared_source_history(self):
        import json
        c=self.config();r=simulate_nonideal(c,{'trace_samples':256,'source_ram_depth':.08,
                'source_ram_phase_deg':43.,'pump_bias_drift_deg_s':1.,'probe_bias_drift_deg_s':-.5},'scan')
        json.dumps(r,allow_nan=False)
        ram=r['nonideal']['ram'];trace=ram['source_trace'];t=np.asarray(trace['time_s']);fm=trace['frequency_hz']
        for arm in ['pump','probe']:
            expected=1+.08*np.cos(2*np.pi*fm*(t-trace[arm+'_delay_s'])+np.deg2rad(43.))
            np.testing.assert_allclose(trace[arm+'_intensity_multiplier'],expected,atol=1e-14)
        for d in ram['coefficient_diagnostics']:
            np.testing.assert_allclose(d['summed_fourier_power'],d['mean_intensity_product'],atol=1e-12)
        clean=simulate_nonideal(c,{'trace_samples':256,'pump_bias_drift_deg_s':1.,'probe_bias_drift_deg_s':-.5},'scan')
        self.assertGreater(np.max(abs(np.asarray(r['gain_spectra'])-clean['gain_spectra'])),1e-7)
        self.assertTrue(any('not full cyclostationary' in w for w in r['warnings']))

    def test_ram_rejects_fast_compression_and_clipping(self):
        c=self.config()
        with self.assertRaisesRegex(ModelError,'gain nearly frozen'):
            simulate_nonideal(c,{'source_ram_depth':.05,'edfa_gain_time_us':.01,'trace_samples':256})
        c['receiver']['max_voltage_v']=.1
        with self.assertRaisesRegex(ModelError,'unclipped detector'):
            simulate_nonideal(c,{'source_ram_depth':.05,'trace_samples':256})


if __name__=='__main__': unittest.main()
