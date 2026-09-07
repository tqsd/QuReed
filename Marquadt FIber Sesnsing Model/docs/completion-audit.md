# Independent completion audit: original M0-M8 requirements

**Final decision, 2026-09-05 22:32:21 UTC / 2026-09-06 local: ACCEPTED within the documented numerical/software scope.** The final resolution section below closes the dated findings; historical cutoffs are preserved.

Evidence cutoff: **2026-09-05 21:58:39 UTC**. This is a requirement-to-artifact audit, not a new derivation or a blanket completion declaration. The implementation was changing during the audit; later work must have its own evidence rather than inheriting this cutoff's status.

## Authority, method, and status meanings

The reviewer read the original supplied plan completely at `C:\Users\ge85yix\.codex\attachments\06959ee9-ceb1-4939-9972-26207839c583\pasted-text-1.txt` and the current [milestones.md](../milestones.md) completely. The original M0-M7 tasks and acceptance topics are mapped below; the nine original M8 topics are then mapped to the expanded M8.1-M8.6 gates. Grouped rows combine closely related task and acceptance statements, not omit them.

- **VERIFIED** means identified implementation plus inspected test/assertion, saved output, independent calculation, or directly inspected screenshot supports the stated bounded requirement. It does not mean arbitrary parameters or laboratory performance were proved.
- **PARTIAL / PENDING** identifies a concrete missing implementation, acceptance detail, or evidence item at the cutoff.
- **UNPROVEN / QUALIFIED** distinguishes a scientific/hardware claim not established by software tests; where the plan explicitly permits assumptions, this is not automatically an implementation failure.

The reviewer did not operate the live browser during this pass. Earlier independent physics and integration checks, including the two now-resolved freshness defects, are recorded in [m8-review.md](m8-review.md). No implementation, dashboard, milestone checkbox, or source document was changed by this audit.

## Evidence inventory actually inspected

| Evidence | What it establishes and what it does not |
|---|---|
| [Current test report](../results/verification/test-report.json) and `results/verification/tests.log` | PASS, 95 tests, zero failures/errors/skips, 131.693 s; report timestamp 2026-09-05T21:46:50.076450Z. Inspected test definitions cover 35 baseline tests, 18 nonideal/dynamics tests, 22 quantum tests, 11 exporter tests, and 9 extension contracts. This does not cover later new effects automatically. |
| [Archived baseline report](../results/verification/test-report-m0-m7.json) | PASS, 35 tests at 20:51:47.993648Z. This is the appropriate historical M0-M7 report, distinct from the changing current report. |
| [Baseline verification narrative](verification.md) | Records literal parameter-edit/save/reload/local/scan interactions and the earlier failure routes. Its final-M8 wording is stale at this cutoff and needs reconciliation. |
| [Source audit](source-audit.md), [parameter ledger](parameters.md), [physics](physics.md), [physics review](physics-review.md) | Primary-PDF provenance, explicit source ambiguity, coordinate/normalization conventions, model equations and independent acoustic checks. |
| [M8 review](m8-review.md), [nonideal](nonideal.md), [dynamics](dynamics.md), [quantum](quantum.md) | Inspected scoped model equations, auxiliary-noise/physicality/resource conventions, independent numerical references and resolved findings; not a full quantum SBS or laboratory calibration proof. |
| [README](../README.md), [advanced operation](advanced-usage.md), [advanced exports](advanced-results.md), `launch_gui.ps1`, `config.toml` | Concrete launch/save/run instructions, all family options and units, existing parent virtual environment, no installation on open, defined export semantics. |
| [Local output](../results/local/report.html), [spatial scan](../results/scan/report.html) | Native runs with exact snapshots; local 1 x 251 and scan 36 x 251, each with zero queued events. |
| [Nonideal local](../results/gui_nonideal-local_20260905_234659_664448/report.html), [nonideal scan](../results/gui_nonideal-scan_20260905_235026_534730/report.html) | Saved native GUI acquisitions, seed 2027, 1 x 251 and 36 x 251, zero queued events. Full scan execution 134.127 s. These are not the earlier small export-smoke fixture. |
| [Quantum scan](../results/quantum-scan/report.html) | Actual completed 36 x 251 native quantum scan, zero queued events, 50.723 s; state/readout/resource data and exact input snapshot exist. Not a live homodyne-GUI interaction record by itself. |
| [Nominal transient](../results/transient-baseline/report.html), [stronger transient](../results/depleted-demo/report.html) | Completed 151-frame native runs with 40-to-80-cell refinement and zero queued events. Nominal boundary relative changes are about 0.0602%/0.0601%; stronger changes about 0.0611%/0.0720%. |
| `experiment-transient-baseline.json`, `experiment-depleted-demo.json` | Distinct root-level presets: both 150 ns; nominal probe/gain scales 1/1 versus stronger 50/100, with explicit assumed-provenance labels. |
| Directly viewed `results/verification/apparatus.png` | Full original board, all source/arm/receiver blocks, four bidirectional segments and optical/electrical routes visible. Icons are functional model blocks, not manufacturer emulators. |
| Directly viewed `m8-advanced-controls.png`, `m8-external-stale.png`, `m8-nonideal-measurement.png`, `m8-nonideal-scan.png` in `results/verification/` | Advanced seed 2027 editing/save view; visible external-file stale warning without discarded edits; nonideal local spectrum and fit flag; multi-position scan table and actual physical controls. These screenshots do not establish future homodyne/dynamics GUI actions. |

