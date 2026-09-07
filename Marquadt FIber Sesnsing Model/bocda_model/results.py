"""Persist BOCDA results and static, independently viewable reports."""
from __future__ import annotations

import csv
import html
import json
from copy import deepcopy
from pathlib import Path

import numpy as np


def save_results(result, outdir, config=None):
    """Write JSON/CSV/PNG/HTML artifacts; return an absolute-path manifest."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt

    out = Path(outdir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    nonideal=result.get('nonideal',{})
    is_nonideal=result.get('extension_kind')=='nonideal' or nonideal.get('enabled',False)
    def target(key, filename):
        paths[key] = str(out / filename)
        return out / filename

    with target('json', 'results.json').open('w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, allow_nan=False)
    with target('config', 'settings_used.json').open('w', encoding='utf-8') as f:
        settings=deepcopy(config if config is not None else result['config'])
        if is_nonideal:
            settings.setdefault('extensions',{})['nonideal']=deepcopy(nonideal.get('options',{}))
            settings['extension_kind']='nonideal'
        json.dump(settings, f, indent=2, allow_nan=False)
    x = np.array(result['frequency_hz']) / 1e9
    pos = np.array(result['positions_m'])
    sx, sy, sr = [np.array(result[k]) for k in ['spectra_x_v','spectra_y_v','spectra_r_v']]
    with target('spectra_csv','spectra.csv').open('w', newline='', encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['target_m','frequency_hz','X_peak_V','Y_peak_V','R_peak_V','integrated_gain','actual_fm_hz','external_delay_s'])
        for i,z in enumerate(pos):
            for j,frequency in enumerate(result['frequency_hz']):
                w.writerow([z,frequency,sx[i,j],sy[i,j],sr[i,j],result['gain_spectra'][i][j],
                            result['controls'][i]['frequency_hz'],result['controls'][i]['delay_s']])
    with target('profile_csv','profile.csv').open('w', newline='', encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['target_m','fit_resonance_hz','sampled_peak_hz','fit_linewidth_hz','fit_r_squared','flags'])
        for z, fit in zip(pos,result['fits']):
            w.writerow([z,fit['resonance_hz'],fit.get('peak_resonance_hz'),fit['linewidth_hz'],fit['r_squared'],';'.join(fit['flags'])])
    with target('spatial_csv','spatial_response.csv').open('w', newline='', encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['offset_from_peak_m','normalized_local_resonant_response'])
        w.writerows(zip(result['spatial']['offset_m'],result['spatial']['response']))

    with plt.rc_context({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130}):
        selected=int(np.argmin(abs(pos-result['config']['scan']['target_m'])))
        fig,ax=plt.subplots(figsize=(8,4.5))
        ax.plot(x,1e6*sx[selected],label='X')
        ax.plot(x,1e6*sy[selected],label='Y')
        ax.plot(x,1e6*sr[selected],label='R',lw=2)
        fit=result['fits'][selected]
        if 'fitted_curve_v' in fit:
            fit_x=np.array(fit.get('fit_frequency_hz',result['frequency_hz']))/1e9
            ax.plot(fit_x,1e6*np.array(fit['fitted_curve_v']),':',color='black',label='Local Lorentzian + linear background')
        ax.set(xlabel='Pump - probe frequency (GHz)',ylabel='Lock-in peak voltage (microV)',
               title=f"Local spectrum | target {pos[selected]*100:.1f} cm")
        ax.grid(alpha=.2); ax.legend(fontsize=8); fig.tight_layout()
        fig.savefig(target('spectrum_plot','local_spectrum.png')); plt.close(fig)

        fig,ax=plt.subplots(figsize=(8,4.2))
        spatial=result['spatial']
        offset=np.array(spatial['offset_m'])*100
        ax.plot(offset,spatial['response'],label='Dynamic acoustic Floquet response')
        if 'quasistatic_response' in spatial:
            ax.plot(offset,spatial['quasistatic_response'],'--',label='Quasi-static comparison')
        ax.axhline(.5,color='gray',ls=':',label='Half maximum')
        fwhm=spatial['fwhm_m']
        label='Unlocalized (zero FM excursion)' if fwhm is None else f'Computed local-response FWHM: {100*fwhm:.2f} cm'
        if is_nonideal: label='Clean FM spatial reference | '+label
        ax.set(xlabel='Distance from correlation peak (cm)',ylabel='Normalized local resonant response',title=label)
        ax.grid(alpha=.2); ax.legend(fontsize=8); fig.tight_layout()
        fig.savefig(target('spatial_plot','spatial_response.png')); plt.close(fig)

        fig,(ax1,ax2)=plt.subplots(2,1,figsize=(8,7),gridspec_kw={'height_ratios':[1.4,1]},constrained_layout=True)
        if len(pos)>1:
            mesh=ax1.pcolormesh(pos*100,x,sr.T*1e6,shading='auto',cmap='viridis')
            fig.colorbar(mesh,ax=ax1,label='Lock-in R (microV peak)')
        else:
            ax1.plot(x,sr[0]*1e6)
            ax1.set(xlabel='Pump - probe frequency (GHz)',ylabel='Lock-in R (microV peak)')
        if len(pos)>1: ax1.set(xlabel='Target position (cm)',ylabel='Pump - probe frequency (GHz)')
        ax1.set_title('Raw measured spectrum; off-peak background retained')
        fiber=result['fiber']
        ax2.step(np.array(fiber['z_m'])*100,np.array(fiber['resonance_hz'])/1e9,where='mid',label='Configured material resonance',color='gray')
        fitted=np.array([v if v is not None else np.nan for v in result['fitted_resonance_hz']])/1e9
        ax2.plot(pos*100,fitted,'o-',label='Local resonance fit',ms=4)
        flagged=np.array([bool(f['flags']) for f in result['fits']])
        if flagged.any(): ax2.plot(pos[flagged]*100,fitted[flagged],'x',color='crimson',ms=8,label='Flagged fit / mixing')
        for b in fiber['boundaries_m']: ax2.axvline(b*100,color='gray',lw=.5,alpha=.5)
        ax2.set(xlabel='Target position (cm)',ylabel='Brillouin frequency (GHz)',title='Configured input versus reconstructed measurement')
        ax2.grid(alpha=.2); ax2.legend(fontsize=8)
        fig.savefig(target('profile_plot','profile_map.png')); plt.close(fig)

    esc=html.escape
    warnings=''.join(f'<li>{esc(str(w))}</li>' for w in result['warnings'])
    diagnostics=''.join(f'<tr><td>{esc(str(k))}</td><td>{esc(str(v))}</td></tr>' for k,v in result['diagnostics'].items())
    rows=[]
    for z,fit in zip(pos,result['fits']):
        resonance='no signal' if fit['resonance_hz'] is None else format(fit['resonance_hz']/1e9,'.6f')
        flags=esc(', '.join(fit['flags']) or 'none')
        rows.append(f'<tr><td>{z:.4f}</td><td>{resonance}</td><td>{flags}</td></tr>')
    fits=''.join(rows)
    nonideal_html=''
    if is_nonideal:
        from .nonideal_results import save_nonideal_diagnostics
        supplemental=save_nonideal_diagnostics(result,out)
        paths.update(supplemental)
        titles={'nonideal_eom_plot':'EOM transfer and signed SBS sideband roles',
                'nonideal_edfa_plot':'EDFA compressed-gain transient',
                'nonideal_source_noise_plot':'Shared-source phase and intensity noise',
                'nonideal_polarization_plot':'Polarization variation and scrambling',
                'nonideal_detector_noise_plot':'Detector noise contributions and clipping',
                'nonideal_bias_drift_plot':'Acquisition-time EOM bias drift and optical budget',
                'nonideal_ram_plot':'Shared delayed residual amplitude modulation'}
        images=''.join(f'<h3>{esc(titles[key])}</h3><img src="{esc(Path(path).name)}" alt="{esc(titles[key])}">'
                       for key,path in supplemental.items() if key in titles)
        links=' · '.join(f'<a href="{esc(Path(path).name)}">{esc(Path(path).stem.replace("nonideal_","").replace("_"," "))} CSV</a>'
                         for key,path in supplemental.items() if str(path).endswith('.csv'))
        nonideal_html=f'''<h2>Nonideal component and receiver diagnostics</h2>
        <p class="note">The spatial-response figure above is the <strong>clean FM reference</strong>, not the nonideal point-spread function. Nonideal effects are in the measured spectra. Stokes sidebands contribute gain; anti-Stokes sidebands contribute loss, while all optical power fractions remain positive. Fit flags above must be considered when interpreting reconstructed resonances.</p>
        <p>Noise PSDs are one-sided voltage densities after detector transimpedance/bandwidth and before IQ filtering. The source traces show one realization; optical phase spectra use ensemble coherence. Deterministic voltage clipping precedes additive small-signal noise, so strongly clipped noise statistics are approximate. The EDFA trace is illustrative dynamics; spectra use its specified steady mean and tag response.</p>
        {images}<p>{links}</p><details><summary>Complete nonideal options (also saved in settings_used.json)</summary><pre>{esc(json.dumps(nonideal.get('options',{}),indent=2))}</pre></details>'''
    # Report is intentionally static: readable without a running Python or GUI process.
    body=f'''<!doctype html><html><head><meta charset="utf-8"><title>BOCDA simulation results</title>
    <style>body{{font:16px system-ui;max-width:1000px;margin:35px auto;padding:0 20px;background:#fafbfc;color:#172b40}}img{{max-width:100%;background:white;border:1px solid #ddd}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:7px;border-bottom:1px solid #ddd;text-align:left}}.note{{background:#fff4d8;padding:15px}}code{{font-size:13px}}</style></head>
    <body><h1>BOCDA classical simulation</h1><p>Mode: {esc(result['mode'])}. {len(pos)} position(s), {len(x)} frequency samples per position.</p>
    <p class="note">These are numerical checks of an explicitly approximate classical model. Source frequency-excursion conventions remain qualified; the calculated spatial response is not forced to equal the paper's quoted 3 cm.</p>
    <h2>Local spectrum</h2><img src="local_spectrum.png" alt="Local lock-in spectrum">
    <h2>Spatial response</h2><img src="spatial_response.png" alt="Dynamic correlation response and quasi-static comparison">
    <h2>Fiber reconstruction</h2><img src="profile_map.png" alt="Spatial spectrum map and fitted resonance profile">
    <table><tr><th>Target (m)</th><th>Fit resonance (GHz)</th><th>Fit flags</th></tr>{fits}</table>
    {nonideal_html}<h2>Model diagnostics</h2><table>{diagnostics}</table><h2>Warnings and qualifications</h2><ul>{warnings}</ul>
    <p><a href="results.json">Complete results JSON</a> · <a href="settings_used.json">Settings used</a> · <a href="spectra.csv">Spectra CSV</a> · <a href="profile.csv">Profile CSV</a> · <a href="spatial_response.csv">Spatial response CSV</a></p></body></html>'''
    target('report','report.html').write_text(body,encoding='utf-8')
    with target('manifest','manifest.json').open('w',encoding='utf-8') as f:
        json.dump(paths,f,indent=2)
    return paths
