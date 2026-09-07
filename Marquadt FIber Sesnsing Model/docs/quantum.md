# Selected-mode quantum and homodyne extension

Date: 2026-09-05. Role: Computational Physicist. Status: **NUMERICAL implementation, supported effective-channel assumptions, independent review required.**

Question: what states and matched homodyne statistics follow from a declared Gaussian approximation to the classical BOCDA gain, and does observing more modes improve a resource-matched measurement?

This is an additional effective model, not a claim that the classical solver determined the apparatus's full quantum scattering matrix. Code: [quantum.py](../bocda_model/quantum.py); checks: [test_quantum.py](../tests/test_quantum.py). The main agent maintains GUI/CLI integration.

## API and scope

The public default_options() and schema() functions return flat settings and GUI labels/types/units. analyze_quantum(classical_result, options) returns per-position/per-frequency quadrature and electrical moments, a selected state, channel checks, explicit modes and FI comparisons. Output arrays preserve [position][frequency] indexing. Disabled analysis does no quantum computation.

The effective channel is independent, phase-insensitive, amplitude-only and stationary after FM-cycle averaging. Its gain is $G=1+g$, where $g$ is the classical integrated weak-gain spectrum. This defines a valid amplifier and matches the classical first-order coherent power increase. It does not upgrade the weak-gain approximation to a depleted-pump quantum model.

Loss is lumped **after** the amplifier, with
$\eta_{\rm path}=P_{\rm detector,noSBS}/P_{\rm probe,input}$. A distributed amplifier/loss model can have a different noise figure despite identical mean transmission. Pump EDFA noise is not automatically inserted as Stokes-mode thermal occupation.

## Definitions and channel checks

There are finitely many optical bosonic modes, each with infinite-dimensional Fock space. No Fock cutoff is introduced: this model propagates moments, not truncated density matrices. Quadratures use $[x,p]=i$, $a=(x+ip)/\sqrt2$, vacuum covariance $I/2$ and symmetrized covariance $V$.

The total input photon budget is defined at the probe entrance:
$$
N_{\rm in}=\frac{P_{\rm probe,input}T}{h\nu_{\rm opt}},\qquad
\nu_{\rm opt}=\frac{c}{\lambda}.
$$
For a displaced squeezed vacuum, $|\alpha|^2=N_{\rm in}-\sinh^2r$; negative allocations are rejected. Its covariance is a rotated $\operatorname{diag}(e^{-2r},e^{2r})/2$. Squeezing photons are not an extra uncounted resource.

The acoustic bath uses a separate frequency:
$$
n_B=\frac1{\exp[h\nu_{\rm bath}/(k_BT_B)]-1}.
$$
Default $\nu_{\rm bath}=10.85$ GHz and $T_B=293.15$ K give an occupation between 500 and 600, not the almost empty optical thermal occupation at 1550 nm. Temperature zero is handled explicitly.

The amplifier dilation is
$$
a'=\sqrt G\,a+\sqrt{G-1}\,b^\dagger,\qquad G-(G-1)=1.
$$
For an independent thermal bath,
$$
d'=\sqrt G\,d,\qquad V'=G V+(G-1)(n_B+\tfrac12)I.
$$
Vacuum loss then gives $d''=\sqrt{\eta_{\rm path}}d'$ and
$V''=\eta_{\rm path}V'+(1-\eta_{\rm path})I/2$.

The code checks
$$
V+\frac{i\Omega}{2}\succeq0,\qquad
Y+\frac i2(\Omega-X\Omega X^T)\succeq0
$$
for $d''=Xd$, $V''=XVX^T+Y$. Photon accounting is
$$
N=\frac{d^Td+\operatorname{tr}V-M}{2}.
$$
For coherent input without a phase mixture, the output is displaced thermal with
$n_{\rm out}=\eta_{\rm path}(G-1)(n_B+1)$. Squeezed input generally produces a displaced **squeezed** thermal state. Passive mixing of unequal covariances can generate multimode correlations, not automatically entanglement or advantage.

