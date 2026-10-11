# TwinDock: fix deployment and make the simulation behave like a real factory

## Why it works on localhost but not on Vercel

This is not a bug in your factory logic. TwinDock's backend is a **long-running process**: a 20 Hz
tick loop, an in-memory world, a simulator that keeps running, and WebSockets that broadcast to
every screen. Vercel runs your backend as **serverless functions**: they start per request, stop
afterwards, can run as several separate copies, and keep nothing in memory between calls.
On Vercel:

- the tick loop and the embedded simulator only run while a request is open, so the compressor,
  generator, machines and vibration never advance;
- each request can hit a fresh copy with a freshly reset world, so auto mode "forgets";
- WebSocket connections are pinned to one function copy for a limited time, and one copy cannot
  broadcast to screens connected to another.

**The fix is to host the backend as one always-running container**, not to rewrite the logic.

## Where to deploy (free or nearly free)

| Option | Good for | Catch |
|---|---|---|
| **Hugging Face Spaces (Docker)** | Easiest free demo link: one container with backend + built frontend | Sleeps after a period without visitors; restarts the simulation on wake. Check current limits. |
| **Render (free web service)** | Simple Git-based deploys, WebSockets | Sleeps after ~15 min idle, ~1 min to wake; 750 free hours a month |
| **Oracle Cloud Always Free VM** | Truly always-on; can also run Mosquitto | More setup (Linux VM, Docker, HTTPS); card verification at sign-up |
| **Your laptop + Cloudflare Tunnel** | Live interview demo with the real board | Only up while your laptop is on |
| Fly.io / Railway / Koyeb | — | No real free tier any more for always-on use |

**Recommendation:** Hugging Face Spaces (or Render) for the public link recruiters open, plus
your laptop for the live demo with the real board. The prompts below add a **warm start** so a
sleeping instance wakes up into a busy factory instead of an empty one.

**MQTT broker in the cloud (optional):** HiveMQ Cloud's free plan (around 100 connections, no card,
check current terms) lets the real board reach a hosted backend from any Wi-Fi. The board would
then need TLS on port 8883, which is extra firmware work; keep it for later.

---

## Part D: Deployment

### D0: Reproduce the production problem locally

```
Read CLAUDE.md, README.md, vercel.json and backend/twindock/main.py, embedded_sim.py.
Explain in docs/deploy_diagnosis.md why the hosted Vercel version shows no compressor,
generator, factory or machine data in auto mode while localhost works. Check: where the 20 Hz
tick and the embedded simulator start, what happens per request on serverless, how many
backend copies can run, and how /ws behaves. Confirm the diagnosis by running the backend the
way production does (single worker, no broker, TWINDOCK_SIM=embedded) and by simulating a
cold start per request. No code changes yet. Commit the document.
```

### D1: One production container

```
Read CLAUDE.md and docs/deploy_diagnosis.md. Make TwinDock run as ONE always-on container.

1. Dockerfile (multi-stage): build the frontend, then a slim Python image that serves the
   built frontend as static files from FastAPI, plus /api and /ws, on $PORT (default 7860).
   Exactly one worker process (the world lives in memory).
2. Simulation mode: embedded by default when no broker is configured; if MQTT_URL is set,
   connect to that broker instead (so the real board can join a hosted backend later).
3. Health: /api/health reports sim clock, tick rate achieved, devices online, uptime.
   Log a warning if the tick loop falls below 15 Hz.
4. Frontend: WebSocket URL derived from window.location (wss on https), auto-reconnect with
   backoff, and on reconnect request a fresh world_snapshot.
5. Remove vercel.json and Vercel build steps; note why in DECISIONS.md.
6. docker build + docker run locally; verify auto mode, compressor, generator, factory lines
   and vibration all update in the browser for 10 minutes. Commit.
```

### D2: Deploy

```
Read CLAUDE.md and the Dockerfile. Add deployment for:
1. Hugging Face Spaces (Docker SDK): README front-matter for the Space, port 7860,
   instructions in docs/deploy.md.
2. Render (render.yaml) as the alternative, with the free plan and health check path.
3. Optional: docs/deploy_vm.md for an always-on Oracle Always Free VM with Docker,
   Mosquitto and HTTPS (Caddy).
4. A "Hosted demo" banner on the site: "Simulated factory · the real SiWx917 board is shown
   in the live demo", so nobody mistakes the hosted SIM data for the board.
Do not commit secrets. Write exact click-by-click steps for me in docs/deploy.md.
```

### D3: Warm start and a visible simulation clock

