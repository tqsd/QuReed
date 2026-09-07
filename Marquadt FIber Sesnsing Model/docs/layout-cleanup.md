# Native GUI layout cleanup

Date: 2026-09-06. Scope: presentation only; no physics or connection changes.

## Changes

- Compact 1380-pixel board, aligned fiber chain and visible pump termination.
- Probe components above the pump chain; detector, lock-in and controller below.
- RF generators placed near the source/modulators.
- Obstacle-aware orthogonal wires with bend and overlap penalties. Wires are recalculated after dragging, including wires not attached to the moved block.
- Solid gold/teal optical paths and lighter dashed blue control paths; crossings are not junctions.
- Light background, taller headers and larger labels. Full names remain available in tooltips and the parameter panel.
- Parameter panel starts closed to show the whole apparatus; clicking a header opens it. Toggle editor hides/shows it.
- Same presentation applied to all four saved experiments and newly generated defaults. Custom nodes and physical values survive layout transformations.

The native QuReed board, port clicks, drag events, serialization and simulation dispatch remain in use. No installed QuReed source was modified. Overlapping user-dragged blocks can make collision-free routing impossible; in that case a visible ordinary elbow is retained, never a changed connection.

## Verification

Final focused suite: **20 tests PASS**, zero failures/errors/skips, 42.1441 s. These comprise four new layout tests, seven existing GUI-contract tests and nine advanced integration tests. The earlier full 105-test scientific-model report remains a dated separate record, not a claim that all tests were rerun for this presentation-only change.

Checks include:

- All four saved schemes equal their original snapshots after removing only device locations. Parsed numerical configurations are exactly equal.
- Native direct/homodyne graphs still have 26/29 wires respectively; routed line segments do not enter unrelated blocks.
- Actual native drag/re-route/save preserves topology and parameters.
- Custom nodes/values survive; the default fiber chain is aligned and the termination fits the board.
- Existing GUI/CLI equality, persistence, stale-state, invalid topology, advanced-mode and receiver contracts pass.

An isolated Edge browser checked the actual localhost GUI at 1440 × 1000. The direct and homodyne layouts were visually inspected with no page errors. Clicking Fiber 3's header opened its physical length/resonance controls. A real Run local spectrum completed with 19 devices, 26 connections, zero remaining events, and exactly the pre-cleanup numerical configuration; the fitted resonance was 10.9010500584 GHz.

- [Direct apparatus screenshot](../results/verification/layout-cleanup.png)
- [Homodyne apparatus screenshot](../results/verification/layout-cleanup-homodyne.png)
- [Successful measurement screenshot](../results/verification/layout-cleanup-measurement.png)
- [Executed local run and exact snapshot](../results/gui_local_20260906_085714_014599/report.html)

## Recovery and opening the updated view

Original snapshots are preserved in `results/layout-cleanup-original/`. If physical settings have changed subsequently, recover only the desired locations rather than replacing the entire experiment with an old snapshot.

The updated GUI was started on local port **8766** so the existing 8765 server/window would not be interrupted. Open http://127.0.0.1:8766/ for that running updated view. For future launches, the normal launcher remains unchanged; stop an old server with Ctrl+C before reusing its port. Reload from disk reloads the JSON, not changed Python renderer code. Use one active editing session and avoid saving stale settings from the older server.
