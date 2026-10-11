// Daily safety report as a one-page PDF (drawn on a canvas, wrapped by wiring/export.ts: no PDF library).
// Counts, response times and near-misses from the last 24 h of alerts; no worker names, roles only.
import { exportPdf } from "../wiring/export";
import { fmtS, reportStats } from "./stats";
import type { MonitorData } from "./useMonitor";

export function exportDailyReport(d: MonitorData): void {
  const W = 1754, H = 1240;
  const c = document.createElement("canvas");
  c.width = W; c.height = H;
  const g = c.getContext("2d")!;
  g.fillStyle = "#FFFFFF"; g.fillRect(0, 0, W, H);
  const st = reportStats(d);
  const t = d.safety_today;
  const day = new Date().toLocaleDateString([], { weekday: "long", year: "numeric", month: "long", day: "numeric" });
  g.fillStyle = "#D91E2A"; g.fillRect(0, 0, W, 10);
  g.fillStyle = "#111"; g.font = "600 40px Inter, system-ui, sans-serif"; g.fillText("TwinDock · Daily safety report", 60, 90);
  g.fillStyle = "#6B6B6B"; g.font = "22px Inter, system-ui, sans-serif";
  g.fillText(`${day} · Riverside campus · covers the last 24 h · simulated devices (SIM), the real board is GW-01 only`, 60, 130);
  const tiles: [string, string][] = [
    ["Alerts raised", String(st.total)], ["Critical", String(st.bySev.critical)], ["Warnings", String(st.bySev.warning)],
    ["Median response", fmtS(st.medianResponse)], ["Median resolution", fmtS(st.medianResolution)], ["Still open", String(st.open)],
    ["Near-misses (< 1.5 m)", String(st.nearMisses)], ["Falls (cancelled)", `${t.falls} (${t.falls_cancelled})`], ["SOS calls", String(t.sos)],
    ["Restricted entries", String(t.restricted)], ["Closest approach", t.closest_m === null ? "—" : `${t.closest_m.toFixed(1)} m`],
    ["Evacuation drills", d.evacuation_last ? "1 (last: " + d.evacuation_last.reason + ")" : "0"],
  ];
  tiles.forEach(([k, v], i) => {
    const x = 60 + (i % 6) * 280, y = 175 + Math.floor(i / 6) * 120;
    g.fillStyle = "#F5F5F5"; g.beginPath(); g.roundRect(x, y, 262, 100, 14); g.fill();
    g.fillStyle = "#6B6B6B"; g.font = "20px Inter, system-ui, sans-serif"; g.fillText(k, x + 18, y + 34);
    g.fillStyle = "#111"; g.font = "600 34px Inter, system-ui, sans-serif"; g.fillText(v, x + 18, y + 78, 230);
  });
  g.fillStyle = "#111"; g.font = "600 28px Inter, system-ui, sans-serif"; g.fillText("Incidents", 60, 450);
  g.font = "600 18px Inter, system-ui, sans-serif"; g.fillStyle = "#6B6B6B";
  const cols = [60, 170, 330, 1010, 1260, 1430, 1590];
  ["Time", "Severity", "What", "Acknowledged by", "Response", "Resolution"].forEach((h, i) => g.fillText(h, cols[i === 0 ? 0 : i]!, 485));
  g.font = "18px Inter, system-ui, sans-serif";
  const rows = d.incidents.slice(0, 22);
  rows.forEach((a, i) => {
    const y = 520 + i * 30;
    if (i % 2 === 0) { g.fillStyle = "#FAFAFA"; g.fillRect(50, y - 21, W - 100, 30); }
    g.fillStyle = "#111";
    g.fillText(new Date(a.raised_ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }), cols[0]!, y);
    g.fillStyle = a.severity === "critical" ? "#DC2626" : a.severity === "warning" ? "#D97706" : "#6B6B6B";
    g.fillText(a.severity, cols[1]!, y);
    g.fillStyle = "#111";
    g.fillText(a.message.slice(0, 74), cols[2]!, y);
    g.fillText(a.acknowledged_by ?? (a.state === "resolved" ? "—" : "not yet"), cols[3]!, y);
    g.fillText(fmtS(a.response_s), cols[4]!, y);
    g.fillText(a.state === "resolved" ? fmtS(a.resolution_s) : "open", cols[5]!, y);
  });
  if (d.incidents.length > rows.length) { g.fillStyle = "#6B6B6B"; g.fillText(`+ ${d.incidents.length - rows.length} more in the monitoring centre`, 60, 520 + rows.length * 30 + 10); }
  if (d.incidents.length === 0) { g.fillStyle = "#6B6B6B"; g.fillText("No alerts in the last 24 h.", 60, 530); }
  g.fillStyle = "#6B6B6B"; g.font = "16px Inter, system-ui, sans-serif";
  g.fillText("Privacy: roles and zones only, no names; positions are shown only during an alert or an evacuation; incident history is deleted after the retention period.", 60, H - 40);
  exportPdf(c, `twindock-safety-report-${new Date().toISOString().slice(0, 10)}.pdf`);
}
