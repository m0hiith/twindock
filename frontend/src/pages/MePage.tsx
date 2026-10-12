// /me/<worker id>: a worker's own safety data (shift hours, break due, their own incidents). Privacy by design:
// workers can see what is held about them. The demo has no sign-in, so this is the worker's link.
import { useEffect, useState } from "react";
import { Brand } from "../hud/Brand";
import { zoneName } from "../fleet/format";
import { useWorld } from "../store/world";

interface Me {
  id: string; role: string; on_shift: boolean; shift_start_ms: number | null; hours_on_shift: number; last_break_ms: number | null;
  break_due: boolean; zone_id: string | null; retention_days: number; history: { at_ms: number; what: string; zone_id: string | null }[];
}

export function MePage() {
  const id = decodeURIComponent(location.pathname.split("/")[2] ?? "WK-01");
  const sites = useWorld((s) => s.sites);
  const [me, setMe] = useState<Me | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    const load = () => fetch(`/api/safety/me/${encodeURIComponent(id)}`).then((r) => (r.ok ? r.json() : Promise.reject(new Error(`No worker ${id}`))))
      .then((d: Me) => setMe(d)).catch((e: unknown) => setErr(String(e)));
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [id]);
  const time = (ms: number) => new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return (
    <div className="mx-auto flex max-w-[560px] flex-col gap-3 p-4">
      <header className="card flex h-[56px] items-center px-4"><Brand tight /></header>
      <h1 className="text-[20px] font-semibold">My safety data · {id}</h1>
      {err && <div role="alert" className="rounded-xl bg-crit-bg px-4 py-2 text-[13px] text-crit">{err}</div>}
      {me && (
        <>
          <div className="card grid grid-cols-2 gap-3 p-4 text-[14px]">
            <div><div className="text-[12px] text-ink-2">Role</div>{me.role.replace(/_/g, " ")}</div>
            <div><div className="text-[12px] text-ink-2">On shift</div>{me.on_shift ? `since ${time(me.shift_start_ms!)} · ${me.hours_on_shift.toFixed(1)} h` : "Not on shift: nothing is tracked"}</div>
            <div><div className="text-[12px] text-ink-2">Break</div>{me.break_due ? "Due: please take a break" : me.last_break_ms ? `last ${time(me.last_break_ms)}` : "—"}</div>
            <div><div className="text-[12px] text-ink-2">Where I am</div>{me.zone_id ? zoneName(sites, me.zone_id) : "—"}</div>
          </div>
          <div className="card flex flex-col gap-2 p-4">
            <div className="text-[15px] font-semibold">My incidents</div>
            {me.history.length === 0 && <div className="text-[13px] text-ink-2">Nothing recorded.</div>}
            {me.history.map((h) => <div key={h.at_ms} className="text-[13px]"><span className="tabular text-ink-2">{time(h.at_ms)}</span> · {h.what}</div>)}
            <div className="text-[12px] text-ink-2">Kept for {me.retention_days} days, then deleted. Helmet and other PPE reminders are never recorded. Nothing is tracked off site or off shift.</div>
          </div>
        </>
      )}
    </div>
  );
}
