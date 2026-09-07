# Integrated M8 verification and handoff

Date: 2026-09-06 (Europe/Berlin). Status: NUMERICAL / software acceptance within explicitly documented approximate models. This extends, rather than replaces, the dated [M0–M7 baseline record](verification.md).

## Integrated automated verification

The final command was `..\.venv\Scripts\python.exe -m bocda_model.verify`, run in this model directory.

- **105 tests PASS**, zero failures, errors or skips.
- Elapsed 206.7715 s under concurrent model/GUI work.
- Report timestamp: 2026-09-05T22:22:22.905481+00:00 (00:22:22 on September 6 locally).
- [Machine-readable report](../results/verification/test-report.json) and [complete test log](../results/verification/tests.log).
- Coverage: 35 baseline tests; 21 nonideal model tests; 7 actual nonideal-export tests; 6 coupled-dynamics tests; 22 quantum/channel/receiver tests; 5 advanced-export tests; 9 native GUI/integration contracts.
- Runtime: Python 3.11.9, QuReed 0.0.2, PhotonWeave 0.1.4, Flet/Flet Runtime 0.22.0, NumPy 2.4.6, SciPy 1.17.1, Matplotlib 3.11.1, Windows.

Tests exercise calculations and actual exported numbers/files, not merely imports. Included cases cover signed sidebands, exact zero-effect recovery, shared phase/RIN histories, actual acquisition-time bias drift, deterministic FM-linked RAM, independent acoustic ODE comparison, preallocation guards, detector clipping, depletion, photon accounting, failed refinement, Gaussian physicality, finite-LO moments, resource-matched mode comparisons, native topology, save/reload, GUI/CLI equality, and stale/error handling.

The independent referee additionally ran all 28 nonideal model/export tests and all six dynamics tests. See [independent model review](m8-review.md) and the granular [original-requirement completion audit](completion-audit.md). Numerical checks are not mathematical proofs or laboratory calibration.

## What was delivered

| Model family | Saved apparatus and actions | Accepted scope |
|---|---|---|
| Classical direct detection | experiment.json; local and scan | 19 native blocks / 26 connections; shared-FM CW source, two arms, four bidirectional fibers, PD plus lock-in. |
| Nonideal direct detection | Same apparatus; nonideal-local and nonideal-scan | EOM transfer/sidebands/drift, phenomenological EDFA dynamics/ASE, shared phase/RIN/RAM, scalar polarization/scrambling, detector filtering/noise/headroom. |
| Coupled transient | experiment-transient-baseline.json and experiment-depleted-demo.json; dynamics | Actual counterpropagating optical envelopes and acoustic envelope; causal boundary inputs, depletion, attenuation, numerical refinement and photon accounting. |
| Selected-mode quantum/homodyne | experiment-homodyne.json; quantum and quantum-scan | 20 blocks / 29 connections, explicit matched LO and composite optical mixer/two-diode receiver, physical effective Gaussian channels, finite-LO moments and resource-fair temporal-mode comparisons. |

These are separate explicit model families. They are not silently composed into a full noisy, depleted quantum-SBS apparatus. All 71 advanced options and native hardware parameters are documented in [advanced usage](advanced-usage.md) and the [baseline parameter ledger](parameters.md). Candidate equipment names are provenance/context, not claims of calibrated hardware emulation.

## Literal live GUI verification

An isolated headless Microsoft Edge instance exercised the actual localhost QuReed/Flet GUI. No user browser profile was used. The native-computer/browser connector was unavailable, so Playwright operated the same local web GUI. The browser reported no JavaScript page errors in successful workflows.

### Direct/nonideal workflow and freshness

- The native 19-block apparatus rendered, with the four-fiber chain and distinct optical/control routes.
- Seed 2027 was entered in Advanced models, saved, and confirmed in experiment.json.
- Actual nonideal local and full 36-position, 251-frequency scan buttons completed through native scheduling with zero remaining events.
- [Local GUI report](../results/gui_nonideal-local_20260905_234659_664448/report.html); [full nonideal GUI scan](../results/gui_nonideal-scan_20260905_235026_534730/report.html).
- A deliberate external JSON name edit triggered the two-second file watcher, hid old measurements and displayed STALE. Attempting Save preserved the externally changed file rather than overwriting it with cached state. The test-only name change was restored and the project reloaded.
- Screenshots: [advanced input](../results/verification/m8-advanced-controls.png), [measurement](../results/verification/m8-nonideal-measurement.png), [full scan](../results/verification/m8-nonideal-scan.png), [external-change guard](../results/verification/m8-external-stale.png).

