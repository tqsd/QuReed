# Milestones: QuReed BOCDA fiber-sensing GUI model

Status: M0–M8 complete for the documented numerical/software scope. The integrated suite passed 105 tests, and live GUI editing, persistence, receiver, scan and advanced-model workflows were verified. Historical baseline evidence and final M8 evidence are recorded separately; neither establishes laboratory calibration or quantum advantage.

Tracker updated: 2026-09-06. This document retains scope, dependencies, deliverables and acceptance gates. Completion is based on reviewed implementation, numerical checks, live GUI evidence and reproducible artifacts—not file existence alone.

Project directory: `C:\Projects\WORKSPACE\SCRATCH\Sensing Qureed\QuReed\Marquadt FIber Sesnsing Model`

## 1. Objective and completion criteria

Build a QuReed GUI experiment resembling the supplied BOCDA diagram. A shared frequency-modulated CW laser is split into pump and probe arms. The fields counterpropagate through a chain of editable fiber segments, and a photodetector plus lock-in measures the Brillouin response.

The user must be able to:

- Open the project and see all optical and electrical connections.
- Edit physical parameters and persist them by saving the project.
- Select a sensing position through a physically consistent modulation/delay mapping.
- Sweep the pump–probe frequency offset at that position.
- See the measured spectrum and fitted Brillouin resonance.
- Scan positions and reconstruct a known resonance change in the fiber.
- Run the same saved experiment from the GUI or command line.

This is exploratory work in SCRATCH. Initial numerical outputs are model checks, not validated experimental predictions.

## 2. Scope and implementation boundaries

The first model is classical: optical envelopes, powers, frequencies, propagation delays, and stimulated Brillouin gain. It uses a weak probe and an undepleted pump. It does not sample the optical carrier at approximately 193 THz.

QuReed provides the GUI, device/port abstractions, connections, and experiment execution. Custom components implement the missing BOCDA behavior. Merely connecting icons or assigning an arbitrary resonance to a selected segment does not constitute a sensing simulation.

The first usable milestone is the complete GUI layout plus a verified spectrum at one selected position. The next milestone adds a spatial scan.

Quantum-state propagation, displaced thermal states, homodyne detection, and multimode comparisons follow the validated classical baseline in M8. They are separate, explicitly qualified models; classical optical power alone is insufficient to establish any quantum-state or quantum-advantage claim.

Implementation artifacts are in this folder. See README.md for launch instructions, docs/parameters.md and docs/advanced-usage.md for settings/provenance, docs/verification.md for dated M0–M7 evidence, and docs/m8-verification.md for the final integrated checks. M8 was originally deferred, then explicitly included and implemented under the all-milestones request. All nine original extension topics are accounted for in docs/completion-audit.md.

## 3. Baseline parameters and provenance

| Quantity | Baseline | Provenance / qualification |
|---|---|---|
| Laser type | Frequency-modulated CW, near 1550 nm | User-provided paper description |
| Brillouin linewidth $\Delta\nu_B$ | 27 MHz | Primary-source confirmed intrinsic gain FWHM; see docs/source-audit.md |
| Laser modulation rate $f_m$ | 699 kHz | User-provided paper value |
| Optical frequency excursion $\Delta f$ | 47 GHz | Default total span (23.5 GHz peak), supported by measured thesis spectrum; source normalization ambiguity retained |
| Pump–probe frequency offset | 10.6–11.1 GHz | User-provided sweep range |
| Splitter power ratio | 50:50 | User-provided layout |
| Group velocity $v_g$ | Approximately $2.04\times10^8$ m/s | Provisional value consistent with reported peak spacing |
| Correlation-peak spacing | Approximately 146 m | Derived estimate, not fiber length |
| Spatial resolution | Source nominal 3 cm; model local-response FWHM about 4.62 cm | Different excursion/width conventions explicitly distinguished; no forced agreement |
| GUI fiber chain | Four 10 cm segments | Demonstration choice, not a paper parameter |
| Altered region | One of the four segments | Demonstration choice |
| Pump intensity-modulation rate | 100 kHz | Confirmed in thesis printed p. 84 / PDF p. 102 |
| Laser linewidth for DFB15TK option | User-recorded 50 kHz typical; 100 kHz maximum | Candidate hardware context only; not an active noise-model input or the AA1406 linewidth |

For a common sinusoidal-FM convention:

$$
\nu_L(t)=\nu_0+\Delta f_{\mathrm{peak}}\sin(2\pi f_m t).
$$

The standard approximate relationships are:

$$
d_{\mathrm{corr}}=\frac{v_g}{2f_m},
\qquad
\delta z\approx\frac{v_g\Delta\nu_B}{2\pi f_m\Delta f_{\mathrm{peak}}}.
$$

