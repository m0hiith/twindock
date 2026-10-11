import assert from "node:assert/strict";
import test from "node:test";
import { fmtS, median, reportStats } from "./stats.ts";

const inc = (rule: string, sev: string, response: number | null, resolution: number | null, state = "resolved") =>
  ({ id: rule, rule_id: rule, severity: sev, state, response_s: response, resolution_s: resolution }) as never;

test("median and time formatting", () => {
  assert.equal(median([]), null);
  assert.equal(median([3, 1, 2]), 2);
  assert.equal(median([1, 2, 3, 10]), 2.5);
  assert.equal(fmtS(null), "—");
  assert.equal(fmtS(42), "42 s");
  assert.equal(fmtS(150), "2.5 min");
});

test("report stats count severities, near-misses and open alerts", () => {
  const d = { incidents: [inc("proximity_critical", "critical", 10, 60), inc("sos", "critical", 20, null, "raised"), inc("heat_stress", "info", null, 30),
    inc("conveyor_jam", "warning", 6, 40)] } as never;
  const s = reportStats(d);
  assert.deepEqual(s.bySev, { critical: 2, warning: 1, info: 1 });
  assert.equal(s.total, 4);
  assert.equal(s.nearMisses, 1);
  assert.equal(s.open, 1);
  assert.equal(s.unacked, 1);
  assert.equal(s.medianResponse, 10);
  assert.equal(s.safetyAlerts, 3); // conveyor jam is not a safety alert
});
