# Simulation architecture

The SIM half of TwinDock (every device except the real SiWx917 board) is produced by one simulation core in
`backend/sim/`. Both ways of running it share that core:

- `tools/site_sim.py`: a standalone process that publishes to Mosquitto (local development next to the real board);
- `backend/twindock/embedded_sim.py`: the same `SiteSim` inside the backend (the hosted container, no broker).

The goal is cause and effect. Machines use air and power because they are running, the compressor loads because
pressure fell, and the generator starts because the grid failed. Randomness appears only where real plants are
random, and always through a named, seeded distribution from the parameter files.

## Layers

```
                 params/*.yaml  (value, unit, source for every number)
                        │
 ┌──────────────────────▼──────────────────────────────────────────────┐
 │ SimCore (core.py)                                                    │
 │   clock t, fixed step dt (0.25 s), event queue, cause log            │
 │   bus q: power_kw, air_demand_nm3_min, air_pressure_bar, zone_powered,│
 │          heat, people_in_zone, flags (fire alarm, open doors)         │
 │   models, stepped in dependency order every dt:                       │
 │     events/flags → consumers → supplies → rooms                       │
 └──────────────────────┬──────────────────────────────────────────────┘
                        │ true state
 ┌──────────────────────▼──────────────────────────────────────────────┐
 │ Measurement layer (sensors.py)                                       │
 │   per device type and channel: period, noise σ, resolution, range,   │
 │   dropouts, the real part in the kit                                 │
 └──────────────────────┬──────────────────────────────────────────────┘
                        │ readings
 ┌──────────────────────▼──────────────────────────────────────────────┐
 │ Devices (devices.py): one per commissioned SIM device in sites.json   │
 │   same channels and payload schemas as ever (mqtt/site_*.json),       │
 │   source "sim"; silent when their zone has no mains power             │
 └──────────────────────┬──────────────────────────────────────────────┘
                        │ twin/<site>/<device>/<channel>
              SiteSim → broker or in-process sink → Engine.on_mqtt → device registry
```

## Two kinds of time

- **Continuous models** advance every fixed step `dt` (params `core.dt_s`): receiver pressure, temperatures,
  tank levels, walking, battery and fuel. Each model reads the bus, updates its own state and writes its outputs.
- **Discrete events** go on a priority queue with the time they fire and their cause: a cycle completes, a
  bearing fails, a truck arrives, a shift changes. Things that happen inside a continuous model (a pressure limit
  crossed, a pump switching on) are recorded with `core.record(name, cause)`. The cause log is what `/model` shows
  and what R7 checks: no event without a cause.

The clock is the backend's simulation clock (`backend/twindock/simclock.py`). The core keeps `t` in seconds since it
started and asks the backend for the local hour (solar, shifts, tariffs), so at ×5 or ×20 the whole campus runs
faster together, and the warm start fast-forwards it.

## Coupling through physical quantities

Models never call each other for shortcuts like "is the compressor broken, then slow the machine". They exchange
quantities on the bus:

| Quantity | Written by | Read by |
|---|---|---|
| electrical load (kW) per consumer, with its zone | machines, conveyors, compressors, dock bays, EV chargers, fire pump | electrical supply (feeders, incomer, generator) |
| compressed-air demand (Nm³/min) per consumer | running machines | compressed air (receiver) |
| header pressure (bar) | compressed air | machines (slower cycles below 6 bar) |
| zone has mains power | electrical supply | compressors, devices (a mains device in a dark zone is silent) |
| fire alarm, open doors | fire panels, doors | fire pump load, rooms (an open cold-room door warms the room) |

The dependency order in `sim/__init__.py` makes one step consistent: events and flags first, then consumers, then
the supplies that react to consumption, then rooms and effluent. A loop such as pressure → machine speed → air
demand → pressure closes with a one-step lag (0.25 s), which is far shorter than any time constant in the plant.

## Parameters

`backend/sim/params/*.yaml`. Each leaf is `{value, unit, source}` or `{dist, <fields>, unit, source}`. The
source starts with `datasheet:`, `standard:`, `typical industry value` or `assumption`, and says why.
`Params` rejects anything else, and `test_sim_core.py` parses the model code and fails on any number that isn't
plain arithmetic (0, 1, 2, unit conversions). Assumptions are labelled as assumptions: the count is on `/model`.

## Randomness

`sim/rand.py`. Each draw names a stream (`"MM-01.dwell"`, `"BG-03.pause"`), and each stream is its own generator
seeded from the run seed and the stream name. The same seed gives the same run. Adding a device or a draw never
changes the dice another device sees, which `test_streams_are_independent_of_which_devices_publish` checks.
Distributions (Weibull, exponential, normal, lognormal, uniform, Bernoulli) are parameters too.

## Measurement layer

Models hold the true state. A device never publishes it directly; its sensor reads it:

```
reading = clip(round_to_resolution(true + N(0, σ)), range)    (or nothing, with the dropout chance)
```

on the sensor's own sample clock, with its phase spread so devices don't all report at once. The specs follow the
kit parts in `hardware/kits/*.json` (SHT45, SCD40, SPS30, MAX31855K, SCT-013-030, SDM630MCT, DS18B20 and others),
so a simulated kit behaves like the kit would. State channels (door open, machine state, counters) report on
change and on a heartbeat.

## The real board

The core only knows SIM devices: `SiteSim` refuses any device whose source isn't `sim`, devices publish only under
`twin/<site>/...`, and the backend's device registry has no path to the gateway store. Nothing in `backend/sim` can
produce a `twin/gateway/*` message. `tests/test_sites.py::test_sim_messages_never_touch_the_real_board` still
guards the boundary.

## Models

| Model | File | What it is |
|---|---|---|
| Doors, occupancy, fire panels, gas, leaks, asset tags, helmets | `models/environment.py` | event-like states, drawn intervals |
| People | `models/people.py` | workers walking their routes, falls, SOS, check-ins, evacuation |
| Production | `models/production.py` | machines and conveyors |
| Telematics, dock bays | `models/vehicles.py` | trucks' speed, cargo temperature; bay occupancy |
| Campus loads | `models/utilities.py` | EV chargers, fire pump |
| Compressed air | `models/utilities.py` | receiver mass balance, load/unload compressor |
| Electrical | `models/utilities.py` | zone loads, solar, incomer, generator, zone power |
| Tanks | `models/utilities.py` | levels with pump control, diesel day tank |
| Rooms, effluent | `models/environment.py` | first-order room air; ETP quality |

R1 to R5 deepen these: the standby compressor and electrical sequences, shift-based production with failures and
OEE from events, logistics, people and safety, and automatic control.

## Performance

The warm start fast-forwards 45 simulated minutes of the whole campus and the engine in about 7 s on a laptop
(`tests/test_warm_start.py` requires under 10 s). Parameter values are cached after first use, and schema checks on
the message path use compiled validators (`backend/twindock/fastcheck.py`).
