"""Classical, weak-gain BOCDA model. See docs/physics.md for conventions."""
from __future__ import annotations

from copy import deepcopy
from math import ceil, factorial, pi
from typing import Callable

import numpy as np
from scipy.linalg import expm
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
from scipy.special import jv


class ModelError(ValueError):
    """Actionable invalid-input or model-validity error."""


def _number(value, label, lower=None, upper=None, strict=False):
    try:
        v = float(value)
    except (TypeError, ValueError) as exc:
        raise ModelError(f"{label} must be a finite number.") from exc
    if not np.isfinite(v):
        raise ModelError(f"{label} must be finite.")
    if lower is not None and (v <= lower if strict else v < lower):
        raise ModelError(f"{label} must be {'greater than' if strict else 'at least'} {lower}.")
    if upper is not None and v > upper:
        raise ModelError(f"{label} must be at most {upper}.")
    return v


def validate_config(config):
    """Validate required fields and resolve units without changing the caller's object."""
    c = deepcopy(config)
    positive = {
        'fm': ['frequency_hz', 'group_velocity_m_s'],
        'laser': ['wavelength_nm'],
        'pump': ['modulation_hz', 'edfa_max_w'],
        'receiver': ['responsivity_a_w', 'transimpedance_v_a', 'bandwidth_hz',
                     'max_voltage_v', 'time_constant_s', 'dwell_s'],
        'scan': ['frequency_start_hz', 'frequency_stop_hz', 'frequency_step_hz', 'cell_m'],
    }
    nonnegative = {'fm': ['excursion_hz'], 'laser': ['power_w'],
                   'splitter': ['loss_db'],
                   'pump': ['eom_loss_db', 'circulator_loss_db'],
                   'probe': ['eom_loss_db', 'isolator_loss_db']}
    try:
        for group, keys in positive.items():
            for key in keys:
                c[group][key] = _number(c[group][key], f'{group}.{key}', 0, strict=True)
        for group, keys in nonnegative.items():
            for key in keys:
                c[group][key] = _number(c[group][key], f'{group}.{key}', 0)
        for group, key in [('fm', 'delay_s'), ('fm', 'phase_rad'),
                           ('pump', 'phase_deg'), ('pump', 'edfa_gain_db'),
                           ('receiver', 'reference_phase_deg')]:
            c[group][key] = _number(c[group].get(key, 0), f'{group}.{key}')
        for group, key in [('splitter', 'pump_fraction'), ('probe', 'pc_overlap'),
                           ('pump', 'modulation_depth')]:
            c[group][key] = _number(c[group][key], f'{group}.{key}', 0, 1)
        order = _number(c['fm'].get('correlation_order', 1), 'fm.correlation_order')
        if int(order) != order:
            raise ModelError('fm.correlation_order must be an integer.')
        c['fm']['correlation_order'] = int(order)
        fo = _number(c['receiver'].get('filter_order', 1), 'receiver.filter_order', 1, 4)
        if int(fo) != fo:
            raise ModelError('receiver.filter_order must be an integer from 1 to 4.')
        c['receiver']['filter_order'] = int(fo)
        if c['fm'].get('excursion_convention') == 'peak_to_peak':
            c['fm']['excursion_convention'] = 'peak-to-peak'
        if c['fm'].get('excursion_convention') not in ('peak', 'peak-to-peak'):
            raise ModelError("fm.excursion_convention must be 'peak' or 'peak-to-peak'.")
        if c['scan'].get('position_control', 'frequency') not in ('frequency', 'delay', 'fixed'):
            raise ModelError("scan.position_control must be frequency, delay, or fixed.")
        segments = c['segments']
        if not isinstance(segments, list) or not segments:
            raise ModelError('At least one fiber segment is required.')
        for i, seg in enumerate(segments):
            for key in ['length_m', 'resonance_hz', 'linewidth_hz']:
                seg[key] = _number(seg[key], f'segments[{i}].{key}', 0, strict=True)
            for key in ['gain_per_w_m', 'attenuation_db_km']:
                seg[key] = _number(seg[key], f'segments[{i}].{key}', 0)
        length = _number(sum(s['length_m'] for s in segments), 'Total fiber length', 0, strict=True)
        for key in ['target_m', 'start_m', 'stop_m']:
            c['scan'][key] = _number(c['scan'][key], f'scan.{key}', 0, length)
        c['scan']['step_m'] = _number(c['scan']['step_m'], 'scan.step_m', 0, strict=True)
        if c['scan']['stop_m'] < c['scan']['start_m']:
            raise ModelError('Scan stop position must not be below start position.')
        if c['scan']['frequency_stop_hz'] <= c['scan']['frequency_start_hz']:
            raise ModelError('Frequency stop must exceed frequency start.')
        if c['scan'].get('background_subtraction', False):
            raise ModelError('Background subtraction is not implemented: use the raw physical response.')
        if c['pump']['modulation_depth'] > .3:
            raise ModelError('This first-order pump-tag model requires modulation_depth <= 0.3.')
    except KeyError as exc:
        raise ModelError(f'Missing configuration field: {exc.args[0]}') from exc
    return c


