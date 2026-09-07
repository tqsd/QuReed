# Optional nonideal optical and receiver model

Status: NUMERICAL, exploratory SCRATCH implementation. Updated: 2026-09-06. See the independent physics review for audited formulas; numerical checks do not establish calibrated predictions for a particular instrument.

`bocda_model.nonideal.simulate_nonideal(config, options, mode, progress)` produces the same spectrum/profile fields as the classical engine and a `nonideal` block containing the complete options, effective configuration, component diagnostics, and stochastic traces. `default_options()` and `schema()` expose flat persisted GUI controls. `enabled=false` returns the unchanged classical calculation. This extension remains in the weak-SBS, first-order intensity-tag regime. The separate `dynamics` model supplies optical pump depletion and transient acoustics.

## EOM transfer, sidebands, and RF errors

The pump Mach-Zehnder intensity transfer is actually sampled over one RF cycle:

$$
T(\theta)=\epsilon+(1-\epsilon)\cos^2\!\left[{\pi/2+b-m(1+a)\cos(\theta+\phi)\over2}\right],
\qquad\epsilon=10^{-ER/10}.
$$

Here $b$, $a$, and $\phi$ are editable bias, RF amplitude, and RF phase errors. The mean transmission adjusts the configured quadrature insertion loss; a Fourier transform supplies the actual relative fundamental and phase. Higher harmonic RMS and the transfer waveform are exported. The receiver calculation retains the fundamental only, consistent with the baseline's small-tag approximation and harmonic-overlap guard. Large effective depth above0.3 is rejected rather than interpreted as an exact large-signal lock-in model.

The probe IQ field is sampled as

$$
E(\theta)=\cos[\pi/2+b+d\cos\theta]
-i\cos[\pi/2+b+d(1+a)\sin(\theta+\phi)]
+\sqrt\epsilon.
$$

Its Fourier powers supply the lower sideband, residual carrier, upper sideband, and small higher sidebands. These fractions are normalized to the total power fixed by the configured probe insertion loss. The raw transfer mean and retained fraction are exported so normalization is explicit. This is a defined idealized IQ transfer, not a manufacturer's complete electrode model.

Negative optical sideband order is below the pump and produces Stokes gain. Positive order is above the pump and produces anti-Stokes loss. For order $n\ne0$, the local detuning is $|n|\nu_{\rm RF}-\nu_B$, with signed contribution $-\operatorname{sgn}(n)$ times its optical-power fraction. The carrier contributes to detected baseline/noise but not resonant SBS. Equal lower/upper sidebands cancel the first-order SBS response in the symmetric model; a dedicated test enforces this. Treating the upper sideband as negligible far-detuned gain was rejected in independent review and corrected. A microwave calibration error shifts the physical frequency axis relative to the displayed command.

## EDFA compression, dynamics, and ASE

The EDFA gain follows a defined phenomenological relaxation model,

$$
\dot G=[G_{\rm eq}(P_{\rm in})-G]/\tau_g,\qquad
G_{\rm eq}(P)={G_0\over1+G_0P/P_{\rm sat}}.
$$

The exported `edfa_trace` integrates this equation with frozen-input exact exponential steps, showing gain relaxation and the modulated output. The scan uses the steady mean compressed gain and its linearized tag response. Writing $s=G_0\bar P/P_{\rm sat}$ gives

$$
{m_{\rm out}\over m_{\rm in}}=
1-{s\over1+s}{1\over1+i\Omega_a\tau_g}.
$$

This is an actual dynamic gain state and a documented saturation law; it is not a full spatial erbium-population/pump-wavelength rate-equation model. The transient trace and steady spectrum are distinct outputs: a spectrum does not implicitly include arbitrary amplifier turn-on history.

ASE uses the high-gain noise-figure approximation $NF=2n_{sp}$. The per-polarization one-sided optical spectral density is $S_{ASE}=n_{sp}h\nu(G-1)$, and two independent polarizations contribute total power $2S_{ASE}B_o$. The ASE optical bandwidth is the **total equivalent noise bandwidth of the receiver's passed bands**. Flat local ASE density is assumed around both detected coherent carriers; these can be separate passbands. This is not asserted to be a single rectangular filter centered on the probe that also passes the pump 10.9 GHz away. The separately configured circulator isolation sets net coherent pump leakage and ASE coupling into the receiver. A real optical filter's additional pump rejection must be folded into this effective leakage setting.

