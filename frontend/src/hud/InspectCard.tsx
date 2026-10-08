// Inspect card for the selected unit. Every row comes from the server's unit or, for the
// gateway, from a real device message (with its age); missing device values say so.
import type { ReactNode } from "react";
import type { Gateway, Unit } from "../contract";
import { ButtonSection, LedSection } from "../control/GatewayPanel";
import { send } from "../store/ws";
import { useView, useWorld } from "../store/world";
import { stateLabel } from "../status";
import { ago, Bar, batteryColor, Icon, kindIcon, kindLabel, LiveBadge, nodeLabel, StatusPill, useTick } from "./ui";

function Row({ k, children, dim }: { k: string; children: ReactNode; dim?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1.5">
      <span className="shrink-0 text-ink-2">{k}</span>
      <span className={`min-w-0 truncate text-right font-medium ${dim ? "text-idle" : "text-ink"}`}>{children}</span>
    </div>
  );
}

const sourceText: Record<Unit["source"], string> = { device: "Board", manual: "Manual", auto: "Auto mode" };

function SourceRow({ u }: { u: Unit }) {
  return <Row k="Source"><span className="inline-flex items-center gap-1.5">{sourceText[u.source]}{u.source === "device" && <LiveBadge />}</span></Row>;
}

const actionText: Record<string, string> = { goto: "Drive to", pick: "Pick at", drop: "Drop at", load: "Load at", charge: "Charge at", dock: "Dock at", depart: "Depart via" };

function ForkliftRows({ u }: { u: Unit }) {
  const next = u.plan?.[0];
  return (
    <>
      <Row k="Model">{String(u.meta?.model ?? "—")}</Row>
      <Row k="Location">{u.node ? nodeLabel(u.node) : `To ${nodeLabel(u.target_node)}`}</Row>
      <Row k="Carrying">{u.carrying ?? "Nothing"}</Row>
      <Row k="Next step">{next ? `${actionText[next.action] ?? next.action} ${nodeLabel(next.node)}` : "No queued steps"}</Row>
      <Row k="Speed"><span className="tabular">{speed(u)}</span></Row>
      <SourceRow u={u} />
    </>
  );
}

const speed = (u: Unit) => (u.speed_mps === undefined ? "—" : `${u.speed_mps.toFixed(1)} m/s`);

function TruckRows({ u }: { u: Unit }) {
  const cap = Number(u.meta?.capacity ?? 0);
  const n = u.cargo?.length ?? 0;
  return (
    <>
      <Row k="Route">{String(u.meta?.route ?? "—")}</Row>
      <Row k="Dock">{u.docked_at ? nodeLabel(u.docked_at) : u.state === "gone" ? "Off site" : "In the yard"}</Row>
      <div className="py-1.5">
        <div className="flex justify-between"><span className="text-ink-2">Cargo</span><span className="tabular font-medium">{n} / {cap} pallets</span></div>
        <Bar pct={cap ? (n / cap) * 100 : 0} className="mt-1.5" />
      </div>
      <Row k="Speed"><span className="tabular">{speed(u)}</span></Row>
      <SourceRow u={u} />
    </>
  );
}

function PalletRows({ u }: { u: Unit }) {
  return (
    <>
      <Row k="SKU">{u.label ?? "—"}</Row>
      <Row k="Contents">{String(u.meta?.contents ?? "—")}</Row>
      <Row k="Location">{u.holder ?? nodeLabel(u.node)}</Row>
    </>
  );
}

function DockRows({ u }: { u: Unit }) {
  const truck = useWorld((s) => Object.values(s.units).find((t) => t.kind === "truck" && t.docked_at === u.node));
  return (
    <>
      <Row k="Door">{String(u.meta?.door ?? "—")}</Row>
      <Row k="Truck">{truck ? `${truck.id} · ${truck.cargo?.length ?? 0}/${truck.meta?.capacity ?? "?"} pallets` : "None"}</Row>
    </>
  );
}

