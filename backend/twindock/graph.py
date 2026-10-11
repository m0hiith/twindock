"""Waypoint graph built from layout.json, with per-kind shortest paths (Dijkstra)."""

from __future__ import annotations

import heapq
import json
import math
from pathlib import Path

from .models import Lane, Layout, MoverKind, Node

DEFAULT_LAYOUT = Path(__file__).resolve().parents[1] / "world" / "layout.json"


def load_layout(path: Path = DEFAULT_LAYOUT) -> Layout:
    return Layout.model_validate(json.loads(path.read_text()))


class Graph:
    def __init__(self, layout: Layout) -> None:
        self.nodes: dict[str, Node] = {n.id: n for n in layout.nodes}
        self._adj: dict[MoverKind, dict[str, list[tuple[str, float]]]] = {"forklift": {}, "truck": {}}
        self._lanes: dict[tuple[str, str], Lane] = {}
        for lane in layout.lanes:
            for end in (lane.a, lane.b):
                if end not in self.nodes:
                    raise ValueError(f"lane {lane.a}-{lane.b} references unknown node {end}")
            d = self.distance(lane.a, lane.b)
            self._lanes[(lane.a, lane.b)] = lane
            self._lanes[(lane.b, lane.a)] = lane
            for kind in lane.kinds:
                adj = self._adj[kind]
                adj.setdefault(lane.a, []).append((lane.b, d))
                adj.setdefault(lane.b, []).append((lane.a, d))

    def distance(self, a: str, b: str) -> float:
        na, nb = self.nodes[a], self.nodes[b]
        return math.hypot(nb.x - na.x, nb.z - na.z)

    def path_length(self, path: list[str]) -> float:
        return sum(self.distance(a, b) for a, b in zip(path, path[1:]))

    def lane(self, a: str, b: str) -> Lane | None:
        return self._lanes.get((a, b))

    def is_reverse(self, a: str, b: str) -> bool:
        """True when driving a -> b means reversing (trucks backing into a bay)."""
        lane = self._lanes.get((a, b))
        return lane is not None and lane.reverse_into == b

    def neighbours(self, kind: MoverKind, node_id: str) -> list[str]:
        return [m for m, _w in self._adj[kind].get(node_id, [])]

    def reachable_by(self, kind: MoverKind, node_id: str) -> bool:
        return node_id in self._adj[kind]

    def shortest_path(self, kind: MoverKind, start: str, goal: str, avoid: set[str] | None = None) -> list[str] | None:
        """Node list from start to goal inclusive, or None if unreachable for this kind.
        `avoid`: nodes the path must not pass through (traffic re-routing around a blocked spot)."""
        adj = self._adj[kind]
        if start not in adj or goal not in adj:
            return None
        if start == goal:
            return [start]
        dist = {start: 0.0}
        prev: dict[str, str] = {}
        heap = [(0.0, start)]
        while heap:
            d, n = heapq.heappop(heap)
            if n == goal:
                break
            if d > dist[n]:
                continue
            for m, w in adj[n]:
                if avoid and m in avoid and m != goal:
                    continue
                nd = d + w
                if nd < dist.get(m, math.inf):
                    dist[m] = nd
                    prev[m] = n
                    heapq.heappush(heap, (nd, m))
        if goal not in dist:
            return None
        path = [goal]
        while path[-1] != start:
            path.append(prev[path[-1]])
        return path[::-1]