The receiver adds signal–ASE beat PSD $4\mathcal R^2(P_s+P_{\rm leak})S_{ASE}$ and two-polarization ASE–ASE PSD $4\mathcal R^2S_{ASE}^2B_o$, with the appropriate leakage factors. Coherent pump leakage therefore contributes to its own ASE beating as well as shot noise. These are high-photon-count classical photocurrent noise terms. No additional quantum-vacuum variance is added to the same receiver calculation. Pump ASE redistribution into broadband SBS gain and finite-gain noise-figure corrections are not modeled.

## Shared-source phase and intensity fluctuations

A source Wiener phase has

$$
\operatorname{Var}[\phi(t+u)-\phi(t)]=2\pi\Delta\nu_L|u|.
$$

The exported source trace samples **one** phase process at the pump and probe retarded times, not two independent lasers. Equal delays cancel relative phase exactly. Its expected beat phase variance is $2\pi\Delta\nu_L|\tau_p-\tau_s|$; the finite sample estimate is exported separately and is not expected to equal the ensemble number exactly.

The spectra use the analytic ensemble response for that same process. With $T=|\tau_p-\tau_s|$, the beat coherence is

$$
C(u)=\exp[-2\pi\Delta\nu_L\min(|u|,T)].
$$

For $a=\gamma+i\omega$, $b=a+2\pi\Delta\nu_L$, the acoustic susceptibility is

$$
H_{\rm noise}(\omega)=\gamma\left[{1-e^{-bT}\over b}+{e^{-bT}\over a}\right].
$$

This yields perfect common-phase cancellation at $T=0$ and Lorentzian FWHM $\Gamma_B+2\Delta\nu_L$ for long delays. Each Bessel sideband and tag susceptibility uses this response. The long-delay expression is used only when the discarded transient factor is below $e^{-24}$ throughout a segment; otherwise each cell's actual delay is evaluated. No arbitrary interpolated linewidth is used.

Fractional intensity noise is a shared stationary OU process with corner frequency $B_R$ and one-sided low-frequency PSD $S_R$. Its variance is $S_R\pi B_R/2$. Delayed lognormal intensity multipliers preserve positivity and are exported alongside phase. Linear interpolation between finite trace samples introduces a sampling approximation; decreasing trace timestep resolves it. Variance above0.1 is rejected to stay within the spectrum's small-noise regime.

The receiver's RIN includes the shared-source cross term. In the slow-tag approximation its relative transfer is

$$
(1+G)e^{-i\Omega_aL/v_g}+G_{ac}e^{-i\Omega_a\tau_{ext}},
$$

where $G_{ac}$ already contains the cellwise pump-to-cell-to-receiver phase. The code also multiplies the pump-derived term by the EDFA's fractional gain response at the tag frequency and adds the coherently delayed leaked-pump RIN amplitude before squaring. Squaring the complex sum retains pump/probe/leakage correlations. The illustrated trace is one realization; it does not drive the ensemble-averaged phase kernel sample by sample. The result therefore combines an ensemble optical spectrum with a reproducible receiver-noise realization, and labels that distinction.

## Polarization and detector

An OU-distributed spatial relative Jones angle has editable RMS and correlation length. The coupling overlap is $\cos^2[\arccos\sqrt{\eta_0}+\theta(z)+A\sin(2\pi f_st)]$. Its finite-dwell average is evaluated analytically through the Bessel expansion of $e^{2iA\sin\phi}$: each harmonic receives $e^{in\Omega_st_{mid}}\operatorname{sinc}(nf_sT_{dwell})$. This removes fixed-sampling aliases even when many scrambling cycles fall in one dwell. Slow scrambling can still change across a sweep and distort the measured profile. This is an explicit scalar relative-polarization model, not a coupled random Jones-matrix propagation solver. The angle, unscrambled overlap, and dwell-averaged overlap for each scan position are exported. The spatial polarization discretization still needs refinement.

Shot-current one-sided PSD is $2e\mathcal RP$, electronic ASD is input-referred, and the detector transfer is the configured one-pole response at the tag frequency. Shot/RIN/electronic/ASE PSDs are combined before transimpedance and bandwidth scaling. A cascaded RC lock-in is sampled using its **exact discrete Gaussian covariance**, obtained from the continuous Lyapunov equation and matrix exponential. X and Y use independent baseband noise realizations. For one RC stage and one-sided pre-mixer voltage PSD $S_V$, each peak-amplitude quadrature has stationary variance $S_V/(2\tau)$; this includes factor-two mixing correctly. States start at zero and persist between frequency dwells within a position.

Saturation clips the deterministic detector waveform to $[0,V_{max}]$ before extracting its fundamental. The clipping fraction is reported. Small-signal filtered noise is added afterward, so heavily clipped noise statistics are approximate and explicitly warned. The code does not claim an exact stochastic hard-clipping circuit simulation.

