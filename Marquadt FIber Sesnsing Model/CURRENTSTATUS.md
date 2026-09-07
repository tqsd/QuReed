# Current status

## Updated

2026-09-06. Exploratory SCRATCH work; no formal project results promoted.

## Active work

M0–M8 are complete within the documented numerical/software scope, including all nine original advanced topics. Independent final review found no remaining blocking acceptance issue. See milestones.md and docs/m8-verification.md.

## Progress

- Connected 19-device apparatus with four bidirectional fiber segments and topology-driven physics.
- Local 251-frequency spectrum and full 36-position scan run through native QuReed scheduling.
- Source/convention audit and independent acoustic-response review completed.
- Final integrated 105-test suite passed with zero failures/errors/skips; the historical 35-test baseline report is preserved separately.
- Live browser rendering fixed with project-local singleton reset; edit/save/reload/stale/local/scan checks passed.
- README and complete parameter/default/provenance reference written.
- Nonideal optics/noise now include actual acquisition-time EOM drift and shared deterministic RAM, with physical traces, diagnostic plots and validity guards.
- Coupled counterpropagating optical/acoustic transients include depletion, causal boundaries, photon accounting and explicit absolute/relative refinement acceptance.
- Native 20-block homodyne variant, effective Gaussian channels and fixed-resource temporal-mode comparisons implemented and reviewed.
- Live GUI save/reload/phase rotation, transient plots, nonzero RAM/drift and external-file freshness verified; CLI examples regenerated and audited.
- All 71 advanced options documented. Normal demonstration drift/RAM and homodyne LO phase restored to zero; exact test snapshots remain with exported results.
- Presentation cleanup completed: compact aligned apparatus, obstacle-aware dashed control routing, larger labels and full-board default view. All four saved numerical configurations and connections are unchanged; 20 focused layout/GUI/advanced tests passed. See docs/layout-cleanup.md for live screenshots and recovery copies.

## Blockers / uncertainty

- Paper's 47 GHz amplitude/full-span convention is inconsistent. Default uses total span, with selector and explicit caveat.
- No unresolved implementation blocker within the agreed scope. Nonideal, classical transient and effective quantum families retain separate documented approximation boundaries.
- No claim of a fully coupled quantum SBS apparatus or quantum advantage follows from the separate effective models.

## Next action

Use launch_gui.ps1, select an experiment and run a local spectrum or advanced model as described in README.md. Future parameter studies should preserve the validity/resource/refinement guards and remain distinct from laboratory calibration.
