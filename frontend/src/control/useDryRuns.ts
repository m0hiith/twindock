// Ask the server whether each candidate move is valid (move_unit with dry_run). The client never
// decides validity itself; it only shows the server's ok/reason/path. Re-checked whenever the
// world changes in a way that could change the answer.
import { useEffect, useState } from "react";
import { request } from "../store/ws";
import { useWorld } from "../store/world";
import type { Candidate, Checked } from "./state";

const DEBOUNCE_MS = 200;

/** Compact fingerprint of everything that move validation depends on. */
function worldSignature(s: ReturnType<typeof useWorld.getState>): string {
  let sig = s.conn;
  for (const u of Object.values(s.units)) {
    if (u.kind === "forklift") sig += `|${u.id}:${u.state}:${u.node}:${u.target_node}:${u.carrying}:${u.source}`;
    else if (u.kind === "truck") sig += `|${u.id}:${u.state}:${u.docked_at}:${u.target_node}:${u.cargo?.length}`;
    else if (u.kind === "pallet") sig += `|${u.id}:${u.node}:${u.holder}`;
    else if (u.kind === "dock" || u.kind === "charger") sig += `|${u.id}:${u.state}`;
  }
  return sig;
}

export function useDryRuns(unitId: string | null, candidates: Candidate[]): { results: Map<string, Checked>; checking: boolean } {
  const sig = useWorld((s) => (unitId ? worldSignature(s) : ""));
  const [results, setResults] = useState<Map<string, Checked>>(new Map());
  const [checking, setChecking] = useState(false);
  const candKey = candidates.map((c) => `${c.key}:${c.target}:${c.action}:${c.pallet_id ?? ""}`).join(",");

  useEffect(() => {
    if (!unitId || candidates.length === 0) {
      setResults(new Map());
      return;
    }
    let cancelled = false;
    setChecking(true);
    const t = setTimeout(() => {
      Promise.all(candidates.map(async (c): Promise<Checked> => {
        const { ack } = request({ type: "move_unit", unit_id: unitId, target_node: c.target, action: c.action, dry_run: true, ...(c.pallet_id ? { pallet_id: c.pallet_id } : {}) });
        const a = await ack;
        return { ...c, ok: a.ok, reason: a.reason, path: a.path };
      })).then((list) => {
        if (cancelled) return;
        setResults(new Map(list.map((r) => [r.key, r])));
        setChecking(false);
      });
    }, DEBOUNCE_MS);
    return () => { cancelled = true; clearTimeout(t); };
    // candKey stands in for candidates (a new array every render).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unitId, candKey, sig]);

  return { results, checking };
}

/** Several candidates can share a key (pick here, else just drive here): keep the first valid one,
 *  or the first one's rejection when none is valid. */
export function firstValid(results: Map<string, Checked>, keys: string[]): Checked | undefined {
  const list = keys.map((k) => results.get(k)).filter((r): r is Checked => r !== undefined);
  return list.find((r) => r.ok) ?? list[0];
}
