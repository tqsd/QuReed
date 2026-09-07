# Independent BOCDA physics review

Date: 2026-09-05. Role: adversarial referee. Status: **SUPPORTED analytical model; NUMERICAL implementation checks.**

Question: does `bocda_model/physics.py` simulate a spatially selective Brillouin measurement from common sinusoidal FM, rather than reading the requested segment's resonance directly?

Scope: review of the classical equations, normalization, limits, and standalone numerical engine. This review does not certify the GUI, the full apparatus's experimental equivalence, or quantum advantage. Source conventions and exact page references are in [source-audit.md](source-audit.md).

## Recommendation and claim ledger

**Approve the baseline physics within its stated linear-acoustic, weak-gain, first-order-intensity-tag limits.** This is not a proof of complete experimental reproduction. Check the execution and integration reports for the separate GUI and end-to-end acceptance evidence.

| Claim | Status | Basis and restriction |
|---|---|---|
| Delay-based correlation and target mapping | SUPPORTED | Explicit counterpropagation algebra; nonzero order required for frequency scanning |
| Cycle-averaged Floquet gain kernel | SUPPORTED / NUMERICAL | Linear acoustic response derivation; independent ODE agrees to below $9\times10^{-11}$ at tested points |
| First-order pump AM susceptibility | SUPPORTED / NUMERICAL | Square-root field modulation derivation; independent AM ODE agrees within $1.2\times10^{-8}$ at tested points |
| Default 47 GHz peak-to-peak interpretation | SUPPORTED, source ambiguity retained | Visually inspected thesis optical spectrum; inconsistent source normalization prevents unconditional attribution |
| Default spatial FWHM of approximately 4.62 cm | NUMERICAL | Computed point-response width, not a universal resolution theorem or reproduction of reported 3 cm |
| Full 27 MHz Lorentzian observed at every position | REFUTED as a general assertion | Spatial integration and off-peak response broaden/mix spectra; fit quality is needed |
| General nonlinear/depleted-pump dynamics | OUT OF BASELINE SCOPE | Baseline gain and AM are explicitly first order |
| Quantum output state or multimode advantage | NOT ESTABLISHED BY CLASSICAL ENGINE | Requires declared modes, environment, Gaussian channel and measurement/resource model |

No claim is labelled PROVED merely because constructive and reviewing agents agree.

## Definitions and assumptions

Use hertz for $f_m$, detuning $\delta$ and gain FWHM $\Gamma=\Delta\nu_B$. Angular frequencies carry an explicit $2\pi$. The pump enters the fiber at $z=0$; the Stokes probe enters at $z=L$. The probe frequency offset is positive when the probe is below the pump. Define $D$ as the physical peak frequency deviation, with entered peak-to-peak excursion divided by two.

The baseline assumes deterministic common sinusoidal FM, undepleted pump, local independent damped acoustic response, negligible acoustic transport over the spatial resolution, fixed effective polarization overlap, and a weak probe with first-order net SBS gain. Optical-carrier cycles need not be sampled. The receiver measures the slow intensity envelope, not the approximately 11 GHz optical frequency difference electrically.

Pump intensity is $P_p(t)=\bar P_p[1+m\cos(2\pi f_a t+\phi_p)]$, with first-order treatment in $m$. The code rejects $m>0.3$ and excessive integrated gain; these are practical domain restrictions, not exact bounds on all omitted corrections.

## Correlation geometry and sign check

Let the external delay difference be $\tau_{\rm ext}=\tau_{p0}-\tau_{s0}$. Then

$$
\tau_p(z)=\tau_{p0}+z/v_g,\qquad
\tau_s(z)=\tau_{s0}+(L-z)/v_g,
$$

$$
\Delta\tau(z)=\tau_{\rm ext}+(2z-L)/v_g.
$$

The difference between the two delayed sinusoids has magnitude

$$
A(z)=2D\sin[\pi f_m\Delta\tau(z)].
$$

Its sign only shifts the phase of a cycle average and disappears in squared Bessel weights. Reducing the phase modulo integer cycles improves numerical cancellation without changing the response. Correlation positions satisfy $f_m\Delta\tau=k$, so

$$
z_k=\frac{L+v_g(k/f_m-\tau_{\rm ext})}{2},\qquad
f_m(z_0)=\frac{k}{\tau_{\rm ext}+(2z_0-L)/v_g}.
$$

The engine implements this relation and rejects a frequency scan of order zero. Its calculation integrates every numerical cell, including neighboring segments; target selection does not directly read only the selected segment.

## Acoustic response and Floquet derivation

For a local beat with unit-magnitude modulation $b(t)=\exp[i\beta\sin(2\pi f_m t)]$, $\beta=A/f_m$, take the normalized acoustic envelope equation

$$
\dot q+[\pi\Gamma+i2\pi\delta]q=\pi\Gamma b(t).
$$

The sign convention could be conjugated consistently without changing average gain. Expanding the beat using Jacobi-Anger gives

$$
b(t)=\sum_{n=-\infty}^{\infty}J_n(\beta)e^{i2\pi n f_m t},\qquad
q(t)=\sum_n J_n(\beta)H(\delta+n f_m)e^{i2\pi n f_m t},
$$

