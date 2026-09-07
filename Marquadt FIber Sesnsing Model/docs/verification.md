# M0–M7 baseline verification and acceptance evidence

Date: 2026-09-05. Status: NUMERICAL / supported within the documented approximate model. Classical software and live GUI acceptance completed. This is a historical baseline record; subsequent integrated M8 evidence is recorded separately in docs/m8-verification.md.

## Automated checks

Run `python -m bocda_model.verify` using the parent QuReed environment for the current integrated suite. The dated 35-test baseline is preserved as [machine-readable results](../results/verification/test-report-m0-m7.json) and [test log](../results/verification/tests-m0-m7.log).

The final 35-test run completed with zero failures, errors, or skips in about 52.8 s. Resource counts are now checked before allocating frequency/position/cell arrays. Coverage includes:

- Delayed-FM Lorentzian limit, sideband normalization and truncation, acoustic tag transfer, phase sign, RC settling.
- Physical position mapping, width-convention sensitivity, range/resolution tradeoff and a tractable 320 m multi-peak fixture.
- Uniform and altered fibers, finite boundary mixing, spatial/frequency-grid refinement, zero gain, zero pump AM.
- Source splitting, optical budget, independent pump/probe power scaling and detector-gain scaling.
- Invalid topology/parameters, unsupported imported device classes and required-port validation.
- Real native QuReed objects: physical port sides, custom parameter save/reload, external-edit protection, stale-result tracking.
- GUI-worker and CLI spectra equality for the same saved snapshot; fresh native devices/signals/events for repeated runs.
- Fiber order follows actual wiring rather than JSON list order. Independent review confirmed the live editor's simulation registry is preserved.

Automated native-object tests do not replace live rendering/interaction checks.

## Example runs

The root ran both commands using the saved 19-device, 26-connection experiment:

- Local spectrum: one target at 0.25 m, 251 frequency samples from 10.6 to 11.1 GHz.
- Position scan: 36 targets from 0.025 to 0.375 m, 251 frequency samples each.

The complete scan through native QuReed assembly/scheduling took about 44.9 s under concurrent load, before export. Both finished with zero queued events. Outputs are in [local](../results/local/report.html) and [scan](../results/scan/report.html).

The third segment's configured 10.90 GHz resonance is recovered against the 10.85 GHz background. A four-interior-position fixture gave approximately 10.8500, 10.8494, 10.9011, 10.8494 GHz. Boundary flags appear in the full scan; the fitter never substitutes configured truth for a measurement.

Default optical budget: pump into fiber 0.0891251 W, probe into fiber $8.91251\times10^{-5}$ W, no-SBS detector probe $7.94314\times10^{-5}$ W. Maximum accumulated gain in the full scan was 0.0042448; estimated pump depletion fraction $4.2448\times10^{-6}$; baseline detector voltage 0.714882 V. These are model settings/checks, not calibrated lab outputs.

## Independent scientific audit

See [source audit](source-audit.md) and [physics review](physics-review.md). A reviewer independently integrated the acoustic ODE rather than generating references from the production Bessel sum:

- Floquet gain comparison: maximum absolute discrepancy below $9\times10^{-11}$ for the stated fixtures.
- Small pump-AM transfer comparison: maximum discrepancy below $1.2\times10^{-8}$.
- Point-response FWHM: about 4.6218 cm for 47 GHz peak-to-peak and 2.3109 cm for 47 GHz peak.

These checks support the implemented equations under their assumptions. They do not prove laboratory equivalence, remove source convention ambiguity, or establish quantum-state behavior.

## Completed live GUI checks

The built-in browser automation could not initialize, so live tests used an isolated headless Microsoft Edge instance with Playwright against the localhost Flet server.

- Fresh and subsequent browser sessions render the native 19-device board.
- Fiber 3 was selected using the actual Apparatus dropdown.
- Its resonance was edited to 10.92 GHz and saved through the GUI; the JSON contained 10920000000.
- The actual Run local spectrum button produced a fitted result near 10.91873 GHz, with actual FM 698.760572 kHz and relative delay 1430.61516 ns displayed.
- The 10.90 GHz default was restored through the GUI. Before applying the edit, the Measurements tab hid old plots and displayed STALE.
- Saving, reloading and rerunning the restored local measurement succeeded.
- The actual Run position scan button completed all 36 positions and displayed the map/profile. Its exported snapshot and results are in results/gui_scan_20260905_224702_362890.
- The final restored local measurement is in results/gui_local_20260905_224646_318935.
- The final experiment.json fingerprint exactly matched default_scheme() after restoration.
- Inspected screenshots: [all apparatus blocks](../results/verification/apparatus.png), [local measurement](../results/verification/measurements.png), [scan measurements](../results/verification/scan-measurements.png), [scan profile](../results/verification/scan-profile.png), and [stale inputs](../results/verification/stale-inputs.png).

## Failed routes and compatibility fixes

1. The upstream GUI persisted values only for variable blocks. Project-scoped runtime serialization now preserves every custom parameter.
2. A browser reload reused native singleton controls carrying old Flet page IDs, causing a blank page and Flutter insertion-range errors. Per-page initialization resets the affected native GUI singleton state.
3. Utility Python files were incorrectly treated as device modules by the stock project explorer. The project hook distinguishes actual devices from support files.
4. Upstream JSON execution logs and swallows DES exceptions. The project uses its native assembler but invokes the scheduler directly so errors propagate.
5. The old beam-splitter PhotonWeave API and Fock initialization defects are avoided by explicitly classical project components, not represented as repaired quantum simulation.
6. Whole-spectrum Lorentzian fitting was biased by physical background. Local fitting with background and explicit ambiguity flags replaced that failed inference route.
7. A blank initial browser capture is retained at `results/gui-initial.png` as diagnostic evidence, not as the delivered GUI.

Installed QuReed source and earlier toy files were preserved. All changes for this implementation are confined to the model project.

## Tested environment

Python 3.11.9, QuReed 0.0.2, PhotonWeave 0.1.4, Flet/Flet Runtime 0.22.0, NumPy 2.4.6, SciPy 1.17.1, Matplotlib 3.11.1 on Windows. The machine-readable report records exact runtime strings.

## Completion boundary

This record covers only the classical M0–M7 GUI demonstration. M8 was originally deferred, then explicitly included by the user's subsequent all-milestones implementation request. Its later implementation, limitations and acceptance evidence belong to the separate advanced-model verification record, not this 35-test baseline. Neither record establishes experimental calibration or quantum advantage.
