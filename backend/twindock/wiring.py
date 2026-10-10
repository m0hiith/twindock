"""hardware/wiring.json, served as-is to the /wiring page.

Read on every request (the file is small) so edits to wiring.json show up on reload without a
backend restart. Sensor readings are not merged in here yet: the page reads them from
gateway_update, and W2 may add a per-part `latest` block alongside this.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contract import first_error, validator

# Repo layout: <repo>/hardware/wiring.json. A Vercel deploy only bundles backend/, so its build
# step copies the file to backend/hardware/wiring.json (see vercel.json); that copy is git-ignored.
_HERE = Path(__file__).resolve()
WIRING = next(
    (p for p in (_HERE.parents[2] / "hardware" / "wiring.json", _HERE.parents[1] / "hardware" / "wiring.json")
     if p.is_file()),
    _HERE.parents[2] / "hardware" / "wiring.json",
)


class WiringInvalid(Exception):
    pass


def load_wiring() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(WIRING.read_text())
    err = first_error(validator("hardware/wiring"), data)
    if err:
        raise WiringInvalid(f"hardware/wiring.json does not match its schema: {err}")
    return data