All numerical run claims above were read from their current result JSON/execution records, not inferred from folder names alone. Historical `backend-smoke` and `nonideal-export-smoke` outputs are not used as substitutes for native full-size run evidence.

## Original M0-M7 task and acceptance map

### M0: source conventions and defaults

| Original requirement topic | Implementation/evidence | Status |
|---|---|---|
| Source excursion and Brillouin linewidth definitions | `source-audit.md` reads original paper/thesis and rendered measured spectrum; intrinsic 27 MHz FWHM verified; 47 GHz total-span default and peak alternative explicit. `test_default_dimensions_and_source_convention`; `test_resolution_convention_and_range_tradeoff`. | VERIFIED source examination; source factor-of-two ambiguity remains QUALIFIED, not magically resolved. |
| Fiber coordinates, opposite propagation, offset/phase signs | `physics.py` delay/control functions and `physics.md`; `project.py` validates reverse probe chain. `test_target_mapping_and_periodic_peaks`, `test_crossed_counterpropagation_rejected`, independent acoustic review. | VERIFIED within stated convention. |
| Path imbalance/order and target-to-physical-control map | Explicit demo delay 1/699000 s and order 1; frequency/delay/fixed modes; equal-delay order-zero restriction. Actual controls displayed in screenshots and result tables. | VERIFIED; demo geometry is not thesis order 84/long path. |
| Every input has units and source/derived/assumed provenance; separate three RF functions | `devices.py` schemas, `parameters.md`, original candidate table, source audit, saved scheme provenance. Separate FM generator, probe microwave sweep and 100 kHz pump reference. | VERIFIED ledger and separation; exact manufacturer equivalence remains UNPROVEN. |
| Weak-probe demonstration powers and shifted region | Saved four 10 cm segments, third at 10.90 GHz versus 10.85 GHz; `power_budget`, peak-gain/depletion guards. Uniform/altered and optical-scaling tests. | VERIFIED model choice, not measured paper power. |
| Spectrum sampling, reproducible spacing and width estimates | 2 MHz frequency step versus 27 MHz linewidth; independent frequency/cell refinement; physical FWHM about 4.62 cm and spacing about 145.923 m, nominal formula separately reported. | VERIFIED; no forced 3 cm match. |

### M1: reliable project, persistence, and execution

| Original requirement topic | Implementation/evidence | Status |
|---|---|---|
| Project identity, scheme and documented environment entry point | `config.toml` has `packages=[]`; launcher explicitly uses parent `.venv`; `gui.main` opens chosen scheme. No additional `.venv` in this project was found. | VERIFIED environment reuse/no implicit installation. |
| Custom discovery, constructors, saved names/UUIDs | Native wrappers and `devices.py`; `integration.discover_device`; `test_discovery_keeps_wrapped_devices_and_skips_utilities`, `test_custom_parameters_survive_native_assembly`. | VERIFIED; support scripts are not instantiated as devices. |
| Save/restart/reload positions, topology, physical values | Project-scoped serialization, atomic save and SnapshotSession; native GUI contract tests plus baseline live edit/save/reload narrative. | VERIFIED tested round trips. |
| Same saved GUI/CLI configuration; no accumulated events/devices/results | Isolated `JsonExecution` assembly and DES event in `runner.py`; repeated-run/native-registry tests, identical GUI/CLI spectra tests, zero-event outputs. | VERIFIED bounded repeated runs; not multi-client server support. |
| Known upstream problems and smallest-scope fixes | README/verification document serializer, selected-scheme, discovery, singleton-page, swallowed-error fixes; prior beam-splitter/Fock defects are avoided by project components, not falsely called fixed. | VERIFIED scope documentation and isolated implementation. |
| Preserve earlier toy/user changes | Launcher/modules act inside this model project; no toy or installed-source mutation observed in this audit. | QUALIFIED: isolation supports preservation; no pre/post bytewise snapshot of every earlier user file was available for independent retrospective proof. |

### M2: complete visible apparatus and power routes

| Original requirement topic | Implementation/evidence | Status |
|---|---|---|
| All source, pump, probe, fiber and receiver blocks visible and described | Full `apparatus.png`, named schemas and descriptions, 19-device/26-connection direct scheme. | VERIFIED; scrolling is documented, no hidden required source. |
| Distinct optical/electrical ports; explicit two-direction four-segment routing | `devices.py` signal types/port directions; full-route validation; native counterpropagating-port and crossed-chain tests. | VERIFIED. |
| Splitter, arm losses, EDFA gain, circulator and input/output power budgets | `physics.power_budget`; `test_power_budget_and_segment_alignment`, `test_optical_and_receiver_scaling`; numerical defaults in parameters/verification. | VERIFIED conservation before losses and configured boundaries. |
| Complete connections, emerging probe through circulator, actionable missing ports | `project.validate_scheme` requires source/receiver routes and opposite-direction chain; incomplete-save/invalid-run and GUI dispatch tests. | VERIFIED; a picture alone is not the route validation evidence. |

### M3: physical BOCDA interaction and localization

