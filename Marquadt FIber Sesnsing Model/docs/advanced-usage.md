# Advanced operation and parameter reference

Date: 2026-09-06. Status: implementation/operation guide for exploratory SCRATCH work. Integrated numerical/GUI acceptance is recorded separately in [M8 verification](m8-verification.md); this guide is not laboratory calibration.

This reference was checked against the current launcher, native project mapping, GUI controls, and extensions.schema()/defaults() APIs. All advanced numbers below are explicit model assumptions or numerical controls, **not measured specifications of Popp's devices**. Baseline source provenance remains in [source audit](source-audit.md) and [baseline parameters](parameters.md).

## Choose the right apparatus and run mode

The direct experiment has **19 blocks / 26 connections**. The separate homodyne experiment has **20 blocks / 29 connections**: it replaces the direct detector by a composite balanced receiver and adds an LO with two electrical references and one optical connection.

| Saved apparatus | Available useful runs | Receiver interpretation |
|---|---|---|
| experiment.json | local, scan, nonideal-local, nonideal-scan, dynamics | Direct photodiode / lock-in for spectra; transient exports optical/acoustic fields |
| experiment-homodyne.json | quantum, quantum-scan; dynamics also allowed | Explicit matched LO + balanced receiver; quantum statistics before the drawn optional lock-in |
| experiment-transient-baseline.json | dynamics (unscaled preset) | Direct 19-block / 26-connection graph; unit pump, probe and gain multipliers |
| experiment-depleted-demo.json | dynamics (stronger-interaction preset) | Same direct graph; pump 1, probe 50 and gain 100, explicitly not paper calibration |

The seven CLI modes map to the GUI as follows:

| CLI mode | GUI tab / button | Calculation |
|---|---|---|
| local | Toolbar: Run local spectrum | Clean weak-gain frequency sweep at one target |
| scan | Toolbar: Run position scan | Clean weak-gain scan over physical target controls |
| nonideal-local | Advanced models > Nonideal optics and detector noise > Run nonideal local | Nonideal weak-gain local spectrum |
| nonideal-scan | Same family > Run nonideal scan | Nonideal weak-gain spatial/spectral scan |
| dynamics | Advanced models > Coupled optical/acoustic transient > Run coupled transient | Finite-time counterpropagating optical/acoustic boundary-value evolution |
| quantum | Advanced models > Gaussian modes and homodyne receiver > Run Gaussian / homodyne | Selected-mode Gaussian channel from the clean local gain spectrum |
| quantum-scan | Same family > Run quantum position scan | Selected-mode readout across the clean spatial/spectral gain map |

There is **no implicit composition** between the three advanced families. The nonideal sideband/gain-loss detector sum is not passed into the Gaussian amplifier. The depleted transient does not silently include the nonideal noise engine or quantum state dynamics. Storing all three settings groups in one JSON does not enable all of them simultaneously.

## GUI workflow, saving and safeguards

1. Launch with the project launcher; do not use the unmodified upstream QuReed entry point.
2. Select the saved JSON in **Experiment**. It lists this model folder's root JSON files, not files inside result folders. Unsaved changes prompt before switching.
3. In **Apparatus**, select a black block header or use **Apparatus block**. Edit values with displayed units. Apply parameters updates the diagram; Save persists it.
4. In **Advanced models**, choose a family. Apply advanced parameters updates its in-memory settings; Save persists both apparatus and advanced edits.
5. Run a family-specific button. Pending valid edits are applied and saved, then the exact saved snapshot is assembled through native QuReed and executed in a worker. Apparatus editing, model switching, Save and Reload are disabled during the run.
6. Read **Measurements**, warnings and the exported report. Do not infer a physical measurement from assigned material properties or a plot's convenient scale.

Changing fields, topology, block positions or model settings invalidates displayed results. They are hidden/marked **STALE**, not silently retained as current. Old output files remain in their result folders.

The external-file guard notices JSON changes on disk and refuses to overwrite them from cached GUI state. **Reload from disk** deliberately loads the new file. If there are unsaved GUI edits, a confirmation offers to keep editing or discard them and reload. Use one active editing session per server; the file guard is protection against accidental stale writes, not collaborative merge support.

**Reset this model's defaults** only changes that family's advanced settings in memory. It does not reset native LO/receiver hardware fields. Quantum's standalone enabled default is false; the provided homodyne scheme enables it. After resetting quantum defaults, enable selected-mode analysis again before running.

### Which settings belong to the native LO/receiver?

