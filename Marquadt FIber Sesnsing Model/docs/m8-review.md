# M8 independent review: nonideal optics, dynamics and quantum modes

Date: 2026-09-05. Status: **MODEL-LEVEL REVIEW COMPLETE: supported within the stated approximations by independent numerical checks.** Full M8 GUI/integration acceptance is separate.

Final integrated update, 2026-09-06 local: **ACCEPTED within the stated numerical/software scope.** See the final sign-off below and [completion-audit.md](completion-audit.md) for preserved historical findings and their actual resolutions.

Question: do the optional extensions implement the stated physical models with correct normalization, explicit approximations and a fair measurement comparison? This audit is independent of the implementation agents. It supplements, and does not repeat, [physics-review.md](physics-review.md).

## Source foundations and required distinctions

- C. R. Giles and E. Desurvire, *Modeling erbium-doped fiber amplifiers*, J. Lightwave Technol. 9, 271-283 (1991), [DOI 10.1109/50.65886](https://doi.org/10.1109/50.65886), [full article](https://optiwave.com/wp-content/uploads/2018/04/modelling.pdf). Equation (32) gives two-polarization ASE power $2n_{sp}(G-1)h\nu B$ under uniform-inversion assumptions; Section VIII develops temporal gain behavior. A lumped saturation/recovery surrogate must be labelled phenomenological rather than equated to the full propagation/rate model.
- F. S. Gokhan and H. Goktas, *Analytical Solution of Brillouin Amplifier Equations for Lossless Medium*, [arXiv:1807.05359](https://arxiv.org/abs/1807.05359). Equation (1) and the stated boundary conditions describe counterpropagating pump/Stokes intensities with inputs at opposite ends. This supports a two-point boundary-value treatment; a forward-only cascade is not a depletion solution.
- C. M. Caves, *Quantum limits on noise in linear amplifiers*, Phys. Rev. D 26, 1817 (1982), [DOI 10.1103/PhysRevD.26.1817](https://doi.org/10.1103/PhysRevD.26.1817). The linear phase-insensitive amplifier requires an auxiliary noise mode. Setting added noise to zero at gain above unity is not a physical bosonic channel.
- C. Weedbrook et al., *Gaussian Quantum Information*, [arXiv:1110.3234](https://arxiv.org/abs/1110.3234). Sections II and V provide Gaussian state, measurement and channel conventions. That review uses vacuum covariance $I$; this project uses $I/2$, so formulas require consistent rescaling.
- G. Carrara et al., *Squeezing as a resource to counteract phase diffusion in optical phase estimation*, [arXiv:2008.03161](https://arxiv.org/abs/2008.03161). Phase diffusion is a generally non-Gaussian noise process on optical states, even when the random phase has a Gaussian distribution. Moment propagation alone does not establish a Gaussian state after averaging.
- M. F. B. Cenni et al., *Thermometry of Gaussian quantum systems using Gaussian measurements*, [arXiv:2110.02098](https://arxiv.org/abs/2110.02098). Appendix B gives the classical Fisher information of a Gaussian probability distribution. The appropriate quantity for a specified homodyne receiver is measurement FI; it must not be renamed quantum Fisher information.
- *Single Sideband Modulation in Brillouin Optical Correlation Domain Analysis*, CLEO Europe 2017, [primary conference abstract](https://opg.optica.org/abstract.cfm?uri=cleo_europe-2017-CH_P_36), describes suppression of the anti-Stokes sideband to remove gain/loss balance. J. H. Youn and K. Y. Song, J. Lightwave Technol. 40, 894-899 (2022), [primary abstract](https://opg.optica.org/abstract.cfm?uri=jlt-40-3-894), explicitly distinguishes Stokes gain from anti-Stokes loss. Thus residual upper probe sidebands cannot be modeled as positive, far-off-resonant gain only.

These sources support modeling frameworks, not device-specific calibration or an experimental performance claim for the Popp apparatus. All extra settings remain assumed unless separately sourced.

## Nonideal optical and receiver gates

1. EOM finite extinction, sideband leakage and bias/RF errors must enter through a stated optical field transfer or an explicitly approximate power-transfer model. Report discarded harmonics and do not conflate amplitude with intensity modulation depth.
2. EDFA ASE needs an explicit spectral-density convention and bandwidth. For one polarization, $S_{ASE}=n_{sp}(G-1)h\nu$ in W/Hz; summing two independent polarizations supplies the factor of two. Keep optical amplifier ASE distinct from the Brillouin channel's acoustic thermal bath and from quantum vacuum noise.
3. A finite-bandwidth filtered detector requires consistent one-sided noise PSD and equivalent noise bandwidth. Saturation must be indicated, and clipping must not silently masquerade as an unbiased spectrum. Noise samples must have a reproducible seed and covariance consistent with the filter or an explicitly stated independent-acquisition approximation.
4. Polarization overlap is an intensity coupling factor in $[0,1]$. Random or deterministic scrambling should average the actual sampled overlap; do not assume a universal factor of one half without identifying the distribution and averaging interval.
5. Shared-source phase noise must use the same stochastic phase at the pump and probe's retarded times. Independent draws for the two paths incorrectly eliminate common-mode cancellation.

### Shared Wiener phase derivation

Define a laser Lorentzian linewidth $\ell$ by

$$
\operatorname{Var}[\phi(t+u)-\phi(t)]=2\pi\ell|u|.
$$

For delayed copies separated by $\tau=|\tau_p-\tau_s|$, the phase difference is a Wiener increment over an interval of length $\tau$. Its variance is $2\pi\ell\tau$. Two such intervals shifted by $u$ overlap over $\max(\tau-|u|,0)$, giving covariance $2\pi\ell\max(\tau-|u|,0)$. Therefore the beat's phase-coherence function is

$$
C_b(u)=\left\langle e^{i[\Delta\phi(t+u)-\Delta\phi(t)]}\right\rangle
=\exp[-2\pi\ell\min(|u|,\tau)].
$$

This is a conditional analytic result for a Wiener process, not a description of arbitrary colored laser noise. At zero delay, phase fluctuations cancel exactly. At delays long compared with acoustic memory, the relative beat's Lorentzian linewidth is twice the individual laser linewidth.

For a local normalized acoustic decay $\gamma=\pi\Gamma$ and angular detuning $\omega=2\pi\delta$, the phase-averaged linear susceptibility is

$$
H_\phi(\delta)=\gamma\left[
\frac{1-e^{-(\gamma+2\pi\ell+i\omega)\tau}}{\gamma+2\pi\ell+i\omega}
+\frac{e^{-(\gamma+2\pi\ell+i\omega)\tau}}{\gamma+i\omega}\right].
$$

It has the correct zero-linewidth and zero-delay limits, and tends to linewidth $\Gamma+2\ell$ with correspondingly reduced peak at long delay. An explicit time-domain shared trajectory can also be used, subject to sampling/ensemble checks. Neither method implies the optical phase-averaged state is Gaussian.

## Depletion and acoustic-dynamics gates

Use opposite-end optical boundaries, explicit initial acoustic conditions, and consistent optical field/power/photon normalization. In the lossless continuous-wave limit, one converted pump photon creates one Stokes photon and one acoustic excitation. Exact energy accounting uses $\omega_p=\omega_s+\Omega_B$; replacing optical frequencies by a common value is an approximation whose small error must be distinguished from numerical conservation.

A steady depleted intensity boundary-value solution with an effective averaged gain is useful, but does not by itself implement time-dependent optical/acoustic dynamics. Conversely, a transient acoustic ODE with fixed optical fields does not implement pump depletion. If both are offered as complementary calculations, name their scope separately and test the overlap of their limiting regimes.

Required checks: zero coupling, zero probe, attenuation-only transport, weak-coupling agreement, boundary residual, pump decrease/Stokes increase in their respective propagation directions, conservation residual, and refinement in space/time or solver tolerance. A numerical failure must remain a failure in the GUI and result record.

## Quantum channel and measurement gates

For a finite collection of optical bosonic modes, each with infinite-dimensional Fock space, use interleaved quadratures with $[x_j,p_k]=i\delta_{jk}$, vacuum $V=I/2$, and $\Omega=\bigoplus_j\left(\begin{smallmatrix}0&1\\-1&0\end{smallmatrix}\right)$. Physical covariance matrices satisfy $V+i\Omega/2\succeq0$.

The effective thermal amplifier has

$$
a_{out}=\sqrt G\,a_{in}+\sqrt{G-1}\,b^\dagger,
\quad V_{out}=GV_{in}+(G-1)(n_B+1/2)I,
$$

with $G\geq1$, $n_B\geq0$. A coherent input yields a displaced thermal mode with $n_{out}=(G-1)(n_B+1)$. Passive loss subsequently adds the vacuum term required to preserve the uncertainty principle. The thermal occupation uses the Brillouin/acoustic frequency, while optical photon number uses the optical carrier energy.

Mode functions, durations and frequency bins must be declared. If $N=PT/(h\nu_{opt})$ is used, $P$ must be the power in that selected normalized mode and $T$ its duration. The local oscillator needs a matched optical mode, an explicit relative phase, efficiency and photon budget. A lock-in time constant is not automatically a quantum mode duration.

For a Gaussian homodyne measurement with mean $\mu(\theta)$ and covariance $\Sigma(\theta)$,

$$
F(\theta)=(\partial_\theta\mu)^T\Sigma^{-1}(\partial_\theta\mu)
+\frac12\operatorname{Tr}\{[\Sigma^{-1}(\partial_\theta\Sigma)]^2\}.
$$

Report the mean and covariance terms separately. They have units inverse square of the estimated parameter. This formula is exact for the stated Gaussian outcome distribution, not for a non-Gaussian phase-averaged mixture approximated by its first two moments.

## Resource-fair multimode comparison gates

- Fix the physical mode set, total time, signal photons, squeezing photons where applicable, LO photons and the encoded parameter. Mode count is constrained by time/bandwidth and cannot be increased freely for extra bath samples.
- Compare one collective output mode with resolved readouts of the same physical field only if the discarded modes are clearly identified. An increase from observing thermal covariance in additional modes is measurement access, not automatically quantum advantage.
- An equal-weight collective mode can be a poor reference when response slopes differ. Include the mean-optimal scalar weighting $w\propto\Sigma^{-1}\partial_\theta\mu$, or explicitly state the restricted reference and avoid claims of globally optimized advantage.
- A parameter-independent invertible transformation of the same commuting measured-quadrature vector, followed by joint readout, must preserve FI. This applies to the implemented real orthogonal mixer with a common homodyne phase, not to an arbitrary change of optical measurement basis involving previously unmeasured conjugate quadratures. Discarding outputs from that same experiment can only lose information.
- For identical independent displaced thermal channels at a common setting, concentrating on the matched collective mean captures the full displacement FI. Additional resolved modes can retain otherwise discarded covariance FI. Include this limit to distinguish the two mechanisms.
- A finite set of independent effective channels does not reproduce all frequency mixing and shared-bath correlations of the physical SBS system. Report that boundary explicitly.

## Implementation audit and numerical evidence

Inspected implementations: `bocda_model/nonideal.py`, `bocda_model/dynamics.py`, and `bocda_model/quantum.py`, with their component tests and model documentation. This is a model-level review, not independent certification of GUI wiring, export completeness, actual laboratory hardware, or every M8 milestone checkbox. Those require the integrated acceptance record.

### Independent calculations, not only implementation tests

The reviewer ran the following read-only Python calculations in the project environment. Their status is **NUMERICAL**, supporting the specified equations within the tested regimes; none establishes experimental calibration or an unconditional quantum sensing advantage.

| Check | Independent reference and result |
|---|---|
| Shared-source acoustic response | Direct quadrature of the damped acoustic-memory integral at delay 0, 1 ns, 20 ns, and 1 microsecond, laser linewidth 2 MHz, acoustic linewidth 27 MHz, detuning 9 MHz: complex susceptibility error at most $5.0\times10^{-16}$. |
| Shared-source cancellation | The two interpolated retarded histories at identical delays have exactly zero relative phase and identical intensity multipliers. |
| Lock-in noise normalization | Independent frequency integration of $2|H_{RC}(f)|^2$ gives I/Q variance factors 500, 250 and 156.25 Hz for 1, 2 and 4 cascaded stages at 1 ms; implementation relative error below $3\times10^{-15}$. The factor of two follows the amplitude-normalized I/Q mixer, not a one-sided/two-sided ambiguity. |
| Polarization averaging | Analytic Bessel/sinc finite-dwell averaging agrees with independent direct time quadrature to $2.3\times10^{-16}$ at 3200 Hz/10 ms, 151.7 Hz/7 ms, and 0.3 Hz/20 ms. The fast case would alias the former 32-point sampler. |
| Nonideal baseline recovery | Disabling individual component imperfections and noise, with the maximum available 120 dB leakage isolation, gives gain-array difference below $8.7\times10^{-19}$ and complex IQ difference $1.79\times10^{-10}$ V ($2.96\times10^{-7}$ relative). The remaining finite pump leakage is explicit. Master-disabled nonideal mode reproduces baseline arrays exactly. |
| Zero-field dynamics | Zero pump or zero probe leaves the other wave in attenuation-only transport and creates no acoustic response from the zero initial seed. Photon-balance residual below $8.1\times10^{-15}$. |
| Attenuation-only dynamics | At 1000 dB/km over 0.4 m with optical coupling disabled, both transmitted power fractions are 0.912010839355908, versus analytic 0.912010839355910. Loss-referenced pump depletion is $1.2\times10^{-15}$. |
| Weak CW dynamics | At $g=0.5\,\mathrm{W^{-1}m^{-1}}$, zero loss, matched 10.85 GHz detuning, the output probe amplification is 1.01797657 with pump depletion 0.000898879. This is consistent with the small undepleted-gain scale $gP_pL=0.0178250$. |
| Strong depleted CW dynamics | Independent `scipy.integrate.solve_bvp` of stationary counterpropagating intensity equations gives depletion 0.1893318925 and probe amplification 4.7864254303. The time-domain solver gives 0.1893500790 / 4.7867927202 at 40 cells, and 0.1893373654 / 4.7865384514 at 80 cells. Refinement reduces the discrepancy; photon-balance residual is below $1.5\times10^{-13}$. |
| Gaussian channel limits | For input $N=17$, gain 2, vacuum auxiliary mode and no loss, output photon number is 35, including the required spontaneous photon. Unity gain preserves the input. Complete loss yields vacuum. Tested CP/uncertainty minima are nonnegative within $4.5\times10^{-15}$ numerical roundoff. |
| Common phase mixture | Two squeezed/displaced modes with a shared Gaussian phase of standard deviation 0.7 rad: 120-point Gauss-Hermite integration agrees with analytic mean to $1.8\times10^{-15}$ and covariance to $7.2\times10^{-15}$. The output is correctly marked generally non-Gaussian. |
| Finite coherent LO | Coherent signal/LO difference-current variance exactly matches $(e/T)^2\eta(N_{LO}+N_s)$ for perfect overlap, power overlap 0.4, and residual frequency mismatch $1/T$. This checks that mode mismatch does not remove the signal's finite-LO shot-noise contribution. |
| Gaussian measurement FI | An independent 200,000-sample likelihood-score calculation gives 0.530257567 versus analytic 0.528997579, a 0.24% statistical difference. Real orthogonal mixing of the same three-dimensional measured vector leaves the analytic FI unchanged. |
| Identical temporal modes | For four identical displaced thermal bins, resolved/equal-collective mean-FI ratio is exactly 1; covariance-FI ratio is exactly 4. Joint real passive mixing changes FI by zero at displayed precision. Extra covariance access is not labeled quantum advantage. |
| Frequency-derivative refinement | For a Lorentzian gain of peak 0.003, linewidth 27 MHz, at 20 MHz detuning, frequency steps 2, 1, 0.5 and 0.25 MHz give derivative relative errors 0.5117%, 0.1283%, 0.03211% and 0.008028%. Corresponding FI is $1.40607938,1.39537299,1.39269238,1.39202199\times10^{-14}\,\mathrm{Hz^{-2}}$, consistent with second-order derivative convergence. |

The depleted reference uses pump input 0.0891250938134 W, probe input 0.00445625469067 W, length 0.4 m, $g=50\,\mathrm{W^{-1}m^{-1}}$, a 150 ns transient with a 2 ns intensity turn-on, and stationary opposite-end boundaries for the independent BVP. These are explicit demonstration settings, not measured Popp parameters. Optical photon conservation uses the unequal-frequency ratio $\nu_p/(\nu_p-\nu_B)$; the acoustic variable is a normalized response in W, not a calibrated mechanical energy.

### Review findings and corrections

- **Resolved:** the first sideband implementation omitted anti-Stokes loss. The corrected form uses detuning $|n|f_{RF}-\nu_B$ and signed response $-\operatorname{sign}(n)$ for a sideband at $\nu_0+n f_{RF}$. Carrier $n=0$ does not supply a resonant SBS contribution. The symmetric two-sideband cancellation regression passes.
- **Resolved:** gain/loss cancellation could hide large individual interactions from a net-response validity guard. The code now checks maximum unweighted individual-sideband gain and an unsigned power-weighted transfer envelope, both distinct from the signed detected response. The restored-overlap/large-interaction regression passes.
- **Resolved:** fixed 32-point sampling could alias fast polarization scrambling. It is replaced by the analytic finite-dwell Bessel/sinc average, independently checked above.
- **Resolved:** depletion/amplification diagnostics originally included attenuation/turn-on deficit. Both now use retarded attenuation-only references; a missing/zero reference is unavailable rather than a spurious 100% depletion. Raw simultaneous-boundary transmission ratios remain separately named. An initially failing zero-coupling test was corrected by fixing the physical normalization, not loosening its tolerance.
- Quantum review corrections include common-phase averaging of the multimode moments, matching the coherent comparison's input phase, and testing finite-LO/saturation conditions in every independent and mixed output, not just one representative bin.
- **Resolved:** the receiver ASE and shared RIN terms now include coherent pump leakage and the pump's EDFA fractional response. ASE equivalent bandwidth is identified separately from a single centered hard filter. Named shot, shared-RIN, electronic, signal-ASE and ASE-ASE voltage PSDs are exported; their sum-to-total regression passes.

### Interpretation and remaining model limits

1. The three advanced modes are alternatives with explicit overlaps, not one fully coupled quantum stochastic solver. In particular, applying a single thermal-amplifier channel to the nonideal detector's net Stokes/anti-Stokes gain is unsupported. Quantum analysis must use the separate clean single-Stokes baseline.
2. The EDFA compression/recovery law is phenomenological. Its ASE is a flat-density, rectangular-equivalent-bandwidth, high-gain-noise-figure approximation; there is no wavelength-resolved erbium rate/propagation solution. The scalar polarization model does not reproduce vector random birefringence.
3. Classical noise is linearized and high-count Gaussian. Clipping the deterministic waveform before adding filtered noise does not predict the exact statistics of a clipped noisy waveform. Clipped results cannot establish unbiased frequency or sensitivity estimates. Shared phase trajectories are illustrative; their ensemble acoustic kernel is calculated analytically.
4. The transient solver omits stochastic phonon forcing and acoustic propagation, and does not infer thermodynamic mechanical energy from its normalized acoustic variable. A sub-FM-period result is not a stationary BOCDA spectrum. Boundary agreement and mesh refinement remain necessary even when the discrete photon identity is excellent.
5. The quantum channel is a physically valid conditional effective amplifier with lumped passive loss. It is not derived as the full frequency-mixing SBS scattering matrix, does not retain dispersive phase information, and does not combine arbitrary shared-bath or nonideal sideband correlations. Ideal LO phase/history matching is an assumption, not a simulated feedback loop.
6. Gaussian phase averaging preserves computable moments but generally destroys Gaussianity. Gaussian FI is disabled for that case and for unsupported detuned multimode readout. The finite-LO 1% variance-correction gate is an operational accuracy condition, not a rigorous bound on the error of FI.
7. The collective-mode references are fixed local scalar projections of the same measured mode set and resources. Mean-optimal and covariance-optimal candidates improve on a possibly poor equal-weight choice, but are not a global optimum over optical LO allocation, arbitrary preparation, or all measurements. Passive real mixing of fully observed quadratures adds no information by itself.

### Recommendation and test record

No unresolved blocking physics error was identified in this bounded model-level review after the corrections above. **Accept these three modules as explicitly scoped numerical models**, retaining all listed approximation and claim-strength limits. This recommendation does not declare all M8 work complete.

The reviewer independently executed the project suites with the project virtual environment and `python -B -m unittest discover -s tests -p <filename> -v`: 20 quantum tests passed (1.621 s); the final 13 nonideal tests passed (14.379 s); and the final 5 dynamics tests passed (3.614 s). These 38 component tests supplement the independent calculations above. Later integration tests or newly added derivative tests must be reported using their actual rerun evidence, not assumed from these counts.

GUI integration, saved native LO wiring, parameter ownership, result-staleness behavior, all export paths, representative default/stronger presets, and the complete M8 acceptance checklist remain the parent integration review's responsibility. In particular, integration must preserve the distinction between a nonideal multi-sideband intensity measurement and the separate effective single-Stokes quantum channel. Numerical checks do not establish hardware calibration, a full quantum SBS derivation, or an experimentally genuine multimode advantage.

## Focused M8 integration code audit

Scope: a later bounded read-only pass over `project.py`, `extensions.py`, `gui.py`, `advanced_gui.py`, `runner.py`, `tests/test_extensions.py`, and the directly relevant `SnapshotSession` freshness and native LO/receiver definitions. No live browser session or project implementation was modified by this reviewer. The scientific model recommendation above remains intact.

### Verified contracts

- Complete topology validation requires the LO optical connection and shared FM/microwave-reference routes for the homodyne receiver. An LO on the original direct receiver is rejected. The fiber pump/probe chain remains validated in opposite directions.
- A separate homodyne apparatus replaces the receiver with an explicitly described composite balanced mixer/two-diode block. Native hardware values override advanced quantum copies; advanced fields display hardware-owned values read-only, and GUI saves remove duplicate hardware keys.
- Independent read-only dispatch checks confirmed: direct apparatus permits local/nonideal/dynamics but rejects quantum; homodyne apparatus permits quantum/dynamics but rejects direct local/nonideal spectra. Quantum dispatch calls the clean classical single-Stokes reference, never the net nonideal sideband detector sum.
- The native homodyne 1000 V/A transimpedance reaches both configuration and quantum options. At 1550 nm and efficiency 0.8, the derived responsivity is 1.000127448 A/W, consistent with $\eta e/(h\nu)$.
- Both apparatus and advanced pending edits are applied before Save/Run; parsing failures stop the run. Changing an advanced group first applies its pending values. Experiment switching asks before discarding unsaved values. The worker receives a deep-copied saved snapshot, and GUI/CLI use the same dispatcher and export path.
- Results labels distinguish transient envelopes, pre-lock-in homodyne voltages, clean spatial reference curves in nonideal runs, and conditional Gaussian/FI claims. Invalid model/receiver combinations and exceptions propagate rather than returning a successful empty result.
- Integrated test code includes GUI/CLI equality for quantum, nonideal and dynamics, native LO topology, hardware ownership, pending-edit freshness, save/reload, experiment switching and advanced scans. This reviewer inspected those tests; the parent is responsible for their actual integrated rerun and live GUI evidence.

### Actionable integration findings

1. **P1 — external disk edits do not invalidate visible measurement freshness.** In the inspected version, `SnapshotSession.results_current()` compares only the in-memory scheme fingerprint and pending-edit flag, not the on-disk digest. A saved successful result continued returning `True` when `Path.read_bytes()` was independently mocked to return changed external bytes. The save overwrite guard is correct, but it does not satisfy the separate requirement to mark measurements stale after external JSON changes. Required correction: compare current disk identity with the session's saved disk identity, fail freshness closed if the file is missing/unreadable, and invoke the GUI freshness check on an appropriate visible refresh/focus/timer event.

2. **P2 — a failed rerun can leave a previous result eligible to reappear as current.** The worker exception path hides the result body and displays failure, but retains `last_result` and `result_fingerprint`. If the failed attempt used the same scheme as an earlier success, a subsequent `_refresh_freshness()` can reveal the old controls with a current-measurement message. The old files are valid historical records, but the UI must not silently relabel them as the failed attempt's result. Required correction: invalidate result freshness at run start or failure, or explicitly separate and label the previous successful acquisition from the failed attempt.

These two findings were sent to the integration owner. At this pass, full integration acceptance is **conditional on their resolution and the parent's live/test evidence**. No further blocking receiver-composition, hardware-parameter or units error was identified in the focused review. The audit did not expand into arbitrary malformed-file fuzzing, multi-client singleton support, or laboratory calibration.

### Targeted correction review: both findings resolved

The integration owner subsequently implemented both fixes. The reviewer inspected only the changed freshness code and the new regression, then independently verified:

- `SnapshotSession.disk_changed()` compares the current file digest and treats missing/unreadable files as changed; `results_current()` now requires that comparison to pass. Separate mocked changed-content, `FileNotFoundError`, and `PermissionError` cases all returned `disk_changed=True` and `results_current=False`.
- The GUI installs a two-second asynchronous disk watcher through `Page.run_task`. A controlled one-cycle coroutine check invoked both freshness refresh and the external-edit warning while preserving the pending-edit flag. This tests callback logic; the parent's live GUI check remains the evidence for actual timer delivery in the running application.
- A new run invalidates the previous result fingerprint. Worker failure clears the old result, fingerprint and output paths, preventing a later freshness refresh from reviving the failed attempt's predecessor.
- `ExtensionContracts.test_external_edit_and_failed_run_cannot_resurrect_old_measurements` passed independently in 8.561 s. Its printed `Deliberate test failure` traceback is the intentionally injected worker error, followed by a passing assertion that old measurements remain hidden and cleared; it is not an unhandled test failure.

**Resolution:** the P1 and P2 findings above are closed at code/regression level. No remaining blocking issue was identified within this focused integration scope. Scientific acceptance is unchanged. Final full-suite and live-GUI evidence, including actual external-file-change notification, remain the integration owner's completion gates.

## Final integrated M8 sign-off

Final inspection at 2026-09-05 22:32:21 UTC / September 6 Europe/Berlin closes the prior integration conditions. The detailed original M0–M8 and expanded M8 acceptance mapping, independent new-effect calculations and dated resolutions are recorded in [completion-audit.md](completion-audit.md); [m8-verification.md](m8-verification.md) links the actual saved executions and live screenshots.

Evidence independently inspected includes:

- The final **105-test PASS** report/log, with zero failures/errors/skips at 2026-09-05T22:22:22.905481Z (206.7715 s), rather than the earlier 35- or 95-test snapshots.
- Actual external-file-change/stale GUI evidence and the previously independently tested failed-run invalidation fixes.
- The native homodyne apparatus, actual phase edit/save/reload/run snapshots and two 251-point outputs: approximately 1.783–1.786 V at phase zero versus maximum absolute mean $1.094\times10^{-16}$ V at 90 degrees, with exactly unchanged variance for the selected phase-insensitive output.
- Live coupled-transient summary, loaded optical/acoustic maps and refinement plots, plus regenerated unscaled/stronger examples with explicit absolute/relative RMS acceptance and transit/acoustic/FM time counts.
- Real acquisition-time MZM/IQ drift and deterministic shared-source RAM, their saved GUI controls, executed 251-point result, 251 bias-history rows, 2048 delayed intensity rows and 200 Fourier-normalization rows. These effects are not static bias errors or stochastic RIN under different labels.
- Independent numerical RAM/DC/tag and drift-calibration checks, followed by **28 passing nonideal/export tests** and **six passing dynamics tests** run by this reviewer. Signed Fourier order, physical mean-product normalization, weak-gain limits, actual drifting power/depletion diagnostics, frozen-dwell/gain approximations and noise limitations are explicit.
- Final manifests with existing absolute targets and exact input snapshots; actual current JSON restoration to zero drift/RAM and zero LO phase; corrected operational documentation and bounded scientific claims.

**Final recommendation: accept the implemented M8 extensions and their integrated GUI/CLI workflows within the documented approximate models. No unresolved blocking review finding remains.** All nine original extension topics are covered, with the source ambiguity and model assumptions retained rather than hidden. This is numerical/software acceptance, not a proof of calibrated candidate hardware, a full quantum-SBS scattering model, an experimental phase-lock system, global measurement optimality or genuine quantum advantage. The earlier conditional paragraphs are historical review stages, not currently open defects.