| Original requirement topic | Implementation/evidence | Status |
|---|---|---|
| Shared delayed modulation and local pump-probe frequency difference across numerical cells | Physical external/local delays and FM difference amplitude; `fiber_grid`, Floquet weights and cell integration; target-mapping test. | VERIFIED; optical carrier is removed analytically. |
| Emerging response integrates all cells under weak-gain assumptions | Segment contributions retained; power and gain/depletion limits; boundary-mixing test confirms both neighboring segments contribute. | VERIFIED; no segment-label oracle. |
| Periodic correlation structure, nonzero-order scanning and multiple peaks | Mapping/periodic tests and actual 320 m reduced-excursion three-peak fixture; resource limits declared for long full-excursion runs. | VERIFIED within resource limits, not arbitrary kilometer performance. |
| Uniform resonance and local detuning enhancement | Zero-FM Lorentzian limit; uniform/altered fiber tests; independent acoustic ODE/Floquet comparison. | VERIFIED within sampled tolerances. |
| Finite spatial resolution/background, localized perturbation and physical-control motion | Measured point-response FWHM and full scan; `test_boundary_mixing_not_truth_lookup`; width convention/range tradeoff tests. | VERIFIED; FWHM is not numerical cell size. |
| Analytic averaging justified; quasi-static approximation assessed; refinement | Acoustic filtered Floquet calculation rather than guessed Gaussian window; static/high-rate comparison; sideband/cell/frequency convergence; independent ODE and tag checks. | VERIFIED numerical model consistency, not paper-equivalent calibration. |

### M4: receiver and one local spectrum

| Original requirement topic | Implementation/evidence | Status |
|---|---|---|
| Consistent pump intensity tag and same-frequency phase reference | First-order pump-field derivation and acoustic tag susceptibility; 100 kHz source-confirmed reference. Resonant-tag and zero-tag tests; independent tag integration. | VERIFIED at declared small tag depth. |
| Photodetection and receiver scaling | Responsivity, transimpedance and one-pole bandwidth explicit; independent power/receiver scaling tests. | VERIFIED model volts; absolute instrument calibration UNPROVEN. |
| Peak/RMS, I/Q convention, filtering, dwell/settling | Factor-two peak-amplitude demodulation, one-to-four RC stages, `test_dwell_and_cascaded_filter`, phase-rotation test and zero-signal checks. | VERIFIED. |
| Actual GUI frequency sweep, spectrum plot and resonance estimate | Local run/report and historical live measurement screenshot/narrative; 251-point saved run; fit agrees away from boundaries within test tolerances. | VERIFIED first user-testable full apparatus. |
| Zero AM/zero SBS, phase behavior, no truth substitution | `test_zero_gain_and_zero_tag`, `test_phase_rotation_and_repeat_isolation`, fit no-signal flags. | VERIFIED exact zero/reference checks. |

### M5: scan and reconstruct the altered fiber

| Original requirement topic | Implementation/evidence | Status |
|---|---|---|
| Physical position sweep and spectrum per position | Native 36 x 251 scan, control values stored; scan arrays and saved-position-grid tests. | VERIFIED. |
| Resonance, fit quality, map/profile with input truth and boundaries | `results.py`, spectra/profile CSV and map plots; uniform/altered and boundary tests; baseline scan evidence. | VERIFIED; configured truth separately labelled. |
| Altered segment recovered; neighboring/boundary mixtures not hidden | Interior-position recovery within 4 MHz fixture tolerance; boundary contributions and nonempty flags; full scan report. | VERIFIED; a boundary fit need not equal either material resonance. |
| Response/edge width and range-resolution tradeoff | Actual point-response FWHM plus perturbed-region scan, not grid spacing; frequency-halving spacing/width test. | VERIFIED stated width metric; no universal reconstructed-edge guarantee. |

### M6: usable controls and consistent results

| Original requirement topic | Implementation/evidence | Status |
|---|---|---|
| Editable segment lengths/resonances/linewidths/gains and source/scan/receiver controls | Native schemas, parameter ledger, GUI parameter parser; historical literal Fiber 3 edit and current native tests. | VERIFIED. |
| Selected physical location/width, dedicated results, units and input/output separation | Measurements view, controls table, local/profile figures, scientific label assertions and inspected screenshots. | VERIFIED. |
| Running/completed/error state and same loaded/displayed/saved/executed configuration | GUI Apply/Save/Run ordering, worker snapshot, freeze controls; GUI/CLI equality and invalid-input tests. | VERIFIED bounded workflows. |
| No stale results after pending changes, topology changes or external edits | Snapshot fingerprints, disk-digest check, two-second watcher and failure invalidation; regression and independently inspected `m8-external-stale.png`. | VERIFIED corrected implementation; historical result files preserved. |

### M7: reproducibility, validation, handoff

| Original requirement topic | Implementation/evidence | Status |
|---|---|---|
| Uniform/altered/zero-gain/zero-AM and sampling/weak-probe checks | Named physics tests and independent review; current 95-test log includes baseline regressions. | VERIFIED tested regimes, not just imports. |
| Power accounting, receiver calibration convention, repeated-run isolation and GUI/CLI agreement | Project/GUI/extension tests plus native outputs and execution metadata. | VERIFIED numerical consistency. |
| Versions and launch/open/save/run/edit/read instructions | Test report records Python 3.11.9, QuReed 0.0.2, PhotonWeave 0.1.4, Flet 0.22.0, NumPy 2.4.6, SciPy 1.17.1, Matplotlib 3.11.1; launcher/README. | VERIFIED documented environment. |
| Reproducible configurations, outputs, limitations, upstream fixes and real errors | Direct example snapshots/CSV/PNG/HTML, root schemes, checked code paths and tests; no swallowed DES failures. | VERIFIED baseline; final M8 documentation reconciliation remains PENDING below. |