def peak_excursion(config):
    fm = config['fm']
    return fm['excursion_hz'] / (2 if fm['excursion_convention'] == 'peak-to-peak' else 1)


def fiber_grid(config):
    """Midpoint cells aligned exactly to every physical segment boundary."""
    counts, total = [], 0
    for seg in config['segments']:
        ratio = seg['length_m'] / config['scan']['cell_m']
        if not np.isfinite(ratio) or ratio > 30000 - total:
            raise ModelError('More than 30000 cells requested; increase numerical cell size.')
        count = max(1, int(ceil(ratio)))
        total += count
        if total > 30000:
            raise ModelError('More than 30000 cells requested; increase numerical cell size.')
        counts.append(count)
    z, dz, labels, boundaries = [], [], [], [0.]
    for i, (seg, count) in enumerate(zip(config['segments'], counts)):
        width = seg['length_m'] / count
        z.extend(boundaries[-1] + (np.arange(count) + .5) * width)
        dz.extend([width] * count)
        labels.extend([i] * count)
        boundaries.append(boundaries[-1] + seg['length_m'])
    return np.array(z), np.array(dz), np.array(labels), np.array(boundaries)


def _sample_count(start, stop, step, maximum, label, minimum=1):
    """Preflight the existing arange(start, stop + .01*step, step) convention."""
    extended_stop = stop + .01 * step
    ratio = (extended_stop - start) / step
    if not np.isfinite(ratio) or ratio > maximum:
        raise ModelError(f'{label} exceeds {maximum} samples; increase its step or reduce its span.')
    count = max(0, int(ceil(ratio)))
    if count < minimum:
        raise ModelError(f'{label} requires at least {minimum} samples; decrease its step or increase its span.')
    return count


def controls_for_target(config, target_m):
    """tau_pump - tau_probe = external_delay + (2*z-L)/vg."""
    f = config['fm']
    length = sum(s['length_m'] for s in config['segments'])
    vg, order = f['group_velocity_m_s'], f['correlation_order']
    freq, delay = f['frequency_hz'], f['delay_s']
    control = config['scan'].get('position_control', 'frequency')
    if control == 'frequency':
        if order == 0:
            raise ModelError('The order-zero equal-delay peak does not move when fm changes; use delay control or nonzero correlation_order.')
        denominator = delay + (2 * target_m - length) / vg
        if denominator == 0 or order / denominator <= 0:
            raise ModelError('Requested target/order requires a non-positive modulation frequency; change external delay/order.')
        freq = order / denominator
    elif control == 'delay':
        delay = order / freq - (2 * target_m - length) / vg
    peak = (length + vg * (order / freq - delay)) / 2
    return {'target_m': float(target_m), 'frequency_hz': float(freq),
            'delay_s': float(delay), 'peak_m': float(peak), 'order': int(order)}


