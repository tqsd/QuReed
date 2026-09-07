"""Inspectable nonideal component/noise figures and unit-labelled CSV exports."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


NOISE_NAMES = {
    'shot': 'Shot noise', 'shared_rin': 'Shared-source RIN',
    'electronic': 'Electronics', 'signal_ase': 'Signal / pump–ASE beat',
    'ase_ase': 'ASE–ASE beat',
}


def save_nonideal_diagnostics(result, outdir):
    """Return absolute artifact paths; omit disabled/unavailable component panels."""
    details=result.get('nonideal',{})
    if not details.get('enabled',False):
        return {}
    out=Path(outdir).resolve(); out.mkdir(parents=True,exist_ok=True)
    paths={}
    def csv_file(key,name,header,rows):
        path=out/name
        with path.open('w',newline='',encoding='utf-8') as stream:
            writer=csv.writer(stream); writer.writerow(header); writer.writerows(rows)
        paths[key]=str(path)
    def figure(rows=1,height=None):
        fig=Figure(figsize=(9,height or (3.4*rows)),dpi=135,layout='constrained')
        FigureCanvasAgg(fig)
        axes=np.atleast_1d(fig.subplots(rows,1))
        for ax in axes:
            ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
            ax.grid(alpha=.2)
        return fig,axes
    def png_file(key,name,fig):
        path=out/name; fig.savefig(path,dpi=135)
        paths[key]=str(path); fig.clear()

    pump=details.get('pump_eom',{})
    probe=details.get('probe_eom',{})
    has_pump=bool(pump.get('phase_rad'))
    has_probe=bool(probe.get('components'))
    if has_pump or has_probe:
        fig,axes=figure(int(has_pump)+int(has_probe)); index=0
        if has_pump:
            phase=np.asarray(pump['phase_rad']); transmission=np.asarray(pump['transmission'])
            axes[index].plot(np.rad2deg(phase),transmission,color='#2878a2',lw=2)
            axes[index].axhline(pump['mean_transmission'],color='#555555',ls='--',label='Cycle mean')
            axes[index].set(xlabel='Pump RF phase (degrees)',ylabel='Intensity transmission (fraction)',
                            title='Pump EOM: finite extinction, bias and RF errors',ylim=(0,1))
            axes[index].legend(fontsize=9); index+=1
            csv_file('nonideal_pump_eom_csv','nonideal_pump_eom.csv',
                     ['rf_phase_rad','intensity_transmission_fraction'],zip(phase,transmission))
        if has_probe:
            components=probe['components']
            order=np.array([c['order'] for c in components]); fraction=np.array([c['power_fraction'] for c in components])
            colors=['#267b52' if n<0 else '#b64a40' if n>0 else '#7c7c7c' for n in order]
            axes[index].bar(order,fraction,color=colors)
            axes[index].set(xlabel='Optical sideband order (negative: Stokes gain; positive: anti-Stokes loss)',
                            ylabel='Optical power fraction',title='Probe IQ spectrum: power is positive; SBS contributions have opposite signs',yscale='log')
            axes[index].set_xticks(order)
            csv_file('nonideal_probe_sidebands_csv','nonideal_probe_sidebands.csv',
                ['optical_sideband_order','power_fraction','signed_sbs_power_fraction','sbs_effect'],
                ((int(n),float(p),float(-np.sign(n)*p),'Stokes gain' if n<0 else 'anti-Stokes loss' if n>0 else 'carrier: baseline only')
                 for n,p in zip(order,fraction)))
        png_file('nonideal_eom_plot','nonideal_eom.png',fig)

    edfa=details.get('edfa_trace',{})
    if edfa.get('time_s'):
        time=np.asarray(edfa['time_s']); pin=np.asarray(edfa['input_power_w']); pout=np.asarray(edfa['output_power_w']); gain=np.asarray(edfa['gain'])
        csv_file('nonideal_edfa_csv','nonideal_edfa.csv',
                 ['time_s','input_power_w','output_power_w','power_gain_linear'],zip(time,pin,pout,gain))
        fig,axes=figure(2)
        axes[0].plot(time*1e6,pin*1e3,label='Input');axes[0].plot(time*1e6,pout*1e3,label='Output')
        axes[0].set(xlabel='Time (microseconds)',ylabel='Optical power (mW)',title='EDFA relaxation trace: time-dependent compressed gain')
        axes[0].legend(fontsize=9)
        axes[1].plot(time*1e6,gain,color='#8a5aa3')
        if details.get('edfa'):
            axes[1].axhline(details['edfa']['compressed_mean_gain'],ls='--',color='#555555',label='Steady mean used by spectrum')
            axes[1].legend(fontsize=9)
        axes[1].set(xlabel='Time (microseconds)',ylabel='Power gain (linear)',
                    title='Illustrative gain-state transient; spectrum uses its stated small-signal response')
        png_file('nonideal_edfa_plot','nonideal_edfa.png',fig)

    source=details.get('shared_source_trace',{})
    if source.get('time_s'):
        columns=['time_s','pump_phase_rad','probe_phase_rad','relative_phase_rad','pump_intensity_multiplier','probe_intensity_multiplier']
        arrays=[np.asarray(source[k]) for k in columns]
        csv_file('nonideal_source_noise_csv','nonideal_source_noise.csv',columns,zip(*arrays))
        time,pp,ps,relative,rp,rs=arrays
        fig,axes=figure(3,height=9.2)
        axes[0].plot(time*1e6,pp,label='Pump: common phase at its delay',lw=1)
        axes[0].plot(time*1e6,ps,label='Probe: same phase process at its delay',lw=1)
        axes[0].set(xlabel='Time (microseconds)',ylabel='Phase (rad)',title='One shared-source realization; optical spectrum uses ensemble coherence')
        axes[0].legend(fontsize=8)
        axes[1].plot(time*1e6,relative,color='#8a5aa3',lw=1)
        expected=source.get('expected_relative_phase_variance_rad2')
        sampled=source.get('sample_relative_phase_variance_rad2')
        caption='Delayed relative phase'
        if expected is not None and sampled is not None:
            caption+=f' | variance: sample {sampled:.3g}, ensemble {expected:.3g} rad²'
        axes[1].set(xlabel='Time (microseconds)',ylabel='Pump − probe phase (rad)',title=caption)
        axes[2].plot(time*1e6,(rp-1)*1e6,label='Pump RIN',lw=1)
        axes[2].plot(time*1e6,(rs-1)*1e6,label='Probe RIN',lw=1)
        axes[2].set(xlabel='Time (microseconds)',ylabel='Fractional intensity deviation (ppm)',title='Delayed samples of one shared intensity-noise process')
        axes[2].legend(fontsize=8)
        png_file('nonideal_source_noise_plot','nonideal_source_noise.png',fig)

    polarization=details.get('polarization',{})
    if polarization.get('z_m'):
        z=np.asarray(polarization['z_m']); angle=np.asarray(polarization['relative_angle_rad']); eta=np.asarray(polarization['unscrambled_overlap'])
        csv_file('nonideal_polarization_csv','nonideal_polarization.csv',
                 ['fiber_position_m','relative_jones_angle_rad','unscrambled_overlap_fraction'],zip(z,angle,eta))
        overlap=np.asarray(polarization.get('mean_overlap_by_position',[eta]))
        positions=np.asarray(result['positions_m'])
        csv_file('nonideal_polarization_scan_csv','nonideal_polarization_scan.csv',
                 ['target_position_m','fiber_position_m','mean_acquisition_overlap_fraction'],
                 ((target,cell,float(overlap[i,j])) for i,target in enumerate(positions) for j,cell in enumerate(z)))
        fig,axes=figure(2)
        axes[0].plot(z*100,angle,label='Spatial relative-angle perturbation',color='#8a5aa3')
        axes[0].set(xlabel='Fiber position (cm)',ylabel='Relative Jones angle (rad)',title='Polarization variation along the physical fiber')
        axes[1].plot(z*100,eta,'--',label='No scrambling',color='#777777')
        selected=int(np.argmin(abs(positions-result['config']['scan']['target_m'])))
        axes[1].plot(z*100,overlap[selected],label=f'Scan-averaged overlap at target {positions[selected]*100:.1f} cm',color='#2878a2')
        if len(positions)>1:
            axes[1].fill_between(z*100,overlap.min(0),overlap.max(0),alpha=.18,color='#2878a2',label='Range across target acquisitions')
        axes[1].set(xlabel='Fiber position (cm)',ylabel='Pump/probe overlap (fraction)',ylim=(0,1),title='Explicit coupling overlap, not a fitted sensing profile')
        axes[1].legend(fontsize=8)
        png_file('nonideal_polarization_plot','nonideal_polarization.png',fig)

    detector=details.get('detector',{})
    if detector.get('one_sided_voltage_psd_v2_hz'):
        positions=np.asarray(result['positions_m']); frequency=np.asarray(result['frequency_hz']); total=np.asarray(detector['one_sided_voltage_psd_v2_hz'])
        components=detector.get('one_sided_voltage_psd_components_v2_hz',{})
        contributions={name:np.asarray(components.get(name,np.zeros_like(total))) for name in NOISE_NAMES}
        variance_factor=float(detector['stationary_IQ_variance_per_psd_hz']); sigma=np.sqrt(np.maximum(total,0)*variance_factor)
        clipping=np.asarray(detector['clipped_sample_fraction_by_position'])
        csv_file('nonideal_detector_noise_csv','nonideal_detector_noise.csv',
            ['target_position_m','frequency_hz','total_one_sided_voltage_psd_v2_hz']+
            [name+'_one_sided_voltage_psd_v2_hz' for name in NOISE_NAMES]+
            ['stationary_iq_sigma_peak_v','clipped_deterministic_sample_fraction'],
            ((float(target),float(freq),float(total[i,j]),*[float(contributions[name][i,j]) for name in NOISE_NAMES],
              float(sigma[i,j]),float(clipping[i])) for i,target in enumerate(positions) for j,freq in enumerate(frequency)))
        selected=int(np.argmin(abs(positions-result['config']['scan']['target_m'])))
        fig,axes=figure(3,height=9.3)
        for name,label in NOISE_NAMES.items():
            asd=np.sqrt(np.maximum(contributions[name][selected],0))*1e9
            if np.any(asd>0): axes[0].plot(frequency/1e9,np.where(asd>0,asd,np.nan),label=label,lw=1)
        total_asd=np.sqrt(np.maximum(total[selected],0))*1e9
        if np.any(total_asd>0):
            axes[0].plot(frequency/1e9,np.where(total_asd>0,total_asd,np.nan),label='Total',color='black',lw=2)
            axes[0].set_yscale('log')
        else: axes[0].text(.5,.5,'No enabled noise contribution',ha='center',transform=axes[0].transAxes)
        axes[0].set(xlabel='Pump − probe frequency (GHz)',ylabel='Voltage ASD (nV/√Hz)',title='One-sided detector noise\nAfter detector bandwidth, before IQ filtering')
        axes[0].legend(fontsize=8,ncol=2)
        axes[1].plot(frequency/1e9,sigma[selected]*1e6,color='#2878a2')
        axes[1].set(xlabel='Pump − probe frequency (GHz)',ylabel='Stationary IQ σ (microV)',title='Predicted RC-filtered IQ noise; finite-dwell states start at zero')
        axes[2].plot(positions*100,clipping*100,'o-',color='#b64a40')
        axes[2].set(xlabel='Target position (cm)',ylabel='Deterministic clipping (%)',ylim=(-1,101),
                    title='Deterministic clipping before additive noise\nStrongly clipped noise statistics are approximate')
        png_file('nonideal_detector_noise_plot','nonideal_detector_noise.png',fig)

    unsigned=details.get('unsigned_transfer_gain_spectra')
    if unsigned is not None:
        unsigned=np.asarray(unsigned);signed=np.asarray(result['gain_spectra'])
        maxima=details['max_individual_sideband_gain_by_position']
        csv_file('nonideal_interaction_csv','nonideal_interaction.csv',
                 ['target_position_m','frequency_hz','net_signed_sbs_gain','unsigned_transfer_gain','maximum_individual_sideband_gain'],
                 ((float(target),float(freq),float(signed[i,j]),float(unsigned[i,j]),float(maxima[i]))
                  for i,target in enumerate(result['positions_m']) for j,freq in enumerate(result['frequency_hz'])))

    history=details.get('bias_history',{})
    if history.get('time_s'):
        columns=['time_s','target_m','frequency_hz','pump_bias_deg','probe_bias_deg',
                 'pump_mean_transmission','pump_edfa_input_w','edfa_gain','pump_edfa_output_w',
                 'pump_fiber_input_w','pump_tag_real','pump_tag_imag','probe_transmission_ratio']
        orders=sorted(history['probe_sideband_power_fraction'],key=int)
        header=columns+['probe_sideband_'+n+'_power_fraction' for n in orders]
        arrays=[np.asarray(history[k]) for k in columns]+[np.asarray(history['probe_sideband_power_fraction'][n]) for n in orders]
        csv_file('nonideal_bias_drift_csv','nonideal_bias_drift.csv',header,zip(*arrays))
        t=np.asarray(history['time_s']);fig,axes=figure(3,height=9.4)
        axes[0].plot(t,history['pump_bias_deg'],label='Pump MZM bias')
        axes[0].plot(t,history['probe_bias_deg'],label='Probe IQ bias')
        axes[0].set(xlabel='Acquisition midpoint time (s)',ylabel='Bias error (degrees)',
                    title='Actual acquisition-time EOM drift; chronology continues across target positions')
        axes[0].legend(fontsize=8)
        axes[1].plot(t,np.asarray(history['pump_edfa_output_w'])*1e3,label='EDFA output')
        axes[1].plot(t,np.asarray(history['pump_fiber_input_w'])*1e3,label='Pump entering fiber')
        axes[1].set(xlabel='Acquisition midpoint time (s)',ylabel='Mean optical power (mW)',
                    title='Changing MZM transmission and carried EDFA gain state')
        axes[1].legend(fontsize=8)
        axes[2].plot(t,history['probe_transmission_ratio'],label='Total probe power / initial value',color='#555555')
        for n,label in [('-1','Stokes sideband fraction'),('0','Carrier fraction'),('1','Anti-Stokes sideband fraction')]:
            if n in history['probe_sideband_power_fraction']:
                axes[2].plot(t,history['probe_sideband_power_fraction'][n],label=label)
        axes[2].set(xlabel='Acquisition midpoint time (s)',ylabel='Ratio / power fraction',
                    title='Actual IQ transfer; fractions are positive, SBS gain/loss remains signed')
        axes[2].legend(fontsize=8,ncol=2)
        png_file('nonideal_bias_drift_plot','nonideal_bias_drift.png',fig)

    ram=details.get('ram',{});trace=ram.get('source_trace',{})
    if trace.get('time_s'):
        columns=['time_s','source_intensity_multiplier','pump_intensity_multiplier','probe_intensity_multiplier']
        arrays=[np.asarray(trace[k]) for k in columns]
        csv_file('nonideal_ram_csv','nonideal_ram.csv',columns,zip(*arrays))
        diagnostics=ram['coefficient_diagnostics'];z=np.asarray(ram['z_m'])
        csv_file('nonideal_ram_floquet_csv','nonideal_ram_floquet.csv',
            ['target_position_m','fiber_position_m','mean_intensity_product','summed_fourier_power',
             'spectral_order_centroid','phase_samples','parseval_max_abs_error','leading_rin_mixing_fraction'],
            ((float(target),float(cell),d['mean_intensity_product'][j],d['summed_fourier_power'][j],
              d['spectral_order_centroid'][j],d['phase_samples'],d['parseval_max_abs_error'],d['leading_rin_mixing_fraction'])
             for target,d in zip(result['positions_m'],diagnostics) for j,cell in enumerate(z)))
        time,source,pump,probe=arrays;fig,axes=figure(3,height=9.4)
        for values,label,style in [(source,'Source','--'),(pump,'Pump at retarded time','-'),(probe,'Probe at retarded time',':')]:
            axes[0].plot(time*1e6,values,style,label=label)
        axes[0].set(xlabel='Time (microseconds)',ylabel='Intensity multiplier',
                    title='Deterministic shared-source RAM at the laser FM rate; not stochastic RIN')
        axes[0].legend(fontsize=8)
        selected=int(np.argmin(abs(np.asarray(result['positions_m'])-trace['target_position_m'])))
        d=diagnostics[selected]
        axes[1].plot(z*100,d['mean_intensity_product'],label='Analytic mean of pump × probe intensity')
        axes[1].plot(z*100,d['summed_fourier_power'],'--',label='Sum of signed-Fourier coefficient powers')
        axes[1].set(xlabel='Fiber position (cm)',ylabel='Mean intensity product',
                    title='Physical Floquet-drive normalization; intentionally not rescaled to unity')
        axes[1].legend(fontsize=8)
        axes[2].plot(z*100,d['spectral_order_centroid'],color='#8a5aa3')
        axes[2].set(xlabel='Fiber position (cm)',ylabel='Fourier order centroid',
                    title='FM–RAM correlation can produce asymmetric acoustic-drive sideband weights')
        png_file('nonideal_ram_plot','nonideal_ram.png',fig)
    return paths