## Candidate hardware and source-claim boundary

All original candidate-device rows are retained: Keysight 33512B laser-FM source; AA1406 / DFB15TK laser; PN1550R5A2 / PNH1550R5A1 coupler; LNA6112 / MX-LN-0.1 pump EOM; EDFA100P / AEDFA-PM-37 EDFA; LNQ4314 / MXIQ-LN-30 probe EOM; SMB100B microwave source; FPC562 PC; IO-H-1550APC isolator; OC-L-1550 / 6015-3-APC circulator; PDA10CS2 detector; generic lock-in. These names remain in the milestone candidate table and source/README context. Native blocks use **functional labels**, not misleading hardware-emulator claims.

AA1406 identity, reported 699 kHz, 27 MHz, 47 GHz, source sweep, 100 kHz pump tag and thesis path/order are source-audited. A DFB15TK linewidth, catalog RF bandwidth, or candidate EOM label does **not** prove 47 GHz optical excursion at 699 kHz, correct gain/power/current, compatible ports, real noise figure, or calibrated voltage. Manufacturer alternatives, absolute device performance, temperature/strain calibration, full apparatus quantum-state identity and experimental quantum advantage remain **UNPROVEN**, explicitly outside software numerical acceptance.

## All nine original M8 topics

| Original topic | Actual model/test evidence | Cutoff verdict |
|---|---|---|
| 1. EOM finite extinction, sidebands, bias drift, RF amplitude/phase error | Pump MZI transfer and IQ sideband spectrum, signed Stokes/anti-Stokes response, extinction/RF/bias-offset and cancellation tests, exported sideband/transfer data. | VERIFIED except genuine acquisition-time bias drift: **PARTIAL**, only static bias errors at cutoff. |
| 2. EDFA ASE, saturation, gain dynamics | Phenomenological gain-state relaxation, compressed mean/tag response, one-/two-polarization ASE ledger, beat-noise exports and relaxation/PSD tests. | VERIFIED scoped model, not full erbium rate propagation. |
| 3. Shared-source phase noise and residual intensity modulation | Shared delayed Wiener trace/coherence/acoustic susceptibility, shared OU RIN and cross terms, exact/integrated kernel tests. | VERIFIED phase/RIN; deterministic FM-linked residual AM is **PENDING**, RIN alone is not RAM. |
| 4. Polarization variation and scrambling | Spatial OU angle and analytic Bessel/sinc finite-dwell scrambling average affect actual cell gain; bounds/fast-alias test and independent quadrature. | VERIFIED scalar model, not vector birefringence propagation. |
| 5. Detector noise/shot noise/bandwidth/saturation | Named PSD terms, detector transfer, exact discrete RC I/Q covariance, waveform clipping/flags, variance/power and sum-to-total tests. | VERIFIED linear/high-count noise model; fully noisy clipping statistics explicitly approximate. |
| 6. Pump depletion and coupled optical/acoustic dynamics | Counterpropagating PDE/ODE solver, opposite boundaries, optical photon accounting, stationary BVP comparison, two saved presets and exports. | VERIFIED model/presets; acceptance tolerance/time-scale reporting detail **PARTIAL** below. |
| 7. Gaussian channels/displaced thermal states | Normalized mode inputs, CP/uncertainty, thermal amplifier + loss, phase-mixture flag, independent moment/channel tests. | VERIFIED conditional effective channels; not inferred from classical power alone. |
| 8. Explicit-LO homodyne/phase reference | Separate native apparatus, hardware-owned LO/receiver, finite-LO moments, shot-noise/phase/mismatch/headroom checks, GUI/CLI equality. | VERIFIED code/test/export; literal homodyne GUI evidence still **PENDING** at cutoff. |
| 9. Defined multimode performance comparison | Temporal bins/resource ledger, mean/covariance FI, same-budget coherent and scalar references, mixing invariance, derivative refinement, full quantum scan export. | VERIFIED defined comparison; genuine optimized/experimental advantage remains UNPROVEN and not required to be positive. |

## Expanded M8.1-M8.6 acceptance map

