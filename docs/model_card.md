# Model card: TwinDock's simulated campus

Everything labelled **SIM** in TwinDock comes from this simulation. The one real device, GW-01 (the SiWx917 board),
is never simulated, and simulated data can never reach it. The `/model` page shows the same content live, including
every parameter with its value, unit and source.

## Purpose and limits

The simulation exists so that the twin has a plant to watch where there is no plant: on the hosted demo and in
development. It aims for **cause and effect a plant engineer would recognise**:
- machines draw air and power because they run;
- the compressor loads because the pressure fell;
- the generator starts because the grid failed;
- a bearing's vibration rises before it breaks.

It is not a design tool. Its numbers are plausible for a small Indian two-line plant, not calibrated against a
real one, and it should not be used to size equipment.

## What is modelled

| Area | Model | Where |
|---|---|---|
| Compressed air | Receiver mass balance (isothermal): dP/dt = (ΣQ_comp − Q_demand − Q_leak)·P_atm/(60·V). Duty and standby 15 kW screws on load/unload bands. Sequencer start delay and star-delta start for the standby. Leaks as a pressure-proportional bleed that grows until a leak fix. Low-air trip with hysteresis. | `backend/sim/models/utilities.py` |
| Electrical | Every consumer's kW and kind (for PF) per zone. Lighting, HVAC and offices. Solar with clouds (OU process) and a zero-export limiter. APFC bank. Generator with the AMF sequence (2 s confirm, 3 s crank, 4 s run-up, transfer, 60 s retransfer delay, 120 s cool-down), fuel curve and coolant. Zone shedding in a grid failure. | same |
| Water and effluent | Day/storage/ETP/fire/diesel tanks with pumps. Canteen (meal times), cooling make-up (2 L/kWh of motor heat) and process demand. ETP capacity and overload. | same |
| Production | Three-shift calendar (set-up, breaks, handover). Press → 12-part buffer → packer, both presses on one infeed fed by the twin's forklifts. Starving and blocking from material. Weibull minor stops with lognormal repairs. Bearing wear (dw/dt = r(1 + a·w)) failing at a drawn limit. Current, I² surface heating and vibration (ISO 10816 class I). | `backend/sim/models/production.py` |
| Rooms | Open halls follow outdoors + k × equipment heat (τ 30 min); offices, labs and the canteen air-conditioned. Humidity from outdoor moisture (Magnus). Cold room with a strip curtain and refrigeration duty. | `backend/sim/models/environment.py` |
| Interlocks (the plant's PLCs) | Low air stops pneumatic machines. Gas alarm: extract fan full, hot work stopped. Fire alarm: fire-door holds released, fire pump runs. Cold room door alarm. | `environment.py`, `utilities.py`, `production.py` |
| People | Three-shift roster arriving and leaving through the gate. Rounds on walkways and marked crossings. Canteen in meal breaks. Evacuation walks. Badge BLE positioning error (OU, σ 1.2 m, τ 15 s). Falls and SOS only on cue or at ~2e-6 per worked hour. | `backend/sim/models/people.py` |
| Vehicles | Truck telematics (speed, cargo temperature, door, harsh events). Dock bays. | `backend/sim/models/vehicles.py` |
| Logistics (twin, auto mode) | Truck schedules with lognormal delay, gate, weighbridge (tare + actual cargo), yard queue, paperwork. Raw material reorder point. Customer orders. Forklift batteries in Ah (rolling resistance, lift, standby, CC/CV charge, opportunity charging). | `backend/twindock/logistics.py`, `world.py` |
| Measurement | Every reading goes through its sensor: period, noise σ, resolution, range, dropouts, from the kit's real part (SHT45, SCD40, SPS30, MAX31855K, SCT-013-030, SDM630MCT, DS18B20, ...). | `backend/sim/sensors.py`, `params/sensors.yaml` |

All randomness uses named, seeded streams and the distributions in `backend/sim/params/*.yaml`. The same seed
gives the same run, and adding a device never changes another device's dice.

## What is simplified

- One receiver and one air header; no pressure drop along pipes; leaks are one lumped orifice.
- A machine cycle is one time with lognormal spread; there are no cylinder or die dynamics.
- Room air is one well-mixed node per zone. Walls, sun on roofs and wind are folded into the outdoor curve and the per-zone k.
- Bearing wear is one number per machine; every other failure mode is lumped into Weibull minor stops.
- The electrical network has no voltage drop, harmonics or protection coordination; the generator's governor and AVR appear only through their timings.
- Forklift energy uses a constant rolling resistance and lift height, with no regenerative braking.
- The warehouse runs at the demo PACE (2.5×) unless `TWINDOCK_PACE=1`. Its handling times scale with it, and its KPIs take PACE back out.

## What is assumed

`/model` counts every parameter by source (datasheet, standard, typical industry value, assumption) and gives
the reason for each assumption. The larger assumptions:
- The weather is a fixed daily cycle of a warm month (no seasons, no rain); the date only changes the seed.
- Orders and supplier lead times are random processes, not a real order book.
- The tariff is an example time-of-day schedule.
- Machine sizes, cycle times and air use are a plausible small press and packer line.

## How it is checked

`backend/sim/validate.py` runs four simulated hours, with a 10-minute grid failure and a 10-minute duty-compressor
trip in them. It checks:
- energy balance (supply = load every step; metered energies agree);
- material conservation;
- the compressor's loaded share (30–95 %), load cycles (≤ 120/h) and motor starts (≤ 6/h);
- each machine's OEE (25–95 %);
- that no true value fell outside its sensor's range;
- that every event has a cause.

It runs in the test suite (`tests/test_validation.py`), and its last results are in `docs/validation.json` and on
`/model`. Model-level tests cover:
- the pressure-band cycle against the receiver equation;
- the generator's timing;
- leaks measured in breaks;
- OEE from a scripted log;
- starving and blocking;
- wear before failure;
- the roster headcount;
- evacuation time against walking distances;
- weighbridge weights;
- battery Ah balance.

## Swapping a simulated kit for real hardware

Each simulated device stands for a kit in `hardware/kits/` (real, buyable parts and their wiring; "Simulated kit"
on `/kits`). To make one real:

1. Build the kit and flash firmware that publishes the same `twin/<site>/<device>/<channel>` topics and payloads
   the simulator uses (`shared/schemas/mqtt/site_*.json`).
2. Allow `source: "device"` on site topics. Today the schema fixes it to `"sim"`, deliberately, so nothing simulated
   can pass as real.
3. Set the device's `source` to `"device"` in `sites.json`. `tools/site_sim.py` then stops simulating it, because
   it only selects `source: "sim"`.
4. The twin shows it LIVE, like GW-01. Rules, charts, the historian and the shift report work unchanged.

The bridges (energy meter, generator controller, fire panel) read existing certified equipment and never control
it.
