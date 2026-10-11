# Device kits plan (FACTORY_PROMPTS.md K0–K2)

One kit = one JSON file in `hardware/kits/`, validated by `shared/schemas/hardware/wiring.json`
and `backend/twindock/wiring.py::validate_kit`. A device in `backend/world/sites.json` names its kit.

| Piece | Where |
|---|---|
| Kit files | `hardware/kits/<kit_id>.json` (FL-01 = `fl01_sensor_pack`, status `built`) |
| Schema | `shared/schemas/hardware/wiring.json`: `kit`, `bom` added; `board_drawing` optional |
| Backend | `GET /api/kits`, `GET /api/kits/{id}`, `GET /api/wiring` (= FL-01) |
| Validation | `validate_kit` + `tests/test_kits.py` (runs over every file) |
| Pages | `/kits` (cards), `/wiring/:kit_id` (picker, banner, three views) |
| Attachment | `kit` on a device in `sites.json` (one design, many devices) |

Kits without a photographed dev board have no `board_drawing`; the breadboard view lays the
processor out as a module at the top of a tree. K1 replaces that with true-scale top-view part drawings.

Decisions: see DECISIONS.md ("Factory extension").

## K2: reference kits

`tools/kits/gen_reference_kits.py` writes the 15 reference kits (run from the repo root; it overwrites
those files, so edit the script and regenerate). Every kit validates with `validate_kit`.

| Kit | Asset | Radio | Power | Devices |
|---|---|---|---|---|
| fl01_sensor_pack | forklift | Wi-Fi SiWx917 | USB | GW-01 (real, **built**) |
| truck_telematics | truck | Wi-Fi SiWx917 | vehicle 12/24 V | TT-01, TT-02 |
| dock_bay | dock | Wi-Fi SiWx917 | 24 V mains | DB-01, DB-02 |
| pallet_asset_tag | pallet | BLE EFR32BG22 | CR2032 | AT-01 |
| machine_monitor | machine | Wi-Fi SiWx917 | 24 V mains | MM-01, MM-02 |
| conveyor_monitor | conveyor | Wi-Fi SiWx917 | 24 V mains | CV-01 |
| compressor_monitor | utility | Wi-Fi SiWx917 | 24 V mains | CP-01 |
| worker_badge | worker | BLE EFR32BG27 | LiPo 300 mAh | BG-01 … BG-04 |
| smart_helmet_clip | worker | BLE EFR32BG22 | CR2032 | HC-01 |
| env_node | environment | Thread EFR32MG24 | USB + LiPo back-up | EN-04 |
| gas_detector_node | environment | Wi-Fi SiWx917 | 24 V mains | GD-01 |
| door_access | building | Thread EFR32MG24 | 12 V | DR-01 |
| energy_meter | energy | Wi-Fi SiWx917 | DIN-rail 5 V | PM-01 |
| water_leak_node | building | Thread EFR32MG24 | 2 × AA | LK-01 |
| tank_level_node | utility | Thread EFR32MG24 | USB | TL-01 |
| fire_panel_bridge | fire | Wi-Fi SiWx917 | 24 V panel aux | FP-01 |

Each kit lists the channels it `publishes`; a device's capabilities must be a subset (test), and the
simulator (`tools/sim_models.py`) publishes them with `source: "sim"`.
