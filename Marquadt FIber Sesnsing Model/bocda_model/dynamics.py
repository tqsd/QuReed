"""Counterpropagating optical/acoustic SBS envelope initial-boundary-value solver."""
from __future__ import annotations
from copy import deepcopy
from math import ceil, pi
import numpy as np
from .physics import ModelError, validate_config, controls_for_target, peak_excursion


def schema():
    return {
        'cells': {'default':40,'type':'int','min':8,'max':200,'description':'Uniform propagation cells; dt=dz/vg'},
        'duration_ns': {'default':150.,'type':'float','min':1.,'max':2000.,'description':'Transient duration (ns); not a full FM-cycle average'},
        'output_frames': {'default':151,'type':'int','min':10,'max':501,'description':'Saved time-position frames'},
        'pump_scale': {'default':1.,'type':'float','min':0.,'max':100.,'description':'Demonstration pump boundary power multiplier'},
        'probe_scale': {'default':50.,'type':'float','min':0.,'max':1000.,'description':'Strong-probe demonstration multiplier'},
        'gain_scale': {'default':100.,'type':'float','min':0.,'max':10000.,'description':'Demonstration local coupling multiplier'},
        'offset_ghz': {'default':10.90,'type':'float','min':0.1,'max':30.,'description':'Pump minus probe offset (GHz)'},
        'fm_enabled': {'default':True,'type':'bool','description':'Use actual delayed common sinusoidal optical FM'},
        'boundary_rise_ns': {'default':2.,'type':'float','min':.01,'max':100.,'description':'Exponential intensity turn-on time (ns)'},
        'initial_acoustic_scale': {'default':0.,'type':'float','min':0.,'max':1.,'description':'Initial normalized acoustic seed relative to sqrt(Pp Ps)'},
        'convergence_check': {'default':True,'type':'bool','description':'Repeat at twice the spatial resolution and half dt'},
        'refinement_rtol': {'default':.01,'type':'float','min':1e-8,'max':.5,'description':'Maximum relative RMS boundary refinement error'},
        'refinement_atol_w': {'default':1e-9,'type':'float','min':0.,'max':.01,'unit':'W','description':'Absolute RMS boundary refinement tolerance, including near-zero outputs'},
    }


def default_options():
    return {key:meta['default'] for key,meta in schema().items()}


def _options(options):
    result=default_options()
    if options: result.update(options)
    for key,meta in schema().items():
        v=result[key]
        if meta['type']=='bool':
            if not isinstance(v,bool): raise ModelError(f'dynamics.{key} must be a boolean.')
        else:
            try: value=float(v)
            except (ValueError,TypeError) as exc: raise ModelError(f'dynamics.{key} must be numeric.') from exc
            if not np.isfinite(value) or not meta['min']<=value<=meta['max']:
                raise ModelError(f'dynamics.{key} must lie between {meta["min"]} and {meta["max"]}.')
            if meta['type']=='int' and int(value)!=value: raise ModelError(f'dynamics.{key} must be an integer.')
            result[key]=int(value) if meta['type']=='int' else value
    return result


