"""Simulation parameters: backend/sim/params/*.yaml, every number with a value, a unit and a source.

A parameter leaf is a mapping with `value`, `unit` and `source` (and optionally `note`). A distribution leaf has
`dist` (weibull, exponential, normal, lognormal, uniform, bernoulli), its own fields, `unit` and `source`. The
source says where the number comes from and must start with one of:

    "datasheet: <part / document>"   a manufacturer's datasheet or manual
    "standard: <name>"               a published standard (ISO, IEC, ...)
    "typical industry value"         what a plant engineer would expect; followed by the reasoning
    "assumption"                     our choice for the demo; followed by why

Code reads parameters by dotted path (`p.v("air.receiver_m3")`) and never hard-codes a model number.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import yaml

PARAMS_DIR = Path(__file__).resolve().parent / "params"
SOURCE_KINDS = ("datasheet:", "standard:", "typical industry value", "assumption")
DIST_FIELDS = {"weibull": ("shape", "scale"), "exponential": ("mean",), "normal": ("mean", "sigma"),
               "lognormal": ("median", "sigma_log"), "uniform": ("low", "high"), "bernoulli": ("p",)}


class ParamError(ValueError):
    pass


@dataclass(frozen=True)
class Leaf:
    path: str
    value: Any
    unit: str
    source: str
    note: str | None = None
    dist: str | None = None

    def wire(self) -> dict[str, Any]:
        d: dict[str, Any] = {"path": self.path, "value": self.value, "unit": self.unit, "source": self.source}
        if self.dist:
            d["dist"] = self.dist
        if self.note:
            d["note"] = self.note
        return d


def _is_leaf(x: Any) -> bool:
    return isinstance(x, dict) and "source" in x and ("value" in x or "dist" in x)


class Params:
    def __init__(self, tree: dict[str, Any]) -> None:
        self.tree = tree
        self.leaves: dict[str, Leaf] = {}
        self._walk(tree, "")
        self.used: set[str] = set()
        self._v: dict[str, Any] = {}    # cache of plain values after first use (models read params every step)
        self._f: dict[str, float] = {}

    @classmethod
    def load(cls, directory: Path = PARAMS_DIR) -> "Params":
        tree: dict[str, Any] = {}
        for f in sorted(directory.glob("*.yaml")):
            data = yaml.safe_load(f.read_text()) or {}
            for k, v in data.items():
                if k in tree:
                    raise ParamError(f"{f.name}: top-level key {k!r} is also defined in another params file")
                tree[k] = v
        return cls(tree)

    def _walk(self, node: Any, path: str) -> None:
        if _is_leaf(node):
            src = str(node["source"])
            if not src.startswith(SOURCE_KINDS):
                raise ParamError(f"{path}: source must start with one of {SOURCE_KINDS}, not {src!r}")
            if "unit" not in node:
                raise ParamError(f"{path}: missing unit (use '1' for a plain number)")
            if "dist" in node:
                kind = node["dist"]
                if kind not in DIST_FIELDS:
                    raise ParamError(f"{path}: unknown distribution {kind!r}")
                missing = [f for f in DIST_FIELDS[kind] if f not in node]
                if missing:
                    raise ParamError(f"{path}: {kind} needs {missing}")
                value = {f: node[f] for f in DIST_FIELDS[kind]}
                self.leaves[path] = Leaf(path, value, str(node["unit"]), src, node.get("note"), kind)
            else:
                self.leaves[path] = Leaf(path, node["value"], str(node["unit"]), src, node.get("note"))
            return
        if isinstance(node, dict):
            for k, v in node.items():
                if k.startswith("_"):
                    continue  # _doc and other comments
                self._walk(v, f"{path}.{k}" if path else str(k))
            return
        raise ParamError(f"{path}: {node!r} is not a parameter (needs value, unit and source)")

    def leaf(self, path: str) -> Leaf:
        try:
            lf = self.leaves[path]
        except KeyError:
            raise ParamError(f"no parameter {path!r}") from None
        self.used.add(path)
        return lf

    def v(self, path: str) -> Any:
        """The value of a plain parameter."""
        try:
            return self._v[path]
        except KeyError:
            pass
        lf = self.leaf(path)  # first use: validates it and records it as used
        if lf.dist:
            raise ParamError(f"{path} is a distribution; draw from it with Rng.draw")
        self._v[path] = lf.value
        return lf.value

    def f(self, path: str) -> float:
        try:
            return self._f[path]
        except KeyError:
            x = self._f[path] = float(self.v(path))
            return x

    def children(self, path: str) -> list[str]:
        """Direct child keys of a group (e.g. the machines under production.machines)."""
        node: Any = self.tree
        for part in path.split("."):
            node = node[part]
        return [k for k in node if not k.startswith("_")]

    def under(self, prefix: str) -> Iterator[Leaf]:
        for p, lf in self.leaves.items():
            if p == prefix or p.startswith(prefix + "."):
                yield lf

    def doc(self, path: str) -> str | None:
        node: Any = self.tree
        for part in path.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        return node.get("_doc") if isinstance(node, dict) else None
