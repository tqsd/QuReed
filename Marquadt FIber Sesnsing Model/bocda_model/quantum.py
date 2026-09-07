"""Selected-mode Gaussian channels and matched homodyne BOCDA extension.

Numerical, explicitly effective model. Quadratures are [x,p]=i and Vvac=I/2.
See docs/quantum.md for the mode, channel, finite-LO, and comparison assumptions.
"""
from __future__ import annotations

from copy import deepcopy
import math

import numpy as np
from scipy.constants import c as C, h as H, k as KB, elementary_charge as Q


class QuantumError(ValueError):
    """Actionable invalid quantum-extension setting or nonphysical covariance."""


def default_options():
    return {
        "enabled": False,
        "mode_duration_s": 1e-4,
        "temperature_k": 293.15,
        "bath_frequency_hz": 10.85e9,
        "lo_power_w": .01,
        "lo_phase_deg": 0.0,
        "lo_detuning_hz": 0.0,
        "lo_mode_overlap": 1.0,
        "quantum_efficiency": .8,
        "input_phase_deg": 0.0,
        "squeeze_r": 0.0,
        "squeeze_angle_deg": 0.0,
        "phase_jitter_std_rad": 0.0,
        "electronics_noise_a_rt_hz": 0.0,
        "homodyne_transimpedance_v_a": 1000.0,
        "homodyne_max_voltage_v": 10.0,
        "mode_count": 4,
        "mixing_angle_deg": 30.0,
        "alternate_squeeze_axes": True,
        "selected_frequency_hz": 10.87e9,
    }


def schema():
    def s(label, unit="", kind="float", **extra):
        return dict(label=label, unit=unit, type=kind, **extra)
    return {
        "enabled": s("Enable selected-mode quantum/homodyne analysis", kind="bool"),
        "mode_duration_s": s("Total selected observation duration", "s", min=1e-9),
        "temperature_k": s("Effective acoustic bath temperature", "K", min=0),
        "bath_frequency_hz": s("Acoustic bath frequency (not optical)", "Hz", min=1),
        "lo_power_w": s("Matched local-oscillator power", "W", min=1e-15),
        "lo_phase_deg": s("Local-oscillator quadrature phase", "deg"),
        "lo_detuning_hz": s("LO residual optical frequency mismatch", "Hz"),
        "lo_mode_overlap": s("LO polarization/spatial power overlap", "", min=0, max=1),
        "quantum_efficiency": s("Balanced detector quantum efficiency", "", min=1e-9, max=1),
        "input_phase_deg": s("Probe displacement phase", "deg"),
        "squeeze_r": s("Input squeezing parameter", "", min=0, max=3),
        "squeeze_angle_deg": s("Input squeezing axis", "deg"),
        "phase_jitter_std_rad": s("Unobserved Gaussian phase jitter", "rad", min=0, max=10),
        "electronics_noise_a_rt_hz": s("One-sided difference-current noise density", "A/sqrt(Hz)", min=0),
        "homodyne_transimpedance_v_a": s("Balanced-receiver transimpedance", "V/A", min=1e-9),
        "homodyne_max_voltage_v": s("Balanced-receiver per-diode and difference limit", "V", min=1e-9),
        "mode_count": s("Orthogonal temporal-bin modes", "", kind="int", min=1, max=16),
        "mixing_angle_deg": s("Adjacent-mode passive mixing angle", "deg"),
        "alternate_squeeze_axes": s("Alternate temporal-bin squeeze axes", kind="bool"),
        "selected_frequency_hz": s("Displayed/Fisher operating frequency", "Hz", min=1),
    }


def validate_options(options=None):
    result = default_options()
    if options:
        unknown = set(options) - set(result)
        if unknown:
            raise QuantumError("Unknown quantum option(s): " + ", ".join(sorted(unknown)))
        result.update(deepcopy(options))
    for name, spec in schema().items():
        value = result[name]
        if spec["type"] == "bool":
            if not isinstance(value, bool):
                raise QuantumError(f"{name} must be a boolean.")
            continue
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
            raise QuantumError(f"{name} must be a finite number.")
        if spec["type"] == "int" and int(value) != value:
            raise QuantumError(f"{name} must be an integer.")
        if "min" in spec and value < spec["min"]:
            raise QuantumError(f"{name} must be at least {spec['min']}.")
        if "max" in spec and value > spec["max"]:
            raise QuantumError(f"{name} must be at most {spec['max']}.")
    result["mode_count"] = int(result["mode_count"])
    return result