| Apparatus block | Authoritative fields | Default / meaning |
|---|---|---|
| Matched local oscillator | lo_power_w, lo_phase_deg, lo_detuning_hz, lo_mode_overlap | 0.01 W, 0 degrees, 0 Hz residual detuning, unit power overlap |
| Balanced receiver | quantum_efficiency, homodyne_transimpedance_v_a, homodyne_max_voltage_v | 0.8, 1000 V/A, 10 V headroom |
| Balanced receiver | bandwidth_hz | 1.1 MHz assumed response bandwidth, inherited as a receiver configuration field |

These seven quantum hardware fields are read-only in Advanced models and must be edited on their Apparatus blocks. The native values override duplicate advanced entries, and Save removes duplicate hardware entries from the advanced group. The balanced receiver's bandwidth is a separate native configuration value, not a quantum option.

Detector responsivity is derived consistently as $\eta e/(h\nu_{\rm opt})$; it is not a second independent quantum-efficiency adjustment. The dedicated balanced transimpedance/headroom are not claims about the original direct detector's specifications.

Common-FM and probe-frequency reference wires declare an ideal coherent LO that follows the complete probe optical phase history, delay and polarization. They do not implement a real servo/phase-lock feedback system. A separate unrelated CW laser is not automatically such an LO.

## Reproducible command-line runs

Open PowerShell in this model directory. The existing parent environment is used; no installation is required.

~~~powershell
Set-Location -LiteralPath 'C:\Projects\WORKSPACE\SCRATCH\Sensing Qureed\QuReed\Marquadt FIber Sesnsing Model'
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment.json --validate
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment-homodyne.json --validate

& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment.json --mode local --out results/example-local
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment.json --mode scan --out results/example-scan
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment.json --mode nonideal-local --out results/example-nonideal-local
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment.json --mode nonideal-scan --out results/example-nonideal-scan
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment-transient-baseline.json --mode dynamics --out results/transient-baseline
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment-depleted-demo.json --mode dynamics --out results/depleted-demo
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment-homodyne.json --mode quantum --out results/example-quantum
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment-homodyne.json --mode quantum-scan --out results/example-quantum-scan
~~~

The commands use the currently saved settings; they do not silently reset the apparatus. For exact reproduction of a previous run, pass that run's **experiment-used.json** as the scheme and select the same mode. Use a new output directory to preserve earlier artifacts: repeating a CLI destination replaces generated files there. The GUI chooses timestamped directories automatically.

There are no per-parameter CLI flags. Advanced options are JSON values under extensions.nonideal, extensions.dynamics or extensions.quantum. Missing options take the API defaults below. Unknown keys are rejected. Hardware-owned fields remain in the native device values.

Validation only checks apparatus/schema validity. It does not run the selected numerical model or establish that an operating point passes gain, duration, receiver or workload gates.

## Nonideal weak-gain model

This family adds finite pump Mach-Zehnder transfer, probe IQ sidebands, acquisition-time EOM bias drift, compressed EDFA gain and its relaxation, pump/ASE leakage, shared-source linewidth/RIN and residual amplitude modulation (RAM), spatial polarization variation/scrambling and detector noise/clipping. It remains a first-order SBS/tag model.

Pump and probe bias drift are deterministic degrees per acquisition second, applied at each frequency dwell's midpoint in the actual position/frequency acquisition order. They are not independent random bias draws. Source RAM is a deterministic fractional intensity sinusoid at the laser FM frequency, with phase relative to the common FM clock; it is distinct from stochastic RIN. All four new controls default to zero.

One shared stochastic phase path is sampled at the two retarded times. The gain calculation uses its declared Wiener ensemble coherence; the exported random trace is an illustrative realization, not an independent laser for each arm. The detector PSD separates shot, shared RIN, electronics, signal-ASE and ASE-ASE terms after detector response and before IQ processing.

Noise is a high-count Gaussian approximation. Deterministic clipping precedes additive small-signal noise, so heavily clipped noise is not a full nonlinear detector model. The clean spatial response plot remains a **reference**, not a recalculated noisy point-spread function.

### All nonideal options

