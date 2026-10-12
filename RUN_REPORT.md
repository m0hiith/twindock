# Run report: deployment and a cause-and-effect simulation

What was asked: [REALISM_DEPLOY_PROMPTS.md](REALISM_DEPLOY_PROMPTS.md), single-stretch: D0, D1, D3, R0, R1, R2, R5, R3, R4, R6, R7, D2, R8, one commit per prompt, decisions in [DECISIONS.md](DECISIONS.md). The previous run's report is [docs/RUN_REPORT_factory_extension.md](docs/RUN_REPORT_factory_extension.md).

_This report is completed at the end of the run (D2, R8, deploy steps)._

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