def omega(modes):
    return np.kron(np.eye(modes), np.array([[0., 1.], [-1., 0.]]))


def physicality(covariance, tolerance=1e-9):
    v = np.asarray(covariance, dtype=float)
    if v.ndim != 2 or v.shape[0] != v.shape[1] or v.shape[0] % 2 or not np.isfinite(v).all():
        raise QuantumError("Covariance must be a finite even-dimensional square matrix.")
    if not np.allclose(v, v.T, rtol=0, atol=tolerance):
        raise QuantumError("Covariance is not symmetric.")
    eigen = float(np.linalg.eigvalsh(v + .5j * omega(len(v)//2)).min())
    if eigen < -tolerance:
        raise QuantumError("Covariance violates V + i Omega/2 >= 0.")
    return eigen


def photon_number(displacement, covariance):
    d, v = np.asarray(displacement, float), np.asarray(covariance, float)
    physicality(v)
    if d.shape != (len(v),) or not np.isfinite(d).all():
        raise QuantumError("Displacement dimension must match finite covariance.")
    return float((d @ d + np.trace(v) - len(d)/2) / 2)


def thermal_occupation(frequency_hz, temperature_k):
    if not np.isfinite(frequency_hz) or frequency_hz <= 0 or not np.isfinite(temperature_k) or temperature_k < 0:
        raise QuantumError("Thermal occupation requires positive frequency and nonnegative temperature.")
    if temperature_k == 0:
        return 0.
    exponent = H * frequency_hz / (KB * temperature_k)
    return 0. if exponent > 700 else float(1 / np.expm1(exponent))


def input_state(total_photons, squeeze_r=0., phase_rad=0., squeeze_angle_rad=0.):
    """D(alpha) S(r) vacuum, with squeezing photons deducted from total budget."""
    if not all(np.isfinite(v) for v in [total_photons, squeeze_r, phase_rad, squeeze_angle_rad]):
        raise QuantumError("State settings must be finite.")
    if total_photons < 0 or not 0 <= squeeze_r <= 3:
        raise QuantumError("Photons must be nonnegative and squeezing r must be between 0 and 3.")
    nsq = math.sinh(squeeze_r)**2
    if nsq > total_photons + 1e-12:
        raise QuantumError("Squeezing consumes more photons than the allocated input budget.")
    coherent = max(0., total_photons - nsq)
    displacement = math.sqrt(2 * coherent) * np.array([math.cos(phase_rad), math.sin(phase_rad)])
    angle = squeeze_angle_rad
    rotation = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
    covariance = rotation @ np.diag([math.exp(-2*squeeze_r), math.exp(2*squeeze_r)]) @ rotation.T / 2
    physicality(covariance)
    return displacement, covariance


def amplifier_loss(displacement, covariance, gain, bath_occupation, transmission=1.):
    """Independent thermal amplifier followed by vacuum loss; returns d,V and CP checks."""
    if not all(np.isfinite(v) for v in [gain, bath_occupation, transmission]):
        raise QuantumError("Channel parameters must be finite.")
    if gain < 1 or bath_occupation < 0 or not 0 <= transmission <= 1:
        raise QuantumError("Require gain >= 1, bath occupation >= 0 and 0 <= transmission <= 1.")
    d, v = np.asarray(displacement, float), np.asarray(covariance, float)
    physicality(v)
    if len(d) != len(v):
        raise QuantumError("Channel state dimensions do not agree.")
    ident = np.eye(len(v))
    x = math.sqrt(transmission * gain) * ident
    y = (transmission * (gain-1) * (bath_occupation+.5) + (1-transmission)/2) * ident
    cp = y + .5j * (omega(len(v)//2) - x @ omega(len(v)//2) @ x.T)
    minimum_cp = float(np.linalg.eigvalsh(cp).min())
    if minimum_cp < -1e-9:
        raise QuantumError("Gaussian channel failed complete-positivity check.")
    outd, outv = x @ d, x @ v @ x.T + y
    uncertainty = physicality(outv)
    return outd, outv, {
        "minimum_cp_eigenvalue": minimum_cp,
        "minimum_uncertainty_eigenvalue": uncertainty,
        "amplifier_commutator": gain - (gain - 1),
        "X": x.tolist(), "Y": y.tolist(),
    }


def phase_average_moments(displacement, covariance, sigma):
    """Exact first/second moments of a random phase mixture, generally NOT Gaussian."""
    if not np.isfinite(sigma) or sigma < 0:
        raise QuantumError("Phase jitter must be finite and nonnegative.")
    d, v = np.asarray(displacement, float), np.asarray(covariance, float)
    if len(d) % 2 or v.shape != (len(d), len(d)):
        raise QuantumError("Phase-average state dimensions must agree.")
    if sigma == 0:
        return d.copy(), v.copy(), True
    # Stable even for a bright coherent displacement and very small phase noise.
    dd = np.outer(d, d)
    rotation90 = -omega(len(d)//2)
    rotated_d = rotation90@d
    one_minus_e1 = -math.expm1(-sigma*sigma)
    one_minus_e2 = -math.expm1(-2*sigma*sigma)
    dm = d * math.exp(-sigma*sigma/2)
    vm = (v + .5*one_minus_e2*(rotation90@v@rotation90.T-v)
          + .5*one_minus_e1**2*dd + .5*one_minus_e2*np.outer(rotated_d, rotated_d))
    physicality(vm, tolerance=max(1e-9, float(np.max(abs(vm)))*1e-12))
    gaussian = sigma == 0 or (np.allclose(d, 0) and np.allclose(v, rotation90@v@rotation90.T))
    return dm, vm, bool(gaussian)


def homodyne(displacement, covariance, optical_frequency_hz, duration_s, lo_power_w,
             phase_rad=0., efficiency=1., transimpedance_v_a=1., electronics_noise_a_rt_hz=0.,
             lo_mode_overlap=1., lo_detuning_hz=0.):
    """Ideal quadrature plus exact finite coherent-LO difference-count moments.

    Finite-LO photocount distributions are not declared Gaussian. FI elsewhere
    uses only the explicitly flagged bright-LO Gaussian homodyne limit.
    """
    if not all(np.isfinite(v) for v in [optical_frequency_hz, duration_s, lo_power_w, phase_rad,
                                         efficiency, transimpedance_v_a, electronics_noise_a_rt_hz,
                                         lo_mode_overlap, lo_detuning_hz]):
        raise QuantumError("Homodyne parameters must be finite.")
    if min(optical_frequency_hz, duration_s, lo_power_w, efficiency) <= 0 or efficiency > 1:
        raise QuantumError("Homodyne requires positive optical frequency, duration, LO power and 0 < efficiency <= 1.")
    if electronics_noise_a_rt_hz < 0 or transimpedance_v_a <= 0:
        raise QuantumError("Electronic noise must be nonnegative and transimpedance positive.")
    if not 0 <= lo_mode_overlap <= 1:
        raise QuantumError("LO mode power overlap must lie between zero and one.")
    sinc = float(np.sinc(lo_detuning_hz*duration_s))
    overlap = lo_mode_overlap*sinc*sinc
    phase_rad += math.pi*lo_detuning_hz*duration_s + (math.pi if sinc < 0 else 0.)
    d, v, _ = amplifier_loss(displacement, covariance, 1., 0., efficiency*overlap)
    e = np.array([math.cos(phase_rad), math.sin(phase_rad)])
    mean, variance = float(e @ d), float(e @ v @ e)
    nsignal = photon_number(displacement, covariance)
    nlo = lo_power_w * duration_s / (H * optical_frequency_hz)
    nlo_detected = efficiency*nlo
    coefficient = Q / duration_s * math.sqrt(2*nlo_detected)
    current_mean = coefficient * mean
    finite_lo_variance = (Q/duration_s)**2 * efficiency * nsignal
    electronic_variance = electronics_noise_a_rt_hz**2/(2*duration_s)
    current_variance = coefficient**2 * variance + finite_lo_variance + electronic_variance
    total_current = Q/duration_s*efficiency*(nlo+nsignal)
    diode_currents = [(total_current+current_mean)/2, (total_current-current_mean)/2]
    return {
        "quadrature_mean": mean, "quadrature_variance": variance,
        "difference_current_a": current_mean, "difference_current_variance_a2": current_variance,
        "difference_voltage_v": transimpedance_v_a*current_mean,
        "difference_voltage_variance_v2": transimpedance_v_a**2*current_variance,
        "finite_lo_variance_a2": finite_lo_variance, "electronics_variance_a2": electronic_variance,
        "lo_photons": nlo, "signal_photons": nsignal,
        "lo_to_signal_photon_ratio": nlo/max(nsignal, 1e-300),
        "finite_lo_relative_variance": finite_lo_variance/max(coefficient**2*variance, 1e-300),
        "responsivity_a_w_from_efficiency": efficiency*Q/(H*optical_frequency_hz),
        "current_per_detected_quadrature_a": coefficient,
        "effective_lo_power_overlap": overlap,
        "effective_lo_phase_rad": phase_rad,
        "individual_diode_mean_current_a": diode_currents,
        "individual_diode_dc_equivalent_voltage_v": [v*transimpedance_v_a for v in diode_currents],
    }


def gaussian_fisher(mean_derivative, covariance, covariance_derivative):
    """Classical FI of a normalized nonsingular multivariate Gaussian likelihood."""
    derivative, covariance, cp = [np.asarray(v, float) for v in [mean_derivative, covariance, covariance_derivative]]
    if covariance.shape != cp.shape or covariance.shape != (len(derivative), len(derivative)):
        raise QuantumError("Fisher mean/covariance dimensions differ.")
    if not all(np.isfinite(v).all() for v in [derivative, covariance, cp]):
        raise QuantumError("Fisher inputs must be finite.")
    if not np.allclose(covariance, covariance.T) or not np.allclose(cp, cp.T):
        raise QuantumError("Fisher covariance and its derivative must be symmetric.")
    if np.linalg.eigvalsh(covariance).min() <= 0:
        raise QuantumError("Fisher likelihood covariance must be positive definite.")
    mean_term = float(derivative @ np.linalg.solve(covariance, derivative))
    weighted = np.linalg.solve(covariance, cp)
    covariance_term = float(.5*np.trace(weighted @ weighted))
    return {"total_per_hz2": max(0., mean_term+covariance_term),
            "mean_per_hz2": max(0., mean_term), "covariance_per_hz2": max(0., covariance_term)}


def passive_mixer(mode_count, angle_rad):
    """Real orthogonal adjacent beam-splitter network, fixed independently of theta."""
    if int(mode_count) != mode_count or mode_count < 1 or not np.isfinite(angle_rad):
        raise QuantumError("Passive mixer requires a positive integer mode count and finite angle.")
    u = np.eye(mode_count)
    cs, sn = math.cos(angle_rad), math.sin(angle_rad)
    for j in range(mode_count-1):
        rotation = np.eye(mode_count)
        rotation[j:j+2,j:j+2] = [[cs, -sn], [sn, cs]]
        u = rotation @ u
    symplectic = np.kron(u, np.eye(2))
    if not np.allclose(symplectic @ omega(mode_count) @ symplectic.T, omega(mode_count), atol=1e-12):
        raise QuantumError("Passive mixer did not preserve commutators.")
    return u, symplectic


def _scalar_fisher(weight, derivative, covariance, covariance_derivative):
    weight = np.asarray(weight, float)
    norm = np.linalg.norm(weight)
    if norm < 1e-30:
        weight = np.ones(len(weight))/math.sqrt(len(weight))
    else:
        weight = weight / norm
    result = gaussian_fisher([weight @ derivative], [[weight @ covariance @ weight]],
                             [[weight @ covariance_derivative @ weight]])
    return dict(result, weights=weight.tolist())


def _single_readout_candidates(derivative, covariance, covariance_derivative):
    m = len(derivative)
    equal = _scalar_fisher(np.ones(m), derivative, covariance, covariance_derivative)
    mean_optimal = _scalar_fisher(np.linalg.solve(covariance, derivative), derivative, covariance, covariance_derivative)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    invsqrt = eigenvectors @ np.diag(eigenvalues**-.5) @ eigenvectors.T
    slopes, vectors = np.linalg.eigh(invsqrt @ covariance_derivative @ invsqrt)
    covariance_optimal = _scalar_fisher(invsqrt @ vectors[:,np.argmax(abs(slopes))],
                                        derivative, covariance, covariance_derivative)
    candidates = {"equal_weight": equal, "mean_optimal": mean_optimal, "covariance_optimal": covariance_optimal}
    best = max(candidates, key=lambda key: candidates[key]["total_per_hz2"])
    return dict(candidates=candidates, best_candidate=best, best=candidates[best],
                qualification="Best of three fixed local projections, not a global optimum of total Fisher information.")


def _multimode(gain, gain_derivative, n_bath, transmission, total_photons, optical_frequency,
               options, bandwidth, finite_lo_valid):
    m, duration = options["mode_count"], options["mode_duration_s"]
    single_duration = duration/m
    if single_duration*bandwidth < 10:
        raise QuantumError("Temporal bins are too short for the receiver bandwidth: require (mode_duration_s/mode_count)*bandwidth_hz >= 10.")
    # A Markov acoustic bath is a declared approximation, enforced away from its memory time.
    efficiency = options["quantum_efficiency"]
    matched_efficiency = efficiency*options["lo_mode_overlap"]
    phi = math.radians(options["lo_phase_deg"])
    phase = math.radians(options["input_phase_deg"])
    axis = math.radians(options["squeeze_angle_deg"])
    squeeze = options["squeeze_r"]
    d, v, dp, vp = np.zeros(2*m), np.zeros((2*m,2*m)), np.zeros(2*m), np.zeros((2*m,2*m))
    inputs = []
    for j in range(m):
        rangle = axis + (math.pi/2 if options["alternate_squeeze_axes"] and j%2 else 0.)
        di, vi = input_state(total_photons/m, squeeze, phase, rangle)
        do, vo, _ = amplifier_loss(di, vi, gain, n_bath, transmission*matched_efficiency)
        sl = slice(2*j, 2*j+2)
        d[sl], v[sl,sl] = do, vo
        dp[sl] = .5*gain_derivative/gain*do
        vp[sl,sl] = transmission*matched_efficiency*gain_derivative*(vi+(n_bath+.5)*np.eye(2))
        inputs.append({"index": j, "start_s": j*single_duration, "stop_s": (j+1)*single_duration,
                       "input_photons": photon_number(di, vi), "squeezing_photons": math.sinh(squeeze)**2})
    u, symplectic = passive_mixer(m, math.radians(options["mixing_angle_deg"]))
    conditional_d, conditional_v = d.copy(), v.copy()
    d, v, gaussian = phase_average_moments(d, v, options["phase_jitter_std_rad"])
    mixed_d, mixed_v = symplectic @ d, symplectic @ v @ symplectic.T
    uncertainty_tolerance = max(1e-9, float(np.max(abs(mixed_v)))*1e-12)
    physicality(mixed_v, tolerance=uncertainty_tolerance)
    e = np.array([math.cos(phi), math.sin(phi)])
    projection = np.kron(np.eye(m), e.reshape(1,2))
    mean, covariance = projection@d, projection@v@projection.T
    derivative, covariance_derivative = projection@dp, projection@vp@projection.T
    # Same total LO photons and elapsed duration, divided equally into bins.
    nlo = options["lo_power_w"]*duration/(H*optical_frequency)
    electronics_quadrature = options["electronics_noise_a_rt_hz"]**2*duration/(4*Q**2*efficiency*nlo)
    covariance += electronics_quadrature*np.eye(m)
    mixed_mean, mixed_covariance = u@mean, u@covariance@u.T
    mixed_derivative, mixed_covariance_derivative = u@derivative, u@covariance_derivative@u.T
    # Both pre-mixer and post-mixer homodyne outputs must meet the bright-LO gate.
    # The finite-LO correction uses true detected signal photons, including modes
    # orthogonal to the LO; reconstruct physical states before detector loss here.
    physical_ds, physical_vs = np.zeros(2*m), np.zeros((2*m, 2*m))
    for j in range(m):
        rangle = axis + (math.pi/2 if options["alternate_squeeze_axes"] and j%2 else 0.)
        di, vi = input_state(total_photons/m, squeeze, phase, rangle)
        physical_ds[2*j:2*j+2], physical_vs[2*j:2*j+2,2*j:2*j+2], _ = amplifier_loss(di,vi,gain,n_bath,transmission)
    worst_correction = 0.
    largest_diode_voltage = 0.
    for basis in [np.eye(2*m), symplectic]:
        state_d, state_v = basis@physical_ds, basis@physical_vs@basis.T
        for j in range(m):
            sl = slice(2*j,2*j+2)
            moment = homodyne(state_d[sl], state_v[sl,sl], optical_frequency, single_duration,
                              options["lo_power_w"], phi, efficiency, options["homodyne_transimpedance_v_a"],
                              options["electronics_noise_a_rt_hz"], options["lo_mode_overlap"])
            worst_correction = max(worst_correction, moment["finite_lo_relative_variance"])
            largest_diode_voltage = max(largest_diode_voltage, max(moment["individual_diode_dc_equivalent_voltage_v"]))
            if max(abs(moment["difference_voltage_v"]), max(moment["individual_diode_dc_equivalent_voltage_v"])) > options["homodyne_max_voltage_v"]:
                raise QuantumError("A temporal-mode balanced-receiver output or individual diode exceeds homodyne_max_voltage_v; reduce LO/probe power or balanced transimpedance.")
    finite_lo_valid = finite_lo_valid and worst_correction <= .01
    enabled = options["phase_jitter_std_rad"] == 0 and options["lo_detuning_hz"] == 0 and finite_lo_valid
    fi = None
    if enabled:
        joint = gaussian_fisher(derivative, covariance, covariance_derivative)
        mixed_joint = gaussian_fisher(mixed_derivative, mixed_covariance, mixed_covariance_derivative)
        candidates = _single_readout_candidates(derivative, covariance, covariance_derivative)
        reduced = _scalar_fisher(np.eye(m)[0], mixed_derivative, mixed_covariance, mixed_covariance_derivative)
        # Coherent preparation reference: same M, total incident photons, T, LO, G, bath and losses.
        coherent_d, coherent_v = input_state(total_photons/m, phase_rad=phase)
        coherent_do, coherent_vo, _ = amplifier_loss(coherent_d, coherent_v, gain, n_bath, transmission*matched_efficiency)
        coherent_dp = .5*gain_derivative/gain*coherent_do
        coherent_vp = transmission*matched_efficiency*gain_derivative*(coherent_v+(n_bath+.5)*np.eye(2))
        coherent_derivative = np.full(m, e@coherent_dp)
        coherent_covariance = np.eye(m)*(e@coherent_vo@e+electronics_quadrature)
        coherent_covariance_derivative = np.eye(m)*(e@coherent_vp@e)
        coherent_joint = gaussian_fisher(coherent_derivative, coherent_covariance, coherent_covariance_derivative)
        fi = {
            "independent_joint": joint, "passively_mixed_joint": mixed_joint,
            "single_collective_readout": candidates, "reduced_first_mixed_mode": reduced,
            "same_budget_coherent_joint": coherent_joint,
            "joint_minus_best_single_candidate_per_hz2": joint["total_per_hz2"]-candidates["best"]["total_per_hz2"],
            "configured_minus_coherent_per_hz2": joint["total_per_hz2"]-coherent_joint["total_per_hz2"],
            "mixing_invariance_absolute_error": abs(joint["total_per_hz2"]-mixed_joint["total_per_hz2"]),
        }
    return {
        "mode_basis": "u_j(t)=sqrt(M/T) exp[-i phi_probe(t)] on [jT/M,(j+1)T/M), zero otherwise; carrier-rotating frame",
        "orthonormal_gram": np.eye(m).tolist(), "modes": inputs,
        "total_input_photons": total_photons, "total_lo_photons": nlo,
        "total_observation_s": duration, "temporal_bin_duration_s": single_duration,
        "receiver_bandwidth_hz": bandwidth,
        "assumed_noise_bandwidth_resource_hz": m/(2*duration),
        "d": d.tolist(), "V": v.tolist(), "mixed_d": mixed_d.tolist(), "mixed_V": mixed_v.tolist(),
        "is_exact_gaussian_under_model": gaussian,
        "phase_jitter_model": "A single unobserved phase rotation shared by all temporal bins; d/V are exact mixture moments, not a Gaussian declaration.",
        "mixing_unitary_real": u.tolist(), "homodyne_mean": mean.tolist(),
        "homodyne_covariance": covariance.tolist(), "mixed_homodyne_mean": mixed_mean.tolist(),
        "mixed_homodyne_covariance": mixed_covariance.tolist(),
        "max_mixed_cross_covariance": float(np.max(abs(mixed_covariance-np.diag(np.diag(mixed_covariance))))),
        "minimum_uncertainty_eigenvalue": physicality(mixed_v, tolerance=uncertainty_tolerance),
        "uncertainty_numerical_tolerance": uncertainty_tolerance,
        "worst_finite_lo_relative_variance": worst_correction,
        "largest_individual_diode_dc_equivalent_voltage_v": largest_diode_voltage,
        "fisher_information": fi,
        "fisher_parameter": "theta_hz: common translation G_theta(f)=G_0(f-theta), with bath occupation held fixed",
        "fisher_status": "Bright-LO Gaussian homodyne approximation" if enabled else "Not evaluated: phase mixture, LO detuning, or insufficient bright-LO limit.",
        "qualification": "Same physical M-mode field and equal incident photons, LO photons, observation time and available bandwidth for every readout. Single-mode readout discards orthogonal output modes. More thermal covariance information is not a claim of quantum advantage. Real passive joint mixing cannot create FI.",
    }


def analyze_quantum(classical_result, options=None):
    """JSON-safe quantum/homodyne arrays and a resource-matched local FI comparison."""
    o = validate_options(options)
    if not o["enabled"]:
        return {"enabled": False, "options": o}
    config = classical_result["config"]
    gains = np.asarray(classical_result["gain_spectra"], float)
    frequencies = np.asarray(classical_result["frequency_hz"], float)
    positions = np.asarray(classical_result["positions_m"], float)
    if gains.shape != (len(positions), len(frequencies)) or len(frequencies) < 3:
        raise QuantumError("Quantum analysis needs a position-by-frequency gain array and at least three frequencies.")
    if not np.isfinite(gains).all() or np.any(gains < 0) or np.any(np.diff(frequencies) <= 0):
        raise QuantumError("Effective amplifier requires finite nonnegative gain and strictly increasing frequencies.")
    gain = 1 + gains
    derivative = -np.gradient(gain, frequencies, axis=1, edge_order=2)
    budget = classical_result["power_budget"]
    probe_in, probe_det = float(budget["probe_fiber_input_w"]), float(budget["probe_detector_no_sbs_w"])
    if probe_in <= 0 or probe_det < 0 or probe_det > probe_in*(1+1e-12):
        raise QuantumError("Quantum power normalization requires positive input probe and passive detector transmission.")
    transmission = min(1., probe_det/probe_in)
    optical_frequency = C/(float(config["laser"]["wavelength_nm"])*1e-9)
    duration = o["mode_duration_s"]
    photons = probe_in*duration/(H*optical_frequency)
    n_bath = thermal_occupation(o["bath_frequency_hz"], o["temperature_k"])
    di, vi = input_state(photons, o["squeeze_r"], math.radians(o["input_phase_deg"]),
                         math.radians(o["squeeze_angle_deg"]))
    bandwidth = float(config["receiver"]["bandwidth_hz"])
    linewidth = min(float(s["linewidth_hz"]) for s in config["segments"])
    if duration/o["mode_count"] * math.pi*linewidth < 100:
        raise QuantumError("Temporal modes must be much longer than acoustic memory: require bin_duration*pi*minimum_linewidth_hz >= 100.")
    if duration > float(config["receiver"]["dwell_s"]):
        raise QuantumError("Quantum mode_duration_s must not exceed the available dwell_s at one spectrum setting.")
    selected_position = int(np.argmin(abs(positions-float(config["scan"]["target_m"]))))
    selected_frequency = int(np.argmin(abs(frequencies-o["selected_frequency_hz"])))
    array_fields = ["quadrature_mean", "quadrature_variance", "difference_current_a",
                    "difference_current_variance_a2", "difference_voltage_v", "difference_voltage_variance_v2",
                    "finite_lo_relative_variance", "signal_photons"]
    arrays = {key: np.empty_like(gain) for key in array_fields}
    selected = None
    for i in range(len(positions)):
        for j in range(len(frequencies)):
            d, v, checks = amplifier_loss(di, vi, float(gain[i,j]), n_bath, transmission)
            d, v, gaussian = phase_average_moments(d, v, o["phase_jitter_std_rad"])
            measurement = homodyne(d, v, optical_frequency, duration, o["lo_power_w"],
                                   math.radians(o["lo_phase_deg"]), o["quantum_efficiency"],
                                   o["homodyne_transimpedance_v_a"], o["electronics_noise_a_rt_hz"],
                                   o["lo_mode_overlap"], o["lo_detuning_hz"])
            if max(abs(measurement["difference_voltage_v"]), max(measurement["individual_diode_dc_equivalent_voltage_v"])) > o["homodyne_max_voltage_v"]:
                raise QuantumError("Balanced receiver difference output or an individual photodiode exceeds homodyne_max_voltage_v; reduce lo_power_w, probe power or homodyne_transimpedance_v_a.")
            for key in array_fields:
                arrays[key][i,j] = measurement[key]
            if (i,j) == (selected_position,selected_frequency):
                selected = {
                    "position_m": float(positions[i]), "frequency_hz": float(frequencies[j]),
                    "effective_amplifier_gain": float(gain[i,j]), "gain_derivative_per_hz": float(derivative[i,j]),
                    "d": d.tolist(), "V": v.tolist(), "is_exact_gaussian_under_model": gaussian,
                    "is_displaced_thermal": bool(gaussian and np.allclose(v, np.eye(2)*np.trace(v)/2)),
                    "measurement": measurement, "channel_checks_before_phase_mixture": checks,
                    "thermal_photons_if_displaced_thermal": float(np.trace(v)/2-.5) if gaussian and np.allclose(v,np.eye(2)*np.trace(v)/2) else None,
                }
    assert selected is not None
    finite_lo_valid = selected["measurement"]["finite_lo_relative_variance"] <= .01
    multi = _multimode(selected["effective_amplifier_gain"], selected["gain_derivative_per_hz"], n_bath,
                       transmission, photons, optical_frequency, o, bandwidth, finite_lo_valid)
    warnings = [
        "Effective independent selected-mode amplifier with G=1+classical integrated gain, then lumped passive loss. It reproduces the weak-gain coherent mean, not a full quantum Floquet scattering matrix.",
        "The bath occupation uses acoustic GHz; photon-energy calibration uses optical c/lambda. Bath temperature, mode selection and LO matching are explicit assumptions.",
        "Homodyne replaces the receiver with a frequency/FM-history/delay/polarization-matched LO. It is not the original intensity lock-in measurement.",
        "Per-spectrum temporal modes use an explicitly stationary cycle-averaged channel, not pump-tag-resolved quantum sidebands.",
        "The FI derivative is a finite-frequency-grid translation of the complete measured gain spectrum, not a per-segment oracle. Check frequency-grid convergence.",
        "Finite-LO current moments include signal-photon noise exactly; FI uses the bright-LO Gaussian quadrature limit and is suppressed when that correction exceeds 1%.",
        "Squeezing photons count against the same total incident probe photons. A configured squeezing benefit is not evidence of genuine multimode advantage or an optimized protocol.",
    ]
    if not finite_lo_valid or multi["worst_finite_lo_relative_variance"] > .01:
        warnings.append("LO is insufficient for the declared Gaussian-FI accuracy gate; increase lo_power_w. Finite-LO moment outputs remain available.")
    if o["phase_jitter_std_rad"] > 0:
        warnings.append("Unobserved phase jitter produces a generally non-Gaussian mixture. Displayed d/V are exact moments, not a complete Gaussian-state description; Gaussian FI is disabled.")
    if o["lo_detuning_hz"] != 0:
        warnings.append("Residual LO detuning is modeled in the single-mode receiver by its complex rectangular-mode overlap. Multimode FI is disabled because different temporal bins acquire different phases; its displayed covariance is the conditional frequency-matched reference, not a prediction for the mismatched receiver.")
    actual_controls = classical_result.get("controls") or [{"frequency_hz": config["fm"]["frequency_hz"]}]
    actual_fm_frequencies = [float(control["frequency_hz"]) for control in actual_controls]
    minimum_fm_cycles = duration/o["mode_count"] * min(actual_fm_frequencies)
    if minimum_fm_cycles < 10:
        warnings.append("Each temporal bin contains fewer than ten FM cycles; the stationary cycle-averaged quantum-channel approximation may be inaccurate.")
    if selected_frequency in (0,len(frequencies)-1):
        warnings.append("Selected FI setting lies at a scan boundary; its one-sided frequency derivative is less reliable.")
    return {
        "enabled": True, "options": o, "frequency_hz": frequencies.tolist(), "positions_m": positions.tolist(),
        **{key: value.tolist() for key,value in arrays.items()},
        "selected": selected, "multimode": multi,
        "input_d": di.tolist(), "input_V": vi.tolist(), "input_total_photons": photons,
        "diagnostics": {"minimum_actual_fm_cycles_per_temporal_bin": minimum_fm_cycles,
                        "actual_fm_frequencies_hz": actual_fm_frequencies,
                        "worst_finite_lo_relative_variance": multi["worst_finite_lo_relative_variance"],
                        "fisher_status": multi["fisher_status"]},
        "optical_frequency_hz": optical_frequency, "bath_occupation": n_bath, "passive_transmission": transmission,
        "quadrature_convention": "[x,p]=i; V_vac=I/2; photon number=(d.d+trace(V)-number_of_modes)/2",
        "mode_definition": "u(t)=exp[-i phi_probe(t)]/sqrt(T) within [0,T], zero outside, in a carrier-rotating frame; LO must match this complete optical phase history.",
        "electrical_convention": "Balanced difference current averaged over a rectangular T, not lock-in peak volts. Responsivity=eta*e/(h*nu_opt); dedicated balanced-receiver transimpedance and per-diode/difference headroom are explicit options, separate from the original PD/LIA.",
        "warnings": warnings,
    }
