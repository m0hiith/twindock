# Why the hosted Vercel deploy shows no factory data (and localhost does)

Short version: TwinDock's backend is a long-running process, and Vercel runs it as serverless functions.
The factory logic is fine. The process that should be running it is never alive long enough, and there
can be several separate copies of it.

## Where the moving parts start

| Part | Where it starts | What it needs |
|---|---|---|
| 20 Hz tick (`App.tick_loop`, `backend/twindock/main.py`) | `asyncio.create_task` in the FastAPI `lifespan` | a process that stays alive and keeps CPU between requests |
| Embedded site simulator (`App.sim_loop` → `EmbeddedSim.step`, every 0.25 s) | same `lifespan`, when `TWINDOCK_SIM=embedded`, or `auto` with no broker reachable | same; every SIM reading (compressor, generator, meters, machines, badges) comes from it |
| World state (units, production counters, vibration baselines, alerts, energy counters) | `state = App()` at import time, in memory | the same process for every request and every screen |
| `/ws` hub (`Hub`) | one in-memory list of sockets per process | every browser connected to the same process, for a long time |
| Machine state, OEE, baselines (`production.py`) | built from SIM readings as they arrive | a continuous stream of readings: the baseline needs 90 s of running data |

Nothing in this design runs per request. The REST endpoints and the WebSocket only read the state the two
loops keep up to date.

## What serverless does to that

1. **Instances run only while a request is in flight.** An idle function instance is frozen: no CPU, so the
   `asyncio` tasks for the tick loop and the simulator stop. When the next request thaws it, both loops cap
   their `dt` (0.25 s and 1 s) so units don't teleport, so 30 s of wall time becomes 1 s of simulation. The
   compressor, generator, machines and vibration don't advance, and every SIM device goes stale because its
   last message is older than 15 s.
2. **Cold starts reset the world.** A new instance imports `main.py` again: a seed world, empty production
   counters, no vibration baseline, auto mode off, no energy history. If the platform runs the `lifespan` at
   all, the simulator has only sent its hellos when the first request is answered, so devices are "online"
   with no readings. If it doesn't run the `lifespan`, neither loop exists.
3. **Several copies can run at once.** Under load, or simply when requests overlap, the platform starts
   more instances. Each has its own world. "Auto mode on" goes to one copy, and the next request may land on
   another copy where it's off, so auto mode "forgets".
4. **WebSockets don't fit.** Vercel Functions can't act as a long-lived WebSocket server (check Vercel's
   current docs on WebSockets and maximum function duration). At best a socket is pinned to one instance until
   its maximum duration ends. Even then, an `event` or `unit_update` from one instance can't reach a browser
   connected to another, because the `Hub` only knows its own sockets.

Localhost works because `uvicorn` is one process that stays up. Both loops run continuously, every browser
shares the same `Hub`, and auto mode, baselines and counters build up over minutes.

## Reproduced locally

`scripts/repro_serverless.py` runs the backend the way production does (one worker, `TWINDOCK_MQTT=0`,
`TWINDOCK_SIM=embedded`) in three ways and samples `/api/snapshot` and `/api/monitor`:

```
1. long-running process (localhost / container)
   after 20 s: {"sim_online": 74, "sim_total": 74, "compressor_bar": 7.23, "generator_state": "off", "machines_with_data": 4, "machines": 4}
2. cold start per request (a fresh instance answers each request)
   request 1: {"sim_online": 74, "sim_total": 74, "compressor_bar": null, "generator_state": null, "machines_with_data": 0, "machines": 4}
   request 2: {"sim_online": 74, "sim_total": 74, "compressor_bar": null, "generator_state": null, "machines_with_data": 0, "machines": 4}
   request 3: {"sim_online": 74, "sim_total": 74, "compressor_bar": null, "generator_state": null, "machines_with_data": 0, "machines": 4}
3. one instance, frozen between requests (no CPU while idle)
   request 1 (3 s after start): {"sim_online": 74, "sim_total": 74, "compressor_bar": 7.14, "generator_state": "off", "machines_with_data": 4, "machines": 4}
   request 2 (after 30 s frozen): {"sim_online": 14, "sim_total": 74, "compressor_bar": null, "generator_state": null, "machines_with_data": 0, "machines": 4}
```

- A cold start per request gives exactly the hosted symptom: devices exist (their hellos), but there is no
  compressor pressure, no generator state and no machine data.
- Freezing between requests makes 60 of the 74 SIM devices stale within one 30 s pause, and the
  compressor, generator and machines show no data again.
- The long-running process shows every value within 20 s.

## Conclusion

Host the backend as **one always-running process** (a container with exactly one worker) that serves the
built frontend, `/api` and `/ws` together. No change to the factory logic is needed for that. D1 does this,
and D3 adds a warm start so a free host that sleeps wakes up into a busy factory instead of an empty one.
