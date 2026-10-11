"""A compiled yes/no check for the JSON Schema subset used in /shared/schemas.

`jsonschema` walks every schema dynamically (~15 µs for a three-field reading), which made validation the largest
cost of the backend's message path and of the warm start (D3). This compiles each schema once into nested Python
closures that answer one question: is this instance valid? Only "yes" is trusted. A "no" (or any schema using a
keyword this module doesn't know) goes back to `jsonschema`, which still produces every error message. So the
schemas stay the single definition, and test_fastcheck.py checks the two agree on real and mutated messages.

Draft 2020-12 semantics for the keywords below; annotations are ignored.
"""

from __future__ import annotations

import re
from typing import Any, Callable
from urllib.parse import urldefrag, urljoin

Check = Callable[[Any], bool]
ANNOTATIONS = {"description", "$schema", "$id", "title", "default", "$comment", "examples", "$defs", "deprecated"}
KNOWN = ANNOTATIONS | {"type", "$ref", "properties", "additionalProperties", "required", "anyOf", "allOf", "minimum",
                       "maximum", "exclusiveMinimum", "exclusiveMaximum", "enum", "const", "items", "minLength",
                       "maxLength", "pattern", "minItems", "maxItems", "uniqueItems"}


class Unsupported(Exception):
    pass


def _is_type(x: Any, t: str) -> bool:
    if t == "integer":
        return (isinstance(x, int) and not isinstance(x, bool)) or (isinstance(x, float) and x.is_integer())
    if t == "number":
        return isinstance(x, (int, float)) and not isinstance(x, bool)
    if t == "string":
        return isinstance(x, str)
    if t == "boolean":
        return isinstance(x, bool)
    if t == "object":
        return isinstance(x, dict)
    if t == "array":
        return isinstance(x, list)
    if t == "null":
        return x is None
    raise Unsupported(f"type {t}")


def _equal(a: Any, b: Any) -> bool:
    """JSON equality: true is not 1, 1 is 1.0."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, dict)) or isinstance(b, (list, dict)):
        return False
    return bool(a == b)


def _num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


class Compiler:
    def __init__(self, schemas_by_id: dict[str, dict[str, Any]]) -> None:
        self.by_id = schemas_by_id
        self._refs: dict[str, Check] = {}

    def _resolve(self, uri: str) -> tuple[dict[str, Any], str]:
        doc_id, frag = urldefrag(uri)
        doc = self.by_id.get(doc_id)
        if doc is None:
            raise Unsupported(f"unknown $ref document {doc_id}")
        node: Any = doc
        for part in [p for p in frag.split("/") if p]:
            node = node[part.replace("~1", "/").replace("~0", "~")]
        return node, doc_id

    def ref(self, uri: str) -> Check:
        if uri not in self._refs:
            holder: list[Check] = []
            self._refs[uri] = lambda x: holder[0](x)  # placeholder, so recursive schemas terminate
            node, doc_id = self._resolve(uri)
            holder.append(self.compile(node, doc_id))
            self._refs[uri] = holder[0]
        return self._refs[uri]

    def compile(self, s: Any, base: str) -> Check:
        if s is True:
            return lambda x: True
        if s is False:
            return lambda x: False
        if not isinstance(s, dict):
            raise Unsupported("schema is not an object")
        unknown = set(s) - KNOWN
        if unknown:
            raise Unsupported(", ".join(sorted(unknown)))
        base = s.get("$id", base)
        checks: list[Check] = []
        if "$ref" in s:
            uri = urljoin(base, s["$ref"])
            checks.append(lambda x, u=uri: self._refs[u](x) if u in self._refs else self.ref(u)(x))
            self.ref(uri)
        if "type" in s:
            ts = s["type"] if isinstance(s["type"], list) else [s["type"]]
            for t in ts:
                _is_type(None, t)  # raises on an unknown type name
            checks.append(lambda x, ts=tuple(ts): any(_is_type(x, t) for t in ts))
        if "const" in s:
            checks.append(lambda x, c=s["const"]: _equal(x, c))
        if "enum" in s:
            checks.append(lambda x, e=tuple(s["enum"]): any(_equal(x, v) for v in e))
        for kw, op in (("minimum", float.__ge__), ("maximum", float.__le__), ("exclusiveMinimum", float.__gt__),
                       ("exclusiveMaximum", float.__lt__)):
            if kw in s:
                checks.append(lambda x, lim=float(s[kw]), op=op: not _num(x) or op(float(x), lim))
        if "minLength" in s:
            checks.append(lambda x, n=s["minLength"]: not isinstance(x, str) or len(x) >= n)
        if "maxLength" in s:
            checks.append(lambda x, n=s["maxLength"]: not isinstance(x, str) or len(x) <= n)
        if "pattern" in s:
            checks.append(lambda x, r=re.compile(s["pattern"]): not isinstance(x, str) or r.search(x) is not None)
        if "minItems" in s:
            checks.append(lambda x, n=s["minItems"]: not isinstance(x, list) or len(x) >= n)
        if "maxItems" in s:
            checks.append(lambda x, n=s["maxItems"]: not isinstance(x, list) or len(x) <= n)
        if s.get("uniqueItems"):
            checks.append(lambda x: not isinstance(x, list) or all(not _equal(x[i], x[j]) for i in range(len(x)) for j in range(i)))
        if "items" in s:
            item = self.compile(s["items"], base)
            checks.append(lambda x, c=item: not isinstance(x, list) or all(c(i) for i in x))
        if "required" in s:
            checks.append(lambda x, r=tuple(s["required"]): not isinstance(x, dict) or all(k in x for k in r))
        if "properties" in s or "additionalProperties" in s:
            props = {k: self.compile(v, base) for k, v in s.get("properties", {}).items()}
            extra = s.get("additionalProperties", True)
            extra_c = None if extra is True else self.compile(extra, base)

            def obj(x: Any, props: dict[str, Check] = props, extra_c: Check | None = extra_c) -> bool:
                if not isinstance(x, dict):
                    return True
                for k, v in x.items():
                    c = props.get(k, extra_c)
                    if c is not None and not c(v):
                        return False
                return True
            checks.append(obj)
        if "anyOf" in s:
            subs = [self.compile(x, base) for x in s["anyOf"]]
            checks.append(lambda x, subs=subs: any(c(x) for c in subs))
        if "allOf" in s:
            subs = [self.compile(x, base) for x in s["allOf"]]
            checks.append(lambda x, subs=subs: all(c(x) for c in subs))
        if len(checks) == 1:
            return checks[0]
        return lambda x, cs=tuple(checks): all(c(x) for c in cs)


def compile_schema(schema: dict[str, Any], schemas_by_id: dict[str, dict[str, Any]], base: str = "") -> Check | None:
    """The compiled check, or None when the schema uses something this module doesn't handle."""
    try:
        return Compiler(schemas_by_id).compile(schema, schema.get("$id", base))
    except (Unsupported, KeyError):
        return None
