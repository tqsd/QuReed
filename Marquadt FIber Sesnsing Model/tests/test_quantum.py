"""Numerical channel and resource-accounting tests; not a proof of SBS equivalence."""
import copy
import json
import math
import unittest

import numpy as np
from scipy.constants import c, h, elementary_charge as e

from bocda_model.quantum import (
    QuantumError, amplifier_loss, analyze_quantum, default_options, gaussian_fisher,
    homodyne, input_state, omega, passive_mixer, phase_average_moments,
    photon_number, physicality, schema, thermal_occupation, validate_options,
)


def fixture():
    frequency = np.linspace(10.80e9, 10.90e9, 51)
    gain = .003/(1+(2*(frequency-10.85e9)/27e6)**2)
    return {
        "config": {
            "laser": {"wavelength_nm": 1550},
            "fm": {"frequency_hz": 699e3},
            "receiver": {"bandwidth_hz": 1.1e6, "dwell_s": .01},
            "segments": [{"linewidth_hz": 27e6}],
            "scan": {"target_m": .25},
        },
        "gain_spectra": [gain.tolist(), (gain*.9).tolist()],
        "positions_m": [.25, .35], "frequency_hz": frequency.tolist(),
        "power_budget": {"probe_fiber_input_w": 1e-8, "probe_detector_no_sbs_w": .8e-8},
    }


