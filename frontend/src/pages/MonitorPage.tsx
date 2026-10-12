// /monitor: the control-room view for a wall display (1920 × 1080, no page scrolling).
// Left: the 3D campus from above with alerts pulsing where they happened. Right: open alerts and the incident timeline,
// worker safety and evacuation. Bottom strip: production, logistics, energy, environment, device health and the real board.
// Everything is read from the server; every tile says whether it is real (GW-01) or simulated.
import { useEffect, useMemo, useState } from "react";
import { AlertRow, type Alert } from "../hud/AlertsPanel";
import { Brand } from "../hud/Brand";
import { InspectCard } from "../hud/InspectCard";
import { CameraMenu } from "../hud/CameraMenu";
import { LivePill } from "../hud/LivePill";
import { MiniMap } from "../hud/MiniMap";
import { Search } from "../hud/Search";
import { kpiCounts } from "../hud/kpis";
import { PageTabs } from "../hud/PageTabs";
import { SafetyPanel } from "../hud/SafetyPanel";
import { ago, Icon, LiveBadge, Pill, SimBadge, TabButton, selectAndCenter, useTick } from "../hud/ui";
import { zoneName } from "../fleet/format";
import { exportDailyReport } from "../monitor/report";
import { fmtS, median, reportStats } from "../monitor/stats";
import { useMonitor, type Incident, type MonitorData } from "../monitor/useMonitor";
import { Scene } from "../scene/Scene";
import { useView, useWorld } from "../store/world";

const NO_ALERTS: Alert[] = [];

export function MonitorPage() {
  const data = useMonitor();
  const [tab, setTab] = useState<"open" | "timeline">("open");
  const setSite = useView((s) => s.setSite);
  useEffect(() => { setSite("ALL"); }, [setSite]); // the overview camera: every site in view
  return (
    <div className="flex h-full w-full flex-col gap-3 overflow-hidden p-4">
      <header className="card flex h-[56px] shrink-0 items-center gap-4 px-4">
        <Brand />
        <span className="text-[15px] font-semibold">Monitoring centre</span>
        <span className="hidden text-[13px] text-ink-2 2xl:inline">Riverside campus</span>
        <PageTabs className="ml-4" />
        <Search />
        <div className="ml-auto"><LivePill /></div>
      </header>
      <div className="flex min-h-0 flex-1 gap-3">
        <section className="card relative min-w-0 flex-1 overflow-hidden" aria-label="Campus map">
          <Scene alertPulses />
          <div className="pointer-events-none absolute right-3 top-3 z-10 flex flex-col items-end gap-2"><InspectCard /></div>
          <div className="pointer-events-none absolute bottom-3 right-3 z-10"><MiniMap /></div>
          <div className="card pointer-events-auto absolute left-3 top-3 z-10 flex flex-col"><CameraMenu /></div>
          <div className="pointer-events-none absolute bottom-3 left-3 rounded-lg bg-white/90 px-2.5 py-1 text-[12px] text-ink-2">
            Pulsing rings are open alerts · click any unit, worker or device to inspect it
          </div>
        </section>
        <aside className="flex w-[480px] shrink-0 flex-col gap-3">
          <div className="card flex min-h-0 flex-[11] flex-col overflow-hidden" aria-label="Alerts">
            <div className="flex items-center gap-1 border-b border-[var(--card-border)] p-1.5">
              <TabButton active={tab === "open"} onClick={() => setTab("open")}>Open alerts</TabButton>
              <TabButton active={tab === "timeline"} onClick={() => setTab("timeline")}>Incident timeline</TabButton>
              {tab === "timeline" && (<>
                <button type="button" disabled={!data} onClick={() => data && exportDailyReport(data)}
                  className="ml-auto h-8 rounded-lg bg-accent px-3 text-[12px] font-medium text-white hover:brightness-95 disabled:opacity-50">Daily report (PDF)</button>
                <a href="/api/report/shift.pdf?which=current" download
                  className="flex h-8 items-center rounded-lg border border-[var(--card-border)] bg-white px-3 text-[12px] font-medium hover:bg-idle-bg">Shift report (PDF)</a>
                <a href="/api/report/shift.pdf?which=previous" download
                  className="flex h-8 items-center rounded-lg border border-[var(--card-border)] bg-white px-3 text-[12px] font-medium hover:bg-idle-bg">Previous shift</a>
              </>)}
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto px-4">{tab === "open" ? <OpenAlerts /> : <Timeline data={data} />}</div>
          </div>
          <SafetyPanel compact className="w-full max-h-[52%] shrink-0 overflow-y-auto" onFocusWorker={(id) => selectAndCenter(id)} />
        </aside>
      </div>
      <Strip data={data} />
    </div>
  );
}