The resolution expression assumes $\Delta\nu_B>f_m$. With the provisional values and 47 GHz as peak deviation, these estimates give approximately 146 m and 2.7 cm. If 47 GHz is peak-to-peak, the peak deviation is 23.5 GHz and the corresponding resolution estimate is approximately 5.3 cm.

These formulas are sanity checks; the simulated spatial response and its chosen width metric must also be measured. Do not force the numerical output to equal 3 cm.

At fixed excursion and linewidth, reducing $f_m$ increases both peak spacing and resolution length. Extending the spacing to 1 km therefore does not retain 3 cm resolution automatically.

### Source confirmation and explicit assumptions

- Actual fiber length, group index, and external pump/probe optical path difference.
- Peak versus peak-to-peak convention for 47 GHz: review complete; inconsistency remains explicit, default uses measured total span.
- Pump and probe powers at the fiber inputs, including arm losses.
- Local Brillouin frequency, gain coefficient, effective mode area, and linewidth convention.
- Pump intensity-modulation depth, frequency, and phase.
- Temperature/strain-to-resonance coefficients if physical temperature/strain labels are used.
- Detector responsivity, transimpedance, selected bandwidth, and saturation limit.
- Lock-in model, reference phase, time constant, filter order, and reporting convention.
- Actual sideband generation/filtering and polarization handling in the source experiment.

Unknown values may receive documented demonstration defaults. They must not be attributed to the paper or used to claim calibrated absolute receiver voltages.

## 4. GUI topology and device responsibilities

The common laser feeds a 50:50 splitter. The probe arm passes through its frequency-shifting EOM, PC, and isolator into the right end of the fiber chain. The pump arm passes through its intensity EOM, EDFA, and circulator into the left end. The emerging probe exits through the circulator toward the photodetector and lock-in.

The pump intensity-modulation reference feeds both the pump EOM and the lock-in. The laser-FM generator and probe microwave generator are distinct controls.

| Block | Initial behavior | Editable controls |
|---|---|---|
| Laser FM generator | Shared sinusoidal optical-frequency modulation command | $f_m$, excursion, phase |
| CW laser | Common optical source with coherent modulation history | Wavelength, power; optional linewidth later |
| Splitter | Power-conserving division | Power ratio, later insertion loss |
| Probe RF/EOM | Ideal selected frequency-shifted sideband | Offset, sweep range/step, transmission |
| PC | Effective pump/probe polarization-overlap factor | Overlap between zero and one |
| Isolator | Forward transmission and backward rejection | Forward loss; finite isolation later |
| Pump reference/EOM | Sinusoidal intensity modulation | Frequency, modulation depth, bias/phase |
| EDFA | Pump gain within an explicit operating range | Gain, output limit; ASE later |
| Circulator | Directional port routing | Insertion loss; leakage later |
| Fiber segment | Local two-direction propagation and SBS interaction | Length, resonance, linewidth, gain, attenuation |
| Photodetector | Probe power to voltage | Responsivity, gain, bandwidth |
| Lock-in | Reference-synchronous demodulation and averaging | Reference phase, time constant/filter |
| Scan controller | Sets physical controls and collects results | Target positions, frequency sweep, dwell time |

The device names below are labels for candidate hardware, not proof that the corresponding system requirements are achievable.

| Function | Candidate hardware recorded from the user |
|---|---|
| Laser FM generator | Keysight 33512B |
| Paper laser | Gooch & Housego AA1406 |
| Alternative laser | Thorlabs DFB15TK |
| 50:50 coupler | Thorlabs PN1550R5A2 or PNH1550R5A1 |
| Pump intensity EOM | Thorlabs LNA6112 or iXblue/Exail MX-LN-0.1-PD-P-P-FA-FA |
| EDFA | Thorlabs EDFA100P or Amonics AEDFA-PM-37-R-NC |
| Probe EOM | Thorlabs LNQ4314 or Exail MXIQ-LN-30 |
| Probe RF generator | Rohde & Schwarz SMB100B, with suitable frequency option |
| Polarization controller | Thorlabs FPC562 |
| Isolator | Thorlabs IO-H-1550APC |
| Circulator | Thorlabs OC-L-1550 or 6015-3-APC |
| Photodetector | Thorlabs PDA10CS2 |
| Lock-in amplifier | Generic model initially; hardware selection remains open |

A narrow unmodulated linewidth does not establish a laser's ability to achieve 47 GHz excursion at 699 kHz. Driver bandwidth, tuning response, allowed modulation current, EOM bias/drive, RF options, and connector compatibility require separate verification before hardware-equivalent simulation claims.