def fm_difference_amplitude(z, length, control, config):
    dt = control['delay_s'] + (2 * np.asarray(z) - length) / config['fm']['group_velocity_m_s']
    # Remainder improves cancellation close to integer cycles / correlation peaks.
    cycles = control['frequency_hz'] * dt
    cycles -= np.rint(cycles)
    return 2 * peak_excursion(config) * np.sin(pi * cycles)


def floquet_weights(beta, padding=0):
    """Nonnegative-order J_n(beta)^2; negative orders have identical weights."""
    b = np.abs(np.atleast_1d(beta))
    largest = float(np.max(b)) if b.size else 0.
    nmax = int(ceil(largest + 12 * np.cbrt(largest + 1) + 24 + padding))
    if nmax > 20000 or b.size * (nmax + 1) > 30000000:
        raise ModelError('FM sideband calculation exceeds the interactive model size limit; shorten fiber or reduce excursion, then refine in stages.')
    n = np.arange(nmax + 1)
    weights = jv(n[None, :], b[:, None]) ** 2
    mass = weights[:, 0] + 2 * weights[:, 1:].sum(axis=1)
    if np.max(np.abs(mass - 1)) > 1e-8:
        raise ModelError('FM sideband truncation failed normalization tolerance.')
    return n, weights


def susceptibilities(detuning_hz, n, fm_hz, linewidth_hz, tag_hz=0):
    """Paired DC response and first-order pump intensity-tag susceptibility."""
    d = np.atleast_1d(detuning_hz)[None, :]
    shift = n[:, None] * fm_hz
    def branch(offset):
        q = d + offset
        h0 = 1 / (1 + 2j * q / linewidth_hz)
        hp = 1 / (1 + 2j * (q + tag_hz) / linewidth_hz)
        hm = 1 / (1 + 2j * (q - tag_hz) / linewidth_hz)
        return h0.real, .5 * h0.real + .25 * (hp + hm.conj())
    dc, ac = branch(shift)
    dcminus, acminus = branch(-shift)
    dc[1:] += dcminus[1:]
    ac[1:] += acminus[1:]
    return dc, ac


def floquet_response(beta, detuning_hz, fm_hz, linewidth_hz, padding=0):
    n, w = floquet_weights(beta, padding)
    dc, _ = susceptibilities(detuning_hz, n, fm_hz, linewidth_hz)
    return w @ dc


def quasistatic_response(amplitude_hz, detuning_hz, linewidth_hz):
    """Analytic cycle average of a quasi-static Lorentzian (comparison only)."""
    amplitude = np.asarray(amplitude_hz)[:, None]
    delta = np.atleast_1d(detuning_hz)[None, :]
    a = 1 + 2j * delta / linewidth_hz
    return np.real(1 / np.sqrt(a * a + (2 * amplitude / linewidth_hz) ** 2))


def power_budget(config, z, dz, labels):
    def tr(db):
        return 10 ** (-db / 10)
    laser = config['laser']['power_w']
    split = config['splitter']
    transmitted = laser * tr(split['loss_db'])
    pump_split = transmitted * split['pump_fraction']
    probe_split = transmitted * (1 - split['pump_fraction'])
    p = config['pump']
    pump_eom = pump_split * tr(p['eom_loss_db'])
    amplified = pump_eom * 10 ** (p['edfa_gain_db'] / 10)
    if amplified * (1 + p['modulation_depth']) > p['edfa_max_w']:
        raise ModelError('EDFA peak output exceeds edfa_max_w; reduce gain/input/depth. Saturation dynamics are not modeled.')
    pump_in = amplified * tr(p['circulator_loss_db'])
    pr = config['probe']
    probe_in = probe_split * tr(pr['eom_loss_db'] + pr['isolator_loss_db'])
    alpha = np.array([config['segments'][i]['attenuation_db_km'] for i in labels]) / 1000
    incremental_db = alpha * dz
    cumulative_db = np.cumsum(incremental_db) - .5 * incremental_db
    pump_cells = pump_in * tr(cumulative_db)
    total_db = float(incremental_db.sum())
    probe_detector = probe_in * tr(total_db + p['circulator_loss_db'])
    budget = {'laser_w': laser, 'splitter_output_sum_w': transmitted,
              'splitter_pump_w': pump_split, 'splitter_probe_w': probe_split,
              'pump_after_eom_w': pump_eom, 'pump_after_edfa_w': amplified,
              'pump_fiber_input_w': pump_in, 'probe_fiber_input_w': probe_in,
              'probe_detector_no_sbs_w': probe_detector,
              'fiber_loss_db': total_db, 'pump_peak_edfa_w': amplified * (1 + p['modulation_depth'])}
    return budget, pump_cells


