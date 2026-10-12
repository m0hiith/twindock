# Run report: deployment and a cause-and-effect simulation

What was asked: [REALISM_DEPLOY_PROMPTS.md](REALISM_DEPLOY_PROMPTS.md), single-stretch: D0, D1, D3, R0, R1, R2, R5, R3, R4, R6, R7, D2, R8 in that
order, one commit per prompt, decisions in [DECISIONS.md](DECISIONS.md), the container running locally after D1 and at the end, push at the end.
`firmware/`, the board's topics and GW-01's behaviour were not touched (`git diff bd96e85^ HEAD -- firmware/` is empty), and
`tests/test_sites.py::test_sim_messages_never_touch_the_real_board` passed before every commit. The previous run's report is
[docs/RUN_REPORT_factory_extension.md](docs/RUN_REPORT_factory_extension.md).

## What each prompt built

| Prompt | Commit | What it built |
|---|---|---|
| D0 diagnosis | `bd96e85` | [docs/deploy_diagnosis.md](docs/deploy_diagnosis.md). Serverless freezes the 20 Hz loop and the simulator between requests, starts a fresh world on cold starts, runs several copies and can't hold the `/ws` hub. Reproduced with `scripts/repro_serverless.py` (cold start: devices with no readings; 30 s frozen: 60 of 74 SIM devices stale). |
| D1 container | `a862419` | `Dockerfile` (Node build stage + slim Python; built frontend, `/api`, `/ws` on `$PORT` 7860, one worker); `MQTT_URL` with TLS; `/api/health` with tick rate; reconnect jitter; Vercel removed. Verified with `docker run` + `scripts/verify_live.py` for 10 min. |
| D3 warm start | `7ae17fc` | One simulation clock for everything; 45 simulated minutes fast-forwarded before serving (seed from the date); ×1/×5/×20 in the top bar, refused while the real board is online; compiled schema checks (`fastcheck.py`) to keep it fast. |
| R0 core | `fc502f7` | `backend/sim/`: params with value/unit/source for every number (YAML), seeded named streams, fixed-step models + event queue with a cause log, measurement layer from the kits' real parts, devices. One core for `tools/site_sim.py` and the embedded simulator. `/model` page. Two kit inconsistencies fixed (energy meter → SDM630MCT with CTs; compressor sized for its 30 A clamp). |
| R1 utilities | `77d84d1` | Duty + standby compressors (sequencer delay, star-delta, leaks, low-air trip); electrical with PF, APFC, measured solar with a zero-export limiter, AMF generator sequence and fuel/coolant; water and ETP. New SIM devices on real kits: CP-02, GS-01 (generator controller bridge, new kit), PM-08. 15-min demand and an example ToD tariff. Fixed a double count of feeder energy in `/api/monitor`. |
| R2 production | `498b618` | Three-shift calendar; press → buffer → packer with starving/blocking; material conserved from raw pallets (fed by the twin's forklifts) to cartons; Weibull minor stops; bearing wear that predicts failures; ISO 10816 class I; OEE folded from an event log with losses by reason. |
| R5 control | `d728997` | Plant interlocks in the simulator (low air, gas ventilation + hot-work stop, fire-door holds, cold-room door alarm); the twin's control loop (`control.py`): bearing work orders that wait for a person's approval, technician dispatch on the walkways, leaks measured in breaks and fixed, compressor service by run hours, peak-demand shedding, a fire-brigade decision. Every action logged as cause → action → result. |
| R3 logistics | `ae634d2` | Truck schedules with delays, gate, weighbridge (tare + actual cargo), yard queue, paperwork; raw material reorder point; finished-goods orders; forklift batteries in Ah with CC/CV and opportunity charging; KPIs from a logistics event log; Logistics tab; on-time dispatch on the HUD. |
| R4 people | `4fa9e61` | Three-shift roster (crews B and C added, with badges), arrivals and departures through the gate, canteen in meal breaks; BLE positioning error; climate-driven rooms (open halls vs air-conditioned) and activity-based heat stress; evacuation time predicted from walking distances; falls only on cue or at a documented rate. |
| R6 historian | `e61b15d` | SQLite historian (deadband compression, 24 h ring buffer, no badge positions); trend charts with 15 min / 1 h / shift and CSV on the device panel, machine card and `/device`; PDF shift report from the historian and logs. |
| R7 validation | `d858556` | `backend/sim/validate.py` (4 simulated hours with a grid failure and a compressor trip; all checks pass, below); [docs/model_card.md](docs/model_card.md); model card + validation on `/model`. |
| D2 deploy | `0bba646` | Hugging Face Space (README front matter, `scripts/push_hf_space.sh`), Render Blueprint (`render.yaml`), always-on VM (`deploy/vm/`: app, internal Mosquitto, Caddy HTTPS), "Hosted demo" banner, [docs/deploy.md](docs/deploy.md), [docs/deploy_vm.md](docs/deploy_vm.md). |
| R8 demo | `b2fd9f6` | [DEMO.md](DEMO.md): the real board first, then the hosted factory beat by beat with the model and parameters behind each; timings measured with a scripted run. |

## Tests and checks (final state)

- Backend: **290 passed** (`cd backend && ../.venv/bin/python -m pytest -q`, about 4 min). New this run: `test_deploy`, `test_fastcheck`
  (compiled vs jsonschema on 2000+ real and mutated messages), `test_warm_start`, `test_sim_core` (sources, no magic numbers in model code,
  seeds, stream independence, sensors, causes), `test_utilities`, `test_lines`, `test_control`, `test_logistics`, `test_people`,
  `test_historian`, `test_validation`.
- Frontend: **16 tests pass**, typecheck clean, production build clean, lint warnings only (existing style rules).
- Container, final commit: `docker build` + `docker run`, then `scripts/verify_live.py` for 6 minutes: auto mode moves forklifts and trucks,
  compressor pressure cycles, the generator takes load in a grid failure and returns to 0 kW, the line counts units, vibration changes on
  every machine, tick loop at 18.6 Hz. All pass. Warm start in the container: 7.9 s for 45 simulated minutes. `/`, `/twin`, `/control`,
  `/model`, `/energy`, `/api/model`, `/api/history`, `/api/report/shift(.pdf)` all answer 200.
- Not done this run: no browser walkthrough of the new UI. The Chrome extension disconnected early in the run, so the Maintenance and
  Logistics tabs, the trend range bars, the speed control, the banner and `/model` are checked by typecheck, build and tests only.

## Simulation validation (R7)

`backend/sim/validate.py`: 4.0 simulated hours, seed 7, from 06:00, with a 10 min grid failure (hour 2) and a 10 min duty-compressor trip (hour 3); 11.8 s of wall time. Also in the test suite (`tests/test_validation.py`). Raw results: [docs/validation.json](docs/validation.json).

| Check | Result | Detail |
|---|---|---|
| Energy balance | pass | worst 1.4e-14 kW; 513.32 kWh supplied = 513.32 kWh used |
| Material conservation | pass | 2640 blanks fed = 105 at infeed + 28 WIP + 2453 good + 54 scrap |
| Compressor duty | pass | loaded 55 % in production, 55.2 load cycles/h, motor starts/h {'CP-01': 0.5, 'CP-02': 0.5} |
| OEE plausible | pass | M-01 48 %, M-02 65 %, M-03 58 %, M-04 80 % |
| Sensor ranges | pass | 0 true values outside a sensor's range; noise held at a limit is normal (e.g. a stopped motor's current reads 0) |
| Events have causes | pass | 5247 events, 0 without a cause |