The channel/measurement framework follows [Weedbrook et al., Gaussian Quantum Information](https://arxiv.org/html/1110.3234), sections II and V. That review uses vacuum variance 1; these equations are explicitly rescaled to vacuum variance $1/2$.

## Optical modes and the LO

The single mode is normalized over explicit duration $T$:
$$
u(t)=T^{-1/2}e^{-i\phi_{\rm probe}(t)},\quad 0\leq t<T,
$$
and zero otherwise in a carrier-rotating description. Its full optical phase history includes frequency offset, FM, delay and polarization. A homodyne LO must match all of them. An unrelated free-running CW laser is not implicitly a matched LO.

The nominal LO is assumed phase locked to that mode; unmodeled relative linewidth is **not** claimed absent experimentally. The phase_jitter_std_rad option describes unobserved quasistatic phase fluctuations, not a complete linewidth transfer function.

The explicit mode_duration_s is not silently equated to the lock-in time constant. It must fit within the frequency dwell. Temporal bins must be long compared with acoustic memory and receiver response. Fewer than ten FM cycles per bin triggers a stationary-channel warning.

Residual LO frequency error $\delta f$ has complex rectangular-mode overlap
$$
q=e^{i\pi\delta fT}\operatorname{sinc}(\delta fT).
$$
The effective power overlap is entered polarization/spatial overlap times $|q|^2$. Its phase enters the measured quadrature, including the sinc sign. Unmatched modes are vacuum ancillary modes in this model, not unspecified thermal light.

Nonzero LO detuning disables multimode FI because different bins acquire different phases. Single-mode moments still include mismatch. In this case the displayed multimode covariance is explicitly the conditional frequency-matched reference, not a mismatched receiver prediction.

## Balanced detection: finite LO and calibration

LO power is explicit and positive. The dedicated balanced receiver defaults to 1000 V/A and 10 V headroom. These are model settings, not attributed specifications of the paper's direct detector. Efficiency $\eta_d$ fixes responsivity:
$$
\mathcal R=\frac{\eta_d e}{h\nu_{\rm opt}}.
$$

Let $N_L=P_LT/(h\nu_{\rm opt})$. Let $\mu_x,V_x$ be signal quadrature moments after detector inefficiency and LO overlap. The balanced difference current averaged over the rectangle has
$$
\langle I_-\rangle=\frac eT\sqrt{2\eta_d N_L}\,\mu_x,
$$
$$
\operatorname{Var}(I_-)=
\left(\frac eT\right)^2[2\eta_dN_LV_x+\eta_dN_s]
+\frac{i_{\rm el}^2}{2T}.
$$
$N_s$ is the signal photon number **before** inefficiency and overlap loss. The $\eta_dN_s$ term is finite coherent-LO noise: dropping it wrongly removes signal shot noise. The one-sided electronic difference-current noise density $i_{\rm el}$ is in A/$\sqrt{\rm Hz}$; rectangular-average noise bandwidth is $1/(2T)$.

For coherent signal and LO the difference-count variance is $\eta_d(N_L+N_s)$, the sum of the two output Poisson means. This checks normalization independently. Voltages equal currents times dedicated transimpedance, and variances multiply by its square. These are averaged currents, **not** baseline lock-in peak phasors.

Finite-LO moments are exact under the mode model, but the full count distribution is not declared Gaussian. FI below uses the bright-LO Gaussian quadrature approximation. It is suppressed when the finite-LO variance correction exceeds 1% for any selected independent or mixed channel. This gate is not a rigorous bound on FI error.

Both individual diodes and the balanced difference are checked against headroom:
$$
I_{1,2}=\tfrac12[\eta_de(N_L+N_s)/T\pm\langle I_-\rangle].
$$
A zero balanced output therefore cannot conceal LO saturation of both diodes. The check uses DC-equivalent transimpedance voltages; a real receiver also requires verified photocurrent limits and common-mode rejection.

## Phase averaging is not generally Gaussian

For unobserved Gaussian phase angle of standard deviation $\sigma$, the code computes exact first and second moments of the mixture, including one **common** phase shared by all temporal modes. It does not declare the mixture Gaussian.

Writing $J$ for the direct sum of $90^\circ$ rotations gives the stable formulas
$$
\bar d=e^{-\sigma^2/2}d,
$$
$$
\bar V=
V+\frac{1-e^{-2\sigma^2}}2(JVJ^T-V)
+\frac{(1-e^{-\sigma^2})^2}{2}dd^T
+\frac{1-e^{-2\sigma^2}}2(Jd)(Jd)^T.
$$
They preserve photons and generate inter-bin classical correlations. Stable exponential differences and an exact zero-jitter identity avoid subtracting huge coherent second moments. Thermal rotation-invariant inputs stay Gaussian; generic displaced inputs do not. Gaussian FI is disabled for entered phase jitter.

## Resource-matched multimode comparison

The $M$ bin modes are
$$
u_j(t)=\sqrt{M/T}\,e^{-i\phi_{\rm probe}(t)}
$$
on disjoint intervals $[jT/M,(j+1)T/M)$, zero otherwise. Thus $\int u_j^*u_k\,dt=\delta_{jk}$. They are selected modes of the **same** field observed for the same $T$. Flat effective channel response and independent Markov bath modes are assumptions, not consequences of orthogonality alone.

Every comparison uses the same $M$-mode field, total incident probe photons, total LO photons, elapsed duration, gain, bath, losses, receiver bandwidth and parameter. Photon allocation is equal across bins, with squeezing photons deducted. Rectangular-bin bandwidth resource $M/(2T)$ is reported; mode count is capped and duration guards prevent treating infinitely many noise modes as free. The fixed analog receiver bandwidth is the same for all compared readouts.

The local parameter is a translation of the **complete** gain spectrum:
$$
G_\theta(f)=G_0(f-\theta),\qquad \partial_\theta G=-\partial_fG.
$$
It approximates a common resonance shift with bath occupation held fixed, not a fully specified temperature derivative of every material property. Derivatives come from the calculated frequency grid, not an addressed segment's resonance. Quantitative FI requires frequency-grid convergence.

Differentiating the normalized Gaussian homodyne log likelihood yields
$$
F=\mu'^T\Sigma^{-1}\mu'
+\frac12\operatorname{tr}[(\Sigma^{-1}\Sigma')^2].
$$
Displacement and covariance contributions are separate outputs. This is **classical FI of a specified measurement**, not quantum FI.

The code compares:

1. All independent temporal-bin homodyne outcomes.
2. Fixed real orthogonal beam-splitter mixing followed by joint homodyne. Mixing/LO phases are parameter independent; FI must remain unchanged.
3. One reduced mixed output, discarding the others.
4. A single collective readout: equal-weight, mean-optimal ($w\propto\Sigma^{-1}\mu'$), and covariance-optimal scalar projection candidates. The largest candidate is reported, **not** a global optimum of total scalar FI.
5. Coherent input with the same $M$, total photons, displacement phase, LO, duration and channel. Squeezing versus this reference is a preparation-resource comparison, not automatic multimode advantage.

For equal coherent channels, joint and collective-single **mean** FI agree. Joint covariance FI can be $M$ times one selected mode's contribution because other orthogonal thermal modes carry variance information. That is improved access to existing information, not information created by beam splitters or evidence of quantum advantage. At the bright baseline the covariance contribution is typically tiny compared with displacement information.

Positive joint-minus-reduced FI means reduction discarded information. A configured-minus-coherent difference may reflect squeezing allocation and phase; it is neither an optimized-protocol comparison nor an entanglement witness.

## Checks and limitations

From the model directory, use the existing parent virtual environment:

~~~powershell
& '..\.venv\Scripts\python.exe' -m unittest tests.test_quantum -v
~~~

The initial focused suite has 20 tests: vacuum/thermal amplifier limits, CP/uncertainty, squeezing photon accounting, finite-LO Poisson limits, LO phase/sinc null, phase moments against 64-node Gaussian integration, common-phase correlations, passive symplectic/photon invariance, FI against an independently sampled Gaussian score, JSON/input preservation, resource-matched FI terms, headroom, invalid observation/budget, weak-LO suppression and zero-gain FI.

At baseline 10.87 GHz, a numerical check gave $G=1.0028894$, displaced thermal occupation about 1.451, and detector quadrature variance about 1.661. For 10 mW LO, efficiency 0.8 and 1000 V/A, balanced voltage was about 1.785 V, the brighter diode DC-equivalent voltage about 5.933 V, and single-mode finite-LO variance correction about 0.240%. These are model outputs, not instrument calibration or experimental reproduction.

| Claim | Status | Qualification |
|---|---|---|
| Amplifier/loss commutator, CP and uncertainty | NUMERICAL plus channel construction | Independent referee review required |
| Coherent selected output displaced thermal | SUPPORTED within channel | Not generic jitter mixtures or squeezed inputs |
| Finite-LO current moments | NUMERICAL analytic-limit checks | Declared modes and vacuum orthogonal inputs |
| Passive joint mixing preserves measurement FI | NUMERICAL tests | Same quadratures/no discarded outcomes |
| Extra thermal modes carry covariance information | SUPPORTED within independent modes | No quantum-advantage claim |
| Full modulated SBS quantum coupling, quantum depletion or optimized multimode advantage | NOT ESTABLISHED | Requires additional physical model |

No density-matrix cutoff convergence is claimed. No non-Gaussian phase mixture is promoted to Gaussian, FI is not called QFI, and numerical comparisons are not proofs. Handoff: independent channel/normalization review and GUI/CLI tests of persisted settings.