def lockin_filter(signal, time_constant_s, dwell_s, order=1):
    """End-of-dwell samples for cascaded RC stages, starting at zero for a sweep."""
    a = -np.eye(order) / time_constant_s
    for k in range(1, order):
        a[k, k - 1] = 1 / time_constant_s
    transition = expm(a * dwell_s)
    state = np.zeros(order, complex)
    output = []
    for sample in signal:
        equilibrium = np.full(order, sample, complex)
        state = equilibrium + transition @ (state - equilibrium)
        output.append(state[-1])
    return np.asarray(output)


def estimate_resonance(frequency, values, nominal_linewidth):
    x, y = np.asarray(frequency, float) / 1e9, np.asarray(values, float)
    scale = float(np.ptp(y))
    if scale <= 1e-18:
        return {'resonance_hz': None, 'linewidth_hz': None, 'r_squared': None,
                'flags': ['no_signal'], 'peak_count': 0, 'peak_resonance_hz': None}
    yn = (y - y.min()) / scale
    peaks, _ = find_peaks(yn, prominence=.12,
                         distance=max(1, int(.5 * nominal_linewidth / ((x[1]-x[0])*1e9))))
    peak = int(np.argmax(y))
    def line(xx, base, amplitude, center, width):
        return base + amplitude / (1 + (2 * (xx - center) / width) ** 2)
    flags = []
    try:
        pars, _ = curve_fit(line, x, yn, p0=[0, 1, x[peak], nominal_linewidth/1e9],
                            bounds=([-2, 0, x[0], (x[1]-x[0])],
                                    [2, 5, x[-1], x[-1]-x[0]]), maxfev=5000)
        global_pred = line(x, *pars)
        global_r2 = 1 - float(np.sum((yn-global_pred)**2)/np.sum((yn-yn.mean())**2))
        # Off-peak FM background is broad and is not itself Lorentzian. Fit only
        # a local peak window, with a sloping background, without reading truth.
        window = abs(x-x[peak]) <= 1.25*nominal_linewidth/1e9
        xx, yy = x[window], yn[window]
        def local_line(v, base, slope, amplitude, center, width):
            return base+slope*(v-x[peak])+amplitude/(1+(2*(v-center)/width)**2)
        local, _ = curve_fit(local_line, xx, yy,
                p0=[float(yy.min()),0,float(np.ptp(yy)),x[peak],nominal_linewidth/1e9],
                bounds=([-5,-50,0,xx[0],x[1]-x[0]],
                        [5,50,10,xx[-1],10*nominal_linewidth/1e9]),maxfev=10000)
        pred = local_line(xx,*local)
        r2 = 1-float(np.sum((yy-pred)**2)/max(np.sum((yy-yy.mean())**2),1e-30))
        center,width=local[3]*1e9,local[4]*1e9
        if r2 < .98:
            flags.append('poor_local_lorentzian_fit')
        if abs(pars[2]-x[peak])*1e9 > .5*nominal_linewidth:
            flags.append('asymmetric_background_or_boundary_mixing')
        if len(peaks) > 1:
            flags.append('multiple_peaks_or_boundary_mixing')
        if peak in (0, len(x)-1):
            flags.append('peak_at_sweep_edge')
        return {'resonance_hz': float(center), 'linewidth_hz': float(width),
                'r_squared': r2, 'flags': flags, 'peak_count': int(len(peaks)),
                'peak_resonance_hz': float(x[peak]*1e9),
                'global_r_squared':global_r2, 'global_linewidth_hz':float(pars[3]*1e9),
                'fit_method':'local Lorentzian plus linear background around largest measured peak',
                'fit_frequency_hz':(xx*1e9).tolist(),
                'fitted_curve_v': (pred*scale+y.min()).tolist()}
    except (RuntimeError, ValueError):
        return {'resonance_hz': float(x[peak]*1e9), 'linewidth_hz': None,
                'r_squared': None, 'flags': ['fit_failed_using_sampled_peak'],
                'peak_count': int(len(peaks)), 'peak_resonance_hz': float(x[peak]*1e9)}