## Deploy: what you do

Full click-by-click steps, the environment variables and the laptop demo are in [docs/deploy.md](docs/deploy.md). In short:

**Hugging Face Spaces (the public link)**
1. huggingface.co → avatar → **New Space** → name `twindock`, SDK **Docker** (Blank), hardware **CPU basic (free)**, **Public** → **Create Space**.
2. Avatar → **Settings → Access Tokens → Create new token** → type **Write** → copy it.
3. Once: `brew install git-lfs` (already installed on this Mac during the run).
4. From the repo root: `HF_SPACE=<your-hf-username>/twindock ./scripts/push_hf_space.sh`. The username is your HF username; the password is the token.
5. Space → **Logs** until **Running** → **App**. Link: `https://<your-hf-username>-twindock.hf.space`.

**Render (alternative)**
1. dashboard.render.com (sign in with GitHub) → **New + → Blueprint**.
2. Connect `m0hiith/twindock`; if it isn't listed, **Configure account** and give Render's GitHub app access to it. Pick branch `master`.
3. Render reads `render.yaml` (free Docker web service, health check `/api/health`). Name it, click **Apply**.
4. Wait for **Live**; the link is at the top (`https://twindock.onrender.com` or similar). It sleeps after ~15 min idle and wakes in about a minute.

Nothing secret is in the repository. If you later connect a cloud broker, put `MQTT_URL` in the host's secret settings.

## Things to know

- Docker on this Mac is now **Colima** (`colima start` / `colima stop`, VM with 4 CPUs and 6 GB) with the Homebrew `docker` CLI, because
  Docker Desktop had been removed. `git-lfs` was installed with Homebrew for the Hugging Face push.
- The real board was not connected during this run; Part 1 of DEMO.md still needs firmware Steps A–F tested on hardware (its readiness
  table).
- Assumptions are labelled as such: `/model` counts every parameter by source, and DECISIONS.md explains each modelling choice.