def _run(c,o,cells,progress=None):
    segments=c['segments']; bounds=np.r_[0,np.cumsum([s['length_m'] for s in segments])]
    length=float(bounds[-1]); vg=c['fm']['group_velocity_m_s']; dz=length/cells; dt=dz/vg
    requested_steps=o['duration_ns']*1e-9/dt if dt>0 else np.inf
    if not np.isfinite(requested_steps) or requested_steps>250000:
        raise ModelError('Transient envelope workload exceeds 250000 steps; increase fiber cell length or shorten duration.')
    steps=int(ceil(requested_steps))
    if steps>250000 or steps*cells>40000000:
        raise ModelError('Transient envelope workload exceeds250000 steps or40million cell-steps; shorten duration or reduce cells.')
    z=(np.arange(cells)+.5)*dz
    labels=np.minimum(np.searchsorted(bounds,z,side='right')-1,len(segments)-1)
    gamma=pi*np.array([segments[i]['linewidth_hz'] for i in labels])
    gain=o['gain_scale']*np.array([segments[i]['gain_per_w_m'] for i in labels])*c['probe']['pc_overlap']
    resonance=np.array([segments[i]['resonance_hz'] for i in labels])
    alpha=np.array([segments[i]['attenuation_db_km'] for i in labels])*np.log(10)/10000
    source=c['laser']['power_w']*10**(-c['splitter']['loss_db']/10)
    pp=source*c['splitter']['pump_fraction']*10**((c['pump']['edfa_gain_db']-c['pump']['eom_loss_db']-c['pump']['circulator_loss_db'])/10)*o['pump_scale']
    ps=source*(1-c['splitter']['pump_fraction'])*10**(-(c['probe']['eom_loss_db']+c['probe']['isolator_loss_db'])/10)*o['probe_scale']
    control=controls_for_target(c,c['scan']['target_m'])
    taup=control['delay_s']+z/vg; taus=(length-z)/vg
    freq=control['frequency_hz']; excursion=peak_excursion(c) if o['fm_enabled'] else 0.
    offset=o['offset_ghz']*1e9
    carrier=299792458./(c['laser']['wavelength_nm']*1e-9)
    if offset>=carrier: raise ModelError('Probe optical frequency must remain positive; reduce offset or check laser wavelength units.')
    ratio=carrier/(carrier-offset)
    mismatch_bound=np.max(abs(offset-resonance)+2*excursion*abs(np.sin(pi*freq*(taup-taus))))
    if dt*2*pi*mismatch_bound>1.:
        raise ModelError('Acoustic detuning advances by more than1radian per time step; increase cells or reduce detuning/FM excursion.')
    if dt*np.max(gamma)>1 or dz*np.max(gain)*max(pp,ps)>.2:
        raise ModelError('Local coupling/acoustic rate is too fast for this time step; increase cells or reduce demonstration power/gain.')
    p=np.zeros(cells,complex); s=p.copy(); q=np.full(cells,o['initial_acoustic_scale']*np.sqrt(pp*ps),complex)
    def derivative(t,p,s,q):
        mismatch=offset-resonance+excursion*(np.sin(2*pi*freq*(t-taup)+c['fm']['phase_rad'])-np.sin(2*pi*freq*(t-taus)+c['fm']['phase_rad']))
        dp=-vg*.5*gain*ratio*q*s-vg*.5*alpha*p
        ds=vg*.5*gain*q.conj()*p-vg*.5*alpha*s
        dq=gamma*p*s.conj()-(gamma+2j*pi*mismatch)*q
        loss=dz*np.sum(alpha*(abs(p)**2/ratio+abs(s)**2))
        return dp,ds,dq,float(loss)
    def reaction(t,p,s,q,h):
        a=derivative(t,p,s,q)
        b=derivative(t+h/2,p+h*a[0]/2,s+h*a[1]/2,q+h*a[2]/2)
        d=derivative(t+h/2,p+h*b[0]/2,s+h*b[1]/2,q+h*b[2]/2)
        e=derivative(t+h,p+h*d[0],s+h*d[1],q+h*d[2])
        return (p+h*(a[0]+2*b[0]+2*d[0]+e[0])/6,
                s+h*(a[1]+2*b[1]+2*d[1]+e[1])/6,
                q+h*(a[2]+2*b[2]+2*d[2]+e[2])/6,
                h*(a[3]+2*b[3]+2*d[3]+e[3])/6)
    save_indices=set(np.linspace(0,steps,min(steps+1,o['output_frames']),dtype=int).tolist())
    times=[]; pmap=[]; smap=[]; qreal=[]; qimag=[]
    trace_t=[]; in_p=[]; in_s=[]; out_p=[]; out_s=[]; balance=[]
    input_energy=output_energy=loss_energy=0.
    def frame(t):
        times.append(float(t)); pmap.append((abs(p)**2).tolist()); smap.append((abs(s)**2).tolist())
        qreal.append(q.real.tolist()); qimag.append(q.imag.tolist())
    frame(0.)
    for step in range(steps):
        t=step*dt
        p,s,q,loss=reaction(t,p,s,q,dt/2); loss_energy+=loss
        outgoing_p=float(abs(p[-1])**2); outgoing_s=float(abs(s[0])**2)
        midpoint=t+dt/2
        rise=1-np.exp(-midpoint/(o['boundary_rise_ns']*1e-9))
        incoming_p=pp*rise*(1+c['pump']['modulation_depth']*np.cos(2*pi*c['pump']['modulation_hz']*midpoint+np.deg2rad(c['pump']['phase_deg'])))
        incoming_s=ps*rise
        p=np.r_[np.sqrt(max(incoming_p,0)),p[:-1]]
        s=np.r_[s[1:],np.sqrt(max(incoming_s,0))]
        input_energy+=dt*(incoming_p/ratio+incoming_s)
        output_energy+=dt*(outgoing_p/ratio+outgoing_s)
        p,s,q,loss=reaction(t+dt/2,p,s,q,dt/2); loss_energy+=loss
        if not np.all(np.isfinite(p)) or not np.all(np.isfinite(q)):
            raise ModelError('Transient solver became nonfinite; reduce time step or coupling.')
        if step+1 in save_indices:
            frame((step+1)*dt)
            stored=dt*float(np.sum(abs(p)**2/ratio+abs(s)**2))
            trace_t.append((step+1)*dt); in_p.append(incoming_p); in_s.append(incoming_s)
            out_p.append(outgoing_p); out_s.append(outgoing_s)
            balance.append((stored+output_energy+loss_energy-input_energy)/max(input_energy,1e-30))
            if progress: progress(step+1,steps)
    final_storage=dt*float(np.sum(abs(p)**2/ratio+abs(s)**2))
    error=(final_storage+output_energy+loss_energy-input_energy)/max(input_energy,1e-30)
    retarded=(steps-.5)*dt-length/vg
    no_sbs_pump=(pp*(1-np.exp(-max(retarded,0)/(o['boundary_rise_ns']*1e-9)))
        *(1+c['pump']['modulation_depth']*np.cos(2*pi*c['pump']['modulation_hz']*retarded+np.deg2rad(c['pump']['phase_deg'])))
        *np.exp(-np.sum(alpha)*dz))
    no_sbs_probe=ps*(1-np.exp(-max(retarded,0)/(o['boundary_rise_ns']*1e-9)))*np.exp(-np.sum(alpha)*dz)
    if abs(error)>1e-3: raise ModelError(f'Transient photon-flux balance error {error:.3g} exceeds1e-3; refine cells.')
    return {'time_s':times,'z_m':z.tolist(),'pump_power_w':pmap,'probe_power_w':smap,
            'acoustic_real_w':qreal,'acoustic_imag_w':qimag,
            'boundary_time_s':trace_t,'pump_input_w':in_p,'probe_input_w':in_s,
            'pump_output_w':out_p,'probe_output_w':out_s,'photon_balance_trace_relative':balance,
            'diagnostics':{'cells':cells,'steps':steps,'dt_s':dt,'dz_m':dz,
                'photon_weight_pump_to_probe_ratio':ratio,'input_weighted_energy_j':input_energy,
                'output_weighted_energy_j':output_energy,'stored_weighted_energy_j':final_storage,
                'attenuated_weighted_energy_j':loss_energy,'photon_balance_relative':error,
                'pump_boundary_mean_w':pp,'probe_boundary_mean_w':ps,
                'pump_depletion_fraction_final':(1-out_p[-1]/no_sbs_pump) if no_sbs_pump>1e-30 else None,
                'depletion_unavailable_reason':None if no_sbs_pump>1e-30 else 'No reference pump has reached the output, or pump input is zero.',
                'pump_no_sbs_retarded_output_w':no_sbs_pump,
                'pump_total_transmission_deficit_final':1-out_p[-1]/max(in_p[-1],1e-30),
                'probe_amplification_final':(out_s[-1]/no_sbs_probe) if no_sbs_probe>1e-30 else None,
                'probe_no_sbs_retarded_output_w':no_sbs_probe,
                'probe_total_transmission_ratio_final':out_s[-1]/max(in_s[-1],1e-30),
                'fm_periods_simulated':steps*dt*freq,'controls':control}}