## 5. Fiber segmentation and spatial selection

Three distinct scales are represented:

1. GUI segments: physical regions with specified material properties.
2. Numerical cells: smaller subdivisions used for calculation.
3. Sensing resolution: width of the actual spatial measurement response.

Initially display four consecutive 10 cm segments. Use numerical cells appreciably smaller than the expected resolution and refine them until relevant outputs converge.

Each segment participates in both propagation directions. Its position is computed from the lengths of preceding segments; a segment identifier is not a measurement location selector.

The controller may offer a convenient target-position field, but it must map that target to the modulation frequency and/or relative delay using an explicit coordinate convention and correlation order. In particular, an equal-delay central peak need not move when $f_m$ changes. A suitable external delay and peak order must be selected if scanning around 699 kHz is intended to move the peak.

Finite spatial response, off-peak background, and contributions from neighboring segments must be included or explicitly identified as approximations. A boundary measurement may contain more than one local resonance.

## 6. Milestone tracker

Check an item only after its acceptance evidence exists. Automated numerical checks and live GUI checks are recorded separately; neither constitutes experimental calibration.

| Milestone | Deliverable | Depends on | Status |
|---|---|---|---|
| M0 | Parameter conventions and assumptions | This plan | Complete with explicit source ambiguity |
| M1 | Reliable QuReed project and GUI persistence | M0 | Complete |
| M2 | Full optical layout and segmented fiber | M1 | Complete |
| M3 | BOCDA interaction and physical position control | M0, M2 | Complete within documented weak-gain model |
| M4 | Detector/lock-in and one local resonance sweep | M3 | Complete |
| M5 | Spatial scan and reconstructed resonance profile | M4 | Complete |
| M6 | Usable parameter controls, displays, and saving | M4–M5 | Complete, including live GUI checks |
| M7 | Validation, examples, and handoff | M1–M6 | Complete: archived 35-test baseline; all regressions included in the final 105-test suite |
| M8 | Nonideal optics, coupled dynamics, quantum channels, homodyne, and multimode comparisons | M7 | Complete: 105 integrated tests, independent review and live advanced-GUI acceptance |

### M0 — Establish conventions and reproducible defaults

Tasks:

- [x] Confirm the source definitions of modulation excursion and Brillouin linewidth.
- [x] Define fiber coordinates, propagation directions, optical-frequency offset sign, and phase conventions.
- [x] Choose and document the path imbalance and correlation order needed for the demonstration scan.
- [x] Record every value with units and provenance: paper, manufacturer, derived, or assumed.
- [x] Choose demonstration powers and a resonance change compatible with the weak-probe approximation.
- [x] Set spectrum sampling fine enough to resolve a 27 MHz linewidth.

Acceptance:

- The configuration distinguishes laser FM, probe frequency shift, and pump intensity modulation.
- Peak spacing and resolution estimates are reproducible.
- The mapping between target position and physical controls is explicit.
- Missing source values do not appear as confirmed experimental facts.

### M1 — Establish a GUI project that saves and runs

Tasks:

- [x] Add project configuration, initial scheme, and a documented environment entry point.
- [x] Reuse the known QuReed environment without launching an implicit internet installation on project open.
- [x] Verify custom-device discovery and constructors supporting saved names/UUIDs.
- [x] Persist custom device parameters with the scheme or a deliberately coordinated settings file.
- [x] Support both GUI execution and a command-line runner loading the same configuration.
- [x] Record known upstream issues and confine any necessary compatibility fixes to the smallest scope.

Acceptance:

- Project opens without import errors.
- Save, restart, and reload preserve positions, connections, and physical parameter values.
- Repeated execution does not retain stale events, devices, or numerical results.
- Files belonging to the earlier Fiber-Sensing toy and existing user changes are preserved.

Known issues to account for:

- Built-in IdealBeamSplitter failed with the installed PhotonWeave temporal-profile API.
- The old Fock example has a ModeManager import/initialization defect.
- QuReed's GUI serializer originally saved values only for variable components.
- Its execution wrapper originally targeted experiment.json regardless of selected scheme.
- Project-file discovery treats visible Python files as device modules.
- Cached GUI data can overwrite externally edited files when saved or run.

### M2 — Build the visible apparatus and fiber chain

Tasks:

- [x] Place all source, pump, probe, fiber, and receiver blocks in an understandable layout.
- [x] Use clearly identified optical and electrical ports.
- [x] Route counterpropagating fields through four consecutive fiber segments.
- [x] Add names/units and useful parameter descriptions.
- [x] Implement splitter ratios, arm transmission, EDFA gain, and circulator routing.
- [x] Validate complete connections before running, with actionable messages for missing ports.

