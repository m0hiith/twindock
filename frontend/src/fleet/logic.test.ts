/// <reference types="node" />
// Run with: npm test (node --test, native TypeScript type stripping).
import assert from "node:assert/strict";
import test from "node:test";
import type { Device } from "../contract";
import { applyFilter, attentionReasons, DEFAULT_FILTER, needsAttention, signalBars, sortDevices, summarize } from "./logic.ts";

function dev(id: string, over: Partial<Device> = {}): Device {
  return {
    id, site_id: "FAC-01", zone_id: "FAC01_PRODUCTION", type: "env_sensor", protocol: "thread", capabilities: [],
    x: 0, z: 0, last_seen_ms: 1, source: "sim", status: "online", readings: {}, battery_pct: 80, ...over,
  };
}

test("needs attention: stale, offline, fault, battery below 20%", () => {
  assert.equal(needsAttention(dev("A-01")), false);
  assert.equal(needsAttention(dev("A-01", { status: "stale" })), true);
  assert.equal(needsAttention(dev("A-01", { status: "offline" })), true);
  assert.equal(needsAttention(dev("A-01", { status: "fault" })), true);
  assert.equal(needsAttention(dev("A-01", { battery_pct: 19.9 })), true);
  assert.equal(needsAttention(dev("A-01", { battery_pct: 20 })), false);
  assert.equal(needsAttention(dev("A-01", { battery_pct: null })), false); // mains powered
  assert.deepEqual(attentionReasons(dev("A-01", { status: "fault", battery_pct: 5 })), ["fault", "low battery"]);
});

test("real devices always sort first, then worst problem, then id", () => {
  const list = [
    dev("ZZ-01", { status: "fault" }),
    dev("BB-01"),
    dev("GW-01", { source: "device", type: "gateway", protocol: "wifi", status: "offline" }),
    dev("AA-01", { status: "stale" }),
    dev("CC-01", { battery_pct: 10 }),
    dev("AB-01"),
  ];
  assert.deepEqual(sortDevices(list).map((d) => d.id), ["GW-01", "ZZ-01", "AA-01", "CC-01", "AB-01", "BB-01"]);
  // a healthy real device still beats a faulty simulated one
  const healthyReal = dev("GW-01", { source: "device", status: "online" });
  assert.equal(sortDevices([dev("XX-01", { status: "fault" }), healthyReal])[0]?.id, "GW-01");
});

test("default filter is needs attention; other filters combine", () => {
  const list = [
    dev("A-01"), dev("B-01", { status: "stale", protocol: "ble" }), dev("C-01", { battery_pct: 12, site_id: "WH-01" }),
    dev("GW-01", { source: "device", status: "online", type: "gateway", protocol: "wifi" }),
  ];
  assert.deepEqual(applyFilter(list, DEFAULT_FILTER).map((d) => d.id), ["B-01", "C-01"]);
  const all = { ...DEFAULT_FILTER, attentionOnly: false };
  assert.deepEqual(applyFilter(list, all).map((d) => d.id), ["GW-01", "B-01", "C-01", "A-01"]);
  assert.deepEqual(applyFilter(list, { ...all, site: "WH-01" }).map((d) => d.id), ["C-01"]);
  assert.deepEqual(applyFilter(list, { ...all, protocol: "ble" }).map((d) => d.id), ["B-01"]);
  assert.deepEqual(applyFilter(list, { ...all, source: "device" }).map((d) => d.id), ["GW-01"]);
});

test("summary counts", () => {
  const s = summarize([dev("A-01"), dev("B-01", { status: "offline", protocol: "wifi" }), dev("GW-01", { source: "device", protocol: "wifi" })]);
  assert.equal(s.total, 3);
  assert.equal(s.online, 2);
  assert.equal(s.attention, 1);
  assert.equal(s.real, 1);
  assert.deepEqual(s.byProtocol.wifi, { total: 2, online: 1 });
});

test("signal bars", () => {
  assert.equal(signalBars(-50), 4);
  assert.equal(signalBars(-70), 2);
  assert.equal(signalBars(-95), 0);
  assert.equal(signalBars(null), 0);
});