| Expanded task/acceptance group | Evidence and exact qualification | Cutoff status |
|---|---|---|
| M8.1 EOM optical transfer, power normalization, signs, truncation and RF errors | `nonideal.py`, sideband/MZI tests, signed CSV assertions; individual gain and unsigned transfer guards prevent cancellation hiding strong interactions. | VERIFIED except time-varying bias drift. |
| M8.1 EDFA bandwidth/units, saturation/recovery and explicit phenomenology | `nonideal.md`, `edfa_trace`, ASE ledger, recovery test, exported EDFA trace/PSD; no physical calibration attributed to candidates. | VERIFIED. |
| M8.1 shared-history phase/intensity, equal-delay cancellation and quantitative coherence | Shared trace and exact Wiener kernel checked independently; OU intensity covariance handled. | VERIFIED stochastic part; deterministic residual modulation PENDING. |
| M8.1 actual bounded polarization/scrambling and proper averaging | Analytic finite-dwell average; actual per-cell coupling; explicit distribution and independent alias-case test. | VERIFIED. |
| M8.1 detector PSD/ENBW, seed reproducibility, clipping and diagnostics | 13 model tests plus 6 real exporter tests; one-sided named PSDs sum correctly, same seed repeats, clipping flags/limits visible. Noise correlations persist within frequency dwell sequence and reset per-position acquisition. | VERIFIED; test assertions do not establish all colored-noise or saturated-circuit statistics. |
| M8.1 disable effects, edit/save/export options and nonideal local/scan execution | Master-disabled equality and independently checked small-imperfection limit; inspected seed-edit screenshot; completed native GUI local/36-position runs and exact snapshots. | VERIFIED available effects; new drift/RAM will need added tests and rerun evidence. |
| M8.2 optical/acoustic state, boundaries, causal histories, attenuation and genuine depletion | `dynamics.py` and model review; zero-field/loss/weak/strong limits, independent steady BVP, normalized acoustic state and unequal optical photon ratio. | VERIFIED. |
| M8.2 tractable/stronger presets and full field/boundary/refinement artifacts | Two root-level transient schemes and completed reports; 151 frames, all settings and 40-to-80-cell boundary comparisons. | VERIFIED completed presets and exports; launch links still need final documentation update. |
| M8.2 resource preflight, characteristic times, refinement acceptance and visible failures | Workload/detuning/coupling/balance guards and tests; FM periods/dt/dz and relative boundary errors exported. | PARTIAL: explicit propagation/acoustic lifetime ratios, absolute near-zero refinement tolerance, and pass/warn classification against a declared target not yet found. Existing small errors support presets, not a universal convergence certificate. |
| M8.3 normalized modes, optical photon calibration, acoustic bath, effective gain | `quantum.py`, `quantum.md`, channel tests and exact output resource/state fields. | VERIFIED conditional independent-mode model, not full quantum Floquet scattering. |
| M8.3 coherent/squeezed thermal output, CP/uncertainty, vacuum/loss/noise limits | Physicality/channel tests, independent Gaussian mixture quadrature and spontaneous-noise check. | VERIFIED. Non-Gaussian mixtures labelled; moment plots do not claim a density reconstruction. |
| M8.4 native LO/composite mixer/diodes, reference routes, settings ownership | `homodyne_scheme`, topology/mode rejection tests, read-only hardware fields, photon-derived responsivity, 20 blocks/29 connections. | VERIFIED code/native tests; actual homodyne apparatus screenshot not yet inspected. |
| M8.4 phase/overlap/detuning/efficiency/electronics/headroom and finite LO | Exact finite coherent-LO moments, overlap sinc, individual + difference checks, phase and saturation tests; separate time-average units. | VERIFIED scoped receiver; ideal locking remains assumed, not an actual servo. |
| M8.4 save/reload/execute and visually distinct receiver | GUI/CLI quantum equality and hardware edit tests; full CLI scan exists. | PARTIAL: parent literal live LO edit/save/reload/run evidence pending at cutoff. |
| M8.5 physical modes, independence, encoded parameter and resource fairness | Fixed total T, input/LO photons, squeezing budget; normalized temporal bins and bandwidth/acoustic-memory constraints; parameter is a common gain-spectrum translation. | VERIFIED declared resource comparison; not a simultaneous spatial shared-bath covariance model. |
| M8.5 collective/coherent references, mean/covariance FI, invariance/discarding | Equal/mean-optimal/covariance-optimal candidates, same-phase coherent reference, all-output/reduced comparison, independent identical-bin and mixing checks. | VERIFIED restricted architecture; not global receiver/input optimization. |
| M8.5 derivatives/zero-signal and non-Gaussian/finite-LO validity | Analytical Lorentzian derivative refinement now a permanent test, zero-signal/phase-mixture/weak-LO tests; unavailable FI remains blank with reason in exports. | VERIFIED; no positive advantage manufactured. |
| M8.6 seven explicit run modes, schema/ranges/resources, common saved execution | `extensions.py`, `runner.py`, `advanced_gui.py`; native/GUI/CLI scan tests and exact run snapshots. | VERIFIED. |
| M8.6 stale tracking for apparatus/advanced/external changes and failures | Pending edits/fingerprints/disk watcher, deliberate failure regression, independent target audit, inspected live external-stale screenshot. | VERIFIED identified defects resolved. |
| M8.6 JSON/CSV/plots, units/options/seed/diagnostics, same GUI/CLI result | 11 artifact tests inspect actual numbers, rows, strict JSON, decodable PNGs and report labels; full-size artifacts inspected. | VERIFIED existing run types. New effects/tolerances must propagate through exports and tests. |
| M8.6 independent review, current complete suite, live workflows and final docs | Model/integration reviews are complete for inspected code; current 95-test report/log verified; nonideal/live stale evidence present. | PARTIAL: new drift/RAM/refinement work requires review and fresh suite; literal quantum/transient UI evidence and final verification/tracker reconciliation pending. |

## Actionable gaps for final reconciliation