def simulate_dynamics(config,options=None,progress=None):
    c=validate_config(config); o=_options(options)
    result=_run(c,o,o['cells'],progress)
    duration=result['diagnostics']['steps']*result['diagnostics']['dt_s']
    transit=sum(s['length_m'] for s in c['segments'])/c['fm']['group_velocity_m_s']
    lifetimes=1/(pi*np.array([s['linewidth_hz'] for s in c['segments']]))
    result['diagnostics'].update(duration_s=duration,propagation_time_s=transit,
        propagation_transits_simulated=duration/transit,
        acoustic_amplitude_lifetime_min_s=float(lifetimes.min()),
        acoustic_amplitude_lifetime_max_s=float(lifetimes.max()),
        minimum_acoustic_lifetimes_simulated=float(duration/lifetimes.max()),
        refinement_status='not_checked')
    if o['convergence_check']:
        fine=_run(c,o,2*o['cells'])
        coarse_t=np.array(result['boundary_time_s']); fine_t=np.array(fine['boundary_time_s'])
        errors={}
        for key in ['pump_output_w','probe_output_w']:
            a=np.array(result[key]); b=np.interp(coarse_t,fine_t,fine[key])
            errors[key+'_relative_l2']=float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-30))
            rms_error=float(np.sqrt(np.mean((a-b)**2)))
            rms_reference=float(np.sqrt(np.mean(b**2)))
            tolerance=o['refinement_atol_w']+o['refinement_rtol']*rms_reference
            errors[key+'_rms_error_w']=rms_error
            errors[key+'_rms_tolerance_w']=tolerance
            if rms_error>tolerance:
                raise ModelError(f'Transient refinement failed for {key}: RMS error {rms_error:.6g} W '
                    f'exceeds atol + rtol*RMS(reference) = {tolerance:.6g} W. Increase cells or adjust '
                    'documented tolerances; this result is not accepted as converged.')
        result['diagnostics']['refinement_status']='passed'
        result['diagnostics']['refinement']={'coarse_cells':o['cells'],'fine_cells':2*o['cells'],
            'fine_dt_s':fine['diagnostics']['dt_s'],'fine_photon_balance_relative':fine['diagnostics']['photon_balance_relative'],
            'relative_tolerance':o['refinement_rtol'],'absolute_tolerance_w':o['refinement_atol_w'],'status':'passed',**errors}
    result.update(mode='dynamics',config=deepcopy(config),options=o,
        warnings=['Actual finite-duration counterpropagating optical/acoustic envelope solution; not an FM-period-averaged spectrum.',
                  ('Gain/probe multipliers are an explicit stronger-interaction demonstration, not reported paper settings.'
                   if o['gain_scale']!=1 or o['probe_scale']!=1 or o['pump_scale']!=1 else
                   'Unit optical/gain multipliers retain the configured unscaled demonstration budget; missing paper settings remain assumed.'),
                  'Acoustic envelope normalization is W; no thermodynamic acoustic energy or spontaneous noise is inferred.',
                  'Uniform-cell characteristic splitting and RK4 local evolution require spatial/time refinement.'])
    if not o['convergence_check']:
        result['warnings'].append('Refinement was disabled: no convergence acceptance is claimed for this run.')
    return result
