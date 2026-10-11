"""One rules engine for every alert (S6). Rules live in backend/rules/*.yaml.

A rule looks at one kind of subject (machine, worker, device, gateway, line). Each evaluation the
engine builds plain "facts" dicts for every subject (see Engine._facts); a rule raises an alert
for a subject when all its `where` clauses (which subjects it applies to) and `when` clauses (the
condition) hold continuously for `for_s` seconds. The alert resolves as soon as the condition no
longer holds. A missing value never satisfies a clause, so no alert is ever raised on data that
didn't arrive.

Alert lifecycle: raised -> acknowledged (who, when) -> resolved. An alert can resolve without
being acknowledged. Open alerts are shared by every screen.
"""

from __future__ import annotations

import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

RULES_DIR = Path(__file__).resolve().parents[1] / "rules"
SUBJECTS = ("machine", "worker", "device", "gateway", "line")
SEVERITIES = ("info", "warning", "critical")
OPS = ("eq", "ne", "gt", "gte", "lt", "lte", "in", "outside", "present")
KEEP_RESOLVED = 30  # recently resolved alerts kept for the panels
KEEP_LOG = 2000  # every alert of the last day, for the incident timeline and the daily report
LOG_MAX_AGE_MS = 24 * 3_600_000


@dataclass(frozen=True)
class Clause:
    field: str
    op: str
    value: Any = None

    def holds(self, facts: dict[str, Any]) -> bool:
        v = facts.get(self.field)
        if self.op == "present":
            return v is not None
        if v is None:
            return False
        try:
            if self.op == "eq":
                return bool(v == self.value)
            if self.op == "ne":
                return bool(v != self.value)
            if self.op == "gt":
                return bool(v > self.value)
            if self.op == "gte":
                return bool(v >= self.value)
            if self.op == "lt":
                return bool(v < self.value)
            if self.op == "lte":
                return bool(v <= self.value)
            if self.op == "in":
                return v in self.value
            if self.op == "outside":
                lo, hi = self.value
                return bool(v < lo or v > hi)
        except TypeError:
            return False
        return False


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    plain: str
    subject: str
    severity: str
    message: str
    where: tuple[Clause, ...] = ()
    when: tuple[Clause, ...] = ()
    for_s: float = 0.0
    enabled: bool = True

    def applies(self, f: dict[str, Any]) -> bool:
        return all(c.holds(f) for c in self.where)

    def firing(self, f: dict[str, Any]) -> bool:
        return all(c.holds(f) for c in self.when)


def _clauses(raw: Any, rid: str) -> tuple[Clause, ...]:
    out = []
    for c in raw or []:
        if c.get("op") not in OPS:
            raise ValueError(f"rule {rid}: unknown op {c.get('op')!r} (use one of {', '.join(OPS)})")
        out.append(Clause(str(c["field"]), str(c["op"]), c.get("value")))
    return tuple(out)


def load_rules(path: Path = RULES_DIR) -> list[Rule]:
    rules: list[Rule] = []
    for f in sorted(path.glob("*.yaml")):
        for r in yaml.safe_load(f.read_text()) or []:
            rid = str(r["id"])
            if r["subject"] not in SUBJECTS:
                raise ValueError(f"{f.name}: rule {rid}: subject must be one of {SUBJECTS}")
            if r["severity"] not in SEVERITIES:
                raise ValueError(f"{f.name}: rule {rid}: severity must be one of {SEVERITIES}")
            rules.append(Rule(rid, str(r["name"]), str(r["plain"]), r["subject"], r["severity"], str(r["message"]),
                              _clauses(r.get("where"), rid), _clauses(r.get("when"), rid),
                              float(r.get("for_s", 0)), bool(r.get("enabled", True))))
    ids = [r.id for r in rules]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        raise ValueError(f"duplicate rule ids: {sorted(dup)}")
    return rules


class _Fmt(string.Formatter):
    """Message templates: {field} and {field:.1f}; a missing field prints as "?"."""

    def get_value(self, key: Any, args: Any, kwargs: Any) -> Any:
        return kwargs.get(key, "?") if isinstance(key, str) else super().get_value(key, args, kwargs)

    def format_field(self, value: Any, format_spec: str) -> str:
        try:
            return super().format_field(value, format_spec)
        except (ValueError, TypeError):
            return str(value)


_fmt = _Fmt()


