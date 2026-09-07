# Numerical BOCDA model: assumptions, derivation, and checks

Date: 2026-09-05. Role: Computational Physicist. Status: NUMERICAL / supported within the stated approximate equations; not experimental validation or a proof of paper reproduction. Independent review belongs to `physics-review.md`.

Research question: can physically delayed common sinusoidal frequency modulation produce a localized Brillouin sensing response in a chain of editable fiber segments, and can a direct-detection lock-in recover the deliberately altered material resonance?

The implementation is `bocda_model/physics.py`. The GUI and command-line runner call the same `simulate(config, mode='local'|'scan', progress=None)` function. All returned arrays are ordinary lists, all units appear in field names, and no random process is used.

## Definitions and provenance

The laser frequency is

$$
\nu_L(t)=\nu_0+D\sin(2\pi f_m t+\phi_0),
$$

where $D$ is explicitly the **peak** frequency deviation, in Hz. `excursion_convention='peak-to-peak'` converts the entered span to $D$ by dividing by two. The alias `peak_to_peak` is also accepted. `peak` uses the entered number unchanged. The common phase $\phi_0$ cancels from complete-period averages; changing it has no effect in this model.

The reported 47 GHz value has conflicting amplitude/span wording in the supplied source materials. The independently inspected thesis sweep figure spans approximately 47 GHz in total; the project therefore uses 47 GHz peak-to-peak provisionally. This yields $D=23.5$ GHz. It must not silently be relabelled 47 GHz peak to match the quoted 3 cm resolution. See `source-audit.md` for source evidence and qualifications.

The 27 MHz Brillouin linewidth $\Gamma_B$ denotes the **power-gain Lorentzian FWHM**, not acoustic amplitude HWHM. The corresponding acoustic amplitude decay rate is $\gamma=\pi\Gamma_B$ in radians/s and lifetime is $1/\gamma\simeq11.79$ ns. The nominal 699 kHz laser-FM rate, 100 kHz intensity tag, and 10.6–11.1 GHz optical offset sweep are distinct controls.

The demo's four 0.1 m segments, local resonances 10.85 GHz except for 10.90 GHz in the third segment, gain coefficients, optical powers, losses, detector properties, and receiver filtering are explicit simulation settings. They are not a calibrated set of paper instrument settings. Laser wavelength is recorded as provenance; no optical-carrier oscillations are time sampled.

## Coordinates and position selection

Let $z=0$ be the pump-entry end and $z=L$ the probe-entry end. The pump propagates to increasing $z$; the probe propagates to decreasing $z$. The optical offset is positive for pump frequency greater than probe frequency (Stokes gain). Write

$$
\tau_p(z)=T_p+z/v_g,\qquad
\tau_s(z)=T_s+(L-z)/v_g.
$$

The externally imposed source-path imbalance is $T_p-T_s=\tau_{\rm ext}$, and

$$
\Delta\tau(z)=\tau_p-\tau_s=\tau_{\rm ext}+(2z-L)/v_g.
$$

A correlation peak of integer order $k$ obeys $f_m\Delta\tau=k$. Consequently

$$
z_k={L+v_g(k/f_m-\tau_{\rm ext})\over2},\qquad
d_{\rm corr}={v_g\over2f_m}.
$$

Frequency control of a requested target uses

$$
f_m(z_0)={k\over\tau_{\rm ext}+(2z_0-L)/v_g},
$$

whereas delay control uses

$$
\tau_{\rm ext}(z_0)=k/f_m-(2z_0-L)/v_g.
$$

Order zero does not move under frequency variation and is explicitly rejected for that control mode. The demonstration uses order one and nominal external delay $1/(699\,{\rm kHz})$, placing the nominal peak at $L/2$. This is an illustrative delay geometry, not the thesis's reported long path imbalance/order. The sign of the extra source delay does not affect the averaged magnitude but must remain consistent with the target mapping.

`fixed` control leaves frequency/delay unchanged and reports the actual peak separately from the requested target. Fixed controls cannot produce a position scan. Every cell contributes; selecting a target never looks up a segment's resonance as a measurement.

## Damped acoustic response to the delayed common FM

The pump–probe instantaneous offset at each cell is the chosen mean offset plus the difference of two delayed sinusoids. A trigonometric identity gives a sinusoidal detuning excursion with signed amplitude

$$
A(z)=2D\sin[\pi f_m\Delta\tau(z)].
$$

The local optical beat therefore has phase modulation index $\beta=A/f_m$. Up to an irrelevant time origin and phase, its normalized envelope is

$$
u(t)=e^{i\beta\sin\Omega_m t}
 =\sum_{n=-\infty}^{\infty}J_n(\beta)e^{in\Omega_m t},
\quad\Omega_m=2\pi f_m.
$$

The linear, undepleted optical forcing approximation gives the acoustic equation

$$
\dot q+[\gamma+i2\pi\delta]q=\gamma u(t),
\qquad\delta=\nu_p-\nu_s-\nu_B.
$$