class QuantumChannelTests(unittest.TestCase):
    def test_schema_is_complete_and_validated(self):
        self.assertEqual(set(default_options()), set(schema()))
        self.assertEqual(validate_options(), default_options())
        for bad in [{"mode_count":2.1}, {"enabled":"yes"}, {"lo_power_w":0},
                    {"temperature_k":-1}, {"quantum_efficiency":1.1}, {"unknown":1},
                    {"mode_duration_s":float("nan")}, {"squeeze_r":4}]:
            with self.assertRaises(QuantumError):
                validate_options(bad)

    def test_photon_budget_includes_squeezing(self):
        for n, r in [(0,0),(20,.8),(100,2)]:
            d,v = input_state(n,r,.7,.3)
            self.assertAlmostEqual(photon_number(d,v),n,places=10)
            self.assertAlmostEqual(np.linalg.det(v),.25,places=9)
        with self.assertRaises(QuantumError):
            input_state(.1,1)

    def test_vacuum_loss_and_identity(self):
        d,v = input_state(7)
        outd,outv,check = amplifier_loss(d,v,1,100,1)
        np.testing.assert_array_equal(outd,d)
        np.testing.assert_array_equal(outv,v)
        outd,outv,_ = amplifier_loss(d,v,1,0,0)
        np.testing.assert_array_equal(outd,[0,0])
        np.testing.assert_array_equal(outv,np.eye(2)/2)
        self.assertEqual(check["amplifier_commutator"],1)

    def test_amplifier_spontaneous_and_thermal_noise(self):
        d,v = input_state(4)
        for gain, bath, transmission in [(1,300,1),(2,0,1),(1.2,550,.8)]:
            outd,outv,checks = amplifier_loss(d,v,gain,bath,transmission)
            nth = transmission*(gain-1)*(bath+1)
            np.testing.assert_allclose(outv,np.eye(2)*(nth+.5))
            self.assertAlmostEqual(photon_number(outd,outv),transmission*gain*4+nth)
            self.assertGreaterEqual(checks["minimum_cp_eigenvalue"],-1e-12)
            self.assertGreaterEqual(checks["minimum_uncertainty_eigenvalue"],-1e-12)

    def test_nonphysical_covariance_and_channel_rejected(self):
        with self.assertRaises(QuantumError):
            physicality(np.eye(2)*.1)
        for gain,bath,transmission in [(.9,0,1),(1,-1,1),(1,0,1.01)]:
            with self.assertRaises(QuantumError):
                amplifier_loss([0,0],np.eye(2)/2,gain,bath,transmission)

    def test_bath_uses_acoustic_not_optical_frequency(self):
        self.assertEqual(thermal_occupation(10.85e9,0),0)
        n = thermal_occupation(10.85e9,293.15)
        self.assertGreater(n,500)
        self.assertLess(n,600)
        self.assertLess(thermal_occupation(c/1550e-9,293.15),1e-12)

    def test_finite_lo_coherent_counts_equal_poisson_difference(self):
        nsignal, nlo, duration, frequency = 7., 50., 1e-4, c/1550e-9
        d,v = input_state(nsignal)
        measurement = homodyne(d,v,frequency,duration,nlo*h*frequency/duration,
                               efficiency=.7,transimpedance_v_a=1000)
        expected_mean = 2*.7*e/duration*math.sqrt(nsignal*nlo)
        expected_variance = (e/duration)**2*.7*(nsignal+nlo)
        self.assertAlmostEqual(measurement["difference_current_a"]/expected_mean,1,places=12)
        self.assertAlmostEqual(measurement["difference_current_variance_a2"]/expected_variance,1,places=12)
        self.assertAlmostEqual(sum(measurement["individual_diode_mean_current_a"]),
                               e/duration*.7*(nsignal+nlo),places=20)
        self.assertAlmostEqual(measurement["difference_voltage_v"],1000*expected_mean)

    def test_lo_phase_and_mismatch(self):
        d,v = input_state(50)
        a = homodyne(d,v,c/1550e-9,1e-4,.01)
        b = homodyne(d,v,c/1550e-9,1e-4,.01,phase_rad=math.pi/2)
        q = homodyne(d,v,c/1550e-9,1e-4,.01,lo_mode_overlap=.25)
        null = homodyne(d,v,c/1550e-9,1e-4,.01,lo_detuning_hz=1e4)
        self.assertLess(abs(b["difference_current_a"]),abs(a["difference_current_a"])*1e-12)
        self.assertAlmostEqual(q["difference_current_a"]/a["difference_current_a"],.5)
        self.assertLess(abs(null["difference_current_a"]),abs(a["difference_current_a"])*1e-12)
        self.assertAlmostEqual(q["difference_current_variance_a2"],a["difference_current_variance_a2"])

    def test_phase_average_exact_moments_and_energy(self):
        d,v = input_state(20,.5,.2,.7)
        sigma=.37
        mean,covariance,gaussian = phase_average_moments(d,v,sigma)
        nodes,weights = np.polynomial.hermite.hermgauss(64)
        numeric_mean = np.zeros(2)
        numeric_second = np.zeros((2,2))
        for node,weight in zip(nodes,weights/math.sqrt(math.pi)):
            theta = math.sqrt(2)*sigma*node
            r = np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
            numeric_mean += weight*r@d
            numeric_second += weight*r@(v+np.outer(d,d))@r.T
        np.testing.assert_allclose(mean,numeric_mean,rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(covariance,numeric_second-np.outer(numeric_mean,numeric_mean),rtol=1e-11)
        self.assertFalse(gaussian)
        self.assertAlmostEqual(photon_number(mean,covariance),20)
        d0,v0,_ = phase_average_moments(d*1e8,v,0)
        np.testing.assert_array_equal(v0,v)

    def test_common_phase_creates_multimode_correlations(self):
        d=np.array([10.,0.,10.,0.])
        mean,cov,gaussian = phase_average_moments(d,np.eye(4)/2,.2)
        self.assertFalse(gaussian)
        self.assertGreater(cov[1,3],0)
        self.assertAlmostEqual(photon_number(mean,cov),100)

    def test_passive_mixer_is_symplectic_and_number_preserving(self):
        u,s = passive_mixer(4,.4)
        np.testing.assert_allclose(u@u.T,np.eye(4),atol=1e-14)
        np.testing.assert_allclose(s@omega(4)@s.T,omega(4),atol=1e-14)
        d=np.arange(8,dtype=float)
        v=np.eye(8)/2
        self.assertAlmostEqual(photon_number(d,v),photon_number(s@d,s@v@s.T))

    def test_fisher_matches_independent_score_monte_carlo(self):
        covariance=np.array([[2.,.4],[.4,1.]])
        slope=np.array([[.1,.03],[.03,-.08]])
        derivative=np.array([.7,-.2])
        result=gaussian_fisher(derivative,covariance,slope)
        inv=np.linalg.inv(covariance)
        samples=np.random.default_rng(734).multivariate_normal(np.zeros(2),covariance,200000)
        score=samples@inv@derivative+.5*(np.einsum("ni,ij,nj->n",samples,inv@slope@inv,samples)-np.trace(inv@slope))
        self.assertLess(abs(np.mean(score*score)/result["total_per_hz2"]-1),.015)


class QuantumPipelineTests(unittest.TestCase):
    def test_default_pipeline_is_json_safe_and_displaced_thermal(self):
        original=fixture()
        before=copy.deepcopy(original)
        result=analyze_quantum(original,{"enabled":True})
        self.assertEqual(original,before)
        json.dumps(result,allow_nan=False)
        self.assertTrue(result["selected"]["is_exact_gaussian_under_model"])
        self.assertTrue(result["selected"]["is_displaced_thermal"])
        self.assertEqual(np.shape(result["quadrature_mean"]),(2,51))
        self.assertLess(result["multimode"]["largest_individual_diode_dc_equivalent_voltage_v"],10)
        self.assertIsNotNone(result["multimode"]["fisher_information"])

    def test_resource_matched_temporal_modes_and_fisher_terms(self):
        result=analyze_quantum(fixture(),{"enabled":True})
        multi=result["multimode"]
        fi=multi["fisher_information"]
        self.assertAlmostEqual(sum(m["input_photons"] for m in multi["modes"]),result["input_total_photons"])
        self.assertAlmostEqual(sum(m["stop_s"]-m["start_s"] for m in multi["modes"]),multi["total_observation_s"])
        self.assertEqual(multi["modes"][0]["start_s"],0)
        self.assertAlmostEqual(multi["modes"][-1]["stop_s"],multi["total_observation_s"])
        joint=fi["independent_joint"]
        single=fi["single_collective_readout"]["candidates"]["equal_weight"]
        self.assertAlmostEqual(joint["mean_per_hz2"]/single["mean_per_hz2"],1,places=12)
        self.assertAlmostEqual(joint["covariance_per_hz2"]/single["covariance_per_hz2"],4,places=12)
        self.assertLess(fi["mixing_invariance_absolute_error"],1e-25)
        self.assertEqual(fi["configured_minus_coherent_per_hz2"],0)
        self.assertGreaterEqual(joint["total_per_hz2"],fi["reduced_first_mixed_mode"]["total_per_hz2"])

    def test_squeezing_correlations_and_same_phase_reference(self):
        result=analyze_quantum(fixture(),{"enabled":True,"squeeze_r":.6,"input_phase_deg":35})
        multi=result["multimode"]
        self.assertFalse(result["selected"]["is_displaced_thermal"])
        self.assertGreater(multi["max_mixed_cross_covariance"],.01)
        self.assertGreater(multi["modes"][0]["squeezing_photons"],0)
        self.assertAlmostEqual(sum(m["input_photons"] for m in multi["modes"]),multi["total_input_photons"],places=6)
        coherent=analyze_quantum(fixture(),{"enabled":True,"input_phase_deg":35})
        np.testing.assert_allclose(multi["fisher_information"]["same_budget_coherent_joint"]["total_per_hz2"],
                                   coherent["multimode"]["fisher_information"]["independent_joint"]["total_per_hz2"])

    def test_phase_mixture_and_detuning_disable_gaussian_fisher(self):
        for options in [{"phase_jitter_std_rad":.1},{"lo_detuning_hz":1000}]:
            result=analyze_quantum(fixture(),dict(enabled=True,**options))
            self.assertIsNone(result["multimode"]["fisher_information"])
        result=analyze_quantum(fixture(),dict(enabled=True,phase_jitter_std_rad=.1))
        self.assertFalse(result["selected"]["is_exact_gaussian_under_model"])
        self.assertFalse(result["multimode"]["is_exact_gaussian_under_model"])
        self.assertGreater(np.array(result["multimode"]["V"])[1,3],0)

    def test_receiver_headroom_does_not_hide_in_balanced_difference(self):
        # LO phase pi/2 gives zero difference, but both individual detectors saturate.
        with self.assertRaisesRegex(QuantumError,"photodiode"):
            analyze_quantum(fixture(),{"enabled":True,"lo_power_w":.1,"lo_phase_deg":90})
        with self.assertRaisesRegex(QuantumError,"photodiode"):
            analyze_quantum(fixture(),{"enabled":True,"homodyne_transimpedance_v_a":1e5})

    def test_weak_lo_suppresses_fisher_but_retains_exact_moments(self):
        data=fixture()
        data["power_budget"]={"probe_fiber_input_w":1e-3,"probe_detector_no_sbs_w":.8e-3}
        result=analyze_quantum(data,{"enabled":True,"lo_power_w":1e-5})
        self.assertIsNone(result["multimode"]["fisher_information"])
        self.assertGreater(result["selected"]["measurement"]["finite_lo_relative_variance"],.01)
        self.assertGreater(result["selected"]["measurement"]["difference_current_variance_a2"],0)

    def test_invalid_observation_and_budget_are_actionable(self):
        for options in [{"mode_duration_s":.02},{"mode_duration_s":1e-6,"mode_count":16}]:
            with self.assertRaises(QuantumError):
                analyze_quantum(fixture(),dict(enabled=True,**options))
        data=fixture()
        data["power_budget"]["probe_fiber_input_w"]=0
        with self.assertRaises(QuantumError):
            analyze_quantum(data,{"enabled":True})

    def test_zero_gain_zero_gain_derivative_and_disabled_extension(self):
        data=fixture()
        data["gain_spectra"]=np.zeros((2,51)).tolist()
        result=analyze_quantum(data,{"enabled":True})
        self.assertAlmostEqual(result["selected"]["thermal_photons_if_displaced_thermal"],0)
        self.assertEqual(result["multimode"]["fisher_information"]["independent_joint"]["total_per_hz2"],0)
        self.assertEqual(analyze_quantum({},None)["enabled"],False)

    def test_fm_cycle_warning_uses_actual_position_controls(self):
        data=fixture()
        data["controls"]=[{"frequency_hz":350e3},{"frequency_hz":800e3}]
        result=analyze_quantum(data,{"enabled":True})
        self.assertAlmostEqual(result["diagnostics"]["minimum_actual_fm_cycles_per_temporal_bin"],8.75)
        self.assertTrue(any("fewer than ten FM cycles" in warning for warning in result["warnings"]))
        data["config"]["fm"]["frequency_hz"]=100e3
        data["controls"]=[{"frequency_hz":800e3},{"frequency_hz":900e3}]
        result=analyze_quantum(data,{"enabled":True})
        self.assertFalse(any("fewer than ten FM cycles" in warning for warning in result["warnings"]))

    def test_fisher_frequency_derivative_converges_on_analytic_gain(self):
        delta,linewidth=20e6,27e6
        exact=.003*8*delta/linewidth**2/(1+(2*delta/linewidth)**2)**2
        errors=[]
        for step in [4e6,2e6,1e6,.5e6]:
            data=fixture()
            frequency=10.85e9+np.arange(-40e6,40e6+step/2,step)
            gain=.003/(1+(2*(frequency-10.85e9)/linewidth)**2)
            data["frequency_hz"]=frequency.tolist()
            data["gain_spectra"]=[gain.tolist(),gain.tolist()]
            result=analyze_quantum(data,{"enabled":True})
            errors.append(abs(result["selected"]["gain_derivative_per_hz"]/exact-1))
        for coarse,fine in zip(errors[:-1],errors[1:]):
            self.assertGreater(coarse/fine,3.5)
        self.assertLess(errors[-1],.001)


if __name__ == "__main__":
    unittest.main()
