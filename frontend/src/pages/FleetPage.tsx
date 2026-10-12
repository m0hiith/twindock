// /fleet: every device across sites, real (GW-01, LIVE) and simulated (SIM), with health,
// protocol, battery, signal, firmware and a live "last seen" age.
import { useMemo, useState } from "react";
import type { Device } from "../contract";
import { DevicePanel } from "../fleet/DevicePanel";
import { channelLabel, formatReading, zoneName } from "../fleet/format";
import { applyFilter, attentionReasons, DEFAULT_FILTER, MAIN_CHANNEL, summarize, TYPE_LABEL, type FleetFilter } from "../fleet/logic";
import { SignalBars } from "../fleet/ui";
import { Brand } from "../hud/Brand";
import { LivePill } from "../hud/LivePill";
import { PageTabs } from "../hud/PageTabs";
import { ago, Bar, batteryColor, Icon, Pill, protocolLabel, SourceProtocol, useTick } from "../hud/ui";
import { deviceTone } from "../status";
import { useWorld } from "../store/world";

function Stat({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: string }) {
  return (
    <div className="card flex min-w-0 flex-1 flex-col gap-1 p-4">
      <span className="text-[13px] text-ink-2">{label}</span>
      <span className="tabular text-[28px] font-semibold leading-none" style={tone ? { color: tone } : undefined}>{value}</span>
      {sub && <span className="truncate text-[12px] text-ink-2">{sub}</span>}
    </div>
  );
}

function Select<T extends string>({ label, value, options, onChange }: {
  label: string; value: T | null; options: { value: T; label: string }[]; onChange: (v: T | null) => void;
}) {
  return (
    <label className="flex items-center gap-1.5 text-[13px] text-ink-2">
      {label}
      <select value={value ?? ""} onChange={(e) => onChange((e.target.value || null) as T | null)}
        className="h-8 rounded-lg border border-[var(--card-border)] bg-white px-2 text-[13px] text-ink">
        <option value="">All</option>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  );
}

const STATUS_LABEL: Record<Device["status"], string> = { online: "Online", stale: "Stale", offline: "Offline", fault: "Fault" };