For each Fourier component, the dimensionless susceptibility is

$$
H_n(\delta)={1\over1+2i(\delta+nf_m)/\Gamma_B}.
$$

The cycle-averaged real optical work is $\operatorname{Re}\langle u^*q\rangle$. Orthogonality removes unequal Fourier orders, giving

$$
K_{\rm dc}(z,\delta)=\sum_{n=-\infty}^{\infty}
{J_n(\beta(z))^2\over1+[2(\delta+nf_m)/\Gamma_B]^2}.
$$

This is an acoustic-memory calculation, not an arbitrary Gaussian spatial mask or an instantaneous-detuning guess. Negative and positive sidebands are paired for computation. Bessel orders are retained through $N=\lceil|\beta|_{\max}+12(|\beta|_{\max}+1)^{1/3}+24\rceil$, and the numerical identity $J_0^2+2\sum_{n=1}^N J_n^2=1$ must hold to $10^{-8}$ at every cell. The truncation test increases $N$ by 80 and compares outputs.

All periodic peaks are naturally present in $A(z)$ and the cell sum; peaks are also explicitly reported. To prevent unbounded desktop work, the current engine rejects more than 30,000 spatial cells, more than 20,000 nonnegative sideband orders, or a weight matrix exceeding 30 million elements. A kilometer-scale full-span calculation with large $D/f_m$ can exceed these limits. This is a stated resource boundary, not a physical statement that only one peak exists.

## Quasi-static comparison and spatial resolution

For comparison only, the code evaluates the instantaneous Lorentzian averaged over a modulation period:

$$
K_{\rm qs}=\operatorname{Re}\left[
\bigl((1+2i\delta/\Gamma_B)^2+(2A/\Gamma_B)^2\bigr)^{-1/2}
\right].
$$

This comparison is not the production kernel. The dynamic and quasi-static models approach each other for slowly varying detuning. A test checks agreement near 699 kHz and disagreement when $f_m$ becomes comparable to the 27 MHz linewidth. It is insufficient to declare quasi-static validity from $f_m<\Gamma_B$ alone because a very large excursion can cross resonance rapidly.

The often quoted estimate

$$
\delta z_{\rm conventional}={v_g\Gamma_B\over2\pi f_mD}
$$

is recorded alongside a separately measured **FWHM of the local on-resonance dynamic response**. This FWHM is obtained by evaluating the acoustic kernel at offsets around an isolated correlation peak and interpolating the two half-height crossings. It is independent of numerical cell spacing and is not the width of an arbitrary GUI segment.

For $v_g=2.04\times10^8$ m/s, $f_m=699$ kHz, $\Gamma_B=27$ MHz, and 47 GHz full span, the numerical check gives peak spacing about 145.923 m, conventional estimate about 5.34 cm, and local-response FWHM about 4.62 cm. The local quasi-static limit predicts a FWHM of $\sqrt3/2$ times that conventional estimate. This distinction in width definitions does not resolve the source's amplitude/span ambiguity by itself.

Reducing $f_m$ with all other parameters fixed increases both peak spacing and response width. Longitudinal integration creates an off-peak background with long tails. A sharp material boundary therefore produces mixed spectra; no background is subtracted automatically.

## Optical integration and controlled approximation

Cells are midpoint quadrature intervals aligned exactly to every physical segment boundary. Each GUI segment has its own length, resonance, linewidth, gain coefficient, and attenuation. The common numerical cell-size limit sets the count within each segment, while actual widths sum exactly to the segment lengths.

The normalized local gain coefficient has units $(\mathrm W\,\mathrm m)^{-1}$; it incorporates effective mode area and peak material gain. Pump attenuation is integrated from the pump-entry end. The dimensionless accumulated gain is

$$
G(\nu)=\sum_j g_j\,\eta_{\rm pol}\,P_p(z_j)\,\Delta z_j\,K_{{\rm dc},j}(\nu-\nu_{B,j}).
$$

With the pump undepleted and **small total gain**, the measured probe DC power is approximated as

$$
P_{s,\rm out}\simeq P_{s,0}(1+G).
$$

The baseline $P_{s,0}$ includes probe-arm losses, total fiber attenuation, and return circulation loss. This deliberately retains first order in SBS; using $\exp(\langle G\rangle)$ would not correctly average strong time-varying gain. The implementation rejects a peak gain above 0.1 and warns when DC gain exceeds 0.03. The estimated transferred optical power must remain below 1% of pump input power. These checks bound the model domain; they are not a fully coupled pump-depletion solution.

The EDFA is constant gain only within its configured peak-power ceiling; exceeding the ceiling raises an actionable error instead of silently clipping. The ideal probe EOM represents one selected lower sideband through its insertion loss and microwave offset. EDFA ASE, finite sideband suppression, polarization scrambling, fiber reflections, and laser linewidth noise are deferred.

## Intensity tagging, detector, and lock-in

