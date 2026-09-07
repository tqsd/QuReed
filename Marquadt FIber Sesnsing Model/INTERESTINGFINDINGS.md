# Interesting findings

## 2026-09-05 — Source bandwidth and spatial-width conventions

Status: SUPPORTED source interpretation / NUMERICAL model check.

The thesis measured spectrum supports 47 GHz total span, whereas some equations/prose use inconsistent amplitude normalization. The resulting default dynamic local-response FWHM is about 4.62 cm, distinct from the reported nominal 3 cm and the conventional 5.34 cm estimate. Source and calculation are not forced to agree.

Evidence: [M0 source audit](docs/source-audit.md), [M3 physics review](docs/physics-review.md), [spatial response data](results/scan/spatial_response.csv).

Why it matters: choosing peak versus total-span silently changes the predicted width by a factor of two.

Suggested next step: retain the convention selector and verify the experimental laser's measured frequency excursion before laboratory-equivalence claims.

## 2026-09-05 — Boundary spectra cannot be read as a single material value

Status: NUMERICAL.

Physical off-peak background and boundary mixing can shift a whole-spectrum Lorentzian fit. The implementation retains measured spectra, uses a local fit with linear background, and reports ambiguity flags rather than directly assigning the target segment's resonance.

Evidence: [M5 reconstruction](results/scan/profile_map.png), [M3-M5 derivation and failed fit route](docs/physics.md).

Why it matters: a smooth fitted profile or small grid spacing is not evidence of better sensing resolution.

Suggested next step: inspect full spectra and flags at fiber boundaries before interpreting a fitted resonance as a unique local material property.
