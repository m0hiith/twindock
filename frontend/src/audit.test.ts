/// <reference types="node" />
// Value-source audit (SITE_PROMPTS.md S10 item 3). Violet LIVE styling is reserved for real board
// data (CLAUDE.md). Every place that can render it is listed here with the reason it can only show
// real data. A new usage fails this test until someone reviews it and adds it, so a simulated value
// can't quietly start looking LIVE. See docs/value_audit.md for every value on every page.
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import test from "node:test";
import { deviceTone, toneOf } from "./status.ts";

const ROOT = import.meta.dirname;
const LIVE = /LiveBadge \/>|text-live|color\.live|var\(--live\)|bg-\[#F3EDFF\]|tone=\{gw\?\.online \? "live"/g;

// file -> [expected count, why it can only show real data]
const ALLOWED: Record<string, [number, string]> = {
  "hud/ui.tsx": [3, "LiveBadge definition; SourceProtocol picks LIVE only when d.source === \"device\""],
  "hud/InspectCard.tsx": [4, "unit.source === \"device\" (gateway, BLE-tracked forklifts)"],
  "hud/DeviceInspect.tsx": [2, "live = d.source === \"device\" (GW-01, RB-01)"],
  "hud/FleetTable.tsx": [1, "u.source === \"device\""],
  "hud/Search.tsx": [1, "u.source === \"device\""],
  "hud/ShipmentPanel.tsx": [1, "t.source === \"device\""],
  "hud/SelectionPill.tsx": [2, "u.source === \"device\""],
  "control/MovePanel.tsx": [3, "device = unit.source === \"device\""],
  "control/GatewayPanel.tsx": [8, "the real board's own panel (gateway messages only)"],
  "control/SiteMap.tsx": [4, "gateway pole/range ring (real board) and units with source === \"device\""],
  "control/DemoPanel.tsx": [2, "real-board section: GW-01 online state from gateway messages"],
  "device/BleCalibration.tsx": [3, "real BLE tracks from twin/gateway/ble"],
  "device/RssiChart.tsx": [2, "RSSI history from real ble_tracks"],
  "wiring/PartPanel.tsx": [2, "readings from gateway.sensors (real board) while online"],
  "wiring/BreadboardView.tsx": [3, "readings from gateway.sensors (real board)"],
  "pages/WiringPage.tsx": [2, "board online state"],
  "scene/GatewayPole.tsx": [4, "the real board's pole and BLE ring"],
  "status.ts": [1, "tone colour table; deviceTone() gives live only to source device (tested below)"],
  "scene/DevicePucks.tsx": [1, "tone map; deviceTone() returns live only for source device (tested below)"],
};

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) return f === "contract" ? [] : files(p);
    return /\.tsx?$/.test(f) && !f.endsWith(".test.ts") ? [p] : [];
  });
}

test("every violet LIVE usage is reviewed", () => {
  const found: Record<string, number> = {};
  for (const f of files(ROOT)) {
    const n = (readFileSync(f, "utf8").match(LIVE) ?? []).length;
    if (n) found[relative(ROOT, f)] = n;
  }
  const expected = Object.fromEntries(Object.entries(ALLOWED).map(([k, v]) => [k, v[0]]));
  assert.deepEqual(found, expected,
    "LIVE styling changed. Make sure it can only show real board data, then update ALLOWED in audit.test.ts and docs/value_audit.md.");
});

test("site-twin views never use LIVE styling", () => {
  const simOnly = ["scene/ProductionLine.tsx", "scene/Workers.tsx", "scene/Factory.tsx", "hud/ProductionKpis.tsx",
    "hud/MachineRows.tsx", "hud/WorkerRows.tsx", "hud/SafetyPanel.tsx", "hud/SiteDevicesCard.tsx", "control/ProductionPanel.tsx"];
  for (const f of simOnly) assert.equal((readFileSync(join(ROOT, f), "utf8").match(LIVE) ?? []).length, 0, f);
});

test("simulated data can never get the live tone", () => {
  for (const status of ["online", "stale", "offline", "fault"]) {
    assert.notEqual(deviceTone({ status, source: "sim" }), "live");
  }
  assert.equal(deviceTone({ status: "online", source: "device" }), "live");
  for (const state of ["running", "idle", "fault", "maintenance", "no_data"]) assert.notEqual(toneOf({ kind: "machine", state }), "live");
  for (const state of ["walking", "working", "no_data"]) assert.notEqual(toneOf({ kind: "worker", state }), "live");
});