Acceptance:

- No required source is hidden off the visible board.
- Both optical directions are explicit and correctly connected.
- The splitter conserves power before losses.
- Pump and probe boundary powers match the configured optical budget.
- The receiver receives the emerging probe through the intended circulator port.

### M3 — Implement the BOCDA sensing calculation

Tasks:

- [x] Carry the common modulation history and account for local pump/probe propagation delays.
- [x] Evaluate the local frequency difference and Brillouin response across the numerical fiber grid.
- [x] Integrate the local interaction to obtain the emerging probe response in the undepleted-pump regime.
- [x] Include the externally imposed delay and the periodic correlation structure.
- [x] Implement target-position mapping without directly reading only the target segment.
- [x] Define the resolution metric and assess spatial/background response.
- [x] Choose analytic averaging, adaptive quadrature, or sufficiently resolved envelope sampling after checking convergence.

Acceptance:

- A uniform fiber produces the configured resonance.
- Resonance enhancement follows the local pump–probe detuning.
- Correlation-peak locations agree with the defined delays and expected spacing.
- Moving the physical controls moves the intended peak through the accessible region.
- A localized perturbation has a finite-width measured response.
- Grid and modulation-averaging refinement stabilize the results.

Model checks:

- A quasi-static Lorentzian treatment must be identified as an approximation and its validity assessed for the modulation parameters.
- If that treatment fails, an acoustic-envelope response or another justified model is required before claiming quantitative reproduction.
- Do not use a guessed Gaussian spatial window as an unlabelled substitute for the modulation physics.
- Multiple correlation peaks must be accounted for if the fiber spans more than one peak spacing.

### M4 — Build the receiver and demonstrate one local spectrum

Tasks:

- [x] Apply the pump's low-frequency intensity modulation consistently.
- [x] Compute photodetector output using stated responsivity and transimpedance.
- [x] Demodulate using the same reference frequency and a defined phase.
- [x] Define peak/RMS scaling, filtering, and dwell/settling behavior.
- [x] Sweep the probe offset at one selected position.
- [x] Plot the lock-in response and fit or estimate its resonance frequency.

Acceptance:

- The complete GUI experiment runs and returns a local spectrum.
- The inferred resonance agrees with the assigned local value within declared sampling/model tolerances away from boundaries.
- Removing pump intensity modulation removes the ideal reference-synchronous SBS signal.
- Setting SBS coupling to zero removes the SBS contribution.
- Changing reference phase gives the expected quadrature behavior.
- Absolute voltage is claimed only if gain and receiver scaling are specified; otherwise results are explicitly normalized.

This is the first user-testable full-apparatus milestone.

### M5 — Scan position and recover the fiber profile

Tasks:

- [x] Sweep target positions with the validated physical-control mapping.
- [x] Acquire a spectrum at each position.
- [x] Extract the resonance and a fit-quality indicator.
- [x] Display the frequency-versus-position map and reconstructed profile.
- [x] Overlay the configured fiber resonance profile and segment boundaries.
- [x] Evaluate positions inside a segment and near a boundary.

Acceptance:

- The deliberately altered segment is recovered at the expected location.
- Boundary mixing is visible rather than silently replaced with the configured values.
- Poor or multi-peaked fits are flagged.
- Spatial resolution is assessed with a suitable response/edge test, not just the grid spacing.
- Reducing $f_m$ exhibits the expected range/resolution tradeoff with other parameters fixed.

### M6 — Complete the GUI controls and results workflow

Tasks:

- [x] Provide editable fiber length, resonance, linewidth, and gain for each segment.
- [x] Expose scan limits, target position, modulation settings, and receiver settings.
- [x] Show the selected position and spatial-response width, where supported.
- [x] Provide spectrum/profile results in a dedicated view if needed.
- [x] Add running/completed/error status and clear validation messages.
- [x] Keep loaded settings, displayed values, saved configuration, and executed configuration consistent.
- [x] Ensure changing topology or parameters does not leave stale result plots presented as current.

Acceptance:

- The user can change a parameter, save, run, and see its effect.
- Reopening the project reproduces the intended apparatus and settings.
- Result displays state units and any normalization.
- A clear distinction is maintained between editable input parameters and measured/reconstructed outputs.

### M7 — Verify and hand off

Tasks:

- [x] Run the uniform-fiber, altered-segment, zero-gain, and zero-modulation cases.
- [x] Check spatial/frequency sampling convergence and weak-probe consistency.
- [x] Verify power accounting, receiver scaling, and repeated-run isolation.
- [x] Compare GUI and command-line outputs for the same saved setup.
- [x] Record the tested Python, QuReed, and dependency versions.
- [x] Document launch, open, save, run, parameter-editing, and result-reading steps.
- [x] Save a reproducible example configuration and representative outputs.
- [x] Document known limits and any upstream fixes.

