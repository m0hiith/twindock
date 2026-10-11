# Run report: unattended site-extension run (2026-10-10 → 2026-10-11)

What was asked: Stages 0–6 of the site extension (SITE_PROMPTS.md S0, S1, S2, S3, S6, and S10
items 2–4), one commit per stage, then push. Added during the run at your request: no collisions
between forklifts, trucks or people. Every decision made without you is one line in
[DECISIONS.md](DECISIONS.md).

## What each stage built

| Stage | Commit | What it built |
|---|---|---|
| 0. HARDWARE.md | `e2ab4d8` | SDK row is WiSeConnect 4.1.1. The NWP firmware update before the first flash is recorded as an **open** item. |
| 1. S0 site foundation | `f7a42b4` | Plan in [docs/site_plan.md](docs/site_plan.md). `sites.json` holds the sites (WH-01, FAC-01 "Riverside Assembly" east of the warehouse, same grid and waypoint graph), zones and commissioned devices. The device registry (`devices.py`) handles staleness, and GW-01 is derived from the board's own messages only. `tools/site_sim.py` publishes every simulated device on `twin/<site>/<device>/<channel>` with `source: "sim"`. Also: FAC-01 shell in 3D and a site selector. |
| 2. S1 Fleet | `b590887` | `/fleet` page with real devices first and LIVE/SIM on every row. Device side panel with reading history and ages. Device pucks in the twin (map control "Devices"). |
| 3. S2 Production | `5675bfa` | Machines M-01/M-02 on a conveyor line. Vibration baselines (learned, z-score with hysteresis), OEE with a formula tooltip, and a "Degrade" demo command. Finished pallets (FG-xx) go to the factory outbound; auto mode collects them. |
| 4. S3 Worker safety | `c12c1dc` | Simulated BLE badges walk named routes. Proximity to *moving* forklifts gives warning < 3 m and critical < 1.5 m. Restricted zones (press area, cold room). No names on the wire. The real path: a `TD-BADGE-01` tag seen by the board becomes RB-01 (LIVE). |
| 5. S6 Rules and alerts | `886a0f2` | One rules engine (`backend/rules/*.yaml`) for every alert. Lifecycle is raised → acknowledged → resolved, and alerts are shared across screens. `/rules` lists every rule in plain language. Missing or stale data never raises an alert. |
| 6. S10 items 2–4 | `e80ac79` | Demo scenario runner: Control Room → Demo tab, five beats plus reset, run by the backend. Value-source audit: [docs/value_audit.md](docs/value_audit.md) plus tests that keep it true. Performance check (below). Also the site demo in DEMO.md, the README site sections, and the schema.md and CLAUDE.md contract summaries. |
| Traffic (your request) | `8b3a5a0` | `backend/twindock/traffic.py`: vehicles only drive onto waypoint nodes and lanes they have reserved, and a conflict map built from the real footprints rules out overlap. Blockers move aside or make way into a pocket and then resume their task. Forklifts stop for a person on their lane, and simulated workers walk beside the aisles. Layout tweaks: ROAD_IN for returning trucks, the charger junction, deeper rack slots. |

The rule "a simulated device never writes real device state or triggers a real LED or board
command" is enforced in code. It is checked by
`tests/test_sites.py::test_sim_messages_never_touch_the_real_board`, which passed before every
commit. `firmware/` is unchanged by this run (checked with `git diff` against HEAD before each
commit).

## What was skipped, and why

- **S4 (cold room/dock physics in 3D), S5 (energy), S7 (commissioning), S8 (planner), S9
  (firmware campaigns):** not in this run's scope. You asked for S0, S1, S2, S3, S6 and S10
  items 2–4. They are listed as "Not started" in the README and as the roadmap in DEMO.md.
- **S10 item 1** and other S10 items: not asked for.
- **No stage was reverted.** Every stage passed within three attempts.
- **Real-time fps** could not be observed, because the Chrome window was hidden (unattended
  run), and a hidden window throttles requestAnimationFrame. Frame *cost* was measured instead
  (below).

