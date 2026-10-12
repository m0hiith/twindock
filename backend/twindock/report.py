"""Shift report (R6): what one shift made and lost, from the historian and the engine's logs, as data and as a PDF.

Output, OEE and its losses by reason per machine (folded from the machine monitors' state changes and counters in the
historian), downtime events with their alarms, energy and energy per unit (from the meters' kWh registers), safety
alerts with response times (the rules engine's incident log), work orders, and logistics KPIs. Every number is
read back from stored readings or logs; nothing is estimated for the report. All of it is simulated (SIM) except the
real board's readings, which the report does not use.
"""

from __future__ import annotations

import time
from typing import Any

from .production import oee_from_durations

FAULTY = ("fault", "maintenance")


def shift_window(calendar: list[dict[str, Any]], now_ms: int, which: str = "current") -> tuple[str, int, int]:
    """(shift name, start ms, end ms) of the shift running at now_ms, or of the one before it."""
    lt = time.localtime(now_ms / 1000)
    h = lt.tm_hour + lt.tm_min / 60 + lt.tm_sec / 3600
    for sh in calendar:
        start, end = float(sh["start_h"]), float(sh["end_h"])
        span = (end - start) % 24
        since = (h - start) % 24
        if since < span:
            s_ms = now_ms - int(since * 3_600_000)
            if which == "current":
                return str(sh["name"]), s_ms, s_ms + int(span * 3_600_000)
            prev = next(p for p in calendar if float(p["end_h"]) % 24 == start % 24)
            p_span = (float(prev["end_h"]) - float(prev["start_h"])) % 24
            return str(prev["name"]), s_ms - int(p_span * 3_600_000), s_ms
    raise ValueError("no shift covers this hour")


def _durations(states: list[tuple[int, str]], t0: int, t1: int) -> dict[str, float]:
    d: dict[str, float] = {}
    for (t, s), nxt in zip(states, [*states[1:], (t1, "")]):
        a, b = max(t, t0), min(nxt[0], t1)
        if b > a:
            d[s] = d.get(s, 0.0) + (b - a)
    return d


def _delta(h: Any, dev: str, ch: str, t0: int, t1: int) -> float | None:
    a, b = h.value_at(dev, ch, t0), h.value_at(dev, ch, t1)
    if b is None:
        return None
    if a is None:  # the counter started during the shift: take its first value
        pts = h.raw(dev, ch, t0, t1)
        a = pts[0][1] if pts else b
    return max(0.0, b - a)


