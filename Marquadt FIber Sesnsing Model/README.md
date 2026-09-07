# QuReed BOCDA fiber-sensing model

Exploratory numerical project in `SCRATCH`. It models the supplied apparatus with a shared frequency-modulated CW laser, two optical arms, four editable bidirectional fiber segments, direct detection, and a dual-phase lock-in. It is not a calibrated reproduction of Popp's laboratory equipment.

Advanced modes add weak-gain device/noise models, a separate depleted optical/acoustic transient solver, and an explicit LO/balanced-receiver variant for selected Gaussian modes. These are separate model families, not an automatically composed simulation of every nonideality and quantum effect.

## Launch the GUI

Open PowerShell and run:

```powershell
Set-Location -LiteralPath 'C:\Projects\WORKSPACE\SCRATCH\Sensing Qureed\QuReed\Marquadt FIber Sesnsing Model'
.\launch_gui.ps1
```

The launcher uses the existing parent `QuReed\.venv` and opens this experiment automatically. Do not create another environment or run an editable install inside this model folder. No dependency installation happens when the project opens.

For the same native QuReed/Flet board in a browser:

```powershell
.\launch_gui.ps1 -Web -Port 8765
```

Then open [the local GUI](http://127.0.0.1:8765). Keep the PowerShell process running. Close that process to stop serving. The server binds only to the local computer. Use one active editing session per server.

Use this project launcher, not the unmodified `qureed-gui` entry point: it installs project-local runtime fixes for custom parameter persistence, file discovery, counterpropagating ports, and execution. Installed QuReed source and the earlier Fiber-Sensing toy are not changed by this project.

## First measurement

1. The Apparatus tab opens `experiment.json` in a compact full-board view, with four aligned fibers and the pump output visible. Gold/teal solid wires are optical; dashed blue wires are RF/control. Crossings are not junctions.
2. Click the **Position scan** block header to open its parameter panel, or use **Toggle editor** and its Apparatus block list. The local target defaults to 0.25 m, in the deliberately shifted third fiber. Hide the editor again to regain the full diagram width.
3. Choose **Run local spectrum**. Pending parameter edits are applied and the exact input snapshot is saved before execution.
4. Measurements displays X, Y, R, fitted resonance, fit flags, actual FM/delay controls, spatial response, and exported figures.
5. Choose **Run position scan** to sweep 0.025–0.375 m in 0.01 m steps. The expected 10.85 GHz baseline changes to 10.90 GHz inside the third segment (0.20–0.30 m).
6. Edit a fiber's resonance, linewidth, length, gain, or attenuation, Apply parameters, then Save and rerun.

The full scan has 36 positions and 251 frequency points per position. A measured command-line run took about 45 s on this computer under concurrent load; startup and export add overhead. Runtime varies.

Save persists physical parameters, names, positions, and wiring. Reload reads external JSON edits. If the JSON changed externally, the GUI refuses to overwrite it with cached state. Unsaved edits or changed topology mark old measurements stale. Invalid connections fail with a named port to repair.

A folder chooser shows folders, not JSON files. The launcher avoids that confusion by loading the project's scheme directly.

The 2026-09-06 layout cleanup changes presentation only: all physical values and connections are preserved. Wires route around blocks and update after dragging. Original saved layouts are recoverable under `results/layout-cleanup-original/`. See [layout verification](docs/layout-cleanup.md).

## Choose an experiment and advanced model

Use the **Experiment** selector to choose a saved apparatus:

- **experiment.json**: direct detector and lock-in, 19 native blocks and 26 connections.
- **experiment-homodyne.json**: 20 native blocks and 29 connections. A matched LO receives common-FM and probe-frequency references and feeds an explicit balanced receiver. This composite block includes the optical mixer and two photodiodes. Quantum readout is evaluated **before** the drawn optional lock-in.
- **experiment-transient-baseline.json**: the 19-block / 26-connection direct graph with unit pump, probe and gain multipliers, for an unscaled finite transient.
- **experiment-depleted-demo.json**: the same direct graph with probe multiplier 50 and gain multiplier 100. This is an explicitly stronger-interaction demonstration, not a paper-calibrated operating point.

To launch the homodyne apparatus immediately:

~~~powershell
.\launch_gui.ps1 -Scheme experiment-homodyne.json
# Browser alternative:
.\launch_gui.ps1 -Web -Port 8765 -Scheme experiment-homodyne.json
~~~

Switching experiments or reloading asks before discarding unsaved edits. Saved files are preserved. Pending Apparatus and Advanced inputs are applied by Save or Run; **Apply** alone changes the in-memory model. Runs freeze editing, execute in a worker, save their exact input snapshot, then display Measurements. Later edits hide and mark those results stale; previous output files remain available.

In **Advanced models**, choose a family, edit settings, then use **Apply advanced parameters**, Save, or its Run button. **Reset this model's defaults** changes only that family's in-memory advanced settings; save to persist. LO and balanced-receiver fields are read-only here because their **Apparatus** blocks own the values. Resetting advanced defaults does not reset those hardware blocks.

| CLI mode | GUI action | Apparatus / meaning |
|---|---|---|
| local | Run local spectrum | Direct apparatus; clean local frequency sweep |
| scan | Run position scan | Direct apparatus; clean spatial/spectral scan |
| nonideal-local | Run nonideal local | Direct apparatus; weak-gain EOM/EDFA/source/polarization/detector extensions |
| nonideal-scan | Run nonideal scan | Direct apparatus; nonideal spatial/spectral scan |
| dynamics | Run coupled transient | Choose the unscaled transient or depleted-demo preset; optical/acoustic envelopes, not a receiver spectrum |
| quantum | Run Gaussian / homodyne | Homodyne apparatus; clean selected-mode Gaussian-channel analysis |
| quantum-scan | Run quantum position scan | Homodyne apparatus; selected-mode readout across positions |

Quantum analysis must be enabled in Advanced models. Its library default is off, while the supplied homodyne experiment enables it. Direct-detection buttons intentionally reject the homodyne apparatus; quantum buttons reject an apparatus without its connected LO and balanced receiver.

See [advanced operation and every parameter/default](docs/advanced-usage.md), [quantum channel assumptions](docs/quantum.md), and [advanced output guide](docs/advanced-results.md).

## How localization works

The pump travels from the first to fourth segment; the probe travels in the opposite direction. The circulator sends pump toward the fiber and routes the emerging probe to the detector. Each physical fiber has separate input/output ports for both directions.

Three scales are distinct:

| Scale | Default | Meaning |
|---|---:|---|
| Physical GUI segment | 10 cm | Region assigned material properties |
| Numerical cell | At most 2 mm | Quadrature resolution inside each segment |
| Calculated local response FWHM | About 4.62 cm | Width from the dynamic acoustic response, not a chosen grid size |

The shared optical frequency modulation is delayed differently in the two arms. Each numerical cell contributes its local Brillouin response. Target position maps to an actual modulation frequency or path delay; the detector does not directly read the target segment's assigned value. Finite-width localization and off-peak background remain in the measured spectrum.

In **frequency** control mode, target position, external delay, and correlation order determine the actual FM frequency. The nominal FM input is not independently used in this mode. **Delay** mode holds nominal FM and solves the delay. **Fixed** mode leaves both physical controls unchanged and reports the actual correlation peak; it cannot scan positions.

The demo uses correlation order one and external delay $1/(699\,\mathrm{kHz})$. This differs deliberately from the thesis's reported long-delay geometry. Zero-order equal-delay peaks cannot be moved by changing FM frequency alone.

## Frequency and resolution convention

The source reports 47 GHz modulation bandwidth, but its amplitude/span equations are inconsistent. The measured thesis spectrum supports **47 GHz total span**, or **23.5 GHz peak deviation**. That is the default, with an explicit convention selector.

At 699 kHz and intrinsic gain FWHM 27 MHz:

- Correlation-peak spacing is about 145.923 m, not the demo fiber length.
- The conventional approximate resolution formula gives about 5.34 cm.
- The implemented local on-resonance dynamic response has FWHM about 4.62 cm.
- The source's nominal 3 cm is recorded, not forced into the output.

Selecting 47 GHz as *peak* deviation approximately halves the response width. Reducing FM frequency increases both peak spacing and resolution length. The 4.62 cm diagnostic uses a reference linewidth; it is not an exact resolution guarantee everywhere in a fiber with varying linewidth.

Read [source audit](docs/source-audit.md), [equations and approximations](docs/physics.md), and [independent review](docs/physics-review.md) before interpreting quantitative results.

## Parameters and hardware labels

[The full parameter reference](docs/parameters.md) lists every editable default, unit, and provenance. Optical/receiver gains are assumed demonstration values, so reported volts are model voltages, not instrument calibration.

The hardware candidates retained in [milestones.md](milestones.md) are purchasing context, not hardware emulators. In particular, a narrow laser linewidth does not verify the tuning excursion at 699 kHz. EOM drive/bias, EDFA operating power, detector gain bandwidth, RF options, connectors, and polarization behavior need separate experimental verification.

## Command-line execution and tests

From this project directory:

```powershell
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --validate
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --mode local
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --mode scan
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment.json --mode nonideal-local
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment.json --mode nonideal-scan
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment-transient-baseline.json --mode dynamics --out results/transient-baseline
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment-depleted-demo.json --mode dynamics --out results/depleted-demo
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment-homodyne.json --mode quantum
& '..\.venv\Scripts\python.exe' -m bocda_model.runner --scheme experiment-homodyne.json --mode quantum-scan
& '..\.venv\Scripts\python.exe' -m bocda_model.verify
```

Use `--scheme path-to-scheme.json` and `--out path-to-results` with the runner for a separate saved configuration/output location. The GUI and CLI both execute the same saved topology through native QuReed assembly and a DES scan-controller event.

Advanced parameters come from the saved scheme, not undocumented CLI flags. Without an explicit output directory, the CLI writes results/<mode>/ and repeat runs replace that mode's generated artifacts. Use a new output directory to preserve comparisons. GUI outputs are timestamped. Validation checks the saved apparatus; it does not execute a numerical model or certify its operating regime.

The counterpropagating optical problem is solved globally after validating the connections. Individual icons do not pretend to be an independent feed-forward time-domain solver. Each run gets a fresh native device/signal/event registry, preserving the live editor state. Errors propagate to the UI or a nonzero CLI exit status.

## Files and results

| Path | Purpose |
|---|---|
| `experiment.json` | Saved apparatus and parameters; authoritative experiment |
| `config.toml` | QuReed project identity; no implicit package installation |
| Root component Python files | Native project-discoverable device classes |
| `bocda_model/devices.py` | Port definitions, editable schemas and device responsibilities |
| `bocda_model/project.py` | Topology validation and configuration mapping |
| `bocda_model/physics.py` | Delayed-FM acoustic/SBS and receiver calculation |
| `bocda_model/runner.py` | Shared isolated QuReed execution |
| `bocda_model/gui.py`, `integration.py` | Native canvas, editing, persistence and results |
| `tests/` | Physics, saved topology and native GUI regression checks |
| `results/local/`, `results/scan/` | Reproducible example outputs |
| `results/gui_.../` | Timestamped GUI measurement snapshots and outputs |
| `docs/` | Model, sources, independent review, parameters and verification |

Each run exports the exact experiment-used.json snapshot, settings_used.json, complete results.json and a static report.html, plus mode-specific CSV and PNG artifacts. Baseline and nonideal modes provide spectra/profile/spatial-response CSV and figures. X/Y/R are **peak volts**, using a factor-two IQ convention; sinusoidal RMS is peak divided by $\sqrt2$. Assigned material resonance and reconstructed fits are labelled separately. Red fit markers warn about ambiguity, poor line shapes or boundary mixing.

Quantum exports contain balanced time-averaged voltage means/variances, state moments, LO-phase curves, temporal-mode resources and qualified classical FI comparisons. Dynamics exports contain optical/acoustic space-time fields, boundary powers, weighted optical balance and optional refinement diagnostics. These meanings are not interchangeable with lock-in peak spectra. Quantum/dynamics settings JSON stores both the configuration and advanced options. Advanced sources are in bocda_model/nonideal.py, dynamics.py and quantum.py; dispatch, controls and exports are in extensions.py, advanced_gui.py and advanced_results.py.

Inspect [example spatial scan report](results/scan/report.html). Existing generated examples can be regenerated; new GUI runs use timestamped folders.

## Validity limits and troubleshooting

- The baseline is classical, weak-probe, undepleted-pump, and first order in total SBS gain and intensity-tag depth.
- Pump AM depth must be at most 0.3. Peak integrated gain above 0.1, estimated depletion above 1%, EDFA power-ceiling violations, or detector voltage-limit violations are rejected. Keep well below the gain ceiling for accurate SBS amplitudes.
- The detector is a one-pole model; the lock-in is one to four cascaded RC stages sampled at dwell end. Short dwell causes transient bias.
- FM harmonics overlapping the tag or twice the tag can invalidate period averaging and are rejected. This matters when reducing FM frequency.
- Sideband/cell resource limits are explicit. Arbitrary kilometer-length, full-excursion calculations can exceed this implementation's interactive resources.
- In baseline modes the probe EOM represents one ideally selected shifted sideband and additional nonidealities are absent. Select a nonideal mode to include its stated transfer functions and detector statistics. That mode remains weak-gain and does not silently invoke depletion or quantum evolution.
- A Lorentzian fit near a boundary need not equal either assigned resonance. Consult fit flags and the full spectrum.
- No temperature/strain calibration or unique temperature-versus-strain separation is claimed.
- QuReed 0.0.2 uses deprecated Flet UserControl APIs. Those warnings are expected with the tested Flet 0.22.0; do not upgrade the environment blindly.
- If the GUI reports a missing input, reconnect the named port. If it reports external JSON edits, reload deliberately before saving.
- Both named transient presets use 150 ns: only about 0.105 FM periods near 699 kHz, not a cycle-averaged spectrum. The unscaled preset uses unit multipliers; the depleted demo uses probe scale 50 and gain scale 100. Standalone API defaults select the stronger demonstration. Neither preset supplies missing paper calibration.
- Enabled transient refinement requires both boundary-power RMS errors to pass `refinement_atol_w + refinement_rtol * RMS(reference)`, defaulting to 1e-9 W plus 1%. A failed check rejects the run; disabled refinement is labelled `not_checked`. Small photon-balance error alone is not convergence.
- Quantum analysis uses the clean single-Stokes effective amplifier, not the nonideal multi-sideband sum or a full quantum depleted-pump channel. LO matching/locking is an explicit ideal assumption with entered residual mismatch and phase jitter.
- Finite LO power and individual-diode headroom are checked. FI is suppressed for insufficient bright-LO accuracy, entered LO detuning or phase mixtures; unavailable FI is not zero. Photon/time/bandwidth accounting does not imply guaranteed multimode or quantum advantage.

The tested versions and acceptance evidence are recorded by `bocda_model.verify`. The [dated classical baseline](docs/verification.md) is preserved separately from the integrated advanced-model record.

The integrated suite passed **105 tests**, with no failures, errors or skips. Live checks covered input editing, save/reload, stale/error handling, nonideal local/scan, native LO phase rotation and coupled transients. See the [complete M8 verification record](docs/m8-verification.md), [independent requirement audit](docs/completion-audit.md), and [advanced usage](docs/advanced-usage.md). Acceptance is numerical/software acceptance within the documented models, not experimental calibration or a proof of quantum advantage.