| Parameter | Default | Unit | Allowed input | What it controls / edit location |
|---|---:|---|---|---|
| `enabled` | true | boolean | true / false | Enable optional nonideal spectrum calculation |
| `seed` | 2026 | integer seed | 0 to 2147483647; integer | Reproducible noise seed |
| `pump_eom_enabled` | true | boolean | true / false | Finite-extinction sinusoidal Mach-Zehnder transfer |
| `pump_extinction_db` | 30 | dB | 0 to 100 | Pump EOM minimum/maximum transmission extinction (dB) |
| `pump_bias_error_deg` | 2 | deg | -80 to 80 | Pump EOM phase bias error (degrees) |
| `pump_bias_drift_deg_s` | 0 | deg/s | -5 to 5 | Linear pump EOM bias drift per acquisition second |
| `pump_rf_amplitude_error_frac` | 0.02 | dimensionless | -0.9 to 1 | Pump RF voltage amplitude fractional error |
| `pump_rf_phase_error_deg` | 1 | deg | -180 to 180 | Pump RF reference phase error (degrees) |
| `probe_eom_enabled` | true | boolean | true / false | IQ modulator Fourier sidebands with carrier leakage |
| `probe_extinction_db` | 30 | dB | 0 to 100 | Probe coherent carrier leakage extinction (dB) |
| `probe_bias_error_deg` | 1 | deg | -45 to 45 | Probe IQ branch bias error (degrees) |
| `probe_bias_drift_deg_s` | 0 | deg/s | -5 to 5 | Linear probe IQ bias drift per acquisition second |
| `probe_rf_amplitude_error_frac` | 0.02 | dimensionless | -0.9 to 1 | Probe Q/I fractional RF amplitude error |
| `probe_rf_phase_error_deg` | 2 | deg | -90 to 90 | Probe quadrature phase error (degrees) |
| `probe_rf_depth_rad` | 0.25 | rad | 0.01 to 1 | Probe modulation phase depth (rad) |
| `probe_frequency_error_mhz` | 0.1 | MHz | -20 to 20 | Microwave offset calibration error (MHz) |
| `edfa_enabled` | true | boolean | true / false | Compressed EDFA gain with finite gain response |
| `edfa_saturation_power_w` | 0.2 | W | 0.00001 to 100 | EDFA asymptotic compressed output power (W) |
| `edfa_gain_time_us` | 50 | us | 0.01 to 10000 | EDFA gain relaxation time (microseconds) |
| `edfa_ase_enabled` | true | boolean | true / false | Two-polarization EDFA ASE and receiver beat noise |
| `edfa_noise_figure_db` | 5 | dB | 3.0103 to 20 | High-gain noise figure used as 2*nsp (dB) |
| `optical_filter_bandwidth_ghz` | 1 | GHz | 0.001 to 1000 | Total receiver ASE equivalent optical noise bandwidth (GHz) |
| `circulator_isolation_db` | 80 | dB | 0 to 120 | Pump and ASE leakage to receiver (dB) |
| `laser_linewidth_hz` | 50000 | Hz | 0 to 100000000 | Shared Wiener-phase laser Lorentzian linewidth (Hz) |
| `source_ram_depth` | 0 | dimensionless | 0 to 0.1 | Deterministic source intensity modulation depth at laser FM, distinct from RIN |
| `source_ram_phase_deg` | 0 | deg | -180 to 180 | Source RAM phase relative to the laser FM clock |
| `laser_rin_db_hz` | -145 | dB/Hz | -300 to -60 | One-sided low-frequency fractional-intensity PSD (dB/Hz) |
| `rin_bandwidth_mhz` | 5 | MHz | 0.001 to 100 | OU intensity-noise corner frequency (MHz) |
| `trace_samples` | 4096 | samples | 256 to 65536; integer | Exported shared-source stochastic samples |
| `trace_dt_ns` | 2 | ns | 0.01 to 100 | Shared-source trace sampling interval (ns) |
| `polarization_enabled` | true | boolean | true / false | Spatial polarization variation and slow scrambling |
| `polarization_rms_rad` | 0.15 | rad | 0 to 3 | Stationary relative Jones-angle RMS (rad) |
| `polarization_correlation_m` | 0.05 | m | 0.0001 to 1000 | Spatial polarization correlation length (m) |
| `scramble_rate_hz` | 50 | Hz | 0 to 10000 | Sinusoidal polarization scrambler rate (Hz) |
| `scramble_depth_rad` | 0.2 | rad | 0 to 3 | Polarization scrambling angle depth (rad) |
| `detector_shot_noise_enabled` | true | boolean | true / false | Poisson shot noise in Gaussian high-count limit |
| `detector_electronic_asd_a` | 1e-12 | A/sqrt(Hz) | 0 to 0.000001 | One-sided input-current electronic noise ASD (A/sqrtHz) |
| `detector_saturation_enabled` | true | boolean | true / false | Clip detector voltage to [0, configured maximum] |

