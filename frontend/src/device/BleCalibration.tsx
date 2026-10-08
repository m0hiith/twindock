// Calibration helper for BLE zones. Stand at a spot with the tag, wait for a full average, capture.
// From the captures it suggests ble_zones.json thresholds (midpoints between neighbouring spots)
// for the developer to paste into the backend config. It never changes the backend itself.
import { useEffect, useMemo, useState } from "react";
import type { BleTracks } from "../contract";
import { ago, Icon, LiveBadge, nodeLabel, useTick } from "../hud/ui";
import { serverNow, useWorld } from "../store/world";
import { RssiChart } from "./RssiChart";

type Track = BleTracks["tracks"][number];
interface Capture { id: string; node: string; tag: string; rssi: number; at: number }

const STORE_KEY = "twindock.bleCaptures";
const CHART_MS = 3 * 60_000;
const MIN_GAP_DB = 6;     // closer spots can't be told apart reliably with one gateway
const LAST_MARGIN_DB = 5; // the farthest zone still counts this far below its captured average

function loadCaptures(): Capture[] {
  try { return JSON.parse(localStorage.getItem(STORE_KEY) ?? "[]") as Capture[]; } catch { return []; }
}
function saveCaptures(c: Capture[]): void {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(c)); } catch { /* private window: captures just aren't kept */ }
}

function TagCard({ t, config }: { t: Track; config: BleTracks["config"] }) {
  const unit = useWorld((s) => (t.unit_id ? s.units[t.unit_id] : undefined));
  const history = useWorld((s) => s.bleHistory[t.name]) ?? [];
  const live = unit?.source === "device";
  const pendingLeft = t.pending_since_ms !== null ? Math.max(0, config.stable_s - (serverNow() - t.pending_since_ms) / 1000) : null;
  const zoneText = (z: string | null) => (z ? nodeLabel(z) : "Beyond every zone");
  return (
    <div className="card p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-[15px] font-semibold">{t.name}{live && <LiveBadge />}</div>
          <div className="text-[12px] text-ink-2">
            {t.unit_id ? (unit ? `${unit.id} · ${live ? "tracked by this tag" : "manual until a zone holds"}` : `No forklift ${t.unit_id}`) : "Not a forklift tag"} · {t.addr}
          </div>
        </div>
        <div className="text-right">
          <div className="tabular text-[28px] font-semibold leading-none">{t.avg_rssi_dbm?.toFixed(1) ?? "—"}<span className="ml-1 text-[13px] font-medium text-ink-2">dBm</span></div>
          <div className="tabular mt-1 text-[12px] text-ink-2">avg of {t.readings}/{config.window} · raw {t.last_rssi_dbm} · {ago(t.last_seen_ms)}</div>
        </div>
      </div>
      {config.zones.length > 0 && (
        <div className="mt-3 grid grid-cols-3 gap-2 text-[12px]">
          <div className="rounded-lg bg-idle-bg px-2.5 py-1.5"><div className="text-ink-2">Zone now</div><div className="font-semibold">{t.has_zone ? zoneText(t.zone) : "Not yet"}</div></div>
          <div className="rounded-lg bg-idle-bg px-2.5 py-1.5"><div className="text-ink-2">Average says</div><div className="font-semibold">{zoneText(t.raw_zone)}</div></div>
          <div className="rounded-lg bg-idle-bg px-2.5 py-1.5"><div className="text-ink-2">Switching</div>
            <div className="font-semibold">{pendingLeft !== null ? `${zoneText(t.pending_zone)} in ${pendingLeft.toFixed(1)} s` : "—"}</div></div>
        </div>
      )}
      <div className="mt-3"><RssiChart points={history} zones={config.zones} windowMs={CHART_MS} /></div>
    </div>
  );
}

/** Thresholds from captures: per spot the mean of its captures, nearest first, cut halfway between neighbours. */
function suggest(captures: Capture[]): { zones: { node: string; min_rssi_dbm: number }[]; spots: { node: string; rssi: number }[]; tooClose: [string, string][] } {
  const by = new Map<string, number[]>();
  for (const c of captures) by.set(c.node, [...(by.get(c.node) ?? []), c.rssi]);
  const spots = [...by].map(([node, v]) => ({ node, rssi: v.reduce((a, b) => a + b, 0) / v.length })).sort((a, b) => b.rssi - a.rssi);
  const zones = spots.map((s, i) => {
    const next = spots[i + 1];
    const cut = next ? (s.rssi + next.rssi) / 2 : s.rssi - LAST_MARGIN_DB;
    return { node: s.node, min_rssi_dbm: Math.round(cut * 10) / 10 };
  });
  const tooClose: [string, string][] = [];
  spots.forEach((s, i) => { const n = spots[i + 1]; if (n && s.rssi - n.rssi < MIN_GAP_DB) tooClose.push([s.node, n.node]); });
  return { zones, spots, tooClose };
}