1. **Implement and verify actual bias drift and deterministic RAM.** Static MZI/IQ bias offsets and stochastic RIN are valuable but do not fully satisfy those literal original extension topics. Root acknowledged these as implementation gaps and assigned them to the sensing-engine agent; no unseen future result is counted here.
2. **Close the transient convergence/time-scale acceptance detail.** Preserve the good independent BVP/preset results, but state relative and absolute near-zero tolerances, classify failed refinement visibly, and report duration relative to propagation and acoustic relaxation as well as FM period. This is not a request for a new full mechanical-energy model.
3. **Finish literal live advanced receiver/transient evidence.** At the cutoff the homodyne/dynamics algorithms, saved presets and GUI contract tests exist, but a real LO parameter edit/save/reload/run and transient GUI result have not been inspected in the live evidence directory. Root is performing these checks; attach the resulting screenshots and exact executed snapshots before marking those live gates complete.
4. **Reconcile final documentation.** `docs/verification.md` still calls M8 deferred and its final test count 35; `milestones.md` section 10 labels the current 95-test report as 35 rather than linking the archived baseline report. `docs/m8-verification.md` is referenced but not yet present. Update those records and README/preset instructions after actual completion, not before.
5. **Rerun after final code changes.** The verified 95-test report predates forthcoming bias/RAM/refinement changes. Reuse its historical facts only; publish a fresh final integrated report/log, preserve the 35-test baseline record, and identify which examples were regenerated or retain explicitly dated assumptions.

No new blocker was found in the already-audited receiver composition, power/unit normalization, Gaussian state handling, resource fairness or corrected stale-result logic. Nevertheless, **overall all-milestones completion is not established at this cutoff** because the specific remaining items above are real. A final addendum may close them with actual inspected artifacts; laboratory hardware equivalence and genuine quantum advantage should remain explicitly unproven even after software completion.

## Targeted resolution addendum: 2026-09-05 22:10:36 UTC

This addendum records newly inspected work without rewriting the earlier evidence cutoff.

### Transient convergence and time-scale gap closed at implementation/test level

`dynamics.py` now declares a per-boundary-trace acceptance rule: RMS(coarse minus interpolated fine) must not exceed `refinement_atol_w + refinement_rtol * RMS(fine)`. Defaults are 1 nW absolute and 1% relative. The two tolerances have finite validated ranges. Failure raises `ModelError` with actual error/threshold, rather than returning an apparently successful unconverged result. Disabled refinement is explicitly `not_checked` with a warning. Successful output records both RMS errors, both thresholds, grid sizes and the fine-run photon balance.

The actual simulated duration is distinguished from the requested duration and compared with the one-way propagation time and acoustic amplitude lifetimes $1/(\pi\Gamma_B)$ across the material segments. This closes the missing characteristic-time reporting gate; it does not convert a sub-FM-period trajectory into a cycle-averaged spectrum.

The referee independently ran all six `test_dynamics.py` tests: PASS, 4.678 s. The new test explicitly exercises a failed strict-refinement case and the zero-signal absolute-tolerance limit, and checks propagation/acoustic time definitions. Existing no-coupling, finite-FM, strong-depletion/BVP, pre-arrival, conservation and resource tests also passed. The older saved transient examples still need regeneration or an explicit historical-output label before their reports can claim the new acceptance fields.

### RAM kernel independently accepted; integration evidence still pending

The new `ram_floquet_weights` uses one source intensity $I(t)=1+r\cos(2\pi f_mt+\psi)$ evaluated at pump and probe retarded times. Its acoustic drive is the physical product of their field amplitudes and relative optical phase. It retains **signed** Fourier orders and does not normalize away the physical mean-product factor:

$$
\sum_n |u_n|^2=\langle I_p I_s\rangle
=1+\frac{r^2}{2}\cos(2\pi f_m\Delta\tau).
$$

Depth is limited to 0.1; Fourier work is bounded; a Parseval/truncation error above $10^{-8}$ rejects the calculation. The Stokes response uses those signed weights, while the conjugate anti-Stokes beat reverses them and has the physical loss sign. Frozen EDFA gain at the FM rate has its own 1% correction gate. These are genuine deterministic residual-modulation effects, distinct from stochastic RIN.

For an independent check, the referee integrated the driven acoustic differential equation directly, without using the implementation's Fourier weights, and extracted the mean response and linear pump-tag harmonic. The fixture used 10% RAM, 1 MHz FM, 27 MHz Brillouin linewidth, 7 MHz detuning, nonzero FM/RAM phases, unequal delays and a tag at $f_m/7$. Weight asymmetry was 0.051796, so the check can detect a signed-order error that a symmetric Bessel test would hide. Results:

- Parseval error: $2.22\times10^{-16}$.
- Floquet mean response: 0.792868258821636; direct ODE: 0.792868258817171; absolute difference $4.46\times10^{-12}$.
- Complex first-order tag response: $0.792860983714403-0.002493388128881i$; direct-ODE difference $4.97\times10^{-12}$.
- Incorrectly reversing the Stokes weights gives 0.781594481272, demonstrating that the tested sign matters.

This accepts the deterministic cycle-averaged acoustic forcing and first-order tag calculation numerically. Detector/source noise remains the declared slow small-signal approximation, not a newly established full cyclostationary noise calculation. The phase/RAM/Bessel grid limits, actual options, histories and assumptions still need permanent regression/export evidence and the final integrated run.

### Bias-drift normalization independently accepted; final reporting patch pending