## Coupled optical/acoustic transient model

Both optical directions and the normalized acoustic envelope evolve in time, with explicit boundary turn-on and pump depletion. The optical carrier itself is not sampled. The solver uses uniform characteristic cells with $\Delta t=\Delta z/v_g$, split propagation and local RK4 evolution.

Both named presets use **150 ns**, which near **699 kHz** spans about **0.105 FM periods**, not a full-cycle average. The exact count uses the actual position control and is returned alongside propagation transits and acoustic lifetimes in diagnostics.

Choose **experiment-transient-baseline.json** for pump/probe/gain multipliers **1/1/1**, retaining the configured unscaled demonstration budget. Choose **experiment-depleted-demo.json** for **1/50/100**, deliberately exposing stronger coupling and depletion. The standalone API defaults below are the latter values; omitted settings are not an implicit unscaled baseline. Both presets retain missing paper powers and calibration as assumptions, and neither is a full-period BOCDA spectrum.

The acoustic amplitude is normalized in W but is not thermodynamic acoustic power or energy. Its zero-amplitude phase is undefined. Pump depletion and probe amplification use retarded no-SBS references and are unavailable before the relevant signal arrives or for zero input.

With convergence_check enabled, a second calculation doubles cells and halves the time step. Its boundary traces are interpolated onto the coarse times. **Both** pump and probe boundary traces must satisfy the RMS criterion

$$\operatorname{RMS}(P_{\rm coarse}-P_{\rm fine})\leq \mathrm{refinement\_atol\_w}+\mathrm{refinement\_rtol}\operatorname{RMS}(P_{\rm fine}).$$

The defaults permit 1e-9 W absolute plus 1% relative RMS error. A failure raises an actionable error and rejects the run; a pass reports refinement_status=passed and each error/tolerance in W. Disabling refinement reports not_checked, not passed. Relative L2 differences and optical photon-flux balance are also retained. Passing this finite-resolution comparison does not prove continuum accuracy, and small conservation residual alone does not demonstrate convergence. Tighten tolerances and refine when quantitative conclusions depend on small differences.

### All transient options

| Parameter | Default | Unit | Allowed input | What it controls / edit location |
|---|---:|---|---|---|
| `cells` | 40 | cells | 8 to 200; integer | Uniform propagation cells; dt=dz/vg |
| `duration_ns` | 150 | ns | 1 to 2000 | Transient duration (ns); not a full FM-cycle average |
| `output_frames` | 151 | frames | 10 to 501; integer | Saved time-position frames |
| `pump_scale` | 1 | dimensionless | 0 to 100 | Demonstration pump boundary power multiplier |
| `probe_scale` | 50 | dimensionless | 0 to 1000 | Strong-probe demonstration multiplier |
| `gain_scale` | 100 | dimensionless | 0 to 10000 | Demonstration local coupling multiplier |
| `offset_ghz` | 10.9 | GHz | 0.1 to 30 | Pump minus probe offset (GHz) |
| `fm_enabled` | true | boolean | true / false | Use actual delayed common sinusoidal optical FM |
| `boundary_rise_ns` | 2 | ns | 0.01 to 100 | Exponential intensity turn-on time (ns) |
| `initial_acoustic_scale` | 0 | dimensionless | 0 to 1 | Initial normalized acoustic seed relative to sqrt(Pp Ps) |
| `convergence_check` | true | boolean | true / false | Repeat at twice the spatial resolution and half dt |
| `refinement_rtol` | 0.01 | dimensionless | 1e-8 to 0.5 | Maximum relative RMS boundary refinement error |
| `refinement_atol_w` | 1e-9 | W | 0 to 0.01 | Absolute RMS boundary refinement tolerance, including near-zero outputs |

## Selected Gaussian modes and homodyne

This family starts from the **clean single-Stokes** weak-gain calculation and defines an effective phase-insensitive amplifier $G=1+g$, followed by explicitly lumped passive loss. It does not infer the full frequency-coupling quantum channel of FM-driven SBS.

Quadratures use $[x,p]=i$, vacuum covariance $I/2$. Input photons are $PT/(h\nu_{\rm opt})$, while bath occupation uses the separate GHz acoustic frequency. Squeezing photons are deducted from the same total input budget. Coherent input gives a displaced thermal selected output within this model; squeezed input generally does not. Unobserved phase jitter produces a generally non-Gaussian mixture whose exact moments are reported without calling it an exact Gaussian state.