The older full nonideal scan predates the new zero-default RAM/drift branches; it is retained as dated live evidence, not relabeled as a nonzero-RAM scan. Permanent tests verify exact zero-effect recovery and combined two-position nonzero-effect execution.

### Explicit LO phase experiment

The Experiment selector loaded experiment-homodyne.json. Its separate LO, FM/frequency reference routes and balanced composite receiver are visible in the [apparatus screenshot](../results/verification/m8-homodyne-apparatus.png).

1. Ran the actual Gaussian/homodyne action at LO phase 0 degrees.
2. Selected the native Matched local oscillator block; changed its phase to 90 degrees; saved and confirmed `lo_phase_deg=90` in the JSON.
3. Reloaded from disk and ran again.
4. Confirmed phase 90 in both the executed snapshot and resolved hardware options.
5. Restored phase 0 through the GUI and confirmed the saved JSON. Advanced hardware fields are visibly disabled, with a note to edit the native blocks.

| Saved live run | Mean difference voltage across 251 points | Variance comparison |
|---|---|---|
| [Phase 0](../results/gui_quantum_20260906_001112_422515/report.html) | 1.7828648029–1.7864963156 V | Reference. |
| [Phase 90](../results/gui_quantum_20260906_001244_236214/report.html) | Maximum absolute mean $1.0939135\times10^{-16}$ V | Exactly identical variance array. |

This is the expected orthogonal-quadrature behavior of the chosen phase-insensitive displaced-thermal output under the effective model. It does not implement an experimental phase-lock servo.

Screenshots: [pending native phase edit](../results/verification/m8-homodyne-phase-edit.png), [phase-zero result](../results/verification/m8-homodyne-phase0.png), [phase-90 result and information comparison](../results/verification/m8-homodyne-phase90.png), [read-only hardware controls](../results/verification/m8-homodyne-controls.png).

### Coupled transient in the GUI

Loaded experiment-depleted-demo.json, selected Coupled optical/acoustic transient and pressed Run coupled transient. The [live result](../results/gui_dynamics_20260906_001936_641298/report.html) completed with 19 native devices, 26 connections and zero queued events.

The [GUI screenshot](../results/verification/m8-coupled-transient.png) shows:

- 40 cells, 49.02 ps time step, 150 ns simulated duration.
- 76.5 fiber propagation transits, 12.723 longest acoustic amplitude lifetimes, but only 0.104814 FM periods.
- Actual pump depletion 2.0767%, probe amplification 1.4958, weighted photon-balance residual about $-8.23\times10^{-15}$.
- Refinement passed against saved absolute and relative RMS tolerances, not just an unclassified relative-error number.
- Boundary, optical/acoustic field and refinement data/plots saved in the report.

The first screenshot was taken before offscreen images loaded. A second actual transient run, [saved here](../results/gui_dynamics_20260906_002941_288508/report.html), was scrolled to the field/refinement plots and allowed to finish decoding. The [fully rendered field-map screenshot](../results/verification/m8-coupled-field-map.png) confirms all four optical/acoustic panels and the refinement graphics are visible in the GUI; all three image elements reported complete decoding.

The strict-tolerance regression deliberately fails refinement and checks that the error propagates. Disabling refinement produces `not_checked` and a warning; zero-signal acceptance uses the absolute tolerance. No finite transient is advertised as a settled full-cycle spectrum.

### Real nonzero drift and RAM in the GUI

After restarting the server with finalized source, actual visible advanced controls were edited, saved and reloaded:

`seed=2026`, `pump_bias_drift_deg_s=1`, `probe_bias_drift_deg_s=-1`, `source_ram_depth=0.1`, `source_ram_phase_deg=30`.

The [live nonzero-effect report](../results/gui_nonideal-local_20260906_002344_838411/report.html) used exactly those options and completed a 251-frequency local acquisition, with 19/26 native graph and zero queued events.