Acceptance:

- A user can reproduce the demonstration from the instructions.
- Core calculations have meaningful checks, not merely successful imports.
- Numerical errors are not silently converted into a success message.
- Known limitations are stated without claiming a full recreation of the paper.

### M8 — Advanced models and their GUI integration

Status: complete within the declared model families and validity limits. Each checked task is supported by the granular original/expanded requirement map in docs/completion-audit.md and final tests/live evidence in docs/m8-verification.md. All nine original topics are retained, including actual time-varying EOM bias drift and deterministic FM-linked RAM, not just static bias and random intensity noise.

The advanced models have different validity boundaries:

- Nonideal spectrum model: corrections and noise around the weak-SBS sensing calculation.
- Coupled dynamics model: time-dependent classical pump, probe, and acoustic envelopes with pump depletion.
- Quantum model: explicitly defined effective bosonic modes and Gaussian channels under stated assumptions, with a specified receiver.

Do not imply that these are already a single, fully coupled stochastic quantum simulation of the laboratory apparatus. Their common limits must agree where their assumptions overlap; otherwise their outputs and approximations remain separate.

| Submilestone | Original extension topics | Depends on | Required deliverable |
|---|---|---|---|
| M8.1 | EOM imperfections; EDFA; shared laser noise; polarization; detector noise | M7 | Reproducible nonideal local spectra and spatial scans |
| M8.2 | Pump depletion and coupled optical/acoustic dynamics | M7 | Separate transient solver and time/position diagnostics |
| M8.3 | Gaussian channels and displaced thermal states | M7 | Normalized mode-state and covariance calculation |
| M8.4 | Homodyne with explicit LO and phase reference | M8.3 | Visible receiver variant and calibrated measurement model |
| M8.5 | Multimode information/performance comparison | M8.3–M8.4 | Resource-matched measurement comparison with baselines |
| M8.6 | Integration, independent audit, and handoff of all extensions | M8.1–M8.5 | Saved GUI examples, full tests, reviewed limitations, and evidence |

#### M8.1 — Nonideal optical components and receiver

Tasks:

- [x] Implement a stated pump intensity-EOM transfer, finite extinction, bias drift, and RF amplitude/phase errors.
- [x] Represent desired probe sideband, residual carrier, and unwanted sidebands with explicit frequency signs, powers, and truncation limits.
- [x] Distinguish Stokes amplification from anti-Stokes attenuation; unwanted components are not all positive gain channels.
- [x] Add EDFA saturation and gain recovery plus ASE using explicit optical bandwidth and one-/two-polarization conventions.
- [x] Label any lumped EDFA recovery/saturation approximation as phenomenological rather than a full erbium population model.
- [x] Add laser phase noise and residual intensity modulation using the same source history at the two retarded times.
- [x] Add position-dependent polarization overlap and time-dependent scrambling with an explicit distribution/averaging interval.
- [x] Add detector shot noise, electronic noise, filtering, and saturation with consistent units and noise-bandwidth definitions.
- [x] Persist a random seed and export diagnostic traces, component power budgets, noise contributions, and clipping warnings.
- [x] Make enabled effects and their assumed parameters editable and visible in both GUI and exported results.

Acceptance:

- Turning imperfections off recovers the baseline within declared numerical tolerances.
- Equal delayed source paths cancel shared phase noise; separated paths retain the physically appropriate residual correlation. A noise trace is not a substitute for a quantitative coherence check.
- Sideband powers obey their stated normalization, and their gain/loss signs match their frequency ordering.
- EDFA ASE has a reproducible units-and-bandwidth calculation, and its transient response changes with the configured recovery time.
- Polarization overlap stays in its physical range and affects the actual SBS coupling rather than only a plot label.
- Noise variance agrees with the specified spectrum and equivalent noise bandwidth within a stated statistical tolerance; independent acquisitions versus correlated samples are identified.
- Saturated acquisitions are flagged and cannot silently support an unbiased-fit or sensitivity claim.
- Identical saved settings and seed reproduce the same run; changing the seed changes samples but not the expected noise statistics.

Evidence: model assumptions, component limiting-case tests, representative traces, and independent review. Device-specific calibration remains separate from these modeled imperfections.

#### M8.2 — Coupled pump, probe, and acoustic dynamics

Tasks:

