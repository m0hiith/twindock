# README run: blockers and things not verified

Written during the README rewrite on 2026-10-13.

## Not captured

- **`/plan` (planner with the capacity simulation) → `planner.png`.** There is no `/plan` route in
  `frontend/src/App.tsx` and no planner page; the Control Room's Demo tab says "/plan (S8) is not built yet". The
  README lists it under the roadmap, not under features. `backend/twindock/planner.py` is the auto mode, not a capacity
  planner.

## Commands in the README that were not run in this session

- `./scripts/run_broker.sh` and the board steps: no board was connected and the screenshots were taken with the
  embedded simulator (no broker). The broker script is unchanged since the last run that used it.
- Firmware build and flash (`make -f twindock_gw.Makefile`, Commander): needs the Simplicity SDK toolchain and the
  board; not run. The status comes from `firmware/TESTING.md` ("written, builds with 0 errors and 0 warnings, not yet
  run on hardware").
- The Hugging Face and Render deploys: they need the user's accounts. Steps are in `docs/deploy.md`.
