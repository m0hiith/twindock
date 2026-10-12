// Inspect card for a selected site device (twin page). Every value has its age next to it.
import type { Device } from "../contract";
import { channelLabel, formatReading, readingEntries, zoneName } from "../fleet/format";
import { TYPE_LABEL } from "../fleet/logic";
import { SignalBars } from "../fleet/ui";
import { deviceTone } from "../status";
import { send } from "../store/ws";
import { useView, useWorld } from "../store/world";
import { navigate } from "./PageTabs";
import { ago, Icon, Pill, SourceProtocol, useTick } from "./ui";

export function DeviceInspect({ d }: { d: Device }) {
  const sites = useWorld((s) => s.sites);
  useTick(1000);
  const live = d.source === "device";
  const btn = "grid h-8 w-8 place-items-center rounded-lg text-ink-2 transition-colors hover:bg-idle-bg hover:text-ink";
  return (
    <div className="card pointer-events-auto max-h-[calc(100vh-250px)] min-h-0 w-[340px] overflow-y-auto p-4" aria-label={`${d.id} details`}>
      <div className="flex items-start gap-3">
        <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${live ? "bg-[#F3EDFF] text-live" : "bg-idle-bg text-ink-2"}`}>
          <Icon name="sensor" size={20} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="text-[12px] text-ink-2">{TYPE_LABEL[d.type]} · {d.site_id}</div>
          <div className="text-[20px] font-semibold leading-tight">{d.id}</div>
          <div className="truncate text-ink-2">{d.label}</div>
        </div>
        <div className="-mr-1 -mt-1 flex">
          <button type="button" className={btn} aria-label="Locate" title="Locate" onClick={() => useView.getState().focusOn(d.x, d.z)}><Icon name="locate" /></button>
          <button type="button" className={btn} aria-label="Open in Fleet" title="Open in Fleet" onClick={() => navigate(`/fleet?device=${encodeURIComponent(d.id)}`)}><Icon name="open" /></button>
          <button type="button" className={btn} aria-label="Close" title="Close" onClick={() => send({ type: "select_unit", unit_id: null })}><Icon name="close" /></button>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Pill tone={deviceTone(d)}>{d.status.charAt(0).toUpperCase() + d.status.slice(1)}</Pill>
        <SourceProtocol d={d} />
        <span className="text-[12px] text-ink-2">{d.last_seen_ms ? `seen ${ago(d.last_seen_ms)}` : "never seen"}</span>
      </div>
      {d.fault && <div className="mt-2 rounded-lg bg-crit-bg px-3 py-2 text-[13px] text-crit">Fault: {d.fault}</div>}
      <div className="mt-3 divide-y divide-[var(--card-border)] border-t border-[var(--card-border)] pt-1">
        {readingEntries(d).map(([ch, r]) => (
          <div key={ch} className="flex items-center justify-between gap-3 py-1.5 text-[13px]">
            <span className="text-ink-2">{channelLabel(ch)}</span>
            <span><span className="tabular font-medium">{formatReading(ch, r)}</span> <span className="text-[11px] text-ink-2">· {ago(r.received_ms)}</span></span>
          </div>
        ))}
        {Object.keys(d.readings).length === 0 && <div className="py-1.5 text-[13px] text-ink-2">{live ? "Waiting for device" : "No reading yet"}</div>}
        <div className="flex items-center justify-between py-1.5 text-[13px]"><span className="text-ink-2">Zone</span><span className="font-medium">{zoneName(sites, d.zone_id)}</span></div>
        <div className="flex items-center justify-between py-1.5 text-[13px]"><span className="text-ink-2">Battery</span>
          <span className="font-medium">{typeof d.battery_pct === "number" ? `${Math.round(d.battery_pct)}%` : d.source === "sim" && d.protocol === "wifi" ? "Mains" : "—"}</span></div>
        <div className="flex items-center justify-between py-1.5 text-[13px]"><span className="text-ink-2">Signal</span><SignalBars rssi={d.rssi_dbm} /></div>
        <div className="flex items-center justify-between py-1.5 text-[13px]"><span className="text-ink-2">Firmware</span><span className="font-medium">{d.fw_version ?? "—"}</span></div>
      </div>
    </div>
  );
}
