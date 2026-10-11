# Riverside Campus plan (FACTORY_PROMPTS.md F1)

WH-01 (warehouse) and FAC-01 (factory) grow into one campus on the same metre grid (x east, z south, origin = warehouse
north-west corner). `tools/campus/gen_campus.py` patches `backend/world/layout.json` and `backend/world/sites.json`
(idempotent: change the script, run it, commit the JSON). `tests/test_campus.py` checks the result.

Sites are now split by x: **WH-01** is x −14…83, **FAC-01** is x 84…216, both z −12…104. The camera "ALL" view (monitor page) shows both.

```
x:  -14      0         44   58   78  84      104 118        150 158     172    192   216
z                                                                                             
-12  +-----------------------------------------------------------------------------------+
     | green belt                                                                         |
  0  |  WAREHOUSE (WH-01) 44x28        FACTORY 88..140 x 0..26      QC     SUBST  GEN       |
     |  solar roof                     2 lines (line 2 at z=3.5)    LAB    172..188 196..210 |
     |  docks D1-D3 (south)            solar roof                  143..159  corridor x=192  |
 28  |   |yard (truck bays)|           FAC docks | cold room 130..140   WORKSHOP    COMPR.    |
     |   fence, GW-01      [X0]    [cabin][X4]  [X1]  office   [X7]    143..169    172..188  |
 38  |         ... H0 north walkway (z=38.5) ........................................ WATER    |
 40  |=====================  main road z=44 (truck lane)  =================================== |
 44  |    ROAD_E <- WEIGHBRIDGE(64..72) <- GATE_IN     boom barrier x=84      RAW_ROAD x=158  |
 48  |=====================================================================================  |
 52  |  H1 south walkway (z=52) ................................................ H1e .....   |
 56  |  CAR PARK    2W  ADMIN      CANTEEN    MEDICAL  RAW MATERIAL STORE   |    FIRE PUMP    |
     |  EV x6      pk  58..78      88..104    106..114  118..150 x 56..78  docks east wall   |
 76  |                                                                       |    HAZMAT      |
     |  MP-1 (43.5,90)             MP-2 (116,92)            MP-3 (166,88)    |    196..210    |
 98  |=================== south road z=98 =================================================== |
104  +-----------------------------------------------------------------------------------+
```

## Flows

- **Trucks:** ROAD_E → WEIGH (weighbridge) → GATE_IN → yard → docks → exit. Raw material trucks: service road → RD_158 → RAW_ROAD (x=158) → RAW_BAY_1/2, reversing into the raw store's east wall.
- **Material:** raw store → RAW_N (north door) → across the road and walkway (crossing X7) → FAC_YARD → factory south door → FAC_AISLE_1 → production (line 1 at z=9, line 2 at z=3.5) → QC bench → FAC_OUT → link road → warehouse → dock bays.
- **People** use walkways only (kinds `[]` in the graph) and cross roads only at marked crossings:

| Crossing | At | Crosses |
|---|---|---|
| X0 | x −1.5 | main road (warehouse fence walkway ↔ south walkway) |
| X1 | x 96 | main road (factory office ↔ canteen / south walkway) |
| X3 | x 192 | main road / service road (utilities ↔ fire pump, hazmat) |
| X4 | x 79 | main road (security cabin ↔ south walkway, the gate) |
| X7 | x 130 | the raw-material forklift route (north walkway) |

Each crossing has a **hotspot** (proximity warnings are most likely there): `campus.crossings[].hotspot`.

## Zones

Every building is a zone with hazard (`low/medium/high`), required PPE and, where it matters, restricted roles, a lone-worker rule
or a time limit (K3). Hazmat is bunded and at least 12 m from every occupied building; its door is on the west wall, reached by a
long walkway from the east muster route. Generator, substation, compressor room and ETP are lone-worker zones (check-in every 10 min).

## Devices (K2 kits, sensible counts)

Gate 1, parking 1 (EV charger feeder), admin 3, canteen 3, medical 1, raw store 4, manufacturing hall (line 2: 2 machine monitors,
1 conveyor monitor, plus the existing ones), QC lab 2, workshop 3, substation 3, generator 2, compressor room 3, water tanks 2,
ETP 3, hazmat 4, fire pump house 3. 38 new simulated devices; the real board GW-01 is unchanged. Six new workers with badges
(security guard, maintenance, utilities operator, ETP operator, canteen staff, first aider) walk the walkways.

## Not done here (later prompts)

3D buildings (F2), simulated utilities and scenarios (F3), level of detail and mini-map (F4). Dock records (`docks`) for the raw
store are deliberately not registered: trucks are not assigned to them by the movement engine yet; the nodes exist and are tested.