`_bias_history` now evaluates actual pump MZM and probe IQ transfer at chronological frequency-dwell midpoints, continuing across positions. Bias changes linearly with acquisition time; pump transmission, tag, compressed EDFA gain with memory, probe total transmission and individual sideband fractions all change. Bias is frozen within each dwell, with at most 0.1 degree change per dwell or EDFA relaxation time; operating-range, effective tag-depth, passive-transmission and EDFA-peak limits are checked.

The referee compared a compact two-position scan against independent 131072-point optical-phase quadratures. The mean pump MZM transmission agreed to $1.11\times10^{-16}$ and probe IQ power ratio to $2.22\times10^{-16}$. Triggering the history path with $\pm10^{-12}$ degree/s reproduces the zero-drift result to $5.48\times10^{-13}$ relative. Midpoints continued from 0.255 s to 0.265 s across the position boundary without reset. A pump slope of 2 degree/s and probe slope of -1 degree/s changed the spectrum by 0.003916 relative, confirming this is a propagated effect rather than an unused control.

The per-point weak-gain/depletion guards use actual drifting powers. At this inspection the final summary depletion diagnostic still used static budget ratios; that concrete reporting issue was sent to the engine author for correction. Permanent drift/RAM tests, new CSV/plot histories, explicit frozen-dwell/noise-model warnings, updated final documentation, live homodyne/transient evidence and a fresh integrated suite remain pending. Thus this addendum closes the two new kernels' normalization/sign concerns and the transient acceptance implementation gap, **not yet the entire final-completion gate**.

## Live homodyne evidence addendum

The referee directly inspected `m8-homodyne-apparatus.png`, `m8-homodyne-phase-edit.png`, `m8-homodyne-phase0.png` and `m8-homodyne-phase90.png` in `results/verification`. The apparatus visibly distinguishes the matched LO and balanced receiver from the direct detector. Its LO form has native phase/power/mismatch/overlap controls; the phase-edit screenshot shows 90 degrees and a pending-parameter message. The two completed measurement screenshots identify homodyne difference voltage, not the original lock-in voltage, and explicitly display the ideal-locking, selected-mode, same-resource and no-automatic-quantum-advantage qualifications.

Root performed the literal phase edit, Save, raw-JSON check, Reload and Run, then restored phase zero. Independent inspection of the resulting exact execution snapshots and CSVs corroborates the visible change:

| Saved GUI run | Actual phase | Receiver result across all 251 frequency points |
|---|---|---|
| `results/gui_quantum_20260906_001112_422515` | 0 degrees | Mean voltage range 1.78286480290367 to 1.78649631563344 V. |
| `results/gui_quantum_20260906_001244_236214` | 90 degrees | Maximum absolute mean $1.09391349731452\times10^{-16}$ V. |

The variance arrays are exactly identical, as required for this phase-insensitive displaced-thermal output; displacement and its phase-sensitive information vanish in the orthogonal quadrature. The phase-90 hardware settings and `experiment-used.json` both contain `lo_phase_deg=90`. Its native execution records 20 devices, 29 connections, zero remaining events and snapshot hash `599219ed5756094a9679b5b624e3b1809fa17ba619a9aafc2ab24738af2b588e`. This closes the pending **literal homodyne apparatus/edit/save/reload/run evidence gate**. It does not claim that a real experimental phase lock was implemented.

The engine's subsequent reporting correction was also inspected: `estimated_depletion_by_position` and the final maximum now use the actual drift-dependent per-point calculation. Explicit RAM/drift warnings and source-RAM history are present; leading multiplicative-RAM RIN mixing and nearly frozen EDFA response are bounded, while full cyclostationary noise is expressly not claimed. The remaining checks concern permanent tests/exports, live transient/new-effect results, documentation reconciliation and the final integrated suite.

## Final focused RAM/drift regression acceptance

The referee inspected the finalized `nonideal.py`, new sections of `nonideal_results.py`, `docs/nonideal.md`, and permanent tests, then independently ran `python -B -m unittest discover -s tests -p "test_nonideal*.py" -v` in the existing parent environment. Result: **28 tests PASS, 93.288 s**, comprising 21 model tests and seven actual-result exporter tests.

The eight new model tests cover exact zero-RAM/drift branch recovery; changing transmitted powers and optical fractions with continuous acquisition chronology; bounded dwell/range/disabled-component cases; the analytic zero-FM RAM coefficients and mean-product normalization; an independently integrated asymmetric acoustic ODE and 4x/8x Fourier-grid refinement; preallocation workload rejection; combined nonzero RAM/drift shared delayed histories and finite spectra; and incompatible fast EDFA response or detector clipping rejection. The added artifact test uses a real two-position calculation, checks all new settings survive saving, verifies exact CSV counts and representative bias/time values, checks per-cell Parseval agreement, decodes both new PNGs, and verifies links and approximation warnings in the report.

The new exported files are `nonideal_bias_drift.csv/.png`, `nonideal_ram.csv/.png` and `nonideal_ram_floquet.csv`. Their axes/headers distinguish acquisition seconds, optical watts/milliwatts, positive sideband power fractions, deterministic intensity multipliers, Fourier order and physical normalization. Source RAM is explicitly distinct from the stochastic source-noise trace. The detailed documentation states the finite-depth, frozen-equilibrium, first-order tag and leading-noise restrictions rather than asserting an exact combined stochastic device model.