```
Read CLAUDE.md and the simulator. When the backend starts (including after a free host wakes
it up), fast-forward the simulation ~45 simulated minutes at high speed before serving:
machines have baselines, the compressor has cycled, trucks are mid-route, shift is in
progress. Use a fixed seed plus the current date so each day looks different but is
reproducible. Show the simulation clock and speed (×1, ×5, ×20) in the top bar; real-time
speed is the default for the live demo. Tests: warm start finishes under 10 s and produces
non-empty production, utilities and safety state.
```

---

## Part R: Make the simulation behave like a real factory

The goal: every number comes from a **model of cause and effect**, not a random generator.
Machines consume air and power because they are running; the compressor runs because pressure
dropped; the generator starts because the grid failed. Randomness is used only where real
factories are random (failures, arrival times, scrap), with seeded, documented distributions.

### R0: Simulation architecture and parameter sources

```
Read CLAUDE.md, tools/sim_models.py, embedded_sim.py, production.py and safety.py.
Plan in docs/sim_architecture.md, then refactor:

1. One simulation core with a simulation clock, used by both site_sim.py and embedded_sim.py.
   Two parts: continuous models stepped at a fixed dt (thermal, pressure, battery, fuel) and
   discrete events (cycle complete, failure, truck arrival, shift change) on an event queue.
2. Coupling through physical quantities, not shortcuts: electrical load (kW), compressed-air
   demand (Nm³/min), heat, material (units, pallets), people. Each model reads inputs and
   writes outputs; a dependency order per step.
3. All parameters in backend/sim/params/*.yaml, each with value, unit, and source
   ("datasheet: <part/doc>", "standard: <name>", "typical industry value", or "assumption").
   No magic numbers in code.
4. Seeded randomness only through named distributions in params (e.g. Weibull failures,
   exponential arrivals, normal measurement noise with sensor-appropriate sigma).
5. Measurement layer: models hold the true state; each simulated sensor reads it with its
   own resolution, noise, sample rate and dropouts, like the real sensor in its kit.
6. A /model page that lists every model, its equations in plain language, and its parameters
   with sources. Recruiters and engineers can see nothing is random.
Keep every existing schema and the rule that SIM never touches GW-01.
```

### R1: Utilities

```
Read docs/sim_architecture.md and params. Implement physically grounded utilities:

Compressed air
- Two compressors (duty + standby) with load/unload control on a pressure band
  (e.g. 6.5–7.5 bar), a receiver tank (pressure change from net flow and tank volume),
  specific power (kW per m³/min) from a typical datasheet, leaks as a % of demand that
  grows slowly and resets after a leak-fix work order.
- Demand = sum of running machines' air use. If pressure falls below the low limit, the
  standby compressor starts; below the trip limit, pneumatic machines stop with
  "low air pressure".
- Readings: pressure, flow, kW, load/unload state, run hours, discharge temperature.

Electrical
- Site load = sum of all loads (machines by state, compressors, lights, HVAC, chargers,
  cold room). Grid supply, power factor, demand peak per 15 min, time-of-day tariff.
- Rooftop solar output from time of day and a simple cloud factor.
- Diesel generator: on grid failure the ATS waits, sends start; crank, ramp to rated
  speed, transfer critical loads within a realistic time; fuel use from a load-based curve;
  coolant temperature first-order rise; non-critical loads shed. Retransfer and cool-down
  run after the grid returns.

Water and effluent
- Tank levels with pump on/off levels, consumption from canteen, cooling and process,
  ETP inflow/outflow and treated-water quality bands.

Tests for each: steady state, the pressure-band cycle, generator start sequence timing,
energy balance (supply = load within tolerance).
```

### R2: Production lines

```
Read docs/sim_architecture.md. Make production behave like a real line:

1. Shift calendar: shifts, breaks, start-up and shut-down; lines idle in breaks.
2. Each machine: states (running, idle-starved, idle-blocked, setup/changeover, planned
   stop, breakdown, maintenance), ideal cycle time, small cycle-time variation, scrap rate,
   buffers between machines so starving and blocking happen naturally.
3. Material flow conserved: raw pallets in → units → finished pallets → warehouse.
   A test checks in = out + work in progress at all times.
4. Physics per machine: motor current from load and state; surface temperature as a
   first-order thermal model; vibration RMS with a healthy level and a bearing-wear model
   that grows slowly then faster; vibration severity zones per ISO 10816-style bands.
5. Failures from Weibull distributions (MTBF) and repair times (MTTR) in params; wear makes
   failures more likely, so the vibration anomaly actually predicts something in the sim.
6. OEE from actual events: availability, performance and quality computed from the event
   log, never set directly.
Tests: conservation, OEE calculation from a scripted event log, starving/blocking behaviour.
```

### R3: Logistics

