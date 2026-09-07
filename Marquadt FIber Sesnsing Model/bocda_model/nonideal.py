"""Optional nonideal components on the weak-gain, cycle-averaged BOCDA model."""
from __future__ import annotations
from copy import deepcopy
from math import pi
import numpy as np
from scipy.linalg import expm, solve_continuous_lyapunov
from scipy.special import jv
from .physics import (ModelError,simulate,validate_config,fiber_grid,power_budget,_sample_count,
    fm_difference_amplitude,floquet_weights,lockin_filter,estimate_resonance)


def schema():
    def f(default,minimum,maximum,description):
        return {'default':default,'type':'float','min':minimum,'max':maximum,'description':description}
    def b(default,description): return {'default':default,'type':'bool','description':description}
    return {
      'enabled':b(True,'Enable optional nonideal spectrum calculation'),
      'seed':{'default':2026,'type':'int','min':0,'max':2147483647,'description':'Reproducible noise seed'},
      'pump_eom_enabled':b(True,'Finite-extinction sinusoidal Mach-Zehnder transfer'),
      'pump_extinction_db':f(30.,0.,100.,'Pump EOM minimum/maximum transmission extinction (dB)'),
      'pump_bias_error_deg':f(2.,-80.,80.,'Pump EOM phase bias error (degrees)'),
      'pump_bias_drift_deg_s':f(0.,-5.,5.,'Linear pump EOM bias drift per acquisition second (degrees/s)'),
      'pump_rf_amplitude_error_frac':f(.02,-.9,1.,'Pump RF voltage amplitude fractional error'),
      'pump_rf_phase_error_deg':f(1.,-180.,180.,'Pump RF reference phase error (degrees)'),
      'probe_eom_enabled':b(True,'IQ modulator Fourier sidebands with carrier leakage'),
      'probe_extinction_db':f(30.,0.,100.,'Probe coherent carrier leakage extinction (dB)'),
      'probe_bias_error_deg':f(1.,-45.,45.,'Probe IQ branch bias error (degrees)'),
      'probe_bias_drift_deg_s':f(0.,-5.,5.,'Linear probe IQ bias drift per acquisition second (degrees/s)'),
      'probe_rf_amplitude_error_frac':f(.02,-.9,1.,'Probe Q/I fractional RF amplitude error'),
      'probe_rf_phase_error_deg':f(2.,-90.,90.,'Probe quadrature phase error (degrees)'),
      'probe_rf_depth_rad':f(.25,.01,1.,'Probe modulation phase depth (rad)'),
      'probe_frequency_error_mhz':f(.1,-20.,20.,'Microwave offset calibration error (MHz)'),
      'edfa_enabled':b(True,'Compressed EDFA gain with finite gain response'),
      'edfa_saturation_power_w':f(.2,1e-5,100.,'EDFA asymptotic compressed output power (W)'),
      'edfa_gain_time_us':f(50.,.01,10000.,'EDFA gain relaxation time (microseconds)'),
      'edfa_ase_enabled':b(True,'Two-polarization EDFA ASE and receiver beat noise'),
      'edfa_noise_figure_db':f(5.,3.0103,20.,'High-gain noise figure used as 2*nsp (dB)'),
      'optical_filter_bandwidth_ghz':f(1.,.001,1000.,'Total receiver ASE equivalent optical noise bandwidth (GHz)'),
      'circulator_isolation_db':f(80.,0.,120.,'Pump and ASE leakage to receiver (dB)'),
      'laser_linewidth_hz':f(5e4,0.,1e8,'Shared Wiener-phase laser Lorentzian linewidth (Hz)'),
      'source_ram_depth':f(0.,0.,.1,'Deterministic source intensity modulation depth at laser fm (distinct from RIN)'),
      'source_ram_phase_deg':f(0.,-180.,180.,'Source RAM phase relative to the laser FM clock (degrees)'),
      'laser_rin_db_hz':f(-145.,-300.,-60.,'One-sided low-frequency fractional-intensity PSD (dB/Hz)'),
      'rin_bandwidth_mhz':f(5.,.001,100.,'OU intensity-noise corner frequency (MHz)'),
      'trace_samples':{'default':4096,'type':'int','min':256,'max':65536,'description':'Exported shared-source stochastic samples'},
      'trace_dt_ns':f(2.,.01,100.,'Shared-source trace sampling interval (ns)'),
      'polarization_enabled':b(True,'Spatial polarization variation and slow scrambling'),
      'polarization_rms_rad':f(.15,0.,3.,'Stationary relative Jones-angle RMS (rad)'),
      'polarization_correlation_m':f(.05,.0001,1000.,'Spatial polarization correlation length (m)'),
      'scramble_rate_hz':f(50.,0.,10000.,'Sinusoidal polarization scrambler rate (Hz)'),
      'scramble_depth_rad':f(.2,0.,3.,'Polarization scrambling angle depth (rad)'),
      'detector_shot_noise_enabled':b(True,'Poisson shot noise in Gaussian high-count limit'),
      'detector_electronic_asd_a':f(1e-12,0.,1e-6,'One-sided input-current electronic noise ASD (A/sqrtHz)'),
      'detector_saturation_enabled':b(True,'Clip detector voltage to [0, configured maximum]'),
    }


def default_options(): return {k:v['default'] for k,v in schema().items()}


def _options(options):
    result=default_options()
    if options: result.update(options)
    for key,m in schema().items():
        v=result[key]
        if m['type']=='bool':
            if not isinstance(v,bool): raise ModelError(f'nonideal.{key} must be boolean.')
        else:
            try: x=float(v)
            except (ValueError,TypeError) as exc: raise ModelError(f'nonideal.{key} must be numeric.') from exc
            if not np.isfinite(x) or not m['min']<=x<=m['max']:
                raise ModelError(f'nonideal.{key} must lie between {m["min"]} and {m["max"]}.')
            if m['type']=='int' and int(x)!=x: raise ModelError(f'nonideal.{key} must be integer.')
            result[key]=int(x) if m['type']=='int' else x
    return result