- 251 dwell midpoints run from 0.005 to 2.505 s.
- Pump EOM bias actually changes from 2.005 to 4.505 degrees; probe bias from 0.995 to -1.505 degrees.
- The drift-dependent pump input to the fiber ranges from 0.0563008 to 0.0580712 W; it is not a static-bias label.
- Exported 251 bias-history rows, 2048 shared retarded RAM-history rows, and 200 cell Fourier-normalization rows.
- Every manifest target exists, including the absolute executed experiment snapshot path.
- [Control screenshot](../results/verification/m8-drift-ram-controls.png), [completed measurement](../results/verification/m8-drift-ram-measurement.png), and [live RAM diagnostic](../results/verification/m8-live-ram-diagnostic.png).

Offscreen Flutter semantics inputs initially accepted automation keystrokes without changing the underlying control. This was detected by checking the JSON. The verified workflow scrolled the actual controls into view before editing; all reported values come from the actual saved/executed JSON. No unconfirmed edit is counted as evidence.

The test-only drift/RAM settings are restored to zero in the normal demonstration after this check; the exact nonzero input remains reproducible in the report's experiment-used.json. Larger long scans must use slower drift rates or satisfy the explicit accumulated-bias validity guard.

## Regenerated full-size examples and artifact checks

All three CLI examples below were rerun after the convergence/manifest fixes. Inputs were unchanged by execution; settings equal the input-derived configuration and resolved extension options. Strict JSON, CSV row counts/values, PNG decoding, HTML links, absolute manifest paths and zero remaining events were checked independently.

| Report | Dimensions | Representative result |
|---|---|---|
| [Quantum position scan](../results/quantum-scan/report.html) | 36 positions × 251 frequencies; 4 temporal bins | Joint measurement FI $2.8617705\times10^{-11}$ Hz$^{-2}$; best scalar candidate $2.8617537\times10^{-11}$ Hz$^{-2}$. Same-budget coherent reference equal here; no quantum advantage claimed. |
| [Unscaled transient](../results/transient-baseline/report.html) | 40 cells × 151 frames | Depletion fraction $3.4224962\times10^{-6}$; probe amplification 1.0040859; refinement passed. |
| [Stronger transient](../results/depleted-demo/report.html) | 40 cells × 151 frames | Depletion fraction 0.0207669853; probe amplification 1.4958310; refinement passed. |

Both transient presets explicitly report their 150 ns / 76.5 transits / 12.723 acoustic lifetimes / 0.104814 FM periods. The stronger preset uses gain multiplier 100 and probe multiplier 50; these are assumed demonstration settings, not Popp parameters. Boundary acceptance is
$\mathrm{RMS}(P_{coarse}-P_{fine})\le 10^{-9}\,\mathrm{W}+0.01\,\mathrm{RMS}(P_{fine})$,
with the fine boundary interpolated at coarse times.

## Resolved issues and remaining scientific limitations

Resolved during independent review: signed anti-Stokes handling and noncancelling validity guards; JSON-safe physical arrays; native receiver hardware ownership; disk-change freshness; failed-run invalidation; actual bias drift versus static error; deterministic RAM versus stochastic RIN; drift-aware power/depletion diagnostics; declared convergence acceptance near zero; complete input-snapshot manifests.

Important limits remain explicit and are not software failures:

- The 47 GHz peak/full-span ambiguity remains visible. Nominal 3 cm, calculated approximately 4.62 cm local response and approximately 5.34 cm formula estimate are distinct.
- The nonideal model is weak-gain, leading-order/cycle-averaged with stated quasi-static drift, slow EDFA and RAM/noise validity bounds; polarization is scalar, not full vector propagation.
- Coupled dynamics are classical optical/acoustic envelopes; acoustic normalization is not thermodynamic acoustic energy and no spontaneous quantum bath is inferred.
- Quantum states are conditional finite-mode effective channels. Non-Gaussian mixtures and invalid Gaussian FI regimes are flagged; a classical power alone does not establish a quantum state.
- LO matching/locking is an ideal stated assumption. Homodyne readout is before the optional drawn lock-in, not a reuse of its voltage calibration.
- Multimode comparisons fix signal photons, LO photons, observation time and squeezing cost; they are specified temporal-bin comparisons, not a full shared-bath multimode optimization.
- Laboratory device compatibility/calibration, temperature/strain calibration, a complete quantum SBS apparatus and genuine experimental quantum advantage remain unproven.
- Use one editing session per local GUI server because upstream QuReed uses process-level singleton registries.

No installed QuReed files, earlier toy project, user-owned PROJECTGOALS.md or RESULTS.md were changed in this all-milestones implementation. Detailed independent acceptance mapping is retained in completion-audit.md; no formal research result was promoted out of SCRATCH.