All actual nonideal gain/loss and pump-transfer bounds are checked again after sideband/polarization changes, because a small nominal overlap can be restored by scrambling. The gain bound uses the largest **individual sideband** gain, while transferred-power bounds use the sum of absolute sideband contributions. Thus equal Stokes/anti-Stokes cancellation cannot disguise strong individual interactions and evade validity checks. Signed net spectra and unsigned interaction diagnostics are both exported. The baseline spatial-response curve is kept as an explicitly identified unperturbed FM reference; nonideal phase/polarization effects appear in the measured spectra, not in that reference curve.

## Reproducibility and checks

Tests cover Mach-Zehnder extrema/fundamental, IQ sideband normalization and leakage, Stokes/anti-Stokes cancellation, gain relaxation/compression, delayed common-phase cancellation and variance, exact acoustic memory versus direct quadrature, RC noise variance, clipping, classical-disabled equality, seeded full-spectrum reproducibility, and saturation handling. All options and effective parameters travel with saved results. Default seed is2026. Independent referee checks establish formula consistency, not calibration of the candidate instruments.

## Acquisition-time EOM bias drift

Research question: how do slowly changing electrode biases alter the *actual sequence* of measured spectra, rather than merely adding an arbitrary gain error? The four additional controls default to zero, so old nonideal configurations retain the identical computation branch:

| Option | Default | Meaning |
|---|---:|---|
| `pump_bias_drift_deg_s` | 0 | Linear pump MZM phase-bias drift, degrees/second |
| `probe_bias_drift_deg_s` | 0 | Linear probe IQ phase-bias drift, degrees/second |
| `source_ram_depth` | 0 | Deterministic fractional source-intensity sinusoid depth, 0 to 0.1 |
| `source_ram_phase_deg` | 0 | RAM phase in degrees relative to the laser-FM clock |

Let $j=iN_f+k$ index position $i$ then microwave-frequency point $k$. The actual midpoint acquisition time and bias are

$$
t_j=(j+1/2)T_{dwell},\qquad b_{p,s}(t_j)=b_{p,s}(0)+\dot b_{p,s}t_j.
$$

Both EOM transfer functions above are reevaluated at these biases. The pump mean transmission and complex tag fundamental change, as do the probe carrier/sideband fractions. The probe's **total** transmitted power also changes by $\langle |E(b_j)|^2\rangle/\langle |E(b_0)|^2\rangle$: normalizing the spectrum fractions must not hide actual bias-dependent insertion loss. The configured probe insertion loss calibrates the initial bias. A calibration that would produce total transmission above unity is rejected.

EDFA mean gain starts at the initial-bias steady value. Between consecutive midpoint times it carries the state through the exact exponential update for a frozen equilibrium value,

$$
G_j=G_{eq,j}+(G_{j-1}-G_{eq,j})e^{-(t_j-t_{j-1})/\tau_g}.
$$

The tag transfer is locally linearized at that point's input power. This is a **quasistatic within-dwell and piecewise-frozen-equilibrium approximation**, not a continuously integrated modulator/drift/acoustic transient. The implementation bounds bias change to 0.1 degree per dwell and, for pump drift, per EDFA relaxation time. It also enforces the complete scan's bias range, effective tag depth, optical transmission, EDFA peak-power, individual SBS gain, and actual per-point pump-transfer bounds. Slow drift chronology continues across positions; the inherited receiver-filter reset convention at a new position remains explicit. At most 25,000 drift acquisition points are allowed.

`nonideal.bias_history` and `nonideal_bias_drift.csv` retain all midpoint times, positions, commanded frequencies, biases, transmitted powers, EDFA gains, complex tag coefficients, and optical sideband fractions. `nonideal_bias_drift.png` visualizes them. Initial-bias static component panels and the static power budget are not relabeled as time histories. The reported maximum estimated depletion uses actual drift-dependent powers.

## Deterministic FM-linked residual intensity modulation (RAM)

Definitions: the common source intensity multiplier has mean one,

$$
I_L(t)=1+r\cos(\Omega_m t+\psi),\qquad0\le r\le0.1,
$$

whereas stochastic RIN is the separate OU noise process described above. The physical source FM phase is $\phi_L(t)=-(D/f_m)\cos(\Omega_m t+\phi_0)$, so its frequency deviation is $D\sin(\Omega_m t+\phi_0)$. Here $D$ is the **physical peak** excursion, half an entered peak-to-peak span. Pump/probe retardations are

$$
\tau_p=\tau_{ext}+z/v_g,\qquad \tau_s=(L-z)/v_g.
$$