def pump_eom_transfer(depth,extinction_db,bias_error_deg=0,amplitude_error=0,phase_error_deg=0,samples=2048):
    theta=2*pi*np.arange(samples)/samples
    eps=10**(-extinction_db/10)
    phase=pi/2+np.deg2rad(bias_error_deg)-depth*(1+amplitude_error)*np.cos(theta+np.deg2rad(phase_error_deg))
    transmission=eps+(1-eps)*np.cos(phase/2)**2
    coeff=np.fft.fft(transmission)/samples
    fundamental=2*coeff[1]/coeff[0].real
    return {'mean_transmission':float(coeff[0].real),'relative_fundamental_real':float(fundamental.real),
            'relative_fundamental_imag':float(fundamental.imag),
            'higher_harmonic_relative_rms':float(np.sqrt(2*np.sum(abs(coeff[2:samples//2])**2))/coeff[0].real),
            'phase_rad':theta[::8].tolist(),'transmission':transmission[::8].tolist()}


def probe_eom_spectrum(options,samples=2048):
    o=options; theta=2*pi*np.arange(samples)/samples
    depth=o['probe_rf_depth_rad']; bias=np.deg2rad(o['probe_bias_error_deg'])
    field=(np.cos(pi/2+bias+depth*np.cos(theta))
           -1j*np.cos(pi/2+bias+depth*(1+o['probe_rf_amplitude_error_frac'])*np.sin(theta+np.deg2rad(o['probe_rf_phase_error_deg'])))
           +np.sqrt(10**(-o['probe_extinction_db']/10)))
    coeff=np.fft.fft(field)/samples; total=float(np.mean(abs(field)**2))
    components=[]
    for n in range(-7,8):
        power=float(abs(coeff[n%samples])**2/total)
        if power>1e-10: components.append({'order':n,'power_fraction':power})
    return {'components':components,'retained_fraction':sum(x['power_fraction'] for x in components),
            'raw_mean_transmission':total,'normalization':'Normalized spectral fractions; configured EOM insertion loss fixes total transmitted probe power.'}


def edfa_trace(time_s,input_power_w,gain0,saturation_power_w,time_constant_s,initial_gain=None):
    t=np.asarray(time_s,float); pin=np.asarray(input_power_w,float)
    if len(t)!=len(pin) or len(t)<2 or np.any(np.diff(t)<=0) or np.any(pin<0): raise ModelError('EDFA trace requires increasing times and nonnegative matched input powers.')
    g=float(gain0 if initial_gain is None else initial_gain); gain=np.empty(len(t)); gain[0]=g
    for i in range(1,len(t)):
        equilibrium=gain0/(1+gain0*pin[i]/saturation_power_w)
        a=np.exp(-(t[i]-t[i-1])/time_constant_s)
        g=equilibrium+(g-equilibrium)*a; gain[i]=g
    return {'time_s':t.tolist(),'input_power_w':pin.tolist(),'gain':gain.tolist(),'output_power_w':(gain*pin).tolist()}


def shared_source_trace(linewidth_hz,rin_psd_hz,rin_corner_hz,taup,taus,samples,dt,seed):
    rng=np.random.default_rng(seed); offset=min(0,taup,taus); taup-=offset; taus-=offset
    padding=int(np.ceil(max(taup,taus)/dt))+2
    if padding+samples>1000000: raise ModelError('Shared-source delay trace exceeds1million samples; increase trace_dt_ns or shorten external delay.')
    count=padding+samples+2; time=(np.arange(count)-padding)*dt
    phase=np.r_[0,np.cumsum(rng.normal(0,np.sqrt(2*pi*linewidth_hz*dt),count-1))]
    tau=1/(2*pi*rin_corner_hz); variance=rin_psd_hz/(4*tau); a=np.exp(-dt/tau)
    if variance>.1: raise ModelError('RIN variance exceeds the small-noise model domain; reduce RIN PSD or bandwidth.')
    rin=np.empty(count); rin[0]=rng.normal(0,np.sqrt(variance))
    noise=rng.normal(0,np.sqrt(variance*(1-a*a)),count-1)
    for i in range(1,count): rin[i]=a*rin[i-1]+noise[i-1]
    output_t=np.arange(samples)*dt
    pp=np.interp(output_t-taup,time,phase); ps=np.interp(output_t-taus,time,phase)
    rp=np.interp(output_t-taup,time,rin); rs=np.interp(output_t-taus,time,rin)
    return {'time_s':output_t.tolist(),'pump_phase_rad':pp.tolist(),'probe_phase_rad':ps.tolist(),
            'relative_phase_rad':(pp-ps).tolist(),'pump_intensity_multiplier':np.exp(rp-variance/2).tolist(),
            'probe_intensity_multiplier':np.exp(rs-variance/2).tolist(),
            'delay_difference_s':abs(taup-taus),'expected_relative_phase_variance_rad2':2*pi*linewidth_hz*abs(taup-taus),
            'sample_relative_phase_variance_rad2':float(np.var(pp-ps)),
            'rin_stationary_variance':variance,'phase_model':'One shared Wiener path, sampled at the two retarded times; not independent laser draws.'}


def phase_susceptibility(detuning_hz,linewidth_hz,laser_linewidth_hz,delay_s):
    """Exact ensemble mean damped acoustic response to a delayed common Wiener phase."""
    gamma=pi*linewidth_hz; kappa=2*pi*laser_linewidth_hz
    a=gamma+2j*pi*np.asarray(detuning_hz); b=a+kappa
    if np.isinf(delay_s): return gamma/b
    e=np.exp(-b*abs(delay_s))
    return gamma*(-np.expm1(-b*abs(delay_s))/b+e/a)


def _paired(detuning,n,fm,linewidth,laser_linewidth,delay,tag):
    d=np.atleast_1d(detuning)[None,:]; shift=n[:,None]*fm
    def branch(v):
        h=phase_susceptibility(v,linewidth,laser_linewidth,delay)
        hp=phase_susceptibility(v+tag,linewidth,laser_linewidth,delay)
        hm=phase_susceptibility(v-tag,linewidth,laser_linewidth,delay)
        return h.real,.5*h.real+.25*(hp+hm.conj())
    dc,ac=branch(d+shift); dm,am=branch(d-shift)
    dc[1:]+=dm[1:]; ac[1:]+=am[1:]
    return dc,ac


def _signed_response(detuning,n,fm,linewidth,laser_linewidth,delay,tag):
    d=np.atleast_1d(detuning)[None,:]+np.asarray(n)[:,None]*fm
    h=phase_susceptibility(d,linewidth,laser_linewidth,delay)
    hp=phase_susceptibility(d+tag,linewidth,laser_linewidth,delay)
    hm=phase_susceptibility(d-tag,linewidth,laser_linewidth,delay)
    return h.real,.5*h.real+.25*(hp+hm.conj())


def ram_floquet_weights(z,length,control,config,depth,phase_deg=0.,oversampling=4):
    """Full signed Fourier powers of the physically delayed FM+RAM acoustic drive."""
    if not 0<=depth<=.1: raise ModelError('Source RAM depth must lie in [0,0.1] for the bounded model.')
    z=np.atleast_1d(z);fm=control['frequency_hz'];vg=config['fm']['group_velocity_m_s']
    taup=control['delay_s']+z/vg;taus=(length-z)/vg
    cycles=fm*(taup-taus);integer=np.rint(cycles)
    beta=2*config['fm']['excursion_hz']/(2 if config['fm']['excursion_convention'] in ('peak-to-peak','peak_to_peak') else 1)/fm*np.sin(pi*(cycles-integer))*np.where(np.remainder(integer,2)==0,1.,-1.)
    largest=float(np.max(abs(beta)))
    if not np.isfinite(largest) or largest>20000: raise ModelError('RAM modulation index exceeds the bounded Fourier calculation; reduce excursion or path span.')
    nmax=int(np.ceil(largest+12*np.cbrt(largest+1)+24))
    requested=max(256,oversampling*(2*nmax+1))
    nfft=1 << int(np.ceil(np.log2(requested)))
    if nfft>32768 or len(z)*nfft>2000000:
        raise ModelError('RAM Fourier grid exceeds32768 phase samples or2million cell-phase samples; shorten fiber or reduce FM excursion/cells.')
    theta=2*pi*np.arange(nfft)/nfft;phase=np.deg2rad(phase_deg)
    ip=1+depth*np.cos(theta[None,:]-2*pi*fm*taup[:,None]+phase)
    is_=1+depth*np.cos(theta[None,:]-2*pi*fm*taus[:,None]+phase)
    beat_phase=-beta[:,None]*np.sin(theta[None,:]-pi*fm*(taup+taus)[:,None]+config['fm']['phase_rad'])
    drive=np.sqrt(ip*is_)*np.exp(1j*beat_phase)
    coefficients=np.fft.fft(drive,axis=1)/nfft
    orders=np.arange(-nmax,nmax+1);coefficients=coefficients[:,orders%nfft]
    weights=abs(coefficients)**2
    expected=1+.5*depth**2*np.cos(2*pi*cycles)
    error=float(np.max(abs(weights.sum(1)-expected)))
    if error>1e-8: raise ModelError('RAM Fourier truncation failed its physical mean-product normalization check.')
    return orders,weights,{'phase_samples':nfft,'parseval_max_abs_error':error,
        'mean_intensity_product':expected.tolist(),'summed_fourier_power':weights.sum(1).tolist(),
        'spectral_order_centroid':(weights@orders/expected).tolist()}


def _bias_history(c,o,points):
    """Actual MZM/IQ transfer at chronological dwell midpoints, with EDFA gain memory."""
    if points>25000: raise ModelError('Bias-drift history supports at most25000 acquisition points.')
    dwell=c['receiver']['dwell_s'];time=(np.arange(points)+.5)*dwell
    for arm,limit in [('pump',80.),('probe',45.)]:
        rate=o[arm+'_bias_drift_deg_s']
        if rate and not o[arm+'_eom_enabled']: raise ModelError(f'{arm} bias drift requires its EOM model enabled.')
        if abs(rate)*max(dwell,o['edfa_gain_time_us']*1e-6 if arm=='pump' and o['edfa_enabled'] else dwell)>.1:
            raise ModelError(f'{arm} bias changes by more than0.1degree per dwell/gain-relaxation time; reduce drift rate or dwell.')
        end=o[arm+'_bias_error_deg']+rate*time[-1]
        if max(abs(o[arm+'_bias_error_deg']),abs(end))>limit:
            raise ModelError(f'{arm} drifting bias leaves its +/-{limit:g}degree operating range during this acquisition.')
    bp=o['pump_bias_error_deg']+o['pump_bias_drift_deg_s']*time
    bs=o['probe_bias_error_deg']+o['probe_bias_drift_deg_s']*time
    source=c['laser']['power_w']*10**(-c['splitter']['loss_db']/10)*c['splitter']['pump_fraction']
    g0=10**(c['pump']['edfa_gain_db']/10)
    mean=[];pin=[];fund=[];probe_transmission=[];components={n:[] for n in range(-7,8)}
    nominal_probe=probe_eom_spectrum(o)['raw_mean_transmission'] if o['probe_eom_enabled'] else 1.
    for pump_bias,probe_bias in zip(bp,bs):
        if o['pump_eom_enabled']:
            e=pump_eom_transfer(c['pump']['modulation_depth'],o['pump_extinction_db'],pump_bias,o['pump_rf_amplitude_error_frac'],o['pump_rf_phase_error_deg'])
            mean.append(e['mean_transmission']);fund.append(complex(e['relative_fundamental_real'],e['relative_fundamental_imag']))
            pin.append(source*10**(-c['pump']['eom_loss_db']/10)*e['mean_transmission']/.5)
        else:
            mean.append(.5);fund.append(complex(c['pump']['modulation_depth']));pin.append(source*10**(-c['pump']['eom_loss_db']/10))
        spectrum=probe_eom_spectrum({**o,'probe_bias_error_deg':float(probe_bias)}) if o['probe_eom_enabled'] else {'components':[{'order':-1,'power_fraction':1.}],'raw_mean_transmission':1.}
        current=spectrum['components'];probe_transmission.append(spectrum['raw_mean_transmission']/nominal_probe)
        lookup={item['order']:item['power_fraction'] for item in current}
        for n in components:components[n].append(lookup.get(n,0.))
    pin=np.array(pin);gain=np.full(points,g0);response=np.ones(points,complex)
    if o['edfa_enabled']:
        saturation=g0*pin/o['edfa_saturation_power_w'];equilibrium=g0/(1+saturation)
        static=pump_eom_transfer(c['pump']['modulation_depth'],o['pump_extinction_db'],o['pump_bias_error_deg'],o['pump_rf_amplitude_error_frac'],o['pump_rf_phase_error_deg']) if o['pump_eom_enabled'] else {'mean_transmission':.5}
        initial_pin=source*10**(-c['pump']['eom_loss_db']/10)*static['mean_transmission']/.5
        state=g0/(1+g0*initial_pin/o['edfa_saturation_power_w']);previous=0.
        for i,t in enumerate(time):
            a=np.exp(-(t-previous)/(o['edfa_gain_time_us']*1e-6));state=equilibrium[i]+(state-equilibrium[i])*a;gain[i]=state;previous=t
        response=1-saturation/(1+saturation)/(1+2j*pi*c['pump']['modulation_hz']*o['edfa_gain_time_us']*1e-6)
    tag=np.array(fund)*response*np.exp(1j*np.deg2rad(c['pump']['phase_deg']-c['receiver']['reference_phase_deg']))
    if np.max(abs(tag))>.3: raise ModelError('Drifting EOM bias produces tag depth above0.3; reduce drift/depth or change bias.')
    if np.max(probe_transmission)*10**(-c['probe']['eom_loss_db']/10)>1:
        raise ModelError('Drifting IQ transfer exceeds unit total transmission under the configured insertion-loss calibration.')
    if np.max(pin*gain*(1+abs(tag))*(1+o['source_ram_depth']))>c['pump']['edfa_max_w']:
        raise ModelError('Combined bias drift, pump tag and source RAM exceed the EDFA peak output ceiling.')
    return {'time_s':time.tolist(),'pump_bias_deg':bp.tolist(),'probe_bias_deg':bs.tolist(),
            'pump_mean_transmission':mean,'pump_edfa_input_w':pin.tolist(),'edfa_gain':gain.tolist(),
            'pump_edfa_output_w':(pin*gain).tolist(),'pump_fiber_input_w':(pin*gain*10**(-c['pump']['circulator_loss_db']/10)).tolist(),
            'pump_tag_real':tag.real.tolist(),'pump_tag_imag':tag.imag.tolist(),
            'probe_transmission_ratio':probe_transmission,
            'edfa_tag_response_real':response.real.tolist(),'edfa_tag_response_imag':response.imag.tolist(),
            'probe_sideband_power_fraction':{str(n):v for n,v in components.items()},
            'time_convention':'Dwell midpoints; chronology continues across positions. Bias is frozen within each bounded dwell.'}


def receiver_noise(psd_v2_hz,time_constant,dwell,order,count,rng):
    """Exact discrete covariance of cascaded RC stages for each white-noise IQ input."""
    a=-np.eye(order)/time_constant
    for i in range(1,order): a[i,i-1]=1/time_constant
    b=np.zeros(order); b[0]=1/time_constant
    stationary=solve_continuous_lyapunov(a,-np.outer(b,b))
    transition=expm(a*dwell)
    q=stationary-transition@stationary@transition.T
    eigen,vectors=np.linalg.eigh(q); root=vectors@np.diag(np.sqrt(np.maximum(eigen,0)))
    state=np.zeros((order,2)); out=[]
    psd=np.broadcast_to(psd_v2_hz,(count,))
    for i in range(count):
        state=transition@state+np.sqrt(psd[i])*root@rng.standard_normal((order,2))
        out.append(state[-1,0]+1j*state[-1,1])
    return np.array(out),float(stationary[-1,-1])


def clip_fundamental(dc_v,ac_v,maximum_v,samples=512):
    theta=2*pi*np.arange(samples)/samples
    waveform=np.asarray(dc_v)[:,None]+np.real(np.asarray(ac_v)[:,None]*np.exp(1j*theta))
    clipped=np.clip(waveform,0,maximum_v)
    return (2*np.mean(clipped*np.exp(-1j*theta),axis=1),
            np.mean(clipped,axis=1),float(np.mean(clipped!=waveform)))


def polarization_overlap(angle_rad,midpoint_s,dwell_s,rate_hz,depth_rad):
    """Analytic finite-dwell average; avoids time-sampling aliases of fast scrambling."""
    orders=np.arange(-int(np.ceil(2*abs(depth_rad)+24)),int(np.ceil(2*abs(depth_rad)+24))+1)
    averaged=np.sum(jv(orders,2*depth_rad)[:,None]*np.exp(2j*pi*orders[:,None]*rate_hz*np.asarray(midpoint_s)[None,:])
                    *np.sinc(orders[:,None]*rate_hz*dwell_s),axis=0)
    return .5+.5*np.real(np.exp(2j*np.asarray(angle_rad))[:,None]*averaged[None,:])


def simulate_nonideal(config,options=None,mode='local',progress=None):
    o=_options(options); c=validate_config(config)
    if not o['enabled']:
        result=simulate(c,mode,progress); result['nonideal']={'enabled':False,'options':o}; return result
    _sample_count(c['scan']['frequency_start_hz'],c['scan']['frequency_stop_hz'],c['scan']['frequency_step_hz'],1001,'Nonideal frequency sweep',5)
    if mode=='scan': _sample_count(c['scan']['start_m'],c['scan']['stop_m'],c['scan']['step_m'],101,'Nonideal position scan')
    if sum(np.ceil(seg['length_m']/c['scan']['cell_m']) for seg in c['segments'])>2000:
        raise ModelError('Nonideal mode supports at most2000 cells; increase numerical cell size.')
    rng=np.random.default_rng(o['seed']); modified=deepcopy(c)
    details={}; original_depth=c['pump']['modulation_depth']
    if o['pump_eom_enabled']:
        eom=pump_eom_transfer(original_depth,o['pump_extinction_db'],o['pump_bias_error_deg'],o['pump_rf_amplitude_error_frac'],o['pump_rf_phase_error_deg'])
        fundamental=complex(eom['relative_fundamental_real'],eom['relative_fundamental_imag'])
        modified['pump']['eom_loss_db']+=-10*np.log10(eom['mean_transmission']/.5)
        modified['pump']['modulation_depth']=abs(fundamental)
        modified['pump']['phase_deg']+=np.rad2deg(np.angle(fundamental))
        details['pump_eom']=eom
    source=c['laser']['power_w']*10**(-c['splitter']['loss_db']/10)
    pin=source*c['splitter']['pump_fraction']*10**(-modified['pump']['eom_loss_db']/10)
    gain0=10**(c['pump']['edfa_gain_db']/10); gain=gain0; tag=c['pump']['modulation_hz']; response=1+0j
    if o['edfa_enabled']:
        saturation=gain0*pin/o['edfa_saturation_power_w']; gain=gain0/(1+saturation)
        response=1-saturation/(1+saturation)/(1+2j*pi*tag*o['edfa_gain_time_us']*1e-6)
        modified['pump']['edfa_gain_db']=10*np.log10(gain)
        modified['pump']['modulation_depth']*=abs(response)
        modified['pump']['phase_deg']+=np.rad2deg(np.angle(response))
        trace_t=np.linspace(0,5*o['edfa_gain_time_us']*1e-6,512)
        details['edfa_trace']=edfa_trace(trace_t,pin*(1+original_depth*np.cos(2*pi*tag*trace_t)),gain0,o['edfa_saturation_power_w'],o['edfa_gain_time_us']*1e-6)
        details['edfa']={'unsaturated_gain':gain0,'compressed_mean_gain':gain,'mean_output_w':pin*gain,
                         'tag_gain_response_real':float(response.real),'tag_gain_response_imag':float(response.imag)}
    # Saturation is evaluated explicitly below. Keep baseline only as weak-SBS metadata/template.
    maximum=c['receiver']['max_voltage_v']
    if o['detector_saturation_enabled']: modified['receiver']['max_voltage_v']=1e100
    result=simulate(modified,mode,None)
    frequency=np.array(result['frequency_hz']); positions=result['positions_m']
    if len(frequency)>1001 or len(positions)>101: raise ModelError('Nonideal mode supports at most1001 frequencies and101 positions.')
    z,dz,labels,boundaries=fiber_grid(modified); budget,pumpcells=power_budget(modified,z,dz,labels)
    if len(z)>2000: raise ModelError('Nonideal mode supports at most2000 cells.')
    drift_active=bool(o['pump_bias_drift_deg_s'] or o['probe_bias_drift_deg_s'])
    ram_active=o['source_ram_depth']>0
    history=_bias_history(c,o,len(frequency)*len(positions)) if drift_active else None
    if history:
        history['target_m']=np.repeat(positions,len(frequency)).tolist()
        history['frequency_hz']=np.tile(frequency,len(positions)).tolist()
        details['bias_history']=history
    if ram_active:
        peak_multiplier=(1+modified['pump']['modulation_depth'])*(1+o['source_ram_depth'])
        if pin*gain*peak_multiplier>c['pump']['edfa_max_w']:
            raise ModelError('Combined source RAM and pump tag exceed the EDFA peak output ceiling.')
        details['ram']={'depth':o['source_ram_depth'],'phase_deg':o['source_ram_phase_deg'],
                        'frequency_relation':'Deterministic intensity sinusoid at the same laser-FM frequency; mean source intensity multiplier is1.',
                        'coefficient_diagnostics':[]}
    probe=probe_eom_spectrum(o) if o['probe_eom_enabled'] else {'components':[{'order':-1,'power_fraction':1.}],'retained_fraction':1.}
    details['probe_eom']=probe
    angle=np.zeros(len(z)); sigma=o['polarization_rms_rad'] if o['polarization_enabled'] else 0.
    angle[0]=rng.normal(0,sigma)
    for i in range(1,len(z)):
        a=np.exp(-(z[i]-z[i-1])/o['polarization_correlation_m'])
        angle[i]=a*angle[i-1]+rng.normal(0,sigma*np.sqrt(1-a*a))
    theta0=np.arccos(np.sqrt(c['probe']['pc_overlap']))
    details['polarization']={'z_m':z.tolist(),'relative_angle_rad':angle.tolist(),'unscrambled_overlap':(np.cos(theta0+angle)**2).tolist()}
    # Coherent ASE convention: per-polarization PSD nsp*h*nu*(G-1), two independent polarizations.
    carrier=299792458/(c['laser']['wavelength_nm']*1e-9); nsp=.5*10**(o['edfa_noise_figure_db']/10)
    ase_psd=nsp*6.62607015e-34*carrier*max(gain-1,0) if o['edfa_ase_enabled'] else 0.
    optical_bw=o['optical_filter_bandwidth_ghz']*1e9
    leakage=10**(-o['circulator_isolation_db']/10)
    ase_detector=2*ase_psd*optical_bw*leakage
    leaked_pump=pin*gain*leakage
    details['ase']={'nsp':nsp,'polarizations':2,'per_polarization_output_psd_w_hz':ase_psd,
                    'optical_bandwidth_hz':optical_bw,'edfa_total_ase_w':2*ase_psd*optical_bw,
                    'receiver_ase_w':ase_detector,'receiver_pump_leakage_w':leaked_pump}
    vfactor=budget['probe_detector_no_sbs_w']*c['receiver']['responsivity_a_w']*c['receiver']['transimpedance_v_a']
    zfactor=c['receiver']['transimpedance_v_a']; responsivity=c['receiver']['responsivity_a_w']
    detector=1/(1+1j*tag/c['receiver']['bandwidth_hz'])
    phasor=np.exp(1j*np.deg2rad(modified['pump']['phase_deg']-c['receiver']['reference_phase_deg']))
    transport=np.exp(-2j*pi*tag*2*z/c['fm']['group_velocity_m_s'])
    spectra=[]; steady=[]; gains=[]; fits=[]; contributions_all=[]; noise_psds=[]; clipping=[]; overlaps=[]; transfer_envelopes=[]; channel_maxima=[]; depletion_maxima=[]
    noise_components={name:[] for name in ['shot','shared_rin','electronic','signal_ase','ase_ase']}
    for ix,target in enumerate(positions):
        control=result['controls'][ix]; fm=control['frequency_hz']
        if ram_active:
            if o['edfa_enabled']:
                s_values=gain0*(np.array(history['pump_edfa_input_w']) if history else pin)/o['edfa_saturation_power_w']
                frozen_error=np.max(s_values/(1+s_values)/np.sqrt(1+(2*pi*fm*o['edfa_gain_time_us']*1e-6)**2))
                if frozen_error>.01: raise ModelError('RAM requires EDFA gain nearly frozen over the laser-FM cycle (response correction <=1%); increase gain time constant or disable EDFA compression.')
            orders,weights,ram_diagnostic=ram_floquet_weights(z,boundaries[-1],control,c,o['source_ram_depth'],o['source_ram_phase_deg'])
            if len(orders)*len(frequency)>2000000:
                raise ModelError('RAM response exceeds2million Fourier-order/frequency samples; reduce FM excursion or frequency count.')
            rin_corner=o['rin_bandwidth_mhz']*1e6
            ram_rin_correction=o['source_ram_depth']**2/4*(1+(tag/rin_corner)**2)*(1/(1+((tag+fm)/rin_corner)**2)+1/(1+((tag-fm)/rin_corner)**2))
            if ram_rin_correction>.01:
                raise ModelError('RAM would mix more than1% additional RIN PSD into the tag; increase RIN corner bandwidth or reduce RAM depth.')
            ram_diagnostic['leading_rin_mixing_fraction']=float(ram_rin_correction)
            details['ram']['coefficient_diagnostics'].append(ram_diagnostic)
            acoustic_kernel=_signed_response
        else:
            amp=fm_difference_amplitude(z,boundaries[-1],control,c); orders,weights=floquet_weights(amp/fm)
            acoustic_kernel=_paired
        selection=slice(ix*len(frequency),(ix+1)*len(frequency))
        if history:
            power_ratio=np.array(history['pump_fiber_input_w'][selection])/budget['pump_fiber_input_w'] if budget['pump_fiber_input_w'] else np.ones(len(frequency))
            probe_ratio=np.array(history['probe_transmission_ratio'][selection])
            point_probe=budget['probe_detector_no_sbs_w']*probe_ratio
            point_tag=np.array(history['pump_tag_real'][selection])+1j*np.array(history['pump_tag_imag'][selection])
            point_response=np.array(history['edfa_tag_response_real'][selection])+1j*np.array(history['edfa_tag_response_imag'][selection])
            point_gain=np.array(history['edfa_gain'][selection])
            point_leak=np.array(history['pump_edfa_output_w'][selection])*leakage
            point_ase_psd=nsp*6.62607015e-34*carrier*np.maximum(point_gain-1,0) if o['edfa_ase_enabled'] else np.zeros(len(frequency))
            point_ase=2*point_ase_psd*optical_bw*leakage
            optical_components=[{'order':int(n),'power_fraction':np.array(fractions[selection])} for n,fractions in history['probe_sideband_power_fraction'].items() if np.max(fractions)>1e-10]
        else:
            power_ratio=1.;probe_ratio=1.;point_probe=budget['probe_detector_no_sbs_w']
            point_tag=modified['pump']['modulation_depth']*phasor;point_response=response
            point_leak=leaked_pump;point_ase_psd=ase_psd;point_ase=ase_detector
            optical_components=probe['components']
        delays=abs(control['delay_s']+(2*z-boundaries[-1])/c['fm']['group_velocity_m_s'])
        midpoint=(ix*len(frequency)+np.arange(len(frequency))+.5)*c['receiver']['dwell_s']
        if o['polarization_enabled'] and o['scramble_depth_rad'] and o['scramble_rate_hz']:
            overlap=polarization_overlap(theta0+angle,midpoint,c['receiver']['dwell_s'],o['scramble_rate_hz'],o['scramble_depth_rad'])
        else: overlap=np.repeat(np.cos(theta0+angle[:,None])**2,len(frequency),axis=1)
        overlaps.append(np.mean(overlap,axis=1).tolist())
        if history:overlap=overlap*power_ratio[None,:]
        dc=np.zeros(len(frequency)); ac=np.zeros(len(frequency),complex); contributions=[]
        channel_dc={component['order']:np.zeros(len(frequency)) for component in optical_components if component['order']!=0}
        unsigned=np.zeros(len(frequency))
        for i,seg in enumerate(c['segments']):
            mask=labels==i; strength=dz[mask]*pumpcells[mask]*seg['gain_per_w_m']
            gdc=np.zeros(len(frequency)); gac=np.zeros(len(frequency),complex)
            gamma=pi*seg['linewidth_hz']; kappa=2*pi*o['laser_linewidth_hz']
            long_delay=np.all(delays[mask]*(gamma+kappa)>24)
            constant_delay=0 if o['laser_linewidth_hz']==0 else (np.inf if long_delay else None)
            for optical in optical_components:
                # Lower-frequency (Stokes) probe is amplified; upper-frequency
                # (anti-Stokes) residual is attenuated by the driven pump.
                if optical['order']==0: continue
                signed_fraction=-np.sign(optical['order'])*optical['power_fraction']
                channel_weights=weights[:,::-1] if ram_active and optical['order']>0 else weights
                detuning=abs(optical['order'])*(frequency+o['probe_frequency_error_mhz']*1e6)-seg['resonance_hz']
                branch_dc=np.zeros(len(frequency)); branch_ac=np.zeros(len(frequency),complex)
                if constant_delay is not None:
                    kd,ka=acoustic_kernel(detuning,orders,fm,seg['linewidth_hz'],o['laser_linewidth_hz'],constant_delay,tag)
                    wd=channel_weights[mask].T@(strength[:,None]*overlap[mask])
                    wa=channel_weights[mask].T@((strength*transport[mask])[:,None]*overlap[mask])
                    branch_dc=np.sum(wd*kd,axis=0)
                    branch_ac=np.sum(wa*ka,axis=0)
                else:
                    for cell,strength_i in zip(np.flatnonzero(mask),strength):
                        kd,ka=acoustic_kernel(detuning,orders,fm,seg['linewidth_hz'],o['laser_linewidth_hz'],delays[cell],tag)
                        branch_dc+=strength_i*overlap[cell]*(channel_weights[cell]@kd)
                        branch_ac+=strength_i*overlap[cell]*transport[cell]*(channel_weights[cell]@ka)
                gdc+=signed_fraction*branch_dc; gac+=signed_fraction*branch_ac
                channel_dc[optical['order']]+=branch_dc
                unsigned+=abs(signed_fraction)*abs(branch_dc)
            dc+=gdc; ac+=gac; contributions.append(gdc.tolist())
        depth=float(np.max(abs(point_tag))) if history else modified['pump']['modulation_depth']
        actual_gain=max((float(np.max(abs(v))) for v in channel_dc.values()),default=0.)
        transfer_envelopes.append(unsigned.tolist()); channel_maxima.append(actual_gain)
        if actual_gain*(1+depth)*(1+o['source_ram_depth'])>.1:
            raise ModelError('Actual nonideal gain/loss exceeds0.1 after polarization/sideband changes; use the coupled dynamics model.')
        actual_depletion=float(np.max(budget['probe_fiber_input_w']*probe_ratio*unsigned/np.maximum(budget['pump_fiber_input_w']*power_ratio,1e-300)))
        depletion_maxima.append(actual_depletion)
        if actual_depletion>.01:
            raise ModelError('Actual nonideal transfer exceeds1% of pump after polarization/sideband changes; use coupled dynamics.')
        if history:
            signal=vfactor*probe_ratio*point_tag*ac*detector
            signal+=responsivity*zfactor*point_leak*point_tag*detector
        else:
            signal=vfactor*depth*ac*detector*phasor
            signal+=responsivity*zfactor*leaked_pump*depth*detector*phasor
        dc_v=vfactor*probe_ratio*(1+dc)+responsivity*zfactor*(point_ase+point_leak)
        if ram_active:
            # The stored lock-in waveform resolves the slow tag only. Restrict
            # deterministic RAM to a conservatively unclipped linear detector.
            ram_voltage_bound=responsivity*zfactor*o['source_ram_depth']*(point_probe*(1+2*unsigned)*(1+depth)+point_leak)
            if np.any(dc_v+abs(signal)+ram_voltage_bound>=maximum) or np.any(dc_v-abs(signal)-ram_voltage_bound<=0):
                raise ModelError('RAM requires an unclipped detector: increase maximum voltage, reduce power, or reduce RAM depth.')
        if o['detector_saturation_enabled']:
            signal,dc_v,clip=clip_fundamental(dc_v,signal,maximum); clipping.append(clip)
        else: clipping.append(0.)
        clean=lockin_filter(signal,c['receiver']['time_constant_s'],c['receiver']['dwell_s'],c['receiver']['filter_order'])
        power=point_probe*(1+dc)+point_ase+point_leak
        shot=2*1.602176634e-19*responsivity*power if o['detector_shot_noise_enabled'] else np.zeros(len(frequency))
        rin_psd=10**(o['laser_rin_db_hz']/10)/(1+(tag/(o['rin_bandwidth_mhz']*1e6))**2)
        common_rin_transfer=(point_probe*((1+dc)*np.exp(-2j*pi*tag*boundaries[-1]/c['fm']['group_velocity_m_s'])
                             +ac*point_response*np.exp(-2j*pi*tag*control['delay_s']))
                             +point_leak*point_response*np.exp(-2j*pi*tag*control['delay_s']))
        rin=rin_psd*responsivity**2*abs(common_rin_transfer)**2
        signal_ase=4*responsivity**2*(point_probe*(1+dc)+point_leak)*point_ase_psd*leakage
        ase_ase=4*responsivity**2*(point_ase_psd*leakage)**2*optical_bw
        psd=(shot+rin+o['detector_electronic_asd_a']**2+signal_ase+ase_ase)*zfactor**2*abs(detector)**2
        current_components={'shot':shot,'shared_rin':rin,'electronic':o['detector_electronic_asd_a']**2,
                            'signal_ase':signal_ase,'ase_ase':ase_ase}
        for name,component in current_components.items():
            noise_components[name].append((np.broadcast_to(component,(len(frequency),))*zfactor**2*abs(detector)**2).tolist())
        noise,variance_factor=receiver_noise(psd,c['receiver']['time_constant_s'],c['receiver']['dwell_s'],c['receiver']['filter_order'],len(frequency),rng)
        measured=clean+noise
        spectra.append(measured); steady.append(signal); gains.append(dc); contributions_all.append(contributions); noise_psds.append(psd.tolist())
        fits.append(estimate_resonance(frequency,abs(measured),np.mean([s['linewidth_hz'] for s in c['segments']])))
        if progress: progress(ix+1,len(positions))
    control=result['spatial']['selected_control']; target=control['peak_m']; vg=c['fm']['group_velocity_m_s']
    details['shared_source_trace']=shared_source_trace(o['laser_linewidth_hz'],10**(o['laser_rin_db_hz']/10),o['rin_bandwidth_mhz']*1e6,
        control['delay_s']+target/vg,(boundaries[-1]-target)/vg,o['trace_samples'],o['trace_dt_ns']*1e-9,o['seed'])
    if ram_active:
        fm=control['frequency_hz'];time=np.linspace(0,3/fm,min(o['trace_samples'],2048))
        taup=control['delay_s']+target/vg;taus=(boundaries[-1]-target)/vg
        phase=np.deg2rad(o['source_ram_phase_deg']);depth_ram=o['source_ram_depth']
        source_intensity=lambda t:1+depth_ram*np.cos(2*pi*fm*t+phase)
        details['ram']['source_trace']={'time_s':time.tolist(),'source_intensity_multiplier':source_intensity(time).tolist(),
            'pump_intensity_multiplier':source_intensity(time-taup).tolist(),'probe_intensity_multiplier':source_intensity(time-taus).tolist(),
            'pump_delay_s':taup,'probe_delay_s':taus,'target_position_m':target,'frequency_hz':fm,
            'definition':'One deterministic common-source intensity sinusoid at retarded pump/probe times; separate from the stochastic RIN trace.'}
        details['ram']['z_m']=z.tolist()
    spectra=np.array(spectra); steady=np.array(steady)
    result.update(spectra_x_v=spectra.real.tolist(),spectra_y_v=spectra.imag.tolist(),spectra_r_v=abs(spectra).tolist(),
                  steady_x_v=steady.real.tolist(),steady_y_v=steady.imag.tolist(),gain_spectra=np.asarray(gains).tolist(),
                  fits=fits,fitted_resonance_hz=[f['resonance_hz'] for f in fits],segment_gain_contributions=contributions_all,config=deepcopy(config))
    details['polarization']['mean_overlap_by_position']=overlaps
    details['unsigned_transfer_gain_spectra']=transfer_envelopes
    details['max_individual_sideband_gain_by_position']=channel_maxima
    details['estimated_depletion_by_position']=depletion_maxima
    details['detector']={'one_sided_voltage_psd_v2_hz':noise_psds,
                         'one_sided_voltage_psd_components_v2_hz':noise_components,
                         'psd_domain':'One-sided voltage PSD after detector transimpedance and one-pole bandwidth, before IQ mixing/filtering.',
                         'stationary_IQ_variance_per_psd_hz':variance_factor,
                         'clipped_sample_fraction_by_position':clipping,'clip_model':'Deterministic voltage clipping before IQ filtering; noise added after small-signal receiver filtering.'}
    details.update(enabled=True,options=o,effective_config=modified)
    result['nonideal']=details
    result['diagnostics']['model']='Nonideal weak-gain Floquet spectra; exact shared-Wiener ensemble acoustic response; seeded detector realization'
    result['diagnostics']['max_integrated_gain']=float(np.max(gains))
    result['diagnostics']['estimated_pump_depletion_fraction']=float(max(depletion_maxima))
    result['spatial']['response_definition']+=' This remains the clean baseline FM reference; nonideal phase, polarization, RAM and acquisition-time bias drift affect the spectra, not this reference curve.'
    result['warnings']=[w for w in result['warnings'] if 'noise/depletion excluded' not in w]
    result['warnings']+=['Nonideal spectrum still assumes weak SBS gain and first-order intensity tagging; use the separate coupled transient solver for pump depletion.',
                         'Shared-source phase traces are illustrative realizations; optical spectra use their exact Wiener ensemble coherence, not that single trace.',
                         'Polarization uses an explicit scalar relative Jones angle with OU spatial variation and sinusoidal scrambling, not a vector coupled random-birefringence solver.',
                         'Noise is a high-photon-count Gaussian approximation; clipping acts on the deterministic waveform before additive small-signal noise.',
                         'ASE parameters use a two-polarization rectangular optical filter and high-gain noise-figure convention.']
    if history:
        result['warnings'].append('EOM bias drift uses actual acquisition midpoint times across all positions, frozen within each dwell (at most0.1degree change). EDFA mean gain carries relaxation memory with piecewise-frozen equilibrium; tag response is locally linearized. Static power-budget/EOM panels refer to initial bias; use bias-history export for acquisition powers.')
    if ram_active:
        result['warnings'].append('Deterministic shared-source RAM enters the signed Floquet acoustic drive without power renormalization. The detector must remain unclipped. EDFA RAM-frequency gain response and omitted leading RIN mixing are each bounded to1%; mean compression and noise retain the stated slow/small-signal approximation, not full cyclostationary noise propagation.')
    if max(clipping)>0: result['warnings'].append('Detector voltage clipping occurred; the measured fundamental is distorted and noise linearization is approximate.')
    return result