The selected mode duration is explicit, not the lock-in time constant. It must fit within a frequency dwell. For $M$ orthogonal disjoint temporal bins within total duration $T$, the code requires bin duration times receiver bandwidth at least 10 and bin duration times $\pi$ times minimum acoustic linewidth at least 100. Fewer than ten actual FM periods per bin produces a stationary-approximation warning. Rectangular-bin noise bandwidth $M/(2T)$ is reported; bins are not an unlimited free information resource.

Balanced output is a **time-averaged difference current/voltage**, not lock-in peak voltage. Finite coherent-LO noise and electronic noise are retained. LO frequency detuning uses the rectangular-mode sinc overlap. Individual diode headroom is checked even when their balanced difference is almost zero.

The Gaussian homodyne FI comparison is unavailable when entered phase jitter or LO detuning invalidates the declared likelihood, or when the finite-LO variance correction exceeds 1% for the selected independent/mixed channels. That numerical gate is not a rigorous bound on FI error. Unavailable FI is not replaced by zero.

The compared readouts share total signal photons, LO photons, observation time, physical modes, receiver bandwidth and a local common gain-spectrum-shift parameter. Both mean and covariance derivatives enter **classical measurement FI**. Parameter-independent passive mixing plus joint readout preserves FI. More covariance information from retained thermal modes is not automatically quantum advantage. The scalar reference is the best of stated projection candidates, not a globally optimized receiver. See [quantum derivation and limits](quantum.md).

### All quantum options

The defaults below are the standalone API defaults. The supplied homodyne scheme sets enabled=true; native LO/receiver block values are authoritative for the marked rows.

| Parameter | Default | Unit | Allowed input | What it controls / edit location |
|---|---:|---|---|---|
| `enabled` | false | boolean | true / false | Enable selected-mode quantum/homodyne analysis; supplied homodyne scheme sets true |
| `mode_duration_s` | 0.0001 | s | >= 1e-9 | Total selected observation duration |
| `temperature_k` | 293.15 | K | >= 0 | Effective acoustic bath temperature |
| `bath_frequency_hz` | 10850000000 | Hz | >= 1 | Acoustic bath frequency (not optical) |
| `lo_power_w` | 0.01 | W | >= 1e-15 | Matched local-oscillator power; native Matched local oscillator block |
| `lo_phase_deg` | 0 | deg | finite | Local-oscillator quadrature phase; native Matched local oscillator block |
| `lo_detuning_hz` | 0 | Hz | finite | LO residual optical frequency mismatch; native Matched local oscillator block |
| `lo_mode_overlap` | 1 | dimensionless | 0 to 1 | LO polarization/spatial power overlap; native Matched local oscillator block |
| `quantum_efficiency` | 0.8 | dimensionless | 1e-9 to 1 | Balanced detector quantum efficiency; native Balanced receiver block |
| `input_phase_deg` | 0 | deg | finite | Probe displacement phase |
| `squeeze_r` | 0 | dimensionless | 0 to 3 | Input squeezing parameter |
| `squeeze_angle_deg` | 0 | deg | finite | Input squeezing axis |
| `phase_jitter_std_rad` | 0 | rad | 0 to 10 | Unobserved Gaussian phase jitter |
| `electronics_noise_a_rt_hz` | 0 | A/sqrt(Hz) | >= 0 | One-sided difference-current noise density |
| `homodyne_transimpedance_v_a` | 1000 | V/A | >= 1e-9 | Balanced-receiver transimpedance; native Balanced receiver block |
| `homodyne_max_voltage_v` | 10 | V | >= 1e-9 | Balanced-receiver per-diode and difference limit; native Balanced receiver block |
| `mode_count` | 4 | modes | 1 to 16; integer | Orthogonal temporal-bin modes |
| `mixing_angle_deg` | 30 | deg | finite | Adjacent-mode passive mixing angle |
| `alternate_squeeze_axes` | true | boolean | true / false | Alternate temporal-bin squeeze axes |
| `selected_frequency_hz` | 10870000000 | Hz | >= 1 | Displayed/Fisher operating frequency |

## Outputs and how to interpret them

Every successful runner export includes complete results.json, settings_used.json, report.html and experiment-used.json. JSON retains warnings, configuration, mode options, diagnostics and execution metadata. GUI output folders are timestamped; CLI output folders are chosen by the command.

