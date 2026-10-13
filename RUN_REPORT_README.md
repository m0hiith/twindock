# Run report: README rewrite with automatic screenshots

Date: 2026-10-13. Asked: rewrite README.md as a complete project document for a recruiter, a Silicon Labs engineer and a
judge, with every screenshot captured from the running app and every number checked. `firmware/`, the board's topics
and GW-01's behaviour were not touched.

## Commits

| Commit | What |
|---|---|
| `6eec232` | Control Room fix found while capturing: at 1440 px the side panel ran off the right edge (the map column had no `min-w-0`) |
| `4595a1f` | `tools/screenshots/capture.py` (Playwright), the screenshots, `docs/screenshots/CHECKLIST.md`, `docs/readme_blockers.md` |
| `b8cdd24` | README.md rewritten in the 16 requested sections; gateway card shot added |
| `72ba915` | Clean-checkout fixes to the README (Python venv note), this report |
| `9989d72` | README license line: Apache 2.0, after rebasing onto the LICENSE commit on origin |

## What was captured

16 PNGs and one clip in `docs/screenshots/`, from a freshly started backend (embedded simulator, no broker, no board)
and the Vite dev server, desktop 1440 × 900 and phone 390 × 844:
twin-overview, twin-inspect-forklift, twin-gateway-card, campus-factory, control-room, control-phone, device-page,
wiring-breadboard-fl01, wiring-schematic-fl01, wiring-reference-kit (machine_monitor), kits-index, fleet (Needs
attention), monitor, rules, energy, model, and forklift-route.mp4 (13 s). Every image was opened and checked; the
results are in [docs/screenshots/CHECKLIST.md](docs/screenshots/CHECKLIST.md).

Problems found and fixed while checking, never by cropping:
- `/control` at 1440 px: side panel off screen. Fixed in the app (`6eec232`), re-captured.
- Selection is shared server state, so FL-01 selected for one shot opened its card in the next ones. The script now
  clears the selection over `/ws` before every shot (its first try was rejected for a missing `cmd_id`, which it now sends).
- The route clip first showed the search box, then an idle forklift. The script now trims at the measured moment
  the selection lands and sends FL-01 a real `move_unit` intent (as `/control` does; the card says "Source: Manual").
- A cold-room shot showed only a closed roof with no card; it was dropped rather than kept.

## What failed or was not captured

- **`planner.png`**: `/plan` does not exist (site step S8 is not built). The README says so under Features and Roadmap.
- **Homebrew Python**: `python3 -m venv .venv` from a clean checkout failed at `ensurepip` with Homebrew Python 3.14 on
  this Mac. The README now says to use the python.org installer in that case; python.org 3.13 worked.

## Checks on the README

- 42 relative links and 16 images: all resolve; every PNG in `docs/screenshots/` is used. README: 458 lines.
- Numbers, each from a file or a command run today: backend 290 passed, 1 warning (repo, and again in a clean clone);
  frontend 16 passed; typecheck clean; 32 rules, 90 devices (2 LIVE, 88 SIM), 371 parameters by source, all read off
  the running app; 18 kits (`hardware/kits/`); container and validation results from RUN_REPORT.md (2026-10-12); frame
  times from docs/perf_report.md. The README says the 15-minute soak (2026-10-08) was on the warehouse-only twin, and
  that the full campus was measured with a frame bench, not a soak.
- MQTT examples: each one validated against its schema in `shared/schemas/mqtt/` with jsonschema.
- Clean checkout (`git clone` into a scratch folder): venv + pip install, `npm install`, `npm test`, `npm run typecheck`,
  backend pytest, `./scripts/run_backend.sh` (on another port) with `npm run dev` and the `/api` proxy, the screenshot
  install and `capture.py`, all worked.
- Also from the clean clone: `./scripts/run_broker.sh` (Mosquitto 1883); `tools/site_sim.py` sent 756 messages in
  10 s, none on `twin/gateway/*`; `tools/fake_board.py` printed its FAKE BOARD banner and published, and its retained
  hello was then cleared with the README's `mosquitto_pub -r -n` command; broker stopped afterwards.
- `docker build` + `docker run -p 7861:7860` (Colima): `/api/health` ok (embedded simulator, 45-minute warm start in
  7.4 s), `/twin` 200, and `capture.py --base` against the container worked (it shows the "Hosted demo" banner).
  Container and image removed afterwards.

## Not verified

- Firmware build and flash, and anything on the real board: no board and no Simplicity toolchain run. The README keeps
  "written and builds, untested on hardware" from firmware/TESTING.md.
- The Hugging Face and Render deploys: they need the owner's accounts.
- Real fps on the full campus by eye.

## Screenshot command

```sh
.venv/bin/pip install -r tools/screenshots/requirements.txt && .venv/bin/python -m playwright install chromium   # once
.venv/bin/python tools/screenshots/capture.py                               # app on http://localhost:5173
.venv/bin/python tools/screenshots/capture.py --base http://localhost:7860  # the Docker container
.venv/bin/python tools/screenshots/capture.py --only fleet,forklift-route   # some shots only
```