- [x] Evolve both counterpropagating optical envelopes and the acoustic envelope with explicit field normalization and coupling conventions.
- [x] Impose pump and probe inputs at opposite fiber ends and state the initial acoustic field.
- [x] Include optical attenuation, acoustic damping/detuning, and the configured drive histories within the solver's documented scope.
- [x] Let optical energy exchange produce pump depletion; do not apply an arbitrary depletion factor after a fixed-pump calculation.
- [x] Provide a tractable transient demonstration and a separately labelled stronger-interaction preset using assumed parameters.
- [x] Export pump/probe/acoustic time–position data, boundary traces, conservation diagnostics, and refinement comparisons.
- [x] Report the simulated duration relative to propagation time, acoustic relaxation, and FM period; a short transient is not a full-cycle average.
- [x] Reject unreasonable grid/time requests before allocating large arrays and surface numerical failures to the GUI.

Acceptance:

- Zero coupling, zero probe, and attenuation-only transport give the corresponding limiting behavior.
- Boundary conditions are verified independently of an attractive-looking field plot.
- Weak-coupling behavior agrees with an appropriate undepleted reference under matching assumptions.
- A continuous-wave depleted case agrees with an independent boundary-value calculation or another independent reference.
- The pump loses photons while the Stokes field gains photons in their respective propagation directions; acoustic damping/energy accounting and any equal-optical-frequency approximation are explicit.
- Space/time refinement stabilizes boundary outputs and relevant field observables to declared tolerances. For a proposed default convergence target of 1%, also specify absolute tolerances for observables near zero.
- The displayed diagnostics distinguish a discrete conservation identity from agreement with the intended differential equations.

Evidence: solver equations/assumptions, independent reference comparisons, automated limiting cases, convergence table, and an exported transient example.

#### M8.3 — Effective Gaussian states and channels

Tasks:

- [x] Define the finite set of optical modes, their normalized mode functions/durations, quadrature order, commutators, and vacuum covariance convention.
- [x] Convert power to photon number using the optical carrier frequency and the selected mode duration, not the acoustic frequency or an unspecified lock-in time constant.
- [x] State how a validated classical gain informs an effective quantum amplifier, including the gain convention and weak-gain validity boundary.
- [x] Include the amplifier's required auxiliary noise mode and thermal occupation at the acoustic frequency.
- [x] Propagate coherent and optional squeezed input means/covariances through amplification and loss.
- [x] Check channel complete positivity and output uncertainty/positivity with documented tolerances.
- [x] Identify when the output is displaced thermal, when it is squeezed thermal, and when only its moments are being approximated.
- [x] Explicitly flag non-Gaussian phase-averaged mixtures instead of labelling all noisy outputs Gaussian.

Acceptance:

- Vacuum, unity gain, zero thermal occupation, zero loss, and coherent-input limits reproduce independent analytic expectations.
- A phase-insensitive amplifier above unity gain cannot have its required added noise removed.
- Loss introduces the vacuum contribution required by the chosen quadrature normalization.
- Output covariance physicality and channel tests pass for representative and boundary parameter cases; invalid inputs give actionable errors.
- Any classical-to-quantum mapping is documented as a conditional effective model, not proof that every optical mode in the experiment has that state.

Evidence: state/channel definitions, independent analytic checks, uncertainty and channel diagnostics, and a saved selected-mode example.

#### M8.4 — Explicit local oscillator and balanced homodyne receiver

Tasks:

- [x] Supply a distinct saved apparatus variant retaining the original direct-detection experiment.
- [x] Show an LO source, signal/LO mixing, balanced photodetection, and the phase/frequency reference relationships as explicit GUI components or a clearly documented composite receiver.
- [x] Expose LO power, relative phase, residual detuning, mode overlap, detector efficiency, electronic noise, transimpedance, bandwidth, and saturation limits.
- [x] Define ideal phase locking as an assumption when no actual feedback-loop dynamics are simulated.
- [x] Calculate quadrature statistics and calibrated difference-current/voltage statistics, with finite-LO corrections where used.
- [x] Check both individual photodiodes and their difference output for saturation.
- [x] Keep homodyne readout distinct from the original photodiode-plus-lock-in result; any downstream lock-in processing must be explicit.
- [x] Save hardware-owned parameters once and prevent hidden advanced settings from contradicting the displayed LO/receiver blocks.

Acceptance:

- Changing relative phase rotates the measured quadrature as expected; a power-only detector formula does not count as homodyne.
- Vacuum/coherent-state shot noise and the strong-LO limit agree with independent calculations.
- Finite LO strength, imperfect mode matching, detuning, efficiency, electronic noise, and saturation affect the stated observables or trigger validity warnings.
- Missing LO/reference connections are detected before execution.
- The GUI can save, reload, execute, and visibly distinguish the homodyne apparatus from direct detection.

