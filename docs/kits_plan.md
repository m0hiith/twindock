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