@dataclass
class Alert:
    id: str
    rule_id: str
    severity: str
    title: str
    subject_id: str
    message: str
    state: str  # raised | acknowledged | resolved
    raised_ms: int
    target: dict[str, Any]
    acknowledged_by: str | None = None
    acknowledged_ms: int | None = None
    resolved_ms: int | None = None

    def wire(self) -> dict[str, Any]:
        return {"id": self.id, "rule_id": self.rule_id, "severity": self.severity, "title": self.title,
                "subject_id": self.subject_id, "message": self.message, "state": self.state,
                "raised_ms": self.raised_ms, "acknowledged_by": self.acknowledged_by,
                "acknowledged_ms": self.acknowledged_ms, "resolved_ms": self.resolved_ms, "target": self.target}


@dataclass
class Rules:
    rules: list[Rule]
    open: dict[tuple[str, str], Alert] = field(default_factory=dict)
    resolved: list[Alert] = field(default_factory=list)
    log: list[Alert] = field(default_factory=list)  # raised alerts, oldest first (same objects: acks and resolution show up here)
    _since: dict[tuple[str, str], int] = field(default_factory=dict)  # condition true since (ms)
    _n: int = 0

    def evaluate(self, facts: dict[str, list[dict[str, Any]]], now: int) -> tuple[list[Alert], list[Alert]]:
        raised: list[Alert] = []
        resolved: list[Alert] = []
        for r in self.rules:
            if not r.enabled:
                continue
            seen: set[str] = set()
            for f in facts.get(r.subject, []):
                sid = str(f["id"])
                key = (r.id, sid)
                if not r.applies(f):
                    continue
                seen.add(sid)
                if r.firing(f):
                    since = self._since.setdefault(key, now)
                    if key not in self.open and now - since >= r.for_s * 1000:
                        self._n += 1
                        a = Alert(f"A{self._n:05d}", r.id, r.severity, r.name, sid, _fmt.format(r.message, **f),
                                  "raised", now, {k: f[k] for k in ("unit_id", "device_id", "site_id", "x", "z") if f.get(k) is not None})
                        self.open[key] = a
                        raised.append(a)
                        self.log.append(a)
                        del self.log[:-KEEP_LOG]
                else:
                    self._since.pop(key, None)
                    if key in self.open:
                        resolved.append(self._resolve(key, now))
            # subjects that disappeared (e.g. a stale badge no longer reports) can't hold a condition
            for key in [k for k in self.open if k[0] == r.id and k[1] not in seen]:
                self._since.pop(key, None)
                resolved.append(self._resolve(key, now))
        return raised, resolved

    def _resolve(self, key: tuple[str, str], now: int) -> Alert:
        a = self.open.pop(key)
        a.state, a.resolved_ms = "resolved", now
        self.resolved.append(a)
        del self.resolved[:-KEEP_RESOLVED]
        return a

    def acknowledge(self, alert_id: str, by: str, now: int) -> str | None:
        """Returns None on success, else the reason."""
        for a in self.open.values():
            if a.id == alert_id:
                if a.state == "acknowledged":
                    return f"Already acknowledged by {a.acknowledged_by}"
                a.state, a.acknowledged_by, a.acknowledged_ms = "acknowledged", by, now
                return None
        if any(a.id == alert_id for a in self.resolved):
            return "Already resolved"
        return f"No alert {alert_id}"

    def incidents(self, now: int) -> list[dict[str, Any]]:
        """Every alert raised in the last 24 h with who acknowledged it and how fast, newest first."""
        out = []
        for a in reversed(self.log):
            if now - a.raised_ms > LOG_MAX_AGE_MS:
                break
            w = a.wire()
            w["response_s"] = round((a.acknowledged_ms - a.raised_ms) / 1000, 1) if a.acknowledged_ms else None
            w["resolution_s"] = round((a.resolved_ms - a.raised_ms) / 1000, 1) if a.resolved_ms else None
            out.append(w)
        return out

    def wire(self) -> dict[str, Any]:
        sev = {s: i for i, s in enumerate(reversed(SEVERITIES))}
        open_ = sorted(self.open.values(), key=lambda a: (sev[a.severity], -a.raised_ms))
        return {"alerts": [a.wire() for a in open_] + [a.wire() for a in reversed(self.resolved)],
                "rules": [{"id": r.id, "name": r.name, "plain": r.plain, "subject": r.subject, "severity": r.severity,
                           "for_s": r.for_s, "enabled": r.enabled} for r in self.rules]}