Pump power at the input is $\bar P_p[1+m\cos(\Omega_a t+\phi_p)]$, with $\Omega_a=2\pi f_a$. The beat amplitude is $\sqrt{1+m\cos\Omega_a t}=1+(m/2)\cos\Omega_a t+O(m^2)$. The acoustic sidebands at $nf_m\pm f_a$ give the first-order complex tag response per Bessel order:

$$
K_{{\rm ac},n}={1\over2}\operatorname{Re}H_n
 +{1\over4}[H(\delta+nf_m+f_a)+H(\delta+nf_m-f_a)^*].
$$

The two terms arise from modulation of the optical beat multiplying the acoustic field and modulation of the acoustic forcing itself. At zero tag frequency this reduces to $\operatorname{Re}H_n$. At exact resonance and zero FM mismatch it becomes $(1+[1+2if_a/\Gamma_B]^{-1})/2$.

The current model enforces $0\le m\le0.3$ and retains first order in $m$; higher tag harmonics are not calculated. Pump-tag propagation to the cell and then to the receiver contributes $\exp(-i\Omega_a 2z/v_g)$. The tag reference is defined at the pump fiber input. A constant external electrical/optical phase offset belongs in the editable pump/reference phase fields, so the common laser source imbalance must not be counted again in this tag phase.

The photodetector has responsivity $\mathcal R$ A/W, transimpedance $Z$ V/A, and assumed one-pole response $H_d=(1+if_a/f_d)^{-1}$. Its DC plus AC predicted peak voltage must remain below the configured voltage ceiling. The unfiltered lock-in complex amplitude is

$$
V_{XY}=P_{s,0}\mathcal R Z\,m H_d e^{i(\phi_p-\phi_{\rm ref})}
\sum_jg_j\eta_{\rm pol}P_p(z_j)\Delta z_j
 e^{-i\Omega_a2z_j/v_g}\sum_nJ_n^2K_{{\rm ac},n}.
$$

The real optical voltage convention is $\operatorname{Re}(V_{XY}e^{i\Omega_a t})$. Therefore $X$ uses a cosine reference and $Y$ uses a **negative sine** reference, with factor-two demodulator scaling. $X,Y,R$ are **peak volts**, not RMS; divide by $\sqrt2$ for sinusoidal RMS. A positive 90-degree reference rotation produces $X'=Y,\;Y'=-X$.

After reference mixing, one to four identical RC stages of time constant $\tau$ are integrated exactly during each frequency dwell by a matrix exponential. Each position starts at zero state; frequency points within a position carry the previous filter state. Results are samples at the **end** of each dwell, not averages over the dwell. Insufficient settling is reported. The physical instrument's exact digital filter can differ.

The receiver uses rotating-wave averaging: direct harmonics of laser FM are assumed rejected by the slow lock-in. If an FM harmonic approaches $f_a$ or $2f_a$ within a guard bandwidth set by dwell and lock-in time constant, simulation is rejected with an actionable error. A full time-domain receiver is required for that overlap regime. The common optical-source period average does not claim a phase-coherent mixed-frequency simulation under arbitrary commensurability.

## Inference, verification, and limits

The raw frequency spectra retain the physical off-peak background. A full-sweep Lorentzian is computed only as a global line-shape diagnostic. The reported resonance is fitted to a local Lorentzian plus linear background within $1.25\Gamma_B$ of the largest measured sample, with no use of the assigned local resonance as a fit target. Local residuals, additional prominent peaks, and disagreement between global center and sampled peak flag poor fits or boundary/background mixing. A flag is evidence of ambiguity, not a unique decomposition into multiple material modes. Uniform fibers, interior altered positions, and exact boundaries are tested separately.

An initial attempt to use a full-sweep single Lorentzian alone failed: broad modulation background displaced the apparent altered-section center by roughly 6 MHz and could label a mixed boundary spectrum as a good broad line. The current local fit retains and flags the global/background disagreement; it does not delete the background from plotted or exported measurements.

`tests/test_physics.py` covers the Lorentzian zero-FM limit, sideband normalization and truncation, quasi-static limit, acoustic tag response, target/delay periodicity, receiver state integration, peak/RMS phase convention, splitting/loss budget, source-convention width scaling, range/resolution tradeoff, uniform and altered fibers, zero gain, zero pump modulation, cell refinement, boundary mixing, repeat-run isolation, and actionable saturation/model limits. Tests are numerical consistency evidence only. An independent referee must review substantive model claims.

`bocda_model/results.py` exports complete JSON, the exact settings used, frequency/position CSV, measured spatial response CSV, local spectrum PNG, response PNG, map/profile PNG, and a static HTML report. Every plot distinguishes configured material properties from measured/reconstructed quantities.

The engine does not establish temperature versus strain uniquely; their calibration coefficients are not supplied. It does not compute thermal quantum states, shot noise, homodyne observables, multimode quantum advantage, or quantum Fisher information. Those are deferred M8 extensions.