def spatial_diagnostic(config, control, linewidth_hz, samples=601):
    vg, fm = config['fm']['group_velocity_m_s'], control['frequency_hz']
    deviation = peak_excursion(config)
    spacing = vg / (2 * fm)
    approximate = vg * linewidth_hz / (2*pi*fm*deviation) if deviation else None
    if not deviation:
        return {'offset_m': [-spacing/2, 0., spacing/2], 'response': [1., 1., 1.],
                'fwhm_m': None, 'approx_resolution_m': None,
                'peak_spacing_m': spacing, 'quasistatic_max_abs_error': 0.}
    extent = min(2 * approximate, .49 * spacing)
    offset = np.linspace(-extent, extent, samples)
    amp = 2 * deviation * np.sin(2*pi*fm*offset/vg)
    dynamic = floquet_response(amp/fm, [0], fm, linewidth_hz)[:, 0]
    static = quasistatic_response(amp, [0], linewidth_hz)[:, 0]
    center = samples // 2
    below = np.flatnonzero(dynamic[center:] < .5)
    width = None
    if len(below):
        j = center + below[0]
        width = 2 * float(np.interp(.5, dynamic[j-1:j+1][::-1], offset[j-1:j+1][::-1]))
    return {'offset_m': offset.tolist(), 'response': dynamic.tolist(),
            'quasistatic_response': static.tolist(), 'fwhm_m': width,
            'approx_resolution_m': approximate, 'peak_spacing_m': spacing,
            'quasistatic_max_abs_error': float(np.max(np.abs(dynamic-static)))}