$$
H(u)=\frac{1}{1+2iu/\Gamma}.
$$

The SBS power-transfer term is proportional to $\operatorname{Re}[b^*q]$. Averaging over the FM period removes unequal orders, giving

$$
R(z,\delta)=\sum_n J_n[\beta(z)]^2\operatorname{Re}H(\delta+n f_m)
=\sum_n\frac{J_n[\beta(z)]^2}{1+[2(\delta+n f_m)/\Gamma]^2}.
$$

Thus $R\geq0$, $R\leq1$, $R(\beta=0,\delta)=L(\delta)$, and the unweighted spectral masses obey $\sum_nJ_n^2=1$. Pairing positive and negative orders is correct only if the zero order is counted once; the implementation does so. Its normalization check prevents silent sideband truncation errors.

This is the frequency-domain acoustic model suggested by the thesis beat-spectrum convolution, with explicit normalization. It avoids an assumed Gaussian spatial window.

## Quasi-static route: useful comparison, not general justification

Replacing the acoustic dynamics by its instantaneous Lorentzian yields the average

$$
R_{\rm qs}=\operatorname{Re}\left\{\left[(1+2i\delta/\Gamma)^2+(2A/\Gamma)^2\right]^{-1/2}\right\}.
$$

At zero detuning this becomes $[1+(2A/\Gamma)^2]^{-1/2}$. The rate condition near a resonance crossing involves the detuning slew as well as $f_m/\Gamma$; a dimensionless estimate is $4f_m|A|/\Gamma^2$. Consequently, $f_m<\Gamma$ alone is not a uniform justification away from a correlation peak. The implementation uses the Floquet calculation and retains the quasi-static expression only for comparison.

For the baseline on-resonance point-response diagnostic the maximum sampled difference is approximately $1.50\times10^{-4}$. That narrow diagnostic does not imply that every off-resonance time-dependent observable is quasi-static.

## Pump tag and receiver normalization

Since the pump field is proportional to $\sqrt{P_p}$,

$$
\sqrt{1+m\cos(\omega_a t)}=1+\frac m2\cos(\omega_a t)+O(m^2).
$$

For each FM sideband with detuning $u$, the pump field contributes sidebands of amplitude $m/4$. Both the acoustic drive and its product with the optical field change. Taking the real power-transfer term yields the complex peak AM susceptibility

$$
K(u)=\frac12\operatorname{Re}H(u)
+\frac14[H(u+f_a)+H(u-f_a)^*].
$$

At $f_a\to0$, $K\to\operatorname{Re}H$, recovering a gain proportional to pump intensity. This establishes the code's factors of two and conjugation. The pump propagation followed by the returning probe gives a receiver tag phase $\exp[-i2\pi f_a(2z/v_g)]$; external optical/electrical routing delays can enter the separately adjustable reference phase.

The photodetector model applies its one-pole transfer $1/(1+if_a/B)$, responsivity and transimpedance. This $B$ is an assumed small-signal 3 dB bandwidth for the model, not a universal transfer function of every detector gain setting. The lock-in's factor-two IQ convention reports peak phasor volts; RMS would be peak divided by $\sqrt2$. The reference phase rotates $X,Y$ and leaves $R=\sqrt{X^2+Y^2}$ unchanged.

Cascaded first-order RC low-pass stages evolve with their exact step transition for each frequency dwell. Resetting their state at the start of every spectrum represents separately started sweeps and must remain documented. Short dwell causes real fit bias in the model rather than being silently treated as a settled measurement.

## Power integration check

For small gain, the probe output is proportional to

$$
P_{s,\rm det}^{(0)}\left[1+\sum_j\kappa_j P_p(z_j)\eta_{\rm pol}R_j\,\Delta z_j\right].
$$

The factor $P_{s,\rm det}^{(0)}$ already includes the complete passive probe transmission. In first-order gain, a locally amplified contribution has the same total input-to-output attenuation as the baseline probe, so no extra probe attenuation weighting should be duplicated inside the integral. Pump attenuation remains position dependent and is included. Segment boundaries align exactly to the integration cells.

For integrated gain $g$, replacing $e^g$ by $1+g$ neglects approximately $g^2/2$ in total power. The relative error in the SBS-only increase is approximately $g/2$. The baseline's $g\leq0.1$ restriction and $g>0.03$ warning are meaningful, but users requiring percent-level SBS amplitude accuracy should run considerably below the hard ceiling.

## Independent executable checks

The referee imported `physics.py` using the existing QuReed Python environment and independently integrated the acoustic ODE with SciPy `solve_ivp`. These checks did not reuse the Bessel sum to generate the reference values. NumPy's installed API required `trapezoid`; an initial test invocation using removed `trapz` failed and was corrected before any result was accepted.

Use phase variable $x=2\pi f_m t$, integrate from $0$ to $20\pi$ with `rtol=1e-9`, `atol=1e-11`, maximum step 0.02, and trapezoid-average the last period at 8193 points. Parameters: $f_m=699$ kHz and $\Gamma=27$ MHz.