| Model | Useful output files | Important convention |
|---|---|---|
| Clean/nonideal spectra | spectra.csv, profile.csv, spatial_response.csv and spectrum/profile/spatial PNGs | X/Y/R are peak lock-in volts, not RMS; nonideal spatial curve stays the clean reference |
| Quantum | quantum_spectra.csv, quantum_modes.csv, quantum_fisher.csv; spectrum/state/FI PNGs and optional spatial map | Average balanced voltage and variance; FI in inverse Hz squared; unavailable entries are blank |
| Dynamics | dynamics_fields.csv, dynamics_boundaries.csv; field/boundary/refinement PNGs | Optical powers and normalized acoustic envelope versus space/time, not fitted BOCDA spectra |

Additional nonideal diagnostics, sideband fractions, EDFA/source traces and noise PSD contributions are retained in the complete JSON. Consult the actual returned manifest for any supplemental plot paths.

Quantum/dynamics settings_used.json contains **configuration plus extension_options**. It is a settings report, not a native QuReed apparatus JSON. To rerun a measurement use experiment-used.json. The static HTML reports use relative file/image links and can be opened without the GUI. [Advanced result exports](advanced-results.md) documents each path and label.

## Actionable failures and warnings

| Message / condition | Meaning and safe next action |
|---|---|
| Quantum/homodyne requires the connected LO and balanced receiver | Open experiment-homodyne.json, or repair its named LO/reference routes |
| Enable selected-mode quantum/homodyne analysis | Turn on enabled in Advanced models; resetting quantum defaults turns it off |
| This apparatus has a homodyne receiver, not the original direct detector | Use the quantum buttons, or switch to experiment.json for direct spectra |
| JSON changed outside this window | Do not overwrite cached state; review/reload the disk file, preserving any unsaved work you still need |
| Connect block:port / Required route | Repair the named compatible port/wiring; pump and probe must traverse the same fiber chain in opposite directions |
| Invalid/minimum/maximum/unknown parameter | Enter a finite number in the shown units or a supported option; do not use NaN or invent a JSON key |
| Actual nonideal gain/loss exceeds 0.1 or transfer exceeds 1% of pump | Leave the weak-gain regime only with the separately defined coupled model; changing the GUI label does not remove the approximation |
| EDFA ceiling or balanced receiver/individual diode headroom exceeded | Reduce the appropriate input/LO power or gain/transimpedance; verify actual device limits independently |
| Temporal bins too short / acoustic memory / duration exceeds dwell | Increase total mode duration within dwell, reduce mode count, or revise physically justified acquisition settings |
| FI not evaluated / phase mixture / residual LO detuning | Inspect exact finite-LO moments and stated gates; unavailable FI is not a failed zero-information experiment |
| Transient detuning advances more than one radian per step / local rate too fast | Refine cells within resource limits or reduce detuning/coupling/excursion; then rerun refinement |
| Workload, sideband or cell limit | Reduce the numerical scope or choose a tractable case; do not infer arbitrary kilometer-scale simulation support |
| Photon-flux balance error | Refine the transient discretization or reduce extreme settings; conservation and convergence need separate checks |
| Transient refinement failed | Either pump or probe RMS error exceeds its absolute-plus-relative tolerance; increase cells within resource limits, inspect the comparison, or explicitly justify revised tolerances |
| Refinement was disabled | A transient is exported with refinement_status=not_checked; it is not accepted as converged |
| Depletion/amplification unavailable | A retarded reference has not arrived or its input is zero; do not report a numerical depletion percentage |
| Nonideal detector clipping | Fundamental distortion and small-signal noise approximation are flagged; this is not a fully nonlinear stochastic detector model |

During any failed run, the GUI displays the error rather than prior results as current. CLI failures return a nonzero status. Earlier generated artifacts are not erased.

## Verification status and reproducible module checks

The source and parameter tables above were checked against the implemented APIs. Numerical module tests are separate from physical and integrated-GUI acceptance.

~~~powershell
& '..\.venv\Scripts\python.exe' -m unittest tests.test_quantum -v
& '..\.venv\Scripts\python.exe' -m unittest tests.test_advanced_results -v
& '..\.venv\Scripts\python.exe' -m unittest discover -s tests -v
~~~

The final integrated suite passed 105 tests with no failures, errors or skips. Read [M8 verification](m8-verification.md) for actual live GUI workflows, saved outputs, final runtime evidence and limitations, and the [independent original-requirement audit](completion-audit.md) for acceptance mapping. Retain the separately dated [baseline verification](verification.md), [independent physics review](physics-review.md), and [source audit](source-audit.md). Numerical/software acceptance does not establish laboratory calibration, a full quantum SBS apparatus or quantum advantage.