Evidence: saved receiver variant, state-to-measurement equations, hardware/normalization checks, and live GUI parameter-edit/run captures.

#### M8.5 — Resource-fair multimode comparison

Tasks:

- [x] Declare the physical mode set, normalization, orthogonality, duration, and allowed bandwidth/time resolution.
- [x] State which modes are independent and which correlations are modeled; a collection of independent channels is not a full shared-bath SBS calculation.
- [x] Define the estimated parameter, operating point, and units before computing information.
- [x] Fix total observation time, signal photons, LO photons, and squeezing photons where applicable across the comparison.
- [x] Compare resolved multimode measurements with a clearly specified collective single-mode readout and meaningful scalar-reference choices.
- [x] Include a same-budget coherent reference whenever a nonclassical input is used.
- [x] Report mean-sensitive and covariance-sensitive contributions to measurement Fisher information separately.
- [x] Test information preservation under invertible parameter-independent mixing with joint readout, and the consequences of discarding outputs.
- [x] Separate improved collection/readout from a quantum resource advantage; do not rename measurement Fisher information quantum Fisher information.
- [x] Disable or clearly qualify a Gaussian-distribution information formula when the actual modeled outcome is a non-Gaussian mixture.

Acceptance:

- Identical-mode and single-mode limits are reproduced.
- Mode count cannot create free extra observation time, photons, or unconstrained thermal samples.
- The mean-optimal scalar reference is included where applicable; a deliberately poor equal-weight reference does not establish a general multimode advantage.
- Joint invertible mixing preserves information numerically; a reduced measurement cannot gain information merely by discarding data from the same experiment.
- Finite-difference parameter derivatives and reported information stabilize under step refinement, with singular/no-signal cases handled explicitly.
- A finding of no advantage is an acceptable scientific result. Completion requires a fair calculation, not a predetermined positive advantage.

Evidence: resource ledger, explicit measurement definitions, comparison tables/plots, derivative checks, and an independent claim-strength review.

#### M8.6 — Integrate, review, and complete the full model

Tasks:

- [x] Provide clearly named run actions for baseline local/scan, nonideal local/scan, coupled transient, and quantum/homodyne analyses.
- [x] Persist advanced model options with the experiment and validate their names, types, units, ranges, and resource limits.
- [x] Route GUI and command-line execution through the same saved snapshot and numerical implementation.
- [x] Mark results stale after changes to apparatus, advanced options, or externally edited files.
- [x] Export JSON settings/results, appropriate tabular data, readable plots, diagnostics, units, random seeds, and model limitations for every run type.
- [x] Demonstrate advanced GUI option editing, saving, reloading, execution, and result viewing with live interaction evidence.
- [x] Rerun baseline regression tests after the advanced integrations and add independent tests for all M8 model branches.
- [x] Have the independent reviewer inspect the actual completed implementation and resolve or explicitly retain every review finding.
- [x] Update README, parameter provenance, review records, verification evidence, and this tracker without overwriting user-owned project goals/results or unrelated work.
- [x] Audit every original M0–M8 requirement against an artifact and an acceptance result before declaring the overall objective complete.

Acceptance:

- No extension is considered delivered solely because its isolated Python module imports or a GUI button exists.
- Saved GUI and command-line runs agree for the same model/options/seed within the stated tolerances.
- Failed validation, clipping, non-convergence, unsupported assumptions, and missing connections remain visible in the result/status record.
- The final test report covers the integrated working tree, rather than reusing the historical 35-test baseline report as M8 evidence.
- The direct-detection baseline remains usable, and advanced examples can be reproduced using the documented environment.
- All original extension topics are accounted for. Unresolved acceptance failures keep M8 open; numerical checks do not constitute experimental calibration or a proof of quantum advantage.

## 7. Delivered artifacts and artifact requirements

Create these only as their milestones require:

- `config.toml`: QuReed project identity and coordinated settings.
- `experiment.json`: apparatus layout, connections, and persisted device parameters.
- Custom device modules following QuReed's project-discovery conventions.
- A shared numerical engine for GUI and command-line execution.
- A runner kept out of GUI custom-device discovery where needed.
- `README.md`: operation, assumptions, and troubleshooting.
- Results folder: generated plots, spectra/profile data, and the settings used for each run.
- Focused verification scripts or tests and a dependency/version record.

Additional M8 artifacts, created only when their corresponding implementation is ready:

- A separate saved homodyne apparatus, preserving the original experiment.
- Advanced option schemas and shared GUI/command-line run dispatch.
- Nonideal-component and noise diagnostics with reproducible seeds.
- A coupled optical/acoustic dynamics module and transient data/plots.
- Effective quantum-channel and homodyne/multimode analyses with resource ledgers.
- An independent M8 review and integrated verification report with live GUI evidence.