export function BleCalibration() {
  useTick(500);
  const ble = useWorld((s) => s.ble);
  const layout = useWorld((s) => s.layout);
  const [captures, setCaptures] = useState<Capture[]>(loadCaptures);
  const [tag, setTag] = useState("");
  const [node, setNode] = useState("");
  const [copied, setCopied] = useState(false);
  useEffect(() => saveCaptures(captures), [captures]);

  const tracks = ble?.tracks ?? [];
  const config = ble?.config;
  const spots = useMemo(() => (layout?.nodes ?? []).filter((n) => n.kinds.includes("forklift") && n.type !== "junction"), [layout]);
  const chosen = tracks.find((t) => t.name === tag) ?? tracks[0];
  const ready = chosen !== undefined && config !== undefined && chosen.readings >= config.window && chosen.avg_rssi_dbm !== null;
  const s = suggest(captures);
  const json = config ? JSON.stringify({ window: config.window, stable_s: config.stable_s, lost_after_s: config.lost_after_s, zones: s.zones }, null, 2) : "";

  const capture = () => {
    if (!ready || !node) return;
    setCaptures((c) => [...c, { id: `${Date.now()}`, node, tag: chosen.name, rssi: chosen.avg_rssi_dbm!, at: Date.now() }]);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className={`rounded-xl px-4 py-3 text-[13px] ${config && config.zones.length > 0 ? "bg-[#F3EDFF] text-live" : "bg-warn-bg text-warn"}`}>
        {!config ? "Waiting for the backend's BLE tracking state…"
          : config.zones.length > 0
            ? `Tracking on: ${config.zones.length} zones, average of ${config.window} scans, a zone must hold ${config.stable_s} s, tags drop after ${config.lost_after_s} s.`
            : "Tracking off: backend/world/ble_zones.json has no zones yet. Capture spots below, paste the result into that file, restart the backend."}
      </div>

      {tracks.length === 0 ? (
        <div className="card px-4 py-8 text-center text-ink-2">No TD- tags in the latest scan. Is the tag powered and within range of the board?</div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">{tracks.map((t) => <TagCard key={t.name} t={t} config={config!} />)}</div>
      )}

      <div className="card p-4">
        <div className="text-[15px] font-semibold">Capture spots</div>
        <p className="mt-1 text-ink-2">Stand at a spot holding the tag still, wait until the average uses {config?.window ?? 5} scans, then capture. One gateway measures distance only, so choose spots at clearly different distances from the board.</p>
        <div className="mt-3 flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-[12px] text-ink-2">Tag
            <select value={chosen?.name ?? ""} onChange={(e) => setTag(e.target.value)} className="h-10 rounded-lg border border-[var(--card-border)] bg-white px-2 text-[13px] text-ink">
              {tracks.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-[12px] text-ink-2">Spot
            <select value={node} onChange={(e) => setNode(e.target.value)} className="h-10 rounded-lg border border-[var(--card-border)] bg-white px-2 text-[13px] text-ink">
              <option value="">Choose…</option>
              {spots.map((n) => <option key={n.id} value={n.id}>{n.label ?? n.id} ({n.id})</option>)}
            </select>
          </label>
          <button type="button" onClick={capture} disabled={!ready || !node}
            className="h-10 rounded-lg bg-accent px-4 font-semibold text-white disabled:opacity-50">
            {ready ? `Capture ${chosen.avg_rssi_dbm!.toFixed(1)} dBm` : chosen ? `Waiting for ${config?.window ?? 5} scans (${chosen.readings})` : "No tag"}
          </button>
        </div>

        {captures.length > 0 && (
          <table className="mt-4 w-full text-left text-[13px]">
            <thead className="text-[12px] text-ink-2"><tr><th className="py-1 font-normal">Spot</th><th className="font-normal">Tag</th><th className="font-normal">Average</th><th className="font-normal">When</th><th /></tr></thead>
            <tbody className="divide-y divide-[var(--card-border)]">
              {captures.map((c) => (
                <tr key={c.id}>
                  <td className="py-1.5">{nodeLabel(c.node)}</td><td>{c.tag}</td><td className="tabular">{c.rssi.toFixed(1)} dBm</td>
                  <td className="text-ink-2">{new Date(c.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
                  <td className="text-right"><button type="button" aria-label="Remove capture" onClick={() => setCaptures((x) => x.filter((y) => y.id !== c.id))} className="grid h-8 w-8 place-items-center rounded-lg text-ink-2 hover:bg-idle-bg"><Icon name="close" size={14} /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {s.zones.length > 0 && (
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div className="text-[15px] font-semibold">Suggested ble_zones.json</div>
            <button type="button" onClick={() => { void navigator.clipboard?.writeText(json).then(() => setCopied(true)); setTimeout(() => setCopied(false), 1500); }}
              className="h-9 rounded-lg border border-[var(--card-border)] px-3 font-medium hover:bg-idle-bg">{copied ? "Copied" : "Copy JSON"}</button>
          </div>
          <p className="mt-1 text-ink-2">Thresholds sit halfway between neighbouring spots; the farthest spot gets {LAST_MARGIN_DB} dB of slack. Paste into backend/world/ble_zones.json (keep the _doc lines if you like) and restart the backend.</p>
          {s.tooClose.map(([a, b]) => (
            <div key={`${a}${b}`} className="mt-2 rounded-lg bg-warn-bg px-3 py-2 text-[13px] text-warn">
              {nodeLabel(a)} and {nodeLabel(b)} are less than {MIN_GAP_DB} dB apart, too close to tell apart reliably. Drop one or pick spots farther apart.
            </div>
          ))}
          <pre className="tabular mt-3 overflow-x-auto rounded-lg bg-[#F6F6F6] p-3 text-[12px] leading-relaxed">{json}</pre>
        </div>
      )}
    </div>
  );
}