function OpenAlerts() {
  const alerts = useWorld((s) => s.alerts?.alerts ?? NO_ALERTS);
  useTick(2000);
  const open = alerts.filter((a) => a.state !== "resolved");
  const shown = open.slice(0, 6);
  if (open.length === 0) return <div className="flex items-center gap-2 py-6 text-ink-2"><Icon name="check" className="text-ok" /> No open alerts</div>;
  return (
    <div className="divide-y divide-[var(--card-border)]">
      {shown.map((a) => <AlertRow key={a.id} a={a} compact stay />)}
      {open.length > shown.length && <div className="py-2 text-[12px] text-ink-2">+ {open.length - shown.length} more (switch to the timeline)</div>}
    </div>
  );
}

function Timeline({ data }: { data: MonitorData | null }) {
  useTick(5000);
  if (!data) return <div className="py-6 text-ink-2">Loading…</div>;
  const st = reportStats(data);
  return (
    <div className="flex flex-col gap-2 py-2">
      <div className="grid grid-cols-4 gap-2 text-center text-[12px] text-ink-2">
        <div><b className="tabular block text-[17px] text-ink">{st.total}</b>alerts, 24 h</div>
        <div><b className="tabular block text-[17px] text-ink">{fmtS(st.medianResponse)}</b>median response</div>
        <div><b className="tabular block text-[17px] text-ink">{fmtS(st.medianResolution)}</b>median resolution</div>
        <div><b className="tabular block text-[17px] text-ink">{st.unacked}</b>not acknowledged</div>
      </div>
      {data.incidents.length === 0 && <div className="py-4 text-ink-2">No alerts in the last 24 h.</div>}
      <div className="divide-y divide-[var(--card-border)]">
        {data.incidents.slice(0, 40).map((a) => <TimelineRow key={a.id} a={a} />)}
      </div>
    </div>
  );
}