| $\beta$ | $\delta$ | ODE average | Floquet result | Absolute difference |
|---:|---:|---:|---:|---:|
| 0 | 0 MHz | 1.000000000000 | 1.000000000000 | $1.11\times10^{-16}$ |
| 5 | 10 MHz | 0.650946574158 | 0.650946574162 | $3.74\times10^{-12}$ |
| 30 | 0 MHz | 0.541322073249 | 0.541322073160 | $8.86\times10^{-11}$ |
| 100 | 30 MHz | 0.206215855298 | 0.206215855327 | $2.88\times10^{-11}$ |

A separate AM check used the exact drive $\sqrt{1+10^{-3}\cos x}$ at $f_a=100$ kHz, solved the acoustic ODE, and extracted the first harmonic of $\operatorname{Re}(b^*q)$. It agreed with $K$ within $1.17\times10^{-8}$, $3.43\times10^{-10}$ and $4.90\times10^{-9}$ for detunings 0, 10 and 30 MHz. This independently checks peak normalization and quadrature sign in the small-modulation limit; it does not prove finite-depth accuracy at the allowed maximum.

The point-response FWHM is 4.6218047 cm with 47 GHz peak-to-peak excursion, or 2.3109023 cm if 47 GHz is chosen as peak deviation. The nominal formula gives 5.3366537 cm or 2.6683269 cm respectively. These are distinctly labelled outputs, not quantities forced to coincide.

## Limitations and requested follow-through

1. FM-cycle averaging assumes the lock-in isolates the tag from FM harmonics. Lowering $f_m$ can bring $nf_m$ close to $f_a$ or $2f_a$, admitting additional first-order mixing paths. Guard or warn for these cases using the receiver's averaging scale; the baseline rates are well separated.
2. The direct Bessel sum has an explicit interactive resource limit. At the baseline excursion a full correlation-period fiber can require tens of thousands of sidebands, exceeding that limit. Periodic geometry alone is not evidence that arbitrary long multi-peak fibers can run. Demonstrate multiple peaks in a tractable lower-excursion fixture and document the limit, or provide a separately validated high-bandwidth solver.
3. Local linewidth variation makes a single mean-linewidth spatial FWHM a reference diagnostic, not the exact spatial resolution everywhere. The result view should retain that qualification.
4. Finite source linewidth, shared phase noise, residual AM, EOM leakage, EDFA ASE, polarization variation and coherent optical leakage are absent from the baseline. Zero pump AM eliminates the ideal SBS tag, but would not eliminate every possible real detector background.
5. Convergence of spatial and frequency grids, recovery of the altered segment, and comparison of GUI versus CLI need the dedicated end-to-end tests. The narrow checks here do not replace them.

## Scientifically bounded quantum extension

This section is a recommendation for an optional extension, not a claim that the classical calculation alone produces a quantum state. Specify a finite set of optical bosonic modes, each with infinite-dimensional Fock space, and quadratures $[x,p]=i$ with vacuum covariance $I/2$. No entropy or logarithm convention is needed unless such quantities are introduced.

A justified effective phase-insensitive amplifier channel for a selected Stokes mode has

$$
a_{\rm out}=\sqrt G\,a_{\rm in}+\sqrt{G-1}\,b^\dagger,
$$

where $G\geq1$ and the independent acoustic/environment mode has thermal occupation

$$
n_B(T)=\left[\exp\left(\frac{h\nu_B}{k_BT}\right)-1\right]^{-1}.
$$

Commutation is preserved because $G-(G-1)=1$. A thermal environment gives Gaussian covariance noise $(G-1)(n_B+1/2)I$, so

$$
d_{\rm out}=\sqrt G\,d_{\rm in},\qquad
V_{\rm out}=G V_{\rm in}+(G-1)(n_B+1/2)I.
$$

For coherent input, the selected output is a displaced thermal state with $n_{\rm out}=(G-1)(n_B+1)$. Loss of transmissivity $\eta$ subsequently maps $d\mapsto\sqrt\eta d$ and $V\mapsto\eta V+(1-\eta)I/2$. At $G=1$ a coherent input remains coherent, and at zero-temperature bath the amplifier still adds the required spontaneous noise. These tests check channel normalization and the uncertainty principle, not quantum advantage.

To turn input watts into coherent amplitude, define an actual temporal mode and duration $T_m$, e.g. $|\alpha|^2=PT_m/(h\nu_{\rm opt})$ for the selected normalized mode under the stated waveform assumptions. Do not automatically equate a lock-in time constant with that mode duration. Homodyne requires an LO matched to the shifted probe's optical frequency, FM history, polarization and delay, with explicit phase.

Independent per-mode effective channels can be simulated and optionally mixed by a declared passive unitary. That is not the complete frequency-coupling map of SBS driven by a modulated pump. Arbitrarily splitting a signal into more modes does not establish improved information per photon or genuine multimode advantage. Any information comparison must use the same photon budget, acquisition time, parameter and measurement assumptions; correlations from shared technical fluctuations must be included only with a justified stochastic model.

The quantum recommendations are analytically supported under the stated channel assumptions; they are not independently validated code until a separate extension implementation and channel-physicality tests exist.
