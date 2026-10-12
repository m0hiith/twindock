// Devices in one zone, for the building card: a status summary, then one row per device (problems first) with its
// type, source and protocol ("SIM · Thread"), battery and headline reading with its age. A row opens to show every
// channel the device reports, each with its own age, plus locate / inspect / fleet actions.
import { useState } from "react";
import type { Device } from "../contract";
import { channelLabel, formatReading, readingEntries } from "../fleet/format";
import { attentionReasons, MAIN_CHANNEL, sortDevices, TYPE_LABEL } from "../fleet/logic";
import { toneColor, type Tone } from "../status";
import { send } from "../store/ws";
import { useView } from "../store/world";
import { navigate } from "./PageTabs";
import { ago, Icon, SourceProtocol } from "./ui";

const STATUS_TONE: Record<Device["status"], Tone> = { online: "ok", stale: "warn", offline: "idle", fault: "crit" };
const STATUS_LABEL: Record<Device["status"], string> = { online: "online", stale: "stale", offline: "offline", fault: "fault" };

/** The reading a row shows: the type's main channel when it has one, else the first channel reported. */
function headline(d: Device) {
  const main = MAIN_CHANNEL[d.type];
  const r = main ? d.readings[main] : undefined;
  if (main && r) return [main, r] as const;
  return readingEntries(d)[0];
}

function Dot({ tone }: { tone: Tone }) {
  return <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: toneColor[tone].fg }} />;
}

function DeviceRow({ d, open, onToggle }: { d: Device; open: boolean; onToggle: () => void }) {
  const h = headline(d);
  const problems = attentionReasons(d);
  const dim = d.status !== "online";
  const act = "flex h-7 items-center gap-1 rounded-lg px-2 text-[12px] font-medium text-ink-2 hover:bg-white hover:text-ink";
  return (
    <div className={open ? "rounded-lg bg-idle-bg" : ""}>
      <button type="button" aria-expanded={open} onClick={onToggle}
        className="flex w-full items-start gap-2.5 rounded-lg px-2 py-2 text-left hover:bg-idle-bg">
        <span className="mt-[5px]"><Dot tone={STATUS_TONE[d.status]} /></span>
        <span className="min-w-0 flex-1">
          <span className="flex items-baseline gap-1.5 text-[13px]">
            <span className="shrink-0 font-semibold">{d.id}</span>
            <span className="min-w-0 truncate text-ink-2" title={d.label}>{d.label ?? TYPE_LABEL[d.type]}</span>
          </span>
          <span className="mt-0.5 flex flex-wrap items-center gap-x-1.5 gap-y-0.5 text-[11px] text-ink-2">
            <SourceProtocol d={d} />
            <span className="whitespace-nowrap">· {TYPE_LABEL[d.type]}</span>
            {typeof d.battery_pct === "number" && <span className={`whitespace-nowrap ${d.battery_pct < 20 ? "font-medium text-crit" : ""}`}>· {Math.round(d.battery_pct)}% battery</span>}
          </span>
        </span>
        <span className="tabular shrink-0 text-right">
          {h ? (
            <>
              <span className={`block text-[13px] font-semibold ${dim ? "text-idle" : ""}`} title={channelLabel(h[0])}>{formatReading(h[0], h[1])}</span>
              <span className="block text-[11px] text-ink-2">{ago(h[1].received_ms)}</span>
            </>
          ) : <span className="text-[12px] text-ink-2">No data</span>}
        </span>
      </button>
      {open && (
        <div className="px-2 pb-2 pl-[26px]">
          {problems.length > 0 && (
            <div className="mb-1.5 text-[12px] font-medium" style={{ color: toneColor[STATUS_TONE[d.status] === "ok" ? "warn" : STATUS_TONE[d.status]].fg }}>
              Needs attention: {problems.join(", ")}{d.fault ? ` (${d.fault})` : ""}
            </div>
          )}
          <div className="divide-y divide-[var(--card-border)] text-[12px]">
            {readingEntries(d).map(([ch, r]) => (
              <div key={ch} className="flex items-baseline justify-between gap-3 py-1">
                <span className="text-ink-2">{channelLabel(ch)}</span>
                <span className="tabular text-right"><span className="font-medium">{formatReading(ch, r)}</span> <span className="text-[11px] text-ink-2">{ago(r.received_ms)}</span></span>
              </div>
            ))}
            {readingEntries(d).length === 0 && <div className="py-1 text-ink-2">No readings yet</div>}
            <div className="flex items-baseline justify-between gap-3 py-1">
              <span className="text-ink-2">Last message</span>
              <span className="tabular">{d.last_seen_ms ? ago(d.last_seen_ms) : "never"} · {STATUS_LABEL[d.status]}</span>
            </div>
          </div>
          <div className="mt-1.5 flex gap-1">
            <button type="button" className={act} onClick={() => useView.getState().focusOn(d.x, d.z)}><Icon name="locate" size={14} />Locate</button>
            <button type="button" className={act} onClick={() => { send({ type: "select_unit", unit_id: d.id }); useView.getState().focusOn(d.x, d.z); }}><Icon name="sensor" size={14} />Inspect</button>
            <button type="button" className={act} onClick={() => navigate(`/fleet?device=${encodeURIComponent(d.id)}`)}><Icon name="open" size={14} />Fleet</button>
          </div>
        </div>
      )}
    </div>
  );
}

export function ZoneDevices({ devices }: { devices: Device[] }) {
  const [openId, setOpenId] = useState<string | null>(null);
  const list = sortDevices(devices);
  const counts = (["online", "stale", "offline", "fault"] as const)
    .map((s) => [s, devices.filter((d) => d.status === s).length] as const)
    .filter(([, n]) => n > 0);
  return (
    <div className="mt-3 border-t border-[var(--card-border)] pt-3">
      <div className="mb-1 flex items-center justify-between gap-2 px-0.5">
        <span className="text-[13px] font-semibold">Devices <span className="font-normal text-ink-2">{devices.length}</span></span>
        <span className="flex flex-wrap justify-end gap-1">
          {counts.map(([s, n]) => (
            <span key={s} className="tabular inline-flex items-center gap-1 rounded-full px-1.5 py-px text-[11px] font-medium"
              style={{ color: toneColor[STATUS_TONE[s]].fg, background: toneColor[STATUS_TONE[s]].bg }}>
              {n} {STATUS_LABEL[s]}
            </span>
          ))}
        </span>
      </div>
      {list.length === 0 && <div className="px-0.5 py-1.5 text-[13px] text-ink-2">No devices in this zone</div>}
      <div className="-mx-2">
        {list.map((d) => <DeviceRow key={d.id} d={d} open={openId === d.id} onToggle={() => setOpenId(openId === d.id ? null : d.id)} />)}
      </div>
    </div>
  );
}