function TimelineRow({ a }: { a: Incident }) {
  const tone = a.state === "resolved" ? "idle" : a.severity === "critical" ? "crit" : a.severity === "warning" ? "warn" : "info";
  return (
    <div className="py-1.5 text-[12px]">
      <div className="flex items-center gap-2">
        <Pill tone={tone}>{a.state === "resolved" ? "Resolved" : a.severity}</Pill>
        <span className="tabular text-ink-2">{new Date(a.raised_ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</span>
        <span className="min-w-0 flex-1 truncate text-[13px] text-ink">{a.message}</span>
      </div>
      <div className="mt-0.5 pl-1 text-ink-2">
        {a.acknowledged_by ? `Acknowledged by ${a.acknowledged_by} after ${fmtS(a.response_s)}` : a.state === "resolved" ? "Resolved without acknowledgement" : "Not acknowledged yet"}
        {a.resolution_s !== null ? ` · resolved after ${fmtS(a.resolution_s)}` : ""}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ bottom strip

function Tile({ title, badge, children }: { title: string; badge?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="card flex min-w-0 flex-1 flex-col gap-1 p-3">
      <div className="flex items-center gap-2 text-[13px] text-ink-2">{title}<span className="ml-auto">{badge}</span></div>
      {children}
    </div>
  );
}
const Big = ({ children }: { children: React.ReactNode }) => <div className="tabular text-[28px] font-semibold leading-none">{children}</div>;
const Sub = ({ children }: { children: React.ReactNode }) => <div className="truncate text-[12px] text-ink-2">{children}</div>;

function Strip({ data }: { data: MonitorData | null }) {
  const units = useWorld((s) => s.units);
  const production = useWorld((s) => s.production);
  const devices = useWorld((s) => s.devices);
  const gateway = useWorld((s) => s.gateway);
  const sites = useWorld((s) => s.sites);
  useTick(1000);
  const k = useMemo(() => kpiCounts(units), [units]);
  const list = Object.values(devices);
  const sim = list.filter((d) => d.source === "sim");
  const online = sim.filter((d) => d.status === "online").length;
  const low = sim.filter((d) => d.battery_pct !== null && d.battery_pct !== undefined && d.battery_pct < 20).length;
  const stale = sim.filter((d) => d.status === "stale" || d.status === "offline").length;
  // Worst air quality: the zone whose CO₂ or PM2.5 is closest to its limit (1000 ppm, 25 µg/m³).
  const air = sim.flatMap((d) => {
    const co2 = d.readings.co2_ppm?.value, pm = d.readings.pm25_ugm3?.value;
    if (d.status !== "online" || (typeof co2 !== "number" && typeof pm !== "number")) return [];
    const score = Math.max(typeof co2 === "number" ? co2 / 1000 : 0, typeof pm === "number" ? pm / 25 : 0);
    return [{ zone: d.zone_id, co2, pm, score }];
  }).sort((a, b) => b.score - a.score)[0];
  const gw = list.find((d) => d.source === "device" && d.type === "gateway");
  const rssi = gateway?.status?.data.wifi_rssi_dbm;
  const e = data?.energy;
  const line = production?.line;
  return (
    <div className="grid h-[132px] shrink-0 grid-cols-6 gap-3" aria-label="Campus status">
      <Tile title="Production" badge={<SimBadge />}>
        <Big>{line ? line.units_today : "—"} <span className="text-[13px] font-normal text-ink-2">units</span></Big>
        <Sub>OEE {line?.oee == null ? "—" : `${Math.round(line.oee * 100)}%`} · availability {line?.availability == null ? "—" : `${Math.round(line.availability * 100)}%`}</Sub>
      </Tile>
      <Tile title="Logistics">
        <Big>{k.trucksOnSite} <span className="text-[13px] font-normal text-ink-2">trucks on site</span></Big>
        <Sub>{k.docksInUse} of {k.docksUsable} docks busy · {k.trucksDocked} docked</Sub>
      </Tile>
      <Tile title="Energy" badge={<SimBadge />}>
        <Big>{data?.power?.demand_kw == null ? "—" : data.power.demand_kw.toFixed(0)} <span className="text-[13px] font-normal text-ink-2">kW demand</span></Big>
        <Sub>{data?.power?.grid_ok === false ? `GRID FAILURE · generator ${data.power.generator_kw?.toFixed(0) ?? "—"} kW` : `Solar ${data?.power?.solar_kw.toFixed(0) ?? "—"} kW (computed)`} · today {e?.today_kwh == null ? "—" : `${e.today_kwh.toFixed(0)} kWh`} · yesterday {e?.yesterday_kwh == null ? "no data yet" : `${e.yesterday_kwh.toFixed(0)} kWh`}</Sub>
      </Tile>
      <Tile title="Air quality" badge={<SimBadge />}>
        {air ? (<><Big>{air.co2 === undefined ? "" : Math.round(Number(air.co2))} <span className="text-[13px] font-normal text-ink-2">ppm CO₂</span></Big>
          <Sub>Worst: {zoneName(sites, air.zone)}{air.pm === undefined ? "" : ` · PM2.5 ${Number(air.pm).toFixed(0)} µg/m³`}</Sub></>) : <><Big>—</Big><Sub>No air-quality reading yet</Sub></>}
      </Tile>
      <Tile title="Device health" badge={<SimBadge />}>
        <Big>{sim.length ? Math.round((online / sim.length) * 100) : "—"}<span className="text-[15px] text-ink-2">% online</span></Big>
        <Sub>{low} low batteries · {stale} stale or offline</Sub>
      </Tile>
      <Tile title="GW-01 · real board" badge={<LiveBadge />}>
        <div className={`flex items-center gap-2 text-[20px] font-semibold ${gw?.status === "online" ? "text-live" : "text-idle"}`}>
          <span className={`h-2.5 w-2.5 rounded-full ${gw?.status === "online" ? "bg-live" : "bg-idle"}`} />
          {gw?.status === "online" ? "Online" : gw?.last_seen_ms ? "Offline" : "Waiting for device"}
        </div>
        <Sub>{rssi === undefined || rssi === null ? "No Wi-Fi reading yet" : `Wi-Fi ${rssi} dBm`}{gw?.last_seen_ms ? ` · ${ago(gw.last_seen_ms)}` : ""}</Sub>
      </Tile>
    </div>
  );
}

// kept for the tests of the strip's pure helpers
export const _internal = { median };