def shift_report(engine: Any, which: str = "current") -> dict[str, Any]:
    from sim import Params  # the plant's shift calendar lives with the simulation params (backend/sim/params)
    p = Params.load()
    now = engine.clock()
    name, t0, end = shift_window(p.v("production.shifts.calendar"), now, which)
    t1 = min(end, now)
    h = engine.historian
    prod = engine.production
    machines = []
    downtime = []
    good_cartons = 0.0
    for mid, m in prod.machines.items():
        st = h.states(m.device_id, "state", t0, t1)
        dur = _durations(st, t0, t1)
        units = _delta(h, m.device_id, "units", t0, t1) or 0.0
        rejects = _delta(h, m.device_id, "rejects", t0, t1) or 0.0
        o = oee_from_durations(dur, m.ideal_cycle_s, int(units), int(rejects))
        machines.append({"id": mid, "label": m.label, "units": int(units), "rejects": int(rejects), "oee": o["oee"], "availability": o["availability"],
                         "performance": o["performance"], "quality": o["quality"], "losses": o["losses"]})
        if mid not in prod.presses:
            good_cartons += units
        alarms = h.states(m.device_id, "alarm", t0 - 600_000, t1)
        for (t, s), nxt in zip(st, [*st[1:], (t1, "")]):
            if s in FAULTY:
                alarm = next((a for at, a in reversed(alarms) if at <= t + 2000), None) if s == "fault" else None
                downtime.append({"machine": mid, "state": s, "from_ms": max(t, t0), "to_ms": min(nxt[0], t1),
                                 "minutes": round((min(nxt[0], t1) - max(t, t0)) / 60_000, 1), "alarm": alarm})
    u = engine.devices.cfg.get("utilities") or {}
    prod_meter = next((mm for mm, z in (u.get("feeders") or {}).items() if z == "FAC01_PRODUCTION"), None)
    kwh = {k: _delta(h, mid_, "energy_kwh", t0, t1) for k, mid_ in
           (("production", prod_meter), ("grid", u.get("incomer")), ("solar", u.get("solar_meter")), ("generator", u.get("generator"))) if mid_}
    incidents = [i for i in engine.rules.incidents(now) if t0 <= i["raised_ms"] <= t1]
    resp = [i["response_s"] for i in incidents if i["response_s"] is not None]
    wos = engine.control.c.wire()["work_orders"]
    return {
        "shift": name, "from_ms": t0, "to_ms": t1, "complete": t1 >= end, "generated_ms": now, "source": "sim",
        "production": {"good_cartons": int(good_cartons), "pallets": int(good_cartons // max(1, prod.units_per_pallet)), "machines": machines},
        "downtime": sorted(downtime, key=lambda d: d["from_ms"]),
        "energy": {"kwh": {k: None if v is None else round(v, 1) for k, v in kwh.items()},
                   "kwh_per_carton": None if not kwh.get("production") or good_cartons <= 0 else round(kwh["production"] / good_cartons, 3)},
        "safety": {"alerts": len(incidents), "critical": sum(1 for i in incidents if i["severity"] == "critical"),
                   "acknowledged": len(resp), "median_response_s": None if not resp else sorted(resp)[len(resp) // 2],
                   "incidents": [{k: i[k] for k in ("title", "severity", "subject_id", "raised_ms", "response_s", "resolution_s")} for i in incidents[:30]]},
        "work_orders": {"open": [w for w in wos if w["state"] not in ("done", "dismissed")],
                        "done_in_shift": [w for w in wos if w["state"] == "done" and t0 <= w["updated_ms"] <= t1]},
        "logistics": engine.logistics.kpis(),
    }


# ---------------------------------------------------------------------- PDF

def _txt(s: Any) -> str:
    """The PDF's built-in fonts are Latin-1: spell out the few symbols we use."""
    t = str(s)
    for a, b in (("→", "->"), ("·", "-"), ("–", "-"), ("—", "-"), ("³", "3"), ("°", " deg"), ("≥", ">="), ("≤", "<="), ("×", "x"), ("µ", "u")):
        t = t.replace(a, b)
    return t.encode("latin-1", "replace").decode("latin-1")


def _hm(ms: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ms / 1000))


def _pct(x: float | None) -> str:
    return "-" if x is None else f"{x * 100:.0f}%"


def shift_report_pdf(r: dict[str, Any]) -> bytes:
    from fpdf import FPDF

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()
    red = (217, 30, 42)

    def h1(t: str) -> None:
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(17, 17, 17)
        pdf.cell(0, 10, _txt(t), new_x="LMARGIN", new_y="NEXT")

    def h2(t: str) -> None:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*red)
        pdf.cell(0, 8, _txt(t), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(17, 17, 17)

    def line(t: str, size: int = 10) -> None:
        pdf.set_font("Helvetica", "", size)
        pdf.multi_cell(0, 5, _txt(t), new_x="LMARGIN", new_y="NEXT")

    def table(head: list[str], rows: list[list[Any]], widths: list[int]) -> None:
        pdf.set_font("Helvetica", "B", 9)
        for w, c in zip(widths, head):
            pdf.cell(w, 6, _txt(c), border="B")
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for row in rows:
            for w, c in zip(widths, row):
                pdf.cell(w, 5.5, _txt(c))
            pdf.ln()

    h1(f"TwinDock shift report - shift {r['shift']}")
    line(f"Riverside campus, FAC-01 lines. {_hm(r['from_ms'])} to {_hm(r['to_ms'])}"
         f"{'' if r['complete'] else ' (shift still running)'}. Simulated data (SIM).", 9)
    h2("Output")
    pr = r["production"]
    line(f"{pr['good_cartons']} good cartons, {pr['pallets']} pallets.")
    table(["Machine", "Units", "Rejects", "OEE", "A", "P", "Q"],
          [[f"{m['id']} {m['label']}", m["units"], m["rejects"], _pct(m["oee"]), _pct(m["availability"]), _pct(m["performance"]), _pct(m["quality"])]
           for m in pr["machines"]], [52, 20, 20, 22, 22, 22, 22])
    h2("OEE losses by reason (minutes)")
    keys = [("breakdown_s", "Breakdowns"), ("setup_s", "Set-up"), ("starved_s", "Starved"), ("blocked_s", "Blocked"), ("speed_s", "Slow cycles"), ("quality_s", "Scrap")]
    table(["Machine", *[k[1] for k in keys]], [[m["id"], *[f"{m['losses'][k] / 60:.0f}" for k, _ in keys]] for m in pr["machines"]],
          [30, 26, 26, 26, 26, 28, 26])
    h2("Downtime events")
    if not r["downtime"]:
        line("None.")
    else:
        table(["From", "Machine", "State", "Minutes", "Alarm"],
              [[time.strftime("%H:%M", time.localtime(d["from_ms"] / 1000)), d["machine"], d["state"], d["minutes"], d["alarm"] or ""] for d in r["downtime"][:40]],
              [22, 24, 30, 22, 80])
    h2("Energy")
    e = r["energy"]
    line("  ".join(f"{k}: {'-' if v is None else f'{v:.1f} kWh'}" for k, v in e["kwh"].items())
         + f".  Production energy per good carton: {'-' if e['kwh_per_carton'] is None else f'{e['kwh_per_carton']:.3f} kWh'}.")
    h2("Safety")
    s = r["safety"]
    line(f"{s['alerts']} alerts ({s['critical']} critical); {s['acknowledged']} acknowledged; median response "
         f"{'-' if s['median_response_s'] is None else f'{s['median_response_s']:.0f} s'}.")
    if s["incidents"]:
        table(["Raised", "Alert", "Severity", "Subject", "Response"],
              [[time.strftime("%H:%M", time.localtime(i["raised_ms"] / 1000)), i["title"], i["severity"], i["subject_id"],
                "-" if i["response_s"] is None else f"{i['response_s']:.0f} s"] for i in s["incidents"]], [20, 74, 24, 30, 30])
    h2("Work orders")
    wo = r["work_orders"]
    if not wo["open"] and not wo["done_in_shift"]:
        line("None.")
    for w in wo["open"]:
        line(f"Open: {w['id']} {w['kind'].replace('_', ' ')} - {w['asset_label']} ({w['state'].replace('_', ' ')}). Cause: {w['cause']}")
    for w in wo["done_in_shift"]:
        line(f"Done: {w['id']} {w['kind'].replace('_', ' ')} - {w['asset_label']}. {w['result'] or ''}")
    h2("Logistics")
    lg = r["logistics"]
    line(f"Dock to stock {lg['dock_to_stock_min'] if lg['dock_to_stock_min'] is not None else '-'} min; truck turnaround "
         f"{lg['turnaround_min'] if lg['turnaround_min'] is not None else '-'} min; on-time dispatch {_pct(lg['on_time_dispatch'])}; "
         f"forklift utilisation {_pct(lg['forklift_utilisation'])}.")
    pdf.ln(4)
    line("Generated by TwinDock from the historian. Every number is read back from stored (simulated) readings and logs.", 8)
    return bytes(pdf.output())
