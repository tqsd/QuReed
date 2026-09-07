# BOCDA source and convention audit

Date: 2026-09-05. Status: **SUPPORTED source interpretation; NUMERICAL model checks.**

Question: which experimental parameters can be attributed to Popp et al., and what frequency-excursion and resolution conventions can a reproducible model use?

This audit read the original local PDFs, rather than treating earlier conversational answers or the generated equipment notes as primary evidence. PDF page numbers below count the cover as page 1; thesis printed page numbers differ by 18. The model remains exploratory SCRATCH work and is not a calibrated reconstruction of the experiment.

## Authoritative sources

1. A. Popp, F. Sedlmeir, B. Stiller and C. Marquardt, *Eavesdropper localization for quantum and classical channels via nonlinear scattering*, Optica Quantum 2, 21-27 (2024), [DOI 10.1364/OPTICAQ.502944](https://doi.org/10.1364/OPTICAQ.502944). Local source: [paper.pdf](<//nas.ads.mwn.de/ge85yix/TUM-PC/Desktop/Marquadt/paper.pdf>). Inspected PDF pages 2-3, printed pages 22-23, including equations (2)-(3) and figures 2-3.
2. Alexandra Popp's dissertation, local source [21883_Diss_PoppAlexandra.pdf](<//nas.ads.mwn.de/ge85yix/TUM-PC/Desktop/Marquadt/21883_Diss_PoppAlexandra.pdf>). Inspected the BOCDA derivation and characterization in chapters 7-8, especially printed pages 70-76, 84, 86-90. Figure 8.3a on printed page 87/PDF page 105 was rendered and visually inspected to check its frequency axis.

The equipment notes in the source directory are useful navigation aids but do not independently establish experimental facts. Candidate manufacturers and catalog model names remain the user's proposed hardware unless a primary source explicitly identifies them.

## Parameter ledger

| Quantity | Source evidence | Model treatment |
|---|---|---|
| CW pump and probe from one FM laser | Paper printed pp. 22-23, figures 2-3; thesis chapter 8 | Common deterministic FM history; no pulsed time-of-flight localization |
| Master laser AA1406, Gooch & Housego | Thesis printed p. 86/PDF p. 104 | Verified identity; dynamic tuning response is not inferred from an alternative laser's linewidth |
| $f_m=699$ kHz | Paper p. 23; thesis p. 86 | Verified reported operating rate |
| $\Delta f=47$ GHz | Paper p. 23; thesis p. 86 and figure 8.3a p. 87 | Verified reported number; interpretation discussed below |
| $\Delta\nu_B=27$ MHz | Paper pp. 22-23; thesis pp. 72, 75-76 | Underlying gain FWHM in hertz; not guaranteed measured spectrum FWHM |
| Probe offset 10.6-11.1 GHz | Paper p. 23 | Verified reported sweep interval |
| Pump intensity tag 100 kHz | Thesis p. 84/PDF p. 102 | Verified actual tag; distinct from 699 kHz laser FM |
| Pump and probe EDFA maxima 4 W and 1 W | Thesis p. 84 | Amplifier maxima, not evidence of actual operating input powers for our short demo |
| Polarization randomizer 700 kHz | Thesis p. 84 | Actual source nonideality; baseline effective overlap is an explicit simplification |
| External path-length difference 25,145 m and correlation order 84 | Thesis p. 90/PDF p. 108 | Reported values; demo can use a separately documented geometry |
| Correlation spacing 146 m | Paper p. 23 | Reported rounded spacing; not fiber-under-test length |
| Correlation spacing 148.6 m | Thesis p. 86 | Different reported value; do not silently merge with 146 m |
| Nominal resolution 3.0 cm | Paper p. 23; thesis p. 86 | Reported nominal estimate; not a required numerical FWHM |
| Four 10 cm segments; inserted resonance shift | User-approved demonstration plan | Assumed demonstration geometry, not original experimental apparatus |

Other defaults, including group velocity, powers, per-length gain, detector gain, lock-in time constant and modulation depth, require explicit units and an assumed/derived label. Absolute calculated volts are not calibrated experimental predictions.

## Why 47 GHz is not an unambiguous peak deviation

The implementation uses the unambiguous physical definition

$$
\nu_L(t)=\nu_0+D\sin(2\pi f_m t+\phi),
$$

where $D$ is the **peak frequency deviation** in hertz. The full frequency excursion is $2D$. This definition should be displayed alongside the editable convention selector.

Thesis p. 70 describes its symbol $\Delta f$ as an amplitude. However, p. 86 describes the measured 47 GHz as a sweep bandwidth. The rendered figure 8.3a on p. 87 visibly occupies about 193.617-193.665 THz, a **total span** of approximately 47 GHz. The latter supports the default interpretation $2D=47$ GHz, hence $D=23.5$ GHz.

There are normalization inconsistencies in the source equations: a conventional difference of two equally modulated frequencies has amplitude $2D\sin(2\pi f_m z/v_g)$ around a zero-delay reference, whereas paper Eq. (2) has coefficient $\Delta f$ after conversion from angular frequency to hertz. That expression agrees with $\Delta f=2D$. The thesis derivation around Eqs. (7.3) and (7.15)-(7.16) also does not consistently maintain a factor of two. Therefore the text label alone cannot establish that 47 GHz was a physical peak deviation.

**Recommendation:** default to `excursion_hz = 47e9` with `excursion_convention = peak-to-peak`, based on the measured spectrum; retain a visible `peak` alternative to examine sensitivity. This is a supported interpretation with a documented source ambiguity, not a new measurement or a definitive correction of the experiment.

## Linewidth and spatial width are different conventions

Thesis Eqs. (7.7) and (7.19) use the Lorentzian

$$
L(\delta)=\frac{1}{1+(2\delta/\Delta\nu_B)^2}.
$$

Its frequency FWHM is $\Delta\nu_B$. The experimentally collected spectrum also integrates off-peak contributions and can be wider or asymmetric. Thesis p. 75 explicitly shows such broadening even in its simulation; p. 90 attributes experimental asymmetry to residual laser amplitude modulation and AM/FM phase offset. A single Lorentzian fit is therefore an estimator with a quality flag, not an exact description of every local spectrum.

Thesis p. 72 defines its spatial resolution using the half-height positions $z=\pm\Delta z$, while the reported compact formula is commonly treated as a resolution length:

$$
d_{\rm corr}=\frac{v_g}{2f_m},\qquad
\delta z_{\rm nominal}=\frac{v_g\Delta\nu_B}{2\pi f_m D}.
$$

The project's `approx_resolution_m` is this explicitly defined formula using physical peak $D$. It must not be presented as the measured spatial FWHM or as an exact transcription of every source convention.

Independent numerical checks of the implemented acoustic Floquet spatial response, using $v_g=2.04\times10^8$ m/s and the other baseline values, give:

| Interpretation of entered 47 GHz | Physical $D$ | Nominal formula | Calculated point-response FWHM |
|---|---:|---:|---:|
| Peak-to-peak, default | 23.5 GHz | 5.3367 cm | 4.6218 cm |
| Peak, comparison | 47 GHz | 2.6683 cm | 2.3109 cm |

Both give a correlation spacing of 145.9227 m. These FWHM values describe an ideal local on-resonance response; an edge response, finite perturbed segment, reconstructed profile, or fitted measured spectrum has its own width. The source's nominal 3 cm is preserved as provenance, not imposed by adjusting the model.

## Delay and scan interpretation

Let the pump enter at $z=0$, the probe at $z=L$, and define $\tau_{\rm ext}$ as the signed difference of their external FM propagation delays. Then

$$
\Delta\tau(z)=\tau_{\rm pump}(z)-\tau_{\rm probe}(z)
=\tau_{\rm ext}+\frac{2z-L}{v_g}.
$$

Correlation occurs when $f_m\Delta\tau=k$ for integer $k$. Holding external delay fixed, a requested target $z_0$ maps to

$$
f_m(z_0)=\frac{k}{\tau_{\rm ext}+(2z_0-L)/v_g}.
$$

For $k=0$, changing $f_m$ cannot move the equal-delay point. This is why a frequency-scanned demo needs a nonzero order and explicit delay. The thesis's reported large imbalance and high order demonstrate that idea, but its particular raw path-length value should not be substituted into a different coordinate convention without calibration.

Lowering $f_m$ increases spacing and broadens the ideal response at fixed physical excursion. A source-equivalent hardware scan would additionally need the actual frequency-dependent laser tuning response: thesis p. 86 states that its available excursion varies nonlinearly with modulation rate.

## Open questions and handoff

- Raw laser tuning calibration and the source's intended width conventions would be needed to remove the 47 GHz ambiguity conclusively.
- Demonstration optical losses, effective gain, power levels and receiver settings must retain their assumed status.
- The short four-segment model does not recreate the complete auxiliary fiber, residual AM, filtering, polarization scrambling or environmental drift of the source experiment.
- Source facts above can establish provenance. Completion of GUI persistence, numerical convergence, fitting and scans requires separate execution evidence.

Recommendation: **approve the explicit-convention demonstration plan, with these caveats; reject an unqualified claim of exact 3 cm or full experimental reproduction.**
