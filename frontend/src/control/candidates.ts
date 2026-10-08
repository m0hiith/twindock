// What the operator can ask the selected unit to do. These are only proposals: each one is sent
// to the server as a dry run, and the server's answer decides whether it is offered.
import type { Unit } from "../contract";
import type { Layout, LayoutNode } from "../layout";
import type { Action, Candidate } from "./state";

const TARGET_TYPES = new Set<LayoutNode["type"]>(["rack_slot", "zone", "dock", "charger", "bay", "gate"]);

/** Actions to try at a node, best first; the first one the server accepts is offered. */
function actionsAt(u: Unit, n: LayoutNode): Action[] {
  if (u.kind === "truck") return n.type === "gate" ? ["depart"] : n.type === "bay" ? ["dock"] : ["goto"];
  const carrying = Boolean(u.carrying);
  switch (n.type) {
    case "rack_slot":
    case "zone": return carrying ? ["drop"] : ["pick", "goto"];
    case "dock": return carrying ? ["load"] : ["pick", "goto"];
    case "charger": return ["charge"];
    default: return ["goto"];
  }
}

/** Map destinations: one entry per reachable target node, keyed `${node}#${i}`. */
export function destinationCandidates(u: Unit | undefined, layout: Layout | null): { nodes: LayoutNode[]; list: Candidate[] } {
  if (!u || !layout || (u.kind !== "forklift" && u.kind !== "truck")) return { nodes: [], list: [] };
  const nodes = layout.nodes.filter((n) => TARGET_TYPES.has(n.type) && n.kinds.includes(u.kind as "forklift" | "truck"));
  const list = nodes.flatMap((n) => actionsAt(u, n).map((action, i) => ({ key: `${n.id}#${i}`, label: n.label ?? n.id, target: n.id, action })));
  return { nodes, list };
}

export function destinationKeys(u: Unit, n: LayoutNode): string[] {
  return actionsAt(u, n).map((_, i) => `${n.id}#${i}`);
}

export type QuickKind = "pick" | "load" | "charge" | "dock" | "depart";

export const quickLabel: Record<QuickKind, string> = {
  pick: "Pick pallet", load: "Load onto docked truck", charge: "Go charge", dock: "Dock at bay", depart: "Depart",
};

export function quickKinds(u: Unit): QuickKind[] {
  if (u.kind === "forklift") return ["pick", "load", "charge"];
  if (u.kind === "truck") return ["dock", "depart"];
  return [];
}

export function quickCandidates(kind: QuickKind, units: Record<string, Unit>, layout: Layout): Candidate[] {
  const label = (id: string | null | undefined) => layout.nodes.find((n) => n.id === id)?.label ?? id ?? "";
  const all = Object.values(units);
  switch (kind) {
    case "pick":
      return all.filter((p) => p.kind === "pallet" && p.state !== "carried").flatMap((p) => {
        const truck = p.holder ? units[p.holder] : undefined;
        const at = truck ? truck.docked_at : p.node;
        if (!at) return []; // on a truck that isn't at a dock
        return [{ key: `pick:${p.id}`, label: p.id, sub: `${p.label ?? ""} · ${truck ? `on ${truck.id} at ${label(at)}` : label(at)}`, target: at, action: "pick" as const, pallet_id: p.id }];
      }).sort((a, b) => a.label.localeCompare(b.label));
    case "load":
      return all.filter((t) => t.kind === "truck" && t.docked_at).map((t) => ({
        key: `load:${t.id}`, label: `${t.id} at ${label(t.docked_at)}`, sub: `${t.cargo?.length ?? 0}/${t.meta?.capacity ?? "?"} pallets on board`, target: t.docked_at!, action: "load" as const,
      }));
    case "charge":
      return layout.chargers.map((c) => ({ key: `charge:${c.id}`, label: c.label, target: c.node, action: "charge" as const }));
    case "dock":
      return layout.docks.map((d) => ({ key: `dock:${d.id}`, label: d.label, sub: `Door ${d.door}`, target: d.bay_node, action: "dock" as const }));
    case "depart":
      return [{ key: "depart", label: "Leave via the gate", target: layout.gate_node, action: "depart" as const }];
  }
}
