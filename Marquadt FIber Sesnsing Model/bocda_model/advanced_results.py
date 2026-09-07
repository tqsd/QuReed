"""Static exports for advanced quantum and transient envelope simulations.

Uses isolated Figure/FigureCanvasAgg objects rather than pyplot or GUI backends.
Model outputs and extension settings are preserved verbatim in JSON.
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path
import threading

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

_RENDER_LOCK = threading.RLock()


def _table(rows, headers=("Setting / diagnostic", "Value")):
    def esc(value):
        return html.escape(str(value))
    heading = "".join(f"<th>{esc(value)}</th>" for value in headers)
    body = "".join("<tr>"+"".join(f"<td>{esc(value)}</td>" for value in row)+"</tr>" for row in rows)
    return f"<table><thead><tr>{heading}</tr></thead><tbody>{body}</tbody></table>"


def _flatten(data, prefix=""):
    rows = []
    for name, value in data.items():
        label = f"{prefix}.{name}" if prefix else name
        if isinstance(value, dict):
            rows.extend(_flatten(value, label))
        else:
            rows.append((label, json.dumps(value, ensure_ascii=False) if isinstance(value,(list,bool)) else value))
    return rows


def _figure(figsize=(10, 6)):
    figure = Figure(figsize=figsize, dpi=140, layout="constrained")
    FigureCanvasAgg(figure)
    return figure


def _save_figure(fig, path, description):
    # Agg embeds provenance/axis descriptions so tests can inspect actual PNG metadata.
    fig.savefig(path, metadata={"Title":description, "Description":description,
                                "Software":"BOCDA advanced_results / Matplotlib FigureCanvasAgg"})
    fig.clear()


def _write_csv(path, headers, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


def _fisher_rows(quantum):
    fi = quantum["multimode"].get("fisher_information")
    if fi is None:
        return [("not computed", quantum["multimode"]["fisher_status"], None, None, None)]
    definitions = [
        ("Independent joint", fi["independent_joint"]),
        ("Passive mixed joint", fi["passively_mixed_joint"]),
        ("Best scalar candidate", fi["single_collective_readout"]["best"]),
        ("Reduced mixed mode", fi["reduced_first_mixed_mode"]),
        ("Same-budget coherent", fi["same_budget_coherent_joint"]),
    ]
    return [(label,"bright-LO Gaussian approximation",value["total_per_hz2"],
             value["mean_per_hz2"],value["covariance_per_hz2"]) for label,value in definitions]


def _quantum_exports(result, target):
    from .quantum import homodyne

    quantum = result["quantum"]
    if not quantum.get("enabled"):
        raise ValueError("Quantum export requires an enabled, completed quantum analysis.")
    frequency = np.asarray(quantum["frequency_hz"])
    position = np.asarray(quantum["positions_m"])
    selected = quantum["selected"]
    index = int(np.argmin(abs(position-selected["position_m"])))
    options = quantum["options"]
    means = np.asarray(quantum["difference_voltage_v"])
    variance = np.asarray(quantum["difference_voltage_variance_v2"])
    qmean = np.asarray(quantum["quadrature_mean"])
    qvariance = np.asarray(quantum["quadrature_variance"])
    finite = np.asarray(quantum["finite_lo_relative_variance"])
    _write_csv(target("quantum_spectra_csv","quantum_spectra.csv"),
               ["target_m","pump_minus_probe_hz","difference_mean_v","difference_variance_v2",
                "detected_quadrature_mean","detected_quadrature_variance","finite_lo_relative_variance",
                "mode_duration_s","total_input_photons"],
               ([z,f,means[i,j],variance[i,j],qmean[i,j],qvariance[i,j],finite[i,j],
                 options["mode_duration_s"],quantum["input_total_photons"]]
                for i,z in enumerate(position) for j,f in enumerate(frequency)))
    _write_csv(target("quantum_modes_csv","quantum_modes.csv"),
               ["mode_index","start_s","stop_s","input_photons","squeezing_photons"],
               ([m["index"],m["start_s"],m["stop_s"],m["input_photons"],m["squeezing_photons"]]
                for m in quantum["multimode"]["modes"]))
    fi_rows = _fisher_rows(quantum)
    _write_csv(target("quantum_fisher_csv","quantum_fisher.csv"),
               ["readout","status","total_fi_hz_minus2","mean_fi_hz_minus2","covariance_fi_hz_minus2"],fi_rows)

    plots = []
    fig = _figure((10,6.3))
    axes = fig.subplots(2,1,sharex=True)
    axes[0].plot(frequency/1e9,means[index],color="#007c91")
    axes[0].set(ylabel="Balanced mean voltage (V)",
                title=f"Selected temporal mode | target {position[index]*100:.1f} cm")
    axes[1].plot(frequency/1e9,variance[index],color="#76549d",label="Finite-LO + electronic variance")
    axes[1].set(xlabel="Pump - probe frequency (GHz)",ylabel="Voltage variance (V²)")
    axes[1].ticklabel_format(axis="y",style="sci",scilimits=(0,0))
    for ax in axes:
        ax.axvline(selected["frequency_hz"]/1e9,color="gray",linestyle=":",label="Selected operating point")
        ax.grid(alpha=.2)
    fig.suptitle("Homodyne replacement receiver — not lock-in peak voltages",fontsize=12)
    path=target("quantum_spectrum_plot","quantum_spectrum.png")
    _save_figure(fig,path,"Homodyne spectrum: pump-probe GHz, balanced mean voltage V and voltage variance V^2")
    plots.append(("Mean and variance versus frequency",path.name,
                  "Same normalized temporal observation at each independently sampled spectrum setting. Variance includes the finite coherent-LO contribution."))

    fig = _figure((11,8))
    axes = fig.subplots(2,2)
    covariance=np.asarray(selected["V"],float)
    values,vectors=np.linalg.eigh(covariance)
    theta=np.linspace(0,2*np.pi,241)
    ellipse=vectors@np.diag(np.sqrt(np.maximum(values,0)))@np.array([np.cos(theta),np.sin(theta)])
    axes[0,0].plot(ellipse[0],ellipse[1],color="#007c91")
    axes[0,0].set(xlabel="Centered x quadrature",ylabel="Centered p quadrature",
                  title="1σ covariance ellipse" if selected["is_exact_gaussian_under_model"] else "Moment ellipse — non-Gaussian mixture")
    axes[0,0].set_aspect("equal",adjustable="datalim")
    axes[0,0].grid(alpha=.2)
    mixed=np.asarray(quantum["multimode"]["mixed_homodyne_covariance"])
    norm=np.sqrt(np.diag(mixed))
    correlation=mixed/np.outer(norm,norm)
    mesh=axes[0,1].imshow(correlation,vmin=-1,vmax=1,cmap="coolwarm",origin="lower")
    axes[0,1].set(xlabel="Temporal output mode",ylabel="Temporal output mode",
                  title="Mixed homodyne correlation matrix")
    axes[0,1].set_xticks(range(len(mixed)))
    axes[0,1].set_yticks(range(len(mixed)))
    fig.colorbar(mesh,ax=axes[0,1],label="Correlation coefficient")
    phases=np.linspace(-180,180,181)
    moments=[homodyne(selected["d"],selected["V"],quantum["optical_frequency_hz"],
                       options["mode_duration_s"],options["lo_power_w"],np.deg2rad(phase),
                       options["quantum_efficiency"],options["homodyne_transimpedance_v_a"],
                       options["electronics_noise_a_rt_hz"],options["lo_mode_overlap"],options["lo_detuning_hz"])
             for phase in phases]
    axes[1,0].plot(phases,[v["difference_voltage_v"] for v in moments],color="#007c91")
    invalid_phase=np.array([max(abs(v["difference_voltage_v"]),max(v["individual_diode_dc_equivalent_voltage_v"])) > options["homodyne_max_voltage_v"] for v in moments])
    if invalid_phase.any():
        voltage=np.array([v["difference_voltage_v"] for v in moments])
        axes[1,0].plot(phases[invalid_phase],voltage[invalid_phase],".",color="crimson",label="Outside receiver headroom")
        axes[1,0].legend(fontsize=8)
    axes[1,0].set(xlabel="LO phase (degree)",ylabel="Balanced mean voltage (V)",title="Predicted LO phase dependence")
    axes[1,1].plot(phases,[1e6*np.sqrt(v["difference_voltage_variance_v2"]) for v in moments],color="#76549d")
    axes[1,1].set(xlabel="LO phase (degree)",ylabel="Voltage standard deviation (µV)",title="Finite-LO noise versus quadrature")
    for ax in axes[1]:
        ax.axvline(options["lo_phase_deg"],color="gray",linestyle=":")
        ax.grid(alpha=.2)
    fig.suptitle("State moments and matched-mode measurement diagnostics",fontsize=12)
    path=target("quantum_state_plot","quantum_state.png")
    _save_figure(fig,path,"Quantum centered covariance ellipse; temporal correlation; LO phase degrees versus voltage V and standard deviation microV")
    plots.append(("State moments, correlations and LO phase",path.name,
                  "The ellipse shows covariance, not a reconstructed density matrix. A phase-mixture ellipse is not a Gaussian-state claim. Phase curves are predictions for the same fixed optical state; they are not a new physical scan. Any phase outside individual-diode or difference-output headroom is marked red."))

    fig = _figure((11,5.5))
    fi=quantum["multimode"].get("fisher_information")
    if fi is None:
        ax=fig.subplots()
        ax.axis("off")
        ax.text(.5,.7,"Fisher information was not evaluated",ha="center",fontsize=16)
        ax.text(.5,.48,quantum["multimode"]["fisher_status"],ha="center",wrap=True,fontsize=11)
        ax.text(.5,.26,"Suppressed values are not zeros.\nSee warnings and exact finite-LO moment outputs.",ha="center",fontsize=11)
    else:
        axes=fig.subplots(1,2)
        labels=["Independent\njoint","Passive mixed\njoint","Best scalar\ncandidate","Reduced mixed\nmode","Same-budget\ncoherent"]
        for ax,column,title,color in [(axes[0],3,"Displacement information","#007c91"),
                                       (axes[1],4,"Covariance information","#76549d")]:
            values=[row[column] for row in fi_rows]
            ax.bar(range(len(values)),values,color=color)
            ax.set_xticks(range(len(values)),labels,fontsize=8)
            ax.set(title=title,ylabel="Classical Fisher information (Hz⁻²)")
            ax.ticklabel_format(axis="y",style="sci",scilimits=(0,0))
            ax.grid(axis="y",alpha=.2)
        fig.suptitle("Same input photons, LO photons, observation time and physical modes\nFixed local gain-spectrum shift; not quantum Fisher information",fontsize=11)
    path=target("quantum_fisher_plot","quantum_fisher.png")
    _save_figure(fig,path,"Resource-matched classical Fisher information Hz^-2; displacement and covariance terms; suppressed FI is not zero")
    plots.append(("Resource-matched measurement comparison",path.name,
                  "This is classical measurement FI, not quantum Fisher information. Passive mixing plus joint readout cannot create information. The single readout is the best of stated projection candidates, not a global optimum. Extra thermal covariance information is not evidence of quantum advantage."))

    if len(position)>1:
        fig=_figure((11,5))
        axes=fig.subplots(1,2)
        for ax,values,title,label in [(axes[0],means,"Mean balanced output","V"),
                                      (axes[1],1e6*np.sqrt(variance),"Output noise standard deviation","µV")]:
            mesh=ax.pcolormesh(position*100,frequency/1e9,values.T,shading="nearest",cmap="viridis")
            ax.set(xlabel="Target position (cm)",ylabel="Pump - probe frequency (GHz)",title=title)
            fig.colorbar(mesh,ax=ax,label=label)
        path=target("quantum_map_plot","quantum_map.png")
        _save_figure(fig,path,"Quantum scan map: target position cm, frequency GHz, voltage mean V and standard deviation microV")
        plots.append(("Spatial quantum readout map",path.name,"Each map entry is a separate normalized temporal-mode observation; the map is not a simultaneous quantum covariance matrix across fiber positions."))

    summary=[
        ("Selected target (m)",selected["position_m"]),("Selected frequency (Hz)",selected["frequency_hz"]),
        ("Effective amplifier gain",selected["effective_amplifier_gain"]),
        ("Exact Gaussian under declared model",selected["is_exact_gaussian_under_model"]),
        ("Displaced thermal under declared model",selected["is_displaced_thermal"]),
        ("Input photons in total duration",quantum["input_total_photons"]),
        ("Acoustic bath occupation",quantum["bath_occupation"]),
        ("Passive path transmission",quantum["passive_transmission"]),
        ("Fisher interpretation",quantum["multimode"]["fisher_status"]),
        ("Worst multimode finite-LO variance correction",quantum["multimode"]["worst_finite_lo_relative_variance"]),
    ]
    extra = "<h2>Selected channel and receiver checks</h2>"+_table(_flatten(selected["channel_checks_before_phase_mixture"])+_flatten(selected["measurement"]))
    extra += "<h2>Explicit temporal-mode and resource model</h2><p>"+html.escape(quantum["multimode"]["mode_basis"])+"</p>"
    extra += _table(_flatten({key:quantum["multimode"][key] for key in ["total_input_photons","total_lo_photons",
                                 "total_observation_s","temporal_bin_duration_s","receiver_bandwidth_hz","assumed_noise_bandwidth_resource_hz"]}))
    extra += "<h2>Fisher comparison</h2>"+_table(fi_rows,("Readout","Status","Total FI (Hz⁻²)","Mean FI (Hz⁻²)","Covariance FI (Hz⁻²)"))
    extra += "<p>"+html.escape(quantum["multimode"]["qualification"])+"</p>"
    return "Selected-mode quantum / homodyne simulation",summary,plots,extra


def _dynamics_exports(result, target):
    time=np.asarray(result["time_s"],float)
    z=np.asarray(result["z_m"],float)
    pump=np.asarray(result["pump_power_w"])
    probe=np.asarray(result["probe_power_w"])
    qr,qi=np.asarray(result["acoustic_real_w"]),np.asarray(result["acoustic_imag_w"])
    _write_csv(target("dynamics_fields_csv","dynamics_fields.csv"),
               ["time_s","position_m","pump_power_w","probe_power_w","normalized_acoustic_real_w","normalized_acoustic_imag_w"],
               ([t,zz,pump[i,j],probe[i,j],qr[i,j],qi[i,j]] for i,t in enumerate(time) for j,zz in enumerate(z)))
    keys=["boundary_time_s","pump_input_w","pump_output_w","probe_input_w","probe_output_w","photon_balance_trace_relative"]
    _write_csv(target("dynamics_boundary_csv","dynamics_boundaries.csv"),keys,zip(*(result[key] for key in keys)))
    plots=[]
    fig=_figure((11,8))
    axes=fig.subplots(2,2)
    for ax,field,title,label in [
        (axes[0,0],pump*1e3,"Pump envelope power","mW"),
        (axes[0,1],probe*1e3,"Counterpropagating probe power","mW"),
        (axes[1,0],np.sqrt(qr*qr+qi*qi)*1e3,"Normalized acoustic-envelope magnitude","mW (envelope units)"),
        (axes[1,1],np.ma.masked_where(np.hypot(qr,qi)==0,np.angle(qr+1j*qi)),"Normalized acoustic-envelope phase","rad")]:
        mesh=ax.pcolormesh(z*100,time*1e9,field,shading="nearest",cmap="twilight" if label=="rad" else "viridis")
        ax.set(xlabel="Position (cm)",ylabel="Time (ns)",title=title,
               xlim=(0,100*(z[-1]+(z[1]-z[0])/2)),ylim=(0,time[-1]*1e9))
        fig.colorbar(mesh,ax=ax,label=label)
    fig.suptitle("Transient optical/acoustic envelopes — not an FM-averaged spectrum",fontsize=12)
    path=target("dynamics_fields_plot","dynamics_fields.png")
    _save_figure(fig,path,"Transient pump/probe mW, normalized acoustic magnitude envelope mW and phase rad; space cm time ns")
    plots.append(("Space–time envelopes",path.name,
                  "The acoustic amplitude has the solver's W normalization; it is not acoustic power or thermodynamic energy. Phase is masked wherever the acoustic amplitude is zero."))

    fig=_figure((10,6))
    axes=fig.subplots(2,1,sharex=True)
    bt=np.asarray(result["boundary_time_s"])*1e9
    for ax,prefix,title in [(axes[0],"pump","Pump boundaries"),(axes[1],"probe","Probe boundaries")]:
        ax.plot(bt,np.asarray(result[prefix+"_input_w"])*1e3,label="Input boundary")
        ax.plot(bt,np.asarray(result[prefix+"_output_w"])*1e3,label="Output boundary")
        ax.set(ylabel="Optical power (mW)",title=title)
        ax.legend()
        ax.grid(alpha=.2)
    axes[1].set_xlabel("Time (ns)")
    fig.suptitle("Boundary traces include finite propagation delay and turn-on",fontsize=12)
    path=target("dynamics_boundary_plot","dynamics_boundaries.png")
    _save_figure(fig,path,"Transient input and output pump/probe optical power mW versus time ns")
    plots.append(("Boundary powers",path.name,
                  "Input and output at the same plotted time are not a depletion estimator before steady state. Use the retarded no-SBS reference and diagnostics supplied by the solver."))

    diagnostics=result["diagnostics"]
    fig=_figure((11,4.8))
    axes=fig.subplots(1,2)
    axes[0].plot(bt,np.asarray(result["photon_balance_trace_relative"]),color="#007c91")
    axes[0].set(xlabel="Time (ns)",ylabel="Relative weighted optical balance residual",
                title="Discrete photon-flux balance")
    axes[0].ticklabel_format(axis="y",style="sci",scilimits=(0,0))
    axes[0].grid(alpha=.2)
    refinement=diagnostics.get("refinement")
    if refinement:
        labels=["Pump output","Probe output"]
        errors=[refinement["pump_output_w_relative_l2"],refinement["probe_output_w_relative_l2"]]
        axes[1].bar(labels,errors,color=["#007c91","#76549d"])
        axes[1].set(ylabel="Relative L2 difference",title=f"Refinement: {refinement['coarse_cells']} → {refinement['fine_cells']} cells")
        axes[1].ticklabel_format(axis="y",style="sci",scilimits=(0,0))
        axes[1].grid(axis="y",alpha=.2)
    else:
        axes[1].axis("off")
        axes[1].text(.5,.65,"Refinement was not requested",ha="center",fontsize=13)
        axes[1].text(.5,.4,"No convergence claim is inferred\nfrom the balance residual.",ha="center",fontsize=11)
    fig.suptitle("Numerical diagnostics — conservation is not convergence",fontsize=12)
    path=target("dynamics_refinement_plot","dynamics_refinement.png")
    _save_figure(fig,path,"Weighted optical photon-flux balance relative residual and coarse/fine boundary relative L2 refinement")
    plots.append(("Balance and refinement",path.name,
                  "A small discrete balance residual does not prove continuum accuracy. Refinement compares boundary traces at matched times; it is not experimental validation."))
    summary=_flatten(diagnostics)
    extra="<h2>Solver interpretation</h2><p>Finite-duration initial-boundary-value envelope solution. Strong-interaction multipliers are demonstration settings; they are not claimed to be the paper's operating powers.</p>"
    return "Counterpropagating optical/acoustic transient",summary,plots,extra


def save_advanced_results(result,outdir,config=None):
    """Write full settings/data, unit-labelled CSV, figures and a static HTML report."""
    kind=result.get("extension_kind",result.get("mode"))
    if kind not in ("quantum","dynamics"):
        raise ValueError("Advanced exporter supports quantum and dynamics results only.")
    # Fail serialization before creating an incomplete output report.
    data_text=json.dumps(result,indent=2,allow_nan=False)
    settings={"configuration":config if config is not None else result["config"],
              "extension_kind":kind,"mode":result.get("mode"),
              "extension_options":result.get("extension_options",result.get("options",{}))}
    settings_text=json.dumps(settings,indent=2,allow_nan=False)
    out=Path(outdir).resolve()
    out.mkdir(parents=True,exist_ok=True)
    paths={}
    def target(key,name):
        path=out/name
        paths[key]=str(path)
        return path
    target("data","results.json").write_text(data_text,encoding="utf-8")
    paths["json"]=paths["data"]
    target("config","settings_used.json").write_text(settings_text,encoding="utf-8")
    with _RENDER_LOCK:
        title,summary,plots,extra=(_quantum_exports(result,target) if kind=="quantum" else _dynamics_exports(result,target))
    esc=html.escape
    warnings=list(dict.fromkeys(str(v) for v in result.get("warnings",[])))
    if kind=="quantum":
        warnings=list(dict.fromkeys(warnings+[str(v) for v in result["quantum"].get("warnings",[])]))
    sections="".join(f'<section><h2>{esc(heading)}</h2><img src="{esc(filename)}" alt="{esc(heading)}"><p>{esc(caption)}</p></section>'
                     for heading,filename,caption in plots)
    warning_html="<ul>"+"".join(f"<li>{esc(warning)}</li>" for warning in warnings)+"</ul>"
    links=" · ".join(f'<a href="{esc(Path(value).name)}">{esc(key)}</a>' for key,value in paths.items() if key!="json" and not key.endswith("_plot"))
    body=f"""<!doctype html><html><head><meta charset="utf-8"><title>{esc(title)}</title>
    <style>body{{font:16px system-ui;max-width:1150px;margin:36px auto;padding:0 24px;color:#193448;background:#fafbfc}}h1{{line-height:1.2}}img{{max-width:100%;border:1px solid #dde3e7;background:white}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0;table-layout:fixed}}td,th{{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid #dce3e8;overflow-wrap:anywhere}}.note{{background:#fff3d4;border-left:4px solid #bd8d23;padding:16px}}section{{margin-top:30px}}li{{margin:8px 0}}pre{{white-space:pre-wrap}}</style></head>
    <body><h1>{esc(title)}</h1><p>Run mode: {esc(result.get('mode',''))}</p>
    <p class="note">Numerical results under explicit effective-model assumptions. This report is not a claim of exact experimental reproduction, a quantum advantage, or a proof of convergence. Suppressed diagnostics remain unavailable rather than being replaced with zeros.</p>
    <h2>Summary</h2>{_table(summary)}
    {sections}{extra}<h2>Warnings and qualifications</h2>{warning_html}
    <h2>Saved extension settings</h2>{_table(_flatten(settings['extension_options']))}
    <h2>Data and provenance</h2><p>{links}</p>
    <p>The complete results JSON preserves all configurations, state moments, diagnostics and warning text. The settings JSON preserves both the configuration and extension options used for this run.</p>
    </body></html>"""
    target("report","report.html").write_text(body,encoding="utf-8")
    manifest=target("manifest","manifest.json")
    manifest.write_text(json.dumps(paths,indent=2),encoding="utf-8")
    return paths
