# Advanced simulation result exports

Date: 2026-09-05. Role: Computational Physicist. Status: **NUMERICAL artifact verification**, not independent approval of the underlying physics.

Question: can the advanced simulator produce inspectable, portable results without requiring a running GUI?

Implementation: [advanced_results.py](../bocda_model/advanced_results.py). Tests: [test_advanced_results.py](../tests/test_advanced_results.py).

## API and artifacts

Call save_advanced_results(result, outdir, config=None) with the quantum or dynamics wrapper returned by extensions.run_model(). The return value is a dictionary of **absolute** paths:

| Key | Artifact |
|---|---|
| data, json | Full results.json, preserving model outputs, options, diagnostics and warnings |
| config | settings_used.json with configuration, extension kind, run mode and extension_options |
| report | Standalone report.html with relative image/data links |
| manifest | manifest.json containing every returned path |
| quantum_spectra_csv | Position/frequency, mean voltage, variance, quadrature moments and photon/duration normalization |
| quantum_modes_csv | Temporal-bin boundaries and photon/squeezing allocation |
| quantum_fisher_csv | Readout, evaluation status, total/mean/covariance FI in inverse Hz squared |
| quantum_spectrum_plot | Selected-target voltage mean/variance versus optical frequency offset |
| quantum_state_plot | Covariance ellipse, temporal correlations and LO-phase mean/noise curves |
| quantum_fisher_plot | Resource-matched mean/covariance information comparison, or explicit unavailable panel |
| quantum_map_plot | Mean/noise scan map; only produced for more than one position |
| dynamics_fields_csv | All saved time/position optical powers and real/imaginary acoustic-envelope values |
| dynamics_boundary_csv | Boundary optical powers and weighted photon-balance residual versus time |
| dynamics_fields_plot | Pump, probe, normalized acoustic magnitude and phase space-time maps |
| dynamics_boundary_plot | Input/output pump and probe boundary traces |
| dynamics_refinement_plot | Balance trace and coarse/fine boundary differences, or explicit unrequested-refinement notice |

CSV headers contain units or dimensionless normalization names. JSON serialization rejects NaN/infinity rather than emitting non-standard data.

The exporter uses isolated Matplotlib Figure and FigureCanvasAgg objects without pyplot or a GUI backend. Rendering is serialized by a module-local lock, so worker-thread rendering does not mutate the GUI backend. This does not assert that every unrelated Matplotlib caller elsewhere in the process uses the same lock.

## Scientific presentation safeguards

- Quantum output voltages are balanced, rectangular-time-average receiver outputs, not the original lock-in's peak phasor.
- A covariance ellipse is not a reconstructed density matrix. Phase-mixture moment ellipses are explicitly labelled non-Gaussian.
- LO phase curves reuse the computed selected optical state. They are predicted receiver responses, not a new simulation of changing the source. Phases exceeding individual-diode or difference-output headroom are marked red.
- Disabled Fisher information remains unavailable: the CSV uses empty numeric cells and a reason, and the figure shows a notice instead of zero bars.
- The FI comparison preserves total signal/LO photons, observation duration, physical modes and channel parameter. It is measurement FI, not QFI or a claim of quantum advantage.
- The single collective reference is the best of the implemented scalar projection candidates, not a globally optimized receiver.
- Quantum scan-map entries represent separate observations at each spatial/spectral setting. The map is not a simultaneous covariance matrix over fiber positions.
- Transient plots are not FM-cycle-averaged spectra. Demonstration gain/probe multipliers and simulated FM periods remain visible in settings/diagnostics.
- Acoustic-envelope normalization is W, but its magnitude is not interpreted as acoustic power or thermodynamic energy. Phase is masked at zero amplitude.
- Boundary input and output at equal plotted time are not directly a depletion estimator during turn-on. The solver's retarded no-SBS reference remains authoritative.
- A conservation residual is not a convergence estimate. Refinement is plotted separately and absence of refinement is explicit.
- All HTML text from configurations or warnings is escaped. Links and plot paths are relative inside the report for portability.

## Verification

The five artifact tests execute actual small quantum-scan and optical/acoustic simulations through the shared run-model dispatcher. They then export and parse JSON/CSV, check exact numerical values against the computed results, inspect PNG dimensions/pixel variation and embedded label metadata, check mode photon totals, preserve unavailable FI, and exercise HTML escaping.

Run from the model directory:

~~~powershell
& '..\.venv\Scripts\python.exe' -m unittest tests.test_advanced_results -v
~~~

Visual QA inspected a real quantum state/phase plot, FI comparison and transient space-time map. It found and corrected literal newline escapes in FI labels. The plots now wrap comparison labels and titles correctly, mask undefined acoustic phase, and restrict time axes to the simulated nonnegative interval.

This is an export/label/provenance check. It is deliberately not used as evidence that the effective Gaussian model is the complete apparatus's quantum channel or that the transient solver has experimentally validated material coefficients.