def simulate(config, mode='local', progress: Callable | None=None):
    """Run a local frequency sweep or a physical position scan, returning JSON-safe data."""
    c = validate_config(config)
    if mode not in ('local', 'scan'):
        raise ModelError("mode must be 'local' or 'scan'.")
    s, receiver, pump = c['scan'], c['receiver'], c['pump']
    # Complete scalar size checks before any cell/sweep array allocation.
    _sample_count(s['frequency_start_hz'], s['frequency_stop_hz'],
                  s['frequency_step_hz'], 5001, 'Frequency sweep', minimum=5)
    if mode == 'scan':
        _sample_count(s['start_m'], s['stop_m'], s['step_m'], 1001, 'Position scan')
    z, dz, labels, boundaries = fiber_grid(c)
    budget, pump_power = power_budget(c, z, dz, labels)
    frequency = np.arange(s['frequency_start_hz'], s['frequency_stop_hz']+.01*s['frequency_step_hz'], s['frequency_step_hz'])
    targets = np.array([s['target_m']]) if mode == 'local' else np.arange(s['start_m'], s['stop_m']+.01*s['step_m'], s['step_m'])
    if len(frequency) < 5 or len(frequency) > 5001 or len(targets) > 1001:
        raise ModelError('Use 5–5001 frequency samples and at most 1001 target positions.')
    if mode == 'scan' and s.get('position_control') == 'fixed':
        raise ModelError('A position scan requires frequency or delay control; fixed controls do not move the peak.')
    vg = c['fm']['group_velocity_m_s']
    tag = pump['modulation_hz']
    transport = np.exp(-2j*pi*tag*2*z/vg)
    detector = 1/(1+1j*tag/receiver['bandwidth_hz'])
    phase = np.exp(1j*np.deg2rad(pump['phase_deg']-receiver['reference_phase_deg']))
    voltage_factor = budget['probe_detector_no_sbs_w']*receiver['responsivity_a_w']*receiver['transimpedance_v_a']
    controls, spectra, steady, gains, fits, segment_contributions = [], [], [], [], [], []
    warnings = ['Demonstration parameters: voltages are model outputs, not calibrated experimental predictions.',
                'Classical first-order SBS gain and first-order pump intensity tag; quantum/noise/depletion excluded.']
    if s['frequency_step_hz'] > min(seg['linewidth_hz'] for seg in c['segments'])/5:
        warnings.append('Frequency sampling is coarse compared with the Brillouin linewidth.')
    for position_index, target in enumerate(targets):
        control = controls_for_target(c, float(target))
        guard=max(5/(2*pi*receiver['time_constant_s']),2/receiver['dwell_s'])
        for harmonic in (tag,2*tag):
            nearest=max(1,round(harmonic/control['frequency_hz']))
            if abs(nearest*control['frequency_hz']-harmonic)<guard:
                raise ModelError('Pump-tag frequency overlaps an FM harmonic within the lock-in averaging bandwidth; change modulation frequencies or use a full time-domain receiver.')
        controls.append(control)
        amp = fm_difference_amplitude(z, boundaries[-1], control, c)
        n, w = floquet_weights(amp/control['frequency_hz'])
        dc = np.zeros(len(frequency))
        ac = np.zeros(len(frequency), complex)
        contributions = []
        for i, seg in enumerate(c['segments']):
            cells = labels == i
            strength = dz[cells]*pump_power[cells]*seg['gain_per_w_m']*c['probe']['pc_overlap']
            weighted_dc = strength @ w[cells]
            weighted_ac = (strength*transport[cells]) @ w[cells]
            kdc, kac = susceptibilities(frequency-seg['resonance_hz'], n, control['frequency_hz'], seg['linewidth_hz'], tag)
            contribution = weighted_dc @ kdc
            dc += contribution
            ac += weighted_ac @ kac
            contributions.append(contribution.tolist())
        if np.max(dc)*(1+pump['modulation_depth']) > .1:
            raise ModelError('Integrated SBS gain exceeds 0.1: reduce pump power, gain coefficient, or fiber length for the linear weak-gain model.')
        voltage = voltage_factor*pump['modulation_depth']*ac*detector*phase
        filtered = lockin_filter(voltage, receiver['time_constant_s'], receiver['dwell_s'], receiver['filter_order'])
        if voltage_factor*(1+np.max(dc))+np.max(np.abs(voltage)) > receiver['max_voltage_v']:
            raise ModelError('Photodetector would saturate; reduce probe power or transimpedance gain.')
        steady.append(voltage)
        spectra.append(filtered)
        gains.append(dc)
        fits.append(estimate_resonance(frequency, np.abs(filtered), np.mean([seg['linewidth_hz'] for seg in c['segments']])))
        segment_contributions.append(contributions)
        if progress:
            progress(position_index+1, len(targets))
    spectra, steady, gains = np.asarray(spectra), np.asarray(steady), np.asarray(gains)
    max_gain = float(np.max(gains))
    if max_gain > .03:
        warnings.append('Integrated gain exceeds 0.03; the neglected exponential-gain correction is appreciable.')
    depletion = budget['probe_fiber_input_w']*max_gain/max(budget['pump_fiber_input_w'], 1e-300)
    if depletion > .01:
        raise ModelError('Estimated transferred probe power exceeds 1% of the pump; lower probe power for undepleted-pump consistency.')
    if budget['pump_fiber_input_w'] and budget['probe_fiber_input_w']/budget['pump_fiber_input_w'] > .01:
        warnings.append('Probe/pump input-power ratio exceeds 1%; inspect the weak-probe approximation.')
    nominal_linewidth = float(np.mean([seg['linewidth_hz'] for seg in c['segments']]))
    spatial_control=controls[int(np.argmin(abs(targets-s['target_m'])))]
    spatial = spatial_diagnostic(c, spatial_control, nominal_linewidth)
    spatial['reference_linewidth_hz'] = nominal_linewidth
    spatial['response_definition'] = 'Normalized response of a hypothetical local cell at its own resonance, using the mean configured linewidth.'
    if len(set(seg['linewidth_hz'] for seg in c['segments'])) > 1:
        warnings.append('The spatial-response plot uses mean configured linewidth; individual segments have different local response widths.')
    cell_amp = fm_difference_amplitude(z, boundaries[-1], spatial_control, c)
    spatial['z_m'] = z.tolist()
    spatial['cell_response'] = floquet_response(cell_amp/spatial_control['frequency_hz'], [0], spatial_control['frequency_hz'], nominal_linewidth)[:, 0].tolist()
    spatial['peak_m'] = spatial_control['peak_m']
    spatial['selected_control'] = spatial_control
    if spatial['fwhm_m'] and np.max(dz) > spatial['fwhm_m']/5:
        warnings.append('Numerical cells exceed one fifth of the measured spatial FWHM; refine the grid.')
    separation = spatial['peak_spacing_m']
    integer_min = int(ceil(spatial_control['frequency_hz']*(spatial_control['delay_s']-boundaries[-1]/vg)))
    integer_max = int(np.floor(spatial_control['frequency_hz']*(spatial_control['delay_s']+boundaries[-1]/vg)))
    peaks = [(boundaries[-1]+vg*(k/spatial_control['frequency_hz']-spatial_control['delay_s']))/2 for k in range(integer_min, integer_max+1)]
    spatial['correlation_peaks_m'] = peaks
    if len(peaks) > 1:
        warnings.append('Multiple correlation peaks lie inside the fiber; all contribute to the response.')
    r = receiver['dwell_s']/receiver['time_constant_s']
    residual = float(np.exp(-r)*sum(r**k/factorial(k) for k in range(receiver['filter_order'])))
    if residual > .01:
        warnings.append('End-of-dwell lock-in settling error exceeds 1%; spectra include frequency-step carryover.')
    if tag*receiver['time_constant_s'] < 10:
        warnings.append('Lock-in time constant is too short for clean rotating-wave averaging of the intensity tag.')
    return {'mode': mode, 'frequency_hz': frequency.tolist(), 'positions_m': targets.tolist(),
            'spectra_x_v': spectra.real.tolist(), 'spectra_y_v': spectra.imag.tolist(),
            'spectra_r_v': np.abs(spectra).tolist(), 'steady_x_v': steady.real.tolist(),
            'steady_y_v': steady.imag.tolist(), 'gain_spectra': gains.tolist(),
            'fitted_resonance_hz': [fit['resonance_hz'] for fit in fits], 'fits': fits,
            'segment_gain_contributions': segment_contributions,
            'fiber': {'z_m': z.tolist(), 'cell_width_m': dz.tolist(), 'segment_index': labels.tolist(),
                      'boundaries_m': boundaries.tolist(),
                      'resonance_hz': [c['segments'][i]['resonance_hz'] for i in labels]},
            'spatial': spatial, 'controls': controls, 'power_budget': budget,
            'diagnostics': {'max_integrated_gain': max_gain, 'estimated_pump_depletion_fraction': depletion,
                            'detector_baseline_v': voltage_factor, 'receiver_scaling': 'peak volts; factor-two IQ mixer',
                            'end_dwell_step_residual': residual, 'model': 'linear-acoustic Floquet / first-order SBS gain and intensity tag',
                            'configuration_provenance': 'paper values plus explicitly assumed demonstration settings'},
            'warnings': warnings, 'config': c}
