# Performance report: big campus (FACTORY_PROMPTS.md F4)

Measured in Chrome on the development machine (Apple silicon laptop, 1568 × 647 viewport, dev server, simulator running, all 76
simulated devices and 10 workers live, device markers switched on). Frame cost is the whole frame (every `useFrame` callback plus
render, forced to finish on the GPU) averaged over 120 frames, from the `?stats` bench hook; a frame under 16.7 ms means 60 fps.
"Before" is the campus after F2 (commit 5a0534d), "after" is F4.

| View | Draw calls | Triangles | Geometries | Textures | Frame avg / p95 | JS heap |
|---|---|---|---|---|---|---|
| Campus overview, before | 1729 | 85,158 | 245 | 77 | 14.8 / 16.4 ms | 210 MB |
| Campus overview, after (far LOD) | 564 | 62,356 | 146 | 75 | 10.5 / 12.1 ms | 132 MB |
| Factory and east side (mid LOD), after | 456 | 52,822 | 114 | 63 | 9.9 / 12.1 ms | 148 MB |
| Same with interiors on (roofs off), after | 499 | 50,518 | 102 | 63 | 10.1 / 12.2 ms | 149 MB |

What changed
- **Instancing:** the ~660 rooftop solar panels are three instanced meshes (one call each); fixed device markers are four instanced meshes in total instead of about four meshes per device.
- **Level of detail** (from the camera zoom in pixels per metre, with hysteresis): far (< 9 px/m, the campus overview) draws buildings as shell and roof only, no windows, signs, ground labels or device markers; mid and near add them. Interiors are drawn only when the roof is off.
- **Merged static geometry** was already done per material with `Baked`; walls, windows, cars, hydrants, fences and walkways stay merged.
- **Frame cost:** the numbers above were measured on a hidden-window dev build, so real-time rAF could not be observed (see RUN_REPORT.md for the same caveat); the frame-stepping bench is the figure to trust. The target (60 fps on an M1 with everything on) holds with margin on this machine; confirm by eye on the M1.

How to measure again: open `/twin?stats&site=ALL&devices` (the tab must be in front: Chrome stops React effects in background tabs), read `document.body.dataset.twinStats`, and run `window.dispatchEvent(new CustomEvent("twindock-bench", {detail: 120}))`, then read `document.body.dataset.twinBench`.
