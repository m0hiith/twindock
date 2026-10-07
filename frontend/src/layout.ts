// Static geometry served by GET /api/layout (backend/world/layout.json). Not a message, so it
// lives outside /shared; only the fields the frontend draws are typed here.
export type XZ = [number, number];
export type MoverKind = "forklift" | "truck";

export interface LayoutNode {
  id: string;
  type: "rack_slot" | "zone" | "dock" | "bay" | "charger" | "junction" | "gate" | "exit";
  x: number;
  z: number;
  kinds: MoverKind[];
  label?: string;
  spots?: XZ[];
}

export interface Rect { x: number; z: number; w: number; d: number }

export interface Layout {
  version: string;
  site: { id: string; name: string; short: string };
  bounds: { x: XZ; z: XZ };
  buildings: (Rect & { id: string; kind: "warehouse" | "office"; h: number; label?: string;
    doors?: { id: string; dock: string; wall: "south"; x: number; w: number }[] })[];
  racks: (Rect & { id: string; row: string; slots: string[] })[];
  zones: (Rect & { id: string; name: string; purpose: string })[];
  roads: { id: string; points: XZ[]; width: number; dashed: boolean }[];
  parking: (Rect & { id: string })[];
  fence: { lines: XZ[][]; gate: { x: number; z0: number; z1: number } };
  decor: { trees: XZ[]; containers: { x: number; z: number; heading_rad: number; color: string }[] };
  nodes: LayoutNode[];
  lanes: { a: string; b: string; kinds: MoverKind[]; reverse_into?: string | null }[];
  docks: { id: string; node: string; bay_node: string; door: string; label: string }[];
  chargers: { id: string; node: string; label: string }[];
  gate_node: string;
  exit_node: string;
  gateway: { id: string; label: string; x: number; z: number; ble_range_m: number };
}

export async function fetchLayout(): Promise<Layout> {
  const r = await fetch("/api/layout");
  if (!r.ok) throw new Error(`GET /api/layout: ${r.status}`);
  return (await r.json()) as Layout;
}
