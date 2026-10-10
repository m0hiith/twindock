// Side panel for one device: latest readings with ages, history of its main reading,
// where it is on the site, and "Show in twin".
import { useEffect, useState } from "react";
import type { Device } from "../contract";
import { navigate } from "../hud/PageTabs";
import { ago, Icon, Pill, SourceProtocol } from "../hud/ui";
import { deviceTone } from "../status";
import { send } from "../store/ws";
import { useView, useWorld } from "../store/world";
import { channelLabel, formatReading, readingEntries, zoneName } from "./format";
import { attentionReasons, MAIN_CHANNEL, TYPE_LABEL } from "./logic";
import { MiniMap, SignalBars, Sparkline } from "./ui";

/** Switch this screen to the device's site, select it (shared) and fly the camera to it. */
export function showInTwin(d: Pick<Device, "id" | "site_id" | "x" | "z">): void {
  const v = useView.getState();
  v.setSite(d.site_id);
  v.setShowDevices(true);
  send({ type: "select_unit", unit_id: d.id });
  v.focusOn(d.x, d.z);
  navigate("/twin");
}

function useHistory(id: string, channel: string | null): [number, number][] {
  const [points, setPoints] = useState<[number, number][]>([]);
  useEffect(() => {
    setPoints([]);
    if (!channel) return;
    let alive = true;
    const load = () =>
      fetch(`/api/devices/${encodeURIComponent(id)}/history?channel=${encodeURIComponent(channel)}`)
        .then((r) => (r.ok ? r.json() : null))
        .then((j: { points?: unknown } | null) => {
          if (alive && j && Array.isArray(j.points)) setPoints(j.points as [number, number][]);
        })
        .catch(() => undefined);
    void load();
    const t = setInterval(load, 5000);
    return () => { alive = false; clearInterval(t); };
  }, [id, channel]);
  return points;
}

function Row({ k, children }: { k: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5 text-[13px]">
      <span className="text-ink-2">{k}</span>
      <span className="min-w-0 truncate text-right font-medium">{children}</span>
    </div>
  );
}

export function DevicePanel({ d, onClose }: { d: Device; onClose: () => void }) {
  const sites = useWorld((s) => s.sites);
  const layout = useWorld((s) => s.layout);
  const devices = useWorld((s) => s.devices);
  const main = MAIN_CHANNEL[d.type];
  const history = useHistory(d.id, main);
  const site = sites.find((s) => s.id === d.site_id);
  const mainReading = main ? d.readings[main] : undefined;
  const reasons = attentionReasons(d);
  const readings = readingEntries(d).sort(([a], [b]) => (a === main ? -1 : b === main ? 1 : a.localeCompare(b)));
  return (
    <aside className="card m-4 ml-0 flex w-[392px] shrink-0 flex-col overflow-hidden" aria-label={`${d.id} details`}>
      <div className="flex items-start gap-3 border-b border-[var(--card-border)] p-4">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-idle-bg"><Icon name="sensor" size={20} /></span>
        <div className="min-w-0 flex-1">
          <div className="text-[12px] text-ink-2">{TYPE_LABEL[d.type]} · {d.site_id}</div>
          <div className="text-[20px] font-semibold leading-tight">{d.id}</div>
          <div className="truncate text-[13px] text-ink-2">{d.label}</div>
        </div>
        <button type="button" aria-label="Close" onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg hover:bg-idle-bg">
          <Icon name="close" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Pill tone={deviceTone(d)}>{d.status.charAt(0).toUpperCase() + d.status.slice(1)}</Pill>
          <SourceProtocol d={d} />
          {reasons.filter((r) => r !== d.status).map((r) => <Pill key={r} tone="warn">{r.charAt(0).toUpperCase() + r.slice(1)}</Pill>)}
        </div>
        {d.fault && <div className="mt-2 rounded-lg bg-crit-bg px-3 py-2 text-[13px] text-crit">Fault reported: {d.fault}</div>}

        <div className="mt-4 text-[13px] font-semibold">Latest readings</div>
        <div className="mt-1 divide-y divide-[var(--card-border)]">
          {readings.length === 0 && <div className="py-2 text-[13px] text-ink-2">{d.source === "device" ? "Waiting for device" : "No reading yet"}</div>}
          {readings.map(([ch, r]) => (
            <div key={ch} className="flex items-center justify-between gap-3 py-1.5 text-[13px]">
              <span className="text-ink-2">{channelLabel(ch)}</span>
              <span className="flex items-baseline gap-2">
                <span className="tabular font-medium">{formatReading(ch, r)}</span>
                <span className="w-14 text-right text-[11px] text-ink-2">{ago(r.received_ms)}</span>
              </span>
            </div>
          ))}
        </div>

        {main && (
          <>
            <div className="mt-4 flex items-baseline justify-between">
              <span className="text-[13px] font-semibold">{channelLabel(main)} history</span>
              <span className="text-[12px] text-ink-2">{d.source === "device" ? "From the board's status" : "Simulated"}</span>
            </div>
            <div className="mt-1.5">
              <Sparkline points={history} unit={mainReading?.unit ?? (main === "wifi_rssi_dbm" ? "dBm" : undefined)}
                step={typeof mainReading?.value === "boolean"} />
            </div>
          </>
        )}

        <div className="mt-4 text-[13px] font-semibold">Device</div>
        <div className="mt-1 divide-y divide-[var(--card-border)]">
          <Row k="Zone">{zoneName(sites, d.zone_id)}</Row>
          <Row k="Battery">{typeof d.battery_pct === "number" ? `${Math.round(d.battery_pct)}%` : d.source === "sim" && d.protocol === "wifi" ? "Mains powered" : "—"}</Row>
          <Row k="Signal"><SignalBars rssi={d.rssi_dbm} /></Row>
          <Row k="Firmware">{d.fw_version ?? "—"}</Row>
          <Row k="Capabilities">{d.capabilities.join(", ") || "—"}</Row>
          {d.attached_to && <Row k="Mounted on">{d.attached_to}</Row>}
          <Row k="Last seen">{d.last_seen_ms ? ago(d.last_seen_ms) : "Never"}</Row>
        </div>

        {layout && site && (
          <>
            <div className="mt-4 text-[13px] font-semibold">Location</div>
            <div className="mt-1.5">
              <MiniMap layout={layout} site={site} device={d}
                others={Object.values(devices).filter((o) => o.site_id === d.site_id && o.id !== d.id)} />
            </div>
          </>
        )}
      </div>
      <div className="border-t border-[var(--card-border)] p-3">
        <button type="button" onClick={() => showInTwin(d)}
          className="flex h-10 w-full items-center justify-center gap-2 rounded-xl bg-[var(--accent)] text-[13px] font-semibold text-white hover:brightness-95">
          <Icon name="locate" /> Show in twin
        </button>
      </div>
    </aside>
  );
}