## Tests (at the last commit)

- Backend: **114 passed** (`cd backend && ../.venv/bin/python -m pytest -q`). This includes 10
  traffic tests: head-on, following, crossing, parked blocker, pedestrian, and five 10-minute
  auto-mode runs with no overlap and no gridlock.
- Frontend: typecheck clean (`npx tsc -b`), **8 tests passed** (`npm test`), and the build
  succeeds (`npm run build`). The build gives the usual >500 kB chunk-size warning, which is not
  an error.
- Traffic, beyond the suite: 60 random 10-minute auto-mode runs. None had an overlap > 0.15 m, and
  no forklift was blocked for a minute.

## Performance

Measured in Chrome on the Apple M1 (2560×1600 Retina) on `/twin?stats`, with both sites, device
pucks, workers, alerts and auto mode on. A `?stats`-only hook steps whole frames by hand (every
`useFrame` callback + render + a GPU sync) and times them. Under 16.7 ms per frame means 60 fps is
achievable.

| Measurement | Result |
|---|---|
| Draw calls, before merging factory parts | 414 (13.1 ms avg, p95 16.8 ms: too close to the budget) |
| Draw calls, after (`Baked` conveyor/QC, pucks without shadows) | 272 at the default view, ~350–380 zoomed out |
| Frame cost after, 300-frame bench at 1920×873 (with the traffic work in) | 6.4 ms avg, p95 7.1 ms, max 8.6 ms |
| Soak 1 (before traffic), a 60-frame bench every minute, 13 min | avg 4.7–7.5 ms, p95 5.2–15.7 ms, worst single frame 52.9 ms; heap 82–119 MB, no upward trend. A Vite hot reload at ~600 s (my own edit) restarted the page. |
| Soak 2 (final code), same method | 0–3 min on `/twin`: avg 5.4–6.6 ms, p95 ≤ 7.2 ms, max 7.8 ms, 283–285 draw calls. At ~4 min the tab was switched to `/control` (not by me), so the rest only shows the page's memory: heap 71–77 MB, flat, for the remaining 11 min. |

In fps terms: every sample's p95 stayed under the 16.7 ms budget (≥ 60 fps possible); the average
frame costs 5–7.5 ms (≈ 130–190 fps of headroom). No soak ran a full 15 uninterrupted minutes on
`/twin`, but neither showed memory growth. Real fps on screen is still for you to confirm (next section).

## What you must check by hand

1. **Real fps by eye:** open `http://localhost:5173/twin?stats` in a visible window with auto mode
   on, and switch to FAC-01 with "Devices" on. The fps counter should stay around 60. Leave it 15 minutes: no soak in this run covered 15 uninterrupted minutes on `/twin`.
2. **Traffic looks right:** turn on auto mode and watch for a few minutes. Forklifts should wait at
   junctions ("Waiting for FL-0x to clear the way" in the table), back into a pocket to let
   another pass, and never drive through each other or a truck. Waits of a few seconds are
   expected. A wait over ~20 s is a bug worth reporting.
3. **Board items (need the board):** update the NWP firmware first (HARDWARE.md). Then flash Steps
   A–D and run [firmware/TESTING.md](firmware/TESTING.md). Firmware Steps E (BLE) and F (offline
   buffer) are not written. The board twin is still blocked on `frontend/public/board/top.jpg`
   and the hotspot table.
4. **README.md had been reverted** in the working tree (WareTrack credit gone, firmware back to
   "Not started"). The change was made outside this run, on 2026-10-10 at 22:23. I restored it
   from git and re-applied my edits. If you did that on purpose, tell me what you wanted changed.
5. **Rehearse the site demo** in DEMO.md once with the simulator running: the baseline needs about
   90 s before "Degrade" shows anything.
6. **Processes I started** for testing: the Mosquitto broker (`scripts/run_broker.sh`), a backend on
   :8001 (client id `twindock-backend-claude`), `tools/site_sim.py` and Vite on :5180. They are
   stopped at the end of the run. Start your own as in the README.