Consequently, the original actual-bias-drift and deterministic-residual-modulation implementation gaps, their export/test gate, and the stale depletion-summary finding are **closed for the declared model**. Together with the six independently passing dynamics tests above, no additional implementation-level scientific blocker remains from this focused completion audit. The final overall software-completion decision still requires root's actual live transient/new-effect evidence, regenerated transient reports carrying the new tolerance fields, fresh complete-suite report, and final documentation/tracker reconciliation. The earlier 95-test report is still historical and must not be relabeled as the post-change integrated run.

## Final resolution and independent sign-off

Final inspection: **2026-09-05 22:32:21 UTC** (September 6 in Europe/Berlin). The reviewer read [the complete final M8 verification narrative](m8-verification.md), the actual integrated test report/log, final exact run snapshots, current demonstration settings, regenerated example diagnostics/manifests, and the final saved GUI screenshots. This is new evidence, not an inference from the earlier 95-test count.

| Previously open gate | Actual final evidence | Decision |
|---|---|---|
| Integrated post-change suite | `test-report.json`: 105 PASS, zero failures/errors/skips, timestamp 2026-09-05T22:22:22.905481Z, 206.7715 s; `tests.log` independently confirms 105 tests and OK. No `bocda_model/*.py` implementation file was newer than the report at this inspection. | CLOSED. |
| Transient live GUI and full plots | `gui_dynamics_20260906_001936_641298` has native 19/26 graph, zero remaining events, 150 ns, 76.5 transits, 12.723 acoustic lifetimes, 0.104814 FM periods and refinement passed. `m8-coupled-transient.png` visibly reports the correct limits. The later `m8-coupled-field-map.png`, from `gui_dynamics_20260906_002941_288508`, was directly inspected and shows the loaded four optical/acoustic maps plus refinement/conservation plots after scrolling. | CLOSED; the earlier not-yet-loaded image capture is not a missing plot implementation. |
| Actual nonzero RAM/drift GUI save/reload/run | `gui_nonideal-local_20260906_002344_838411` contains exactly seed 2026, pump/probe slopes +1/-1 degree/s, RAM depth 0.1 and phase 30 degrees. It has 251 frequency points and native 19/26 graph with zero events. `m8-drift-ram-controls.png`, `m8-drift-ram-measurement.png` and `m8-live-ram-diagnostic.png` were directly inspected. | CLOSED. |
| New-effect values/exports, not unused controls | Independent JSON/CSV checks give 251 bias rows, 2048 retarded RAM rows and 200 Fourier rows. Acquisition times are 0.005–2.505 s; pump bias 2.005–4.505 degrees; probe bias 0.995 to -1.505 degrees. The actual spectrum, drift curve, shared intensity histories and unnormalized Fourier-product check are visible. | CLOSED. |
| Regenerated full-size examples and valid manifests | `quantum-scan`, `transient-baseline` and `depleted-demo` were regenerated. Both transient reports now carry absolute/relative acceptance thresholds and physical time ratios. The full quantum scan remains 36 by 251 with explicit mode resources. Every manifest target for these and the final live transient/RAM runs exists, including absolute `experiment-used.json` paths. | CLOSED. |
| Safe demonstration restoration | Independently read current JSON: `experiment.json` seed 2026 and both bias slopes, RAM depth and RAM phase all zero; `experiment-homodyne.json` LO phase zero. Exact nonzero/phase-90 input snapshots remain in their report folders. | CLOSED; restoration was actually verified, not assumed from a future promise. |
| Final operational documentation and scientific scope | The complete M8 verification narrative is present. README and advanced-usage now point to recorded acceptance; baseline verification correctly preserves its archived 35-test record. All three example commands/presets and model-family boundaries are documented. Final tracker checkbox synchronization is the implementation owner's administrative handoff. | Evidence sufficient to mark reviewed milestones complete. |

Regenerated transient values were checked directly: the unscaled preset has depletion $3.4224962\times10^{-6}$ and probe amplification 1.0040859; the stronger preset has depletion 0.0207669853 and amplification 1.4958310. Both pass their declared 1 nW plus 1% RMS refinement thresholds. The stronger preset's gain/probe multipliers are still identified as assumed demonstration values. Its excellent photon-balance residual does not replace its independent grid-refinement check.

The final verification wording preserves the scientifically necessary distinctions: source convention uncertainty versus chosen defaults; clean spatial reference versus nonideal measured response; finite transient versus FM-period average; optical/acoustic envelope normalization versus thermodynamic acoustic energy; separate clean effective Gaussian channel versus combined noisy/depleted SBS; phase-matched ideal LO versus an implemented servo; and same-resource measurement FI versus quantum Fisher information or demonstrated quantum advantage. The operational single-session restriction remains explicit. No new physical overclaim was identified in the final handoff documents.

**Recommendation: accept M0–M8, including expanded M8.1–M8.6, as completed numerical/software milestones within their stated model assumptions and resource limits. No unresolved blocking finding remains from this independent source, physics, integration and requirement audit.** The parent may synchronize the milestone tracker accordingly; this reviewer did not modify it. Laboratory compatibility/calibration, a full stochastic vector/depleted quantum-SBS model, globally optimized multimode protocols and genuine experimental quantum advantage remain unproven and are not promoted to completion claims.