Every exported run should identify the saved scheme fingerprint, executed model, resolved settings, numerical resolution/tolerances, random seed if relevant, runtime versions, diagnostics, warnings, and output units. Input truth and reconstructed/estimated quantities must be separate fields.

Avoid duplicating a large virtual environment unnecessarily. If an environment junction or other shared reference is used, document its target and lifecycle.

## 8. Source notes

The supplied figure and component/parameter list are the starting experimental references. Exact attribution to the Popp paper or thesis must be checked against those documents before labelling a value as verified.

- BOCDA parameter definitions and standard resolution/spacing estimates: [Brillouin Optical Correlation-Domain Technologies](https://www.mdpi.com/2076-3417/9/1/187).
- Framework source: [tqsd/QuReed](https://github.com/tqsd/QuReed).
- Candidate laser specifications: [Thorlabs DFB15TK](https://www.thorlabs.de/newgrouppage9.cfm?objectgroup_id=15166&pn=DFB15TK).
- Other candidate manufacturer links remain those supplied in the conversation; their settings and compatibility are not automatically validated.

## 9. Next action

Launch the native GUI with launch_gui.ps1 and choose a saved experiment and run mode as described in README.md. The default experiment has restored zero drift/RAM and the homodyne preset has LO phase zero; nonzero test inputs remain in their executed snapshots. Future parameter studies should retain the documented validity/convergence guards.

Implemented dependency order: component imperfections, coupled dynamics and quantum channels proceeded independently; homodyne and fair mode comparisons followed the state definitions; shared GUI/export integration and independent final acceptance followed assembly. No pending implementation step remains within the agreed scope.

## 10. Baseline acceptance evidence recorded on 2026-09-05

- [Verification report](docs/verification.md): automated checks, literal live UI actions, numerical diagnostics and limitations.
- [Archived baseline test report](results/verification/test-report-m0-m7.json): 35 tests, zero failures/errors/skips.
- [Apparatus screenshot](results/verification/apparatus.png): all 19 native QuReed blocks and the four-segment bidirectional fiber.
- [Live measurement screenshot](results/verification/measurements.png) and [spatial scan screenshot](results/verification/scan-profile.png).
- [Example local run](results/local/report.html) and [36-position spatial scan](results/scan/report.html).
- [Parameter/default/provenance ledger](docs/parameters.md), [source audit](docs/source-audit.md), and [independent physics review](docs/physics-review.md).

GUI verification included changing Fiber 3 to 10.92 GHz, saving it, observing a fit near 10.91873 GHz, confirming stale-result hiding, restoring 10.90 GHz, reloading, and executing both local and spatial scans. The final saved experiment was checked against the original demonstration defaults.

Completion is numerical and software acceptance within stated assumptions, not experimental validation. The reported nominal 3 cm, calculated response FWHM, and modulation-excursion conventions remain distinct.

M8 final evidence is recorded below and separately from the historical baseline. Remaining scientific limitations are explicit model boundaries, not omitted milestone implementations.

## 11. Final integrated M8 acceptance — 2026-09-06

- [Integrated verification](docs/m8-verification.md): 105 tests, zero failures/errors/skips, literal live workflows and exact executed snapshots.
- [Final test report](results/verification/test-report.json) and [test log](results/verification/tests.log): all baseline and advanced branches.
- [Original/expanded requirement audit](docs/completion-audit.md) and [independent model review](docs/m8-review.md).
- [Native homodyne apparatus](results/verification/m8-homodyne-apparatus.png), [phase rotation result](results/verification/m8-homodyne-phase90.png), and [read-only native-owned settings](results/verification/m8-homodyne-controls.png).
- [Accepted live transient](results/verification/m8-coupled-transient.png) and [fully loaded optical/acoustic fields](results/verification/m8-coupled-field-map.png).
- [Live nonzero RAM/drift report](results/gui_nonideal-local_20260906_002344_838411/report.html) and [actual GUI RAM diagnostics](results/verification/m8-live-ram-diagnostic.png).
- [Full quantum scan](results/quantum-scan/report.html), [unscaled transient](results/transient-baseline/report.html), and [stronger-interaction transient](results/depleted-demo/report.html).
- [Complete advanced operation/71-option reference](docs/advanced-usage.md).

The component-noise, classical coupled-dynamics and effective finite-mode quantum families remain separate with explicit assumptions. The accepted multimode comparison fixes resources and includes meaningful scalar/coherent references; it does not assert a predetermined advantage. No laboratory equivalence, full quantum SBS apparatus or experimental quantum advantage has been established. User-owned project goals/results and unrelated work are preserved.
