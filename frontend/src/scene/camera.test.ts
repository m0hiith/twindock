import assert from "node:assert/strict";
import test from "node:test";
import { lodFor, viewCorners } from "./camera.ts";

test("level of detail has hysteresis", () => {
  assert.equal(lodFor(6, "mid"), "far");
  assert.equal(lodFor(9.5, "mid"), "mid");
  assert.equal(lodFor(9.5, "far"), "far"); // stays far until clearly above the threshold
  assert.equal(lodFor(15, "mid"), "mid");
  assert.equal(lodFor(16.5, "mid"), "near");
  assert.equal(lodFor(15, "near"), "near"); // stays near until clearly below
  assert.equal(lodFor(13, "near"), "mid");
});

test("view corners are centred on the target and shrink when zooming in", () => {
  const t = { x: 40, z: 30 };
  const a = viewCorners(t, Math.PI / 4, 10, 1000, 600);
  const cx = a.reduce((s, p) => s + p[0], 0) / 4, cz = a.reduce((s, p) => s + p[1], 0) / 4;
  assert.ok(Math.abs(cx - 40) < 1e-9 && Math.abs(cz - 30) < 1e-9);
  const b = viewCorners(t, Math.PI / 4, 20, 1000, 600);
  const span = (q: [number, number][]) => Math.hypot(q[1]![0] - q[0]![0], q[1]![1] - q[0]![1]);
  assert.ok(Math.abs(span(a) / span(b) - 2) < 1e-9);
  assert.ok(Math.abs(span(a) - 100) < 1e-9); // 1000 px at 10 px/m is 100 m across the top edge
});