Thus the dimensionless acoustic beat drive is actually constructed over a period:

$$
u_z(t)=\sqrt{I_L(t-\tau_p)I_L(t-\tau_s)}
\exp\{i[\phi_L(t-\tau_p)-\phi_L(t-\tau_s)]\}.
$$

Writing $\theta=\Omega_mt$, its phase is $-\beta_z\sin[\theta-\Omega_m(\tau_p+\tau_s)/2+\phi_0]$, with signed $\beta_z=2D\sin[\pi f_m(\tau_p-\tau_s)]/f_m$. Integer correlation-order parity must be retained: the symmetry of $J_n^2$ previously concealed that sign, but FM–RAM weights are generally asymmetric.

Define signed Fourier amplitudes by $u_z(t)=\sum_n c_n(z)e^{in\Omega_mt}$. Solving the linear damped acoustic equation mode by mode gives the cycle-averaged weak-SBS response

$$
R_z(\delta)=\sum_{n=-N}^N |c_n(z)|^2\operatorname{Re}H_{noise}(\delta+n f_m).
$$

The low-frequency intensity-tag response uses the same weights on

$$
K(\delta)=\tfrac12\operatorname{Re}H_{noise}(\delta)
+\tfrac14[H_{noise}(\delta+f_a)+H_{noise}(\delta-f_a)^*].
$$

This retains acoustic lifetime and the existing resolved/nonoverlapping FM/tag-harmonic condition. Anti-Stokes optical components conjugate the beat, reversing the signed Fourier weights before the negative loss contribution is applied. No target-window mask or additive artificial resonance is used.

The weights **must not be rescaled to unity**. Parseval's identity gives the physical normalization

$$
\sum_n|c_n|^2=\langle I_L(t-\tau_p)I_L(t-\tau_s)\rangle
=1+\tfrac12r^2\cos[\Omega_m(\tau_p-\tau_s)].
$$

For zero FM deviation and equal delays, $u=I_L$, so the only coefficients have powers $1,r^2/4,r^2/4$ at orders $0,\pm1$. This is an explicit nonzero-RAM limiting test. An asymmetric FM–RAM test compares the Fourier prediction with a separately integrated complex acoustic ODE, and deliberately reversing the coefficients fails that test. Fourfold/eightfold phase oversampling is compared. Independent referee ODE calculations confirm the sign and tag convention, providing numerical evidence rather than an experimental calibration.

Resource limits are checked before Fourier grid allocation: at most 32,768 phase samples, two million cell–phase samples, and two million signed-order–frequency response samples. The coefficient sum must agree with its analytic mean-product value to $10^{-8}$. The zero-RAM path uses the existing Bessel calculation directly for exact legacy recovery.

### Declared RAM approximations and rejected regimes

The deterministic acoustic forcing is period-averaged from the actual shared intensity histories. The EDFA is allowed only when its fractional gain response correction at $f_m$ is at most 1%, so the source's RAM waveform remains a valid approximation after amplification. Its mean-compression and receiver-noise calculations retain the small-depth expansion, whose neglected mean-compression terms are of order $r^2$; this is not an exact erbium population solution with RAM.

The deterministic RAM-only current is at the FM harmonics and is excluded from the resolved slow lock-in channel. The model conservatively requires enough detector headroom for the RAM plus tag envelope and rejects potentially clipped RAM cases, rather than silently applying a tag-only clipping waveform. Combined source RAM/tag and drift peaks must also satisfy the EDFA ceiling.

The stochastic receiver PSD remains the declared slow, leading-order calculation; it is **not a full cyclostationary RIN propagation model**. For source RIN $S_R(f)$, omitted direct multiplicative-RAM mixing contributes a leading fraction

$$
\epsilon_{mix}=\frac{r^2}{4}\frac{S_R(f_a+f_m)+S_R(|f_a-f_m|)}{S_R(f_a)}.
$$

This contribution is estimated and exported and must not exceed 1%. This bound controls the leading direct RIN sideband mixing, not every higher-order SBS/noise correlation. Phase averaging continues to use the shared-Wiener ensemble susceptibility, independent of deterministic RAM. No total Gaussian-state claim is made about stochastic mixtures.

`nonideal.ram.source_trace`/`nonideal_ram.csv` export one deterministic source sinusoid and both actual retarded intensity histories over three FM periods. `nonideal_ram_floquet.csv` exports each target/cell's mean intensity product, summed Fourier power, spectral centroid, sampling budget, Parseval error, and leading RIN-mixing estimate. `nonideal_ram.png` displays these. The clean FM spatial-reference plot excludes RAM, drift, and other nonideal changes; the measured spectra contain them.
