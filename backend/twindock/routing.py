"""Walking routes for emergencies (F3): shortest path over the pedestrian graph (layout nodes and lanes with `kinds: []`)
from a zone to the nearest muster point that is not next to the hazard. Advice only: nothing is closed or locked."""

from __future__ import annotations

import heapq
import math
from typing import Any

from .models import Layout


class PedGraph:
    def __init__(self, layout: Layout) -> None:
        self.nodes = {n.id: (n.x, n.z) for n in layout.nodes if not n.kinds}
        self.adj: dict[str, list[tuple[str, float]]] = {i: [] for i in self.nodes}
        for lane in layout.lanes:
            if lane.kinds or lane.a not in self.nodes or lane.b not in self.nodes:
                continue
            d = math.dist(self.nodes[lane.a], self.nodes[lane.b])
            self.adj[lane.a].append((lane.b, d))
            self.adj[lane.b].append((lane.a, d))

    def nearest(self, x: float, z: float) -> str:
        return min(self.nodes, key=lambda i: (self.nodes[i][0] - x) ** 2 + (self.nodes[i][1] - z) ** 2)

    def dijkstra(self, start: str) -> tuple[dict[str, float], dict[str, str]]:
        dist = {start: 0.0}
        prev: dict[str, str] = {}
        heap = [(0.0, start)]
        while heap:
            d, n = heapq.heappop(heap)
            if d > dist[n]:
                continue
            for m, w in self.adj[n]:
                if d + w < dist.get(m, math.inf):
                    dist[m] = d + w
                    prev[m] = n
                    heapq.heappush(heap, (d + w, m))
        return dist, prev

    def path(self, prev: dict[str, str], start: str, goal: str) -> list[str]:
        out = [goal]
        while out[-1] != start:
            out.append(prev[out[-1]])
        return out[::-1]


def evacuation_routes(g: PedGraph, zones: dict[str, dict[str, Any]], musters: list[dict[str, Any]], from_zones: list[str],
                      hazards: list[tuple[float, float]], clear_m: float = 40.0) -> list[dict[str, Any]]:
    """One route per zone in `from_zones`: to the nearest muster point at least `clear_m` from every hazard
    (any muster point if none qualifies). Each route is the list of [x, z] points to walk."""
    safe = [m for m in musters if all(math.dist((m["x"], m["z"]), h) >= clear_m for h in hazards)] or list(musters)
    out = []
    for zid in from_zones:
        z = zones.get(zid)
        if z is None or not safe:
            continue
        xs = [p[0] for p in z["polygon"]]
        zs = [p[1] for p in z["polygon"]]
        cx, cz = sum(xs) / len(xs), sum(zs) / len(zs)
        start = g.nearest(cx, cz)
        dist, prev = g.dijkstra(start)
        best = min((m for m in safe if m["node"] in dist), key=lambda m: dist[m["node"]], default=None)
        if best is None:
            continue
        pts = [[round(cx, 1), round(cz, 1)]] + [[g.nodes[n][0], g.nodes[n][1]] for n in g.path(prev, start, best["node"])]
        out.append({"zone_id": zid, "muster_id": best["id"], "length_m": round(dist[best["node"]], 1), "points": pts})
    return out