```
Read docs/sim_architecture.md and planner.py. Make logistics realistic:
1. Truck arrivals from an hourly schedule with random delay; gate check-in, weighbridge
   (gross/tare weight from actual load), yard queue, dock assignment, unload/load time from
   pallet count, paperwork time, departure.
2. Forklift battery in Ah: drain from travel distance, lift events and load weight; charge
   curve at chargers; opportunity charging in breaks.
3. Inventory: stock per SKU group in racks with putaway and picking; reorder point triggers
   raw-material trucks; finished goods dispatched against orders.
4. KPIs computed from events: dock-to-stock time, truck turnaround, on-time dispatch,
   forklift utilisation.
Tests: weighbridge weights match cargo, inventory never negative, battery energy balance.
```

### R4: People and safety

```
Read docs/sim_architecture.md, safety.py and the badge kit. Make people behave realistically:
1. Roster per shift with roles (operators per machine, forklift drivers, technicians,
   QC, security, admin). Walking speed ~1.3 m/s on walkways; breaks and canteen visits.
2. Badge readings come from the badge model (IMU, button, BLE position with realistic
   zone error), not from the person's true position directly.
3. Near-misses arise from actual routes crossing at crossings, not random events.
4. Heat stress from environment readings and activity; rest reminders accordingly.
5. Falls and SOS only through demo triggers or a very low documented rate.
Tests: headcount equals roster on site; evacuation time computed from walking distances.
```

### R5: Automatic actions and control logic (the factory reacts)

```
Read CLAUDE.md and the rules engine. Add control logic so the factory responds like a real one:
1. Interlocks: low air pressure stops pneumatic machines; gas alarm stops hot work and
   ventilation goes to max; fire alarm releases door holds and starts evacuation;
   cold-room door open > limit sounds a local alarm.
2. Maintenance (CMMS-like): abnormal vibration creates a work order; a technician walks
   from the workshop; the machine goes to maintenance; repair time from params; wear resets;
   the baseline relearns. Same for leak fixes and compressor service by run hours.
3. Energy actions: peak demand warning sheds non-critical loads (EV chargers, some
   lighting) and logs it.
4. Operator decisions stay with people: anything that stops production or calls emergency
   services is a recommendation that a human acknowledges on /control or /monitor.
5. Every automatic action appears in the event log with cause → action → result.
Tests: each chain end to end (e.g. bearing wear → anomaly → work order → repair → normal).
```

### R6: Historian and reports

```
Read CLAUDE.md. Add a small historian:
1. Store time series for every reading and every event in SQLite (ring-buffer retention,
   e.g. last 24 simulated hours), downsampled for charts.
2. Trend charts on inspect cards and /device with 15 min / 1 h / shift ranges.
3. Shift report (PDF): output, OEE losses by reason, downtime events, energy per unit,
   safety events and response times, open work orders.
4. CSV export for any chart.
```

### R7: Validation and model card

```
Read docs/sim_architecture.md and all params. Prove the simulation is sane:
1. Automated checks over a 4-hour simulated run: energy balance, material conservation,
   compressor duty cycle within a typical range, OEE in a plausible band, no reading
   outside its sensor's physical range, no event without a cause.
2. docs/model_card.md and the /model page: what is modelled, what is simplified, what is
   assumed, and how each simulated kit would be swapped for real hardware (same topics,
   source: device).
3. Run the checks in the test suite; report results in RUN_REPORT.md.
```

### R8: Demo update

```
Read DEMO.md. Rewrite the demo around cause and effect:
1. Real board segment first (laptop).
2. Hosted segment: warm-started factory; follow one bearing from wear → anomaly → work
   order → technician → repair; a grid failure with generator start and load shedding;
   low air pressure stopping a line and the standby compressor recovering it; a truck
   from gate to dock with weighbridge weights; the shift report.
3. Each beat lists which model and which parameters produce it, so I can explain it.
```

---

## Single-stretch version

```
Read CLAUDE.md, README.md, /shared and REALISM_DEPLOY_PROMPTS.md. Run D0, D1, D3, R0, R1, R2,
R5, R3, R4, R6, R7, D2 and R8 in that order in one continuous run. Do not stop for approval;
record decisions in DECISIONS.md. One commit per prompt. All tests, typecheck and build must
pass before each commit, and the container must run locally (docker run) after D1 and after
the final prompt. If a prompt still fails after three serious attempts, revert its uncommitted
changes, note it in DECISIONS.md and continue. Never touch firmware/, the real board's topics
or GW-01's behaviour. Keep SIM labels everywhere. Push at the end and write RUN_REPORT.md
including the exact steps for me to deploy on Hugging Face Spaces and on Render.
```
