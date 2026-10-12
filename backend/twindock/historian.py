"""A small historian (R6): every device reading and every event in SQLite, on the simulation clock.

- Numbers are stored with exception (deadband) compression, the way plant historians keep size down: a value is kept
  when it moved more than its deadband since the last kept one, or when `max_gap_s` has passed. Counters and flags are
  kept on every change. Text values (machine states, alarms, engine states) go to their own table on every change.
- Retention is a ring buffer: anything older than `retention_s` of simulated time is deleted.
- Queries downsample to a fixed number of buckets (average, minimum, maximum per bucket) for charts and CSV.
- Privacy: worker badge positions are never stored (the K3 privacy rules keep where people were off the record).

The database is a file (TWINDOCK_HISTORIAN_DB, default backend/data/historian.sqlite) or ":memory:" in tests.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "historian.sqlite"
RETENTION_S = 24 * 3600          # a day of simulated time
MAX_GAP_S = 60.0                 # keep at least one point a minute per channel, even if nothing moved
REL_DEADBAND = 0.002             # 0.2 % of the value ...
ABS_DEADBAND = 0.005             # ... but never finer than this (sensor resolutions are 0.001-0.1)
PRUNE_EVERY_S = 300.0
SKIP_CHANNELS = {"position"}     # badge positions: privacy (K3), never stored


class Historian:
    def __init__(self, path: str | Path | None = None, retention_s: float = RETENTION_S) -> None:
        path = str(path if path is not None else os.environ.get("TWINDOCK_HISTORIAN_DB") or DEFAULT_DB)
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.retention_ms = int(retention_s * 1000)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        with self.lock:
            self.db.executescript("""
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=OFF;
                CREATE TABLE IF NOT EXISTS readings (dev TEXT, ch TEXT, t INTEGER, v REAL);
                CREATE INDEX IF NOT EXISTS readings_ix ON readings (dev, ch, t);
                CREATE TABLE IF NOT EXISTS states (dev TEXT, ch TEXT, t INTEGER, s TEXT);
                CREATE INDEX IF NOT EXISTS states_ix ON states (dev, ch, t);
                CREATE TABLE IF NOT EXISTS events (t INTEGER, level TEXT, source TEXT, text TEXT, unit TEXT);
                CREATE INDEX IF NOT EXISTS events_ix ON events (t);
            """)
        self._last: dict[tuple[str, str], tuple[int, Any]] = {}
        self._rows: list[tuple[str, str, int, float]] = []
        self._states: list[tuple[str, str, int, str]] = []
        self._events: list[tuple[int, str, str, str, str | None]] = []
        self._pruned_ms: int | None = None
        self.kept = 0
        self.seen = 0

    # ------------------------------------------------------------------ writing

    def add(self, dev: str, ch: str, t: int, value: Any) -> None:
        if ch in SKIP_CHANNELS or value is None:
            return
        self.seen += 1
        key = (dev, ch)
        last = self._last.get(key)
        if isinstance(value, str):
            if last is None or last[1] != value:
                self._states.append((dev, ch, t, value))
                self._last[key] = (t, value)
            return
        if isinstance(value, bool) or (isinstance(value, int) and not isinstance(value, float)):
            v = float(value)
            if last is not None and last[1] == v and t - last[0] < MAX_GAP_S * 1000:
                return
        elif isinstance(value, float):
            v = value
            if last is not None and isinstance(last[1], float) and t - last[0] < MAX_GAP_S * 1000 \
                    and abs(v - last[1]) <= max(ABS_DEADBAND, REL_DEADBAND * abs(last[1])):
                return
        else:
            return
        self._rows.append((dev, ch, t, v))
        self._last[key] = (t, v)
        self.kept += 1

    def add_event(self, t: int, level: str, source: str, text: str, unit: str | None) -> None:
        self._events.append((t, level, source, text, unit))

    def flush(self, now_ms: int | None = None) -> None:
        if not (self._rows or self._states or self._events) and now_ms is None:
            return
        with self.lock:
            if self._rows:
                self.db.executemany("INSERT INTO readings VALUES (?,?,?,?)", self._rows)
            if self._states:
                self.db.executemany("INSERT INTO states VALUES (?,?,?,?)", self._states)
            if self._events:
                self.db.executemany("INSERT INTO events VALUES (?,?,?,?,?)", self._events)
            if now_ms is not None and (self._pruned_ms is None or now_ms - self._pruned_ms >= PRUNE_EVERY_S * 1000):
                cut = now_ms - self.retention_ms
                for table in ("readings", "states", "events"):
                    self.db.execute(f"DELETE FROM {table} WHERE t < ?", (cut,))
                self._pruned_ms = now_ms
            self.db.commit()
        self._rows, self._states, self._events = [], [], []

    # ------------------------------------------------------------------ reading

    def series(self, dev: str, ch: str, t0: int, t1: int, buckets: int = 300) -> list[list[float]]:
        """[[bucket start ms, avg, min, max, n], ...] between t0 and t1 (buffered points included)."""
        self.flush()
        size = max(1, (t1 - t0) // max(1, buckets))
        with self.lock:
            rows = self.db.execute(
                "SELECT (t - ?) / ? AS b, AVG(v), MIN(v), MAX(v), COUNT(*) FROM readings WHERE dev = ? AND ch = ? AND t >= ? AND t <= ? "
                "GROUP BY b ORDER BY b", (t0, size, dev, ch, t0, t1)).fetchall()
        return [[t0 + int(b) * size, round(a, 4), round(lo, 4), round(hi, 4), n] for b, a, lo, hi, n in rows]

    def raw(self, dev: str, ch: str, t0: int, t1: int) -> list[tuple[int, float]]:
        self.flush()
        with self.lock:
            return [(int(t), float(v)) for t, v in self.db.execute(
                "SELECT t, v FROM readings WHERE dev = ? AND ch = ? AND t >= ? AND t <= ? ORDER BY t", (dev, ch, t0, t1))]

    def value_at(self, dev: str, ch: str, t: int) -> float | None:
        """The last kept value at or before t."""
        self.flush()
        with self.lock:
            row = self.db.execute("SELECT v FROM readings WHERE dev = ? AND ch = ? AND t <= ? ORDER BY t DESC LIMIT 1", (dev, ch, t)).fetchone()
        return None if row is None else float(row[0])

    def states(self, dev: str, ch: str, t0: int, t1: int) -> list[tuple[int, str]]:
        """State changes in [t0, t1], led by the state in force at t0 (if any)."""
        self.flush()
        with self.lock:
            before = self.db.execute("SELECT t, s FROM states WHERE dev = ? AND ch = ? AND t < ? ORDER BY t DESC LIMIT 1", (dev, ch, t0)).fetchone()
            rows = self.db.execute("SELECT t, s FROM states WHERE dev = ? AND ch = ? AND t >= ? AND t <= ? ORDER BY t", (dev, ch, t0, t1)).fetchall()
        out = [(t0, before[1])] if before else []
        return out + [(int(t), str(s)) for t, s in rows]

    def events(self, t0: int, t1: int, sources: Iterable[str] | None = None) -> list[dict[str, Any]]:
        self.flush()
        with self.lock:
            rows = self.db.execute("SELECT t, level, source, text, unit FROM events WHERE t >= ? AND t <= ? ORDER BY t", (t0, t1)).fetchall()
        src = set(sources) if sources else None
        return [{"t": t, "level": lv, "source": s, "text": tx, "unit": u} for t, lv, s, tx, u in rows if src is None or s in src]

    def delete_from(self, t: int) -> None:
        """Forget everything at or after t (the warm start re-simulates that stretch)."""
        self._rows, self._states, self._events, self._last = [], [], [], {}
        with self.lock:
            for table in ("readings", "states", "events"):
                self.db.execute(f"DELETE FROM {table} WHERE t >= ?", (t,))
            self.db.commit()

    def channels(self) -> list[tuple[str, str]]:
        self.flush()
        with self.lock:
            return [(d, c) for d, c in self.db.execute("SELECT DISTINCT dev, ch FROM readings ORDER BY dev, ch")]

    def size(self) -> dict[str, int]:
        self.flush()
        with self.lock:
            return {t: int(self.db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]) for t in ("readings", "states", "events")}