function duration(s: number): string {
  if (s < 3600) return `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
  return `${Math.floor(s / 86400)}d ${Math.floor((s % 86400) / 3600)}h`;
}

function GatewayRows({ gw }: { gw: Gateway | null }) {
  useTick(1000);
  if (!gw || (!gw.hello && !gw.status)) return <div className="py-3 text-center text-ink-2">Waiting for device</div>;
  const st = gw.status;
  const stale = !gw.online;
  const v = <T,>(x: T | undefined, f: (x: T) => string = String) => (x === undefined ? "Not reported" : f(x));
  return (
    <>
      <Row k="Board">{gw.hello ? `${gw.hello.data.board}${gw.hello.data.radio_board ? ` + ${gw.hello.data.radio_board}` : ""}` : "Waiting for hello"}</Row>
      <Row k="Last seen" dim={stale}>{gw.last_seen_ms ? ago(gw.last_seen_ms) : "Never"}</Row>
      {st ? (
        <>
          <Row k="Wi-Fi RSSI" dim={stale}><span className="tabular">{v(st.data.wifi_rssi_dbm, (x) => `${x} dBm`)}</span></Row>
          <Row k="Uptime" dim={stale}><span className="tabular">{v(st.data.uptime_s, duration)}</span></Row>
          <Row k="IP" dim={stale}>{v(st.data.ip)}</Row>
          <Row k="Messages sent" dim={stale}><span className="tabular">{v(st.data.msgs_sent)}</span></Row>
          <Row k="Reconnects" dim={stale}><span className="tabular">{v(st.data.reconnects)}</span></Row>
          <Row k="Flushed on last reconnect" dim={stale}><span className="tabular">{v(st.data.buffered, (n) => `${n} msgs`)}</span></Row>
          <Row k="Status age" dim={stale}>{ago(st.received_ms)}</Row>
        </>
      ) : <Row k="Status">Waiting for device</Row>}
      {Object.entries(gw.sensors).map(([name, s]) => s && (
        <Row key={name} k={stateLabel(name)} dim={stale}><span className="tabular">{s.data.value.toFixed(1)} {s.data.unit} · {ago(s.received_ms)}</span></Row>
      ))}
      <div className="pb-1"><LedSection gw={gw} /></div>
      <div className="pb-2"><ButtonSection gw={gw} /></div>
    </>
  );
}

function subtitle(u: Unit, gw: Gateway | null): string {
  const m = u.meta ?? {};
  switch (u.kind) {
    case "forklift": return m.operator ? `Operator ${m.operator}` : "";
    case "truck": return [m.carrier, m.plate].filter(Boolean).join(" · ");
    case "pallet": return String(m.contents ?? "");
    case "dock": return `Door ${m.door ?? ""}`;
    case "gateway": return gw?.hello ? `${gw.hello.data.board} · fw ${gw.hello.data.fw_version}` : "Waiting for device";
    default: return u.label ?? "";
  }
}

function Action({ label, icon, onClick, href }: { label: string; icon: "locate" | "open" | "close"; onClick?: () => void; href?: string }) {
  const cls = "grid h-8 w-8 place-items-center rounded-lg text-ink-2 transition-colors hover:bg-idle-bg hover:text-ink";
  if (href) return <a href={href} target="_blank" rel="noreferrer" aria-label={label} title={label} className={cls}><Icon name={icon} /></a>;
  return <button type="button" aria-label={label} title={label} onClick={onClick} className={cls}><Icon name={icon} /></button>;
}

export function InspectCard() {
  const u = useWorld((s) => (s.selected ? s.units[s.selected] : undefined));
  const site = useWorld((s) => s.layout?.site.id);
  const gw = useWorld((s) => (u?.kind === "gateway" ? s.gateway : null));
  if (!u) return null;
  const sub = subtitle(u, gw);
  const live = u.source === "device";
  return (
    <div className={`card pointer-events-auto max-h-[calc(100vh-250px)] w-[340px] overflow-y-auto p-4 ${live && gw && !gw.online ? "opacity-90" : ""}`} aria-label={`${u.id} details`}>
      <div className="flex items-start gap-3">
        <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${live ? "bg-[#F3EDFF] text-live" : "bg-info-bg text-info"}`}>
          <Icon name={kindIcon[u.kind]} size={20} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="text-[12px] text-ink-2">{kindLabel[u.kind]} · {site}</div>
          <div className="flex items-center gap-2 text-[20px] font-semibold leading-tight">{u.kind === "dock" || u.kind === "rack" || u.kind === "charger" ? u.label ?? u.id : u.id}{live && <LiveBadge />}</div>
          {sub && <div className="truncate text-ink-2">{sub}</div>}
        </div>
        <div className="-mr-1 -mt-1 flex">
          <Action label="Locate" icon="locate" onClick={() => useView.getState().focusOn(u.x, u.z)} />
          <Action label="Open in Control Room" icon="open" href={`/control?unit=${encodeURIComponent(u.id)}`} />
          <Action label="Close" icon="close" onClick={() => send({ type: "select_unit", unit_id: null })} />
        </div>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <StatusPill unit={u} />
        {u.task !== stateLabel(u.state) && <span className="min-w-0 truncate text-ink">{u.task}</span>}
      </div>

      {u.battery_pct !== undefined && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-[12px]">
            <span className="flex items-center gap-1.5 text-ink-2"><Icon name="battery" size={14} />Battery</span>
            <span className="tabular font-semibold">{Math.round(u.battery_pct)}%</span>
          </div>
          <Bar pct={u.battery_pct} color={batteryColor(u.battery_pct)} className="mt-1.5" />
        </div>
      )}

      <div className="mt-3 divide-y divide-[var(--card-border)] border-t border-[var(--card-border)] pt-1">
        {u.kind === "forklift" && <ForkliftRows u={u} />}
        {u.kind === "truck" && <TruckRows u={u} />}
        {u.kind === "pallet" && <PalletRows u={u} />}
        {u.kind === "dock" && <DockRows u={u} />}
        {u.kind === "gateway" && <GatewayRows gw={gw} />}
        {(u.kind === "rack" || u.kind === "charger") && <Row k="Usage">{u.task}</Row>}
      </div>
    </div>
  );
}