export function FleetPage() {
  const devicesMap = useWorld((s) => s.devices);
  const sites = useWorld((s) => s.sites);
  const [filter, setFilter] = useState<FleetFilter>(DEFAULT_FILTER);
  const [openId, setOpenId] = useState<string | null>(() => new URLSearchParams(location.search).get("device"));
  useTick(1000); // live ages
  const devices = useMemo(() => Object.values(devicesMap), [devicesMap]);
  const rows = applyFilter(devices, filter);
  const sum = summarize(devices);
  const set = (p: Partial<FleetFilter>) => setFilter((f) => ({ ...f, ...p }));
  const zones = sites.flatMap((s) => s.zones).filter((z) => !filter.site || z.site_id === filter.site);
  const open = openId ? devicesMap[openId] : undefined;

  return (
    <div className="flex h-full">
      <div className="min-w-0 flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-[1280px] flex-col gap-4 p-4">
          <header className="card flex h-[60px] items-center gap-4 px-4">
            <Brand tight />
            <PageTabs className="ml-2" />
            <div className="ml-auto"><LivePill /></div>
          </header>

          <div className="flex gap-3">
            <Stat label="Devices online" value={`${sum.online}/${sum.total}`} sub={`${sum.real} real (LIVE) · ${sum.total - sum.real} simulated (SIM)`} />
            <Stat label="Needs attention" value={String(sum.attention)} sub="Stale, offline, fault or battery below 20%"
              tone={sum.attention ? "var(--warn)" : undefined} />
            <div className="card flex min-w-0 flex-[2] flex-col gap-2 p-4">
              <span className="text-[13px] text-ink-2">By protocol (online / total)</span>
              <div className="grid grid-cols-4 gap-3">
                {(Object.keys(sum.byProtocol) as Device["protocol"][]).map((p) => {
                  const b = sum.byProtocol[p];
                  return (
                    <div key={p} className="flex flex-col gap-1">
                      <span className="flex items-baseline justify-between text-[13px]">
                        <span className="font-medium">{protocolLabel[p]}</span>
                        <span className="tabular text-ink-2">{b.online}/{b.total}</span>
                      </span>
                      <Bar pct={b.total ? (b.online / b.total) * 100 : 0} color="var(--ok)" />
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="card flex flex-col">
            <div className="flex flex-wrap items-center gap-3 border-b border-[var(--card-border)] p-3">
              <div className="flex rounded-xl bg-idle-bg p-1" role="group" aria-label="Show">
                {[{ v: true, l: `Needs attention · ${sum.attention}` }, { v: false, l: `All devices · ${sum.total}` }].map((o) => (
                  <button key={String(o.v)} type="button" aria-pressed={filter.attentionOnly === o.v} onClick={() => set({ attentionOnly: o.v })}
                    className={`h-7 rounded-lg px-3 text-[13px] font-medium ${filter.attentionOnly === o.v ? "bg-white text-ink shadow-[0_1px_2px_rgba(0,0,0,0.08)]" : "text-ink-2 hover:text-ink"}`}>
                    {o.l}
                  </button>
                ))}
              </div>
              <Select label="Site" value={filter.site} onChange={(v) => set({ site: v, zone: null })}
                options={sites.map((s) => ({ value: s.id, label: s.id }))} />
              <Select label="Zone" value={filter.zone} onChange={(v) => set({ zone: v })}
                options={zones.map((z) => ({ value: z.id, label: `${z.site_id} ${z.name}` }))} />
              <Select label="Type" value={filter.type} onChange={(v) => set({ type: v })}
                options={(Object.keys(TYPE_LABEL) as Device["type"][]).filter((t) => devices.some((d) => d.type === t)).map((t) => ({ value: t, label: TYPE_LABEL[t] }))} />
              <Select label="Protocol" value={filter.protocol} onChange={(v) => set({ protocol: v })}
                options={(Object.keys(protocolLabel) as Device["protocol"][]).map((p) => ({ value: p, label: protocolLabel[p] }))} />
              <Select label="Source" value={filter.source} onChange={(v) => set({ source: v })}
                options={[{ value: "device" as const, label: "Real (LIVE)" }, { value: "sim" as const, label: "Simulated (SIM)" }]} />
            </div>

            <div className="grid grid-cols-[150px_1.3fr_120px_1fr_96px_110px_80px_80px_96px] gap-3 px-4 py-2 text-[12px] text-ink-2">
              <span>Device</span><span>Type · main reading</span><span>Source</span><span>Site · zone</span><span>Status</span>
              <span>Battery</span><span>Signal</span><span>Firmware</span><span>Last seen</span>
            </div>
            {rows.length === 0 && (
              <div className="flex flex-col items-center gap-1 px-4 py-10 text-center">
                <Icon name="check" size={22} className="text-ok" />
                <span className="font-medium">{filter.attentionOnly ? "Nothing needs attention" : "No devices match these filters"}</span>
                {filter.attentionOnly && <button type="button" className="text-[13px] text-ink-2 underline" onClick={() => set({ attentionOnly: false })}>Show all devices</button>}
              </div>
            )}
            {rows.map((d) => {
              const main = MAIN_CHANNEL[d.type];
              const r = main ? d.readings[main] : undefined;
              const reasons = attentionReasons(d);
              return (
                <button key={d.id} type="button" onClick={() => setOpenId(d.id)} aria-current={openId === d.id}
                  className={`grid grid-cols-[150px_1.3fr_120px_1fr_96px_110px_80px_80px_96px] items-center gap-3 border-t border-[var(--card-border)] px-4 py-2.5 text-left transition-colors ${openId === d.id ? "bg-info-bg" : "hover:bg-[#F8F8F8]"}`}>
                  <span className="min-w-0">
                    <span className="block font-semibold">{d.id}</span>
                    <span className="block truncate text-[12px] text-ink-2">{d.label}</span>
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate">{TYPE_LABEL[d.type]}</span>
                    <span className="block truncate text-[12px] text-ink-2">
                      {r && main ? `${channelLabel(main)} ${formatReading(main, r)}` : "—"}
                    </span>
                  </span>
                  <SourceProtocol d={d} />
                  <span className="min-w-0">
                    <span className="block">{d.site_id}</span>
                    <span className="block truncate text-[12px] text-ink-2">{zoneName(sites, d.zone_id)}</span>
                  </span>
                  <span className="flex flex-col items-start gap-0.5">
                    <Pill tone={deviceTone(d)}>{STATUS_LABEL[d.status]}</Pill>
                    {reasons.includes("low battery") && <span className="text-[11px] font-medium text-warn">Low battery</span>}
                  </span>
                  {typeof d.battery_pct === "number" ? (
                    <span className="flex items-center gap-2">
                      <Bar pct={d.battery_pct} color={batteryColor(d.battery_pct)} className="w-12" />
                      <span className="tabular text-[12px]">{Math.round(d.battery_pct)}%</span>
                    </span>
                  ) : <span className="text-[12px] text-ink-2">{d.source === "sim" && d.protocol === "wifi" ? "Mains" : "—"}</span>}
                  <SignalBars rssi={d.rssi_dbm} />
                  <span className="truncate text-[12px] text-ink-2">{d.fw_version ?? "—"}</span>
                  <span className="tabular text-[12px] text-ink-2">{d.last_seen_ms ? ago(d.last_seen_ms) : "Never"}</span>
                </button>
              );
            })}
          </div>
          <p className="px-1 pb-4 text-[12px] text-ink-2">
            GW-01 is the real SiWx917 board (LIVE): every value comes from its own MQTT messages. Every other device is
            produced by tools/site_sim.py (SIM). Online: last message within 15 s; stale: within 60 s; offline: older or never.
          </p>
        </div>
      </div>
      {open && <DevicePanel d={open} onClose={() => setOpenId(null)} />}
    </div>
  );
}
