// Client mirror of server state. It only ever changes in response to server messages:
// the UI sends intents (ws.ts) and waits for the backend to broadcast the result.
import { create } from "zustand";
import type { CommandAck, Event, Gateway, ServerMessage, Unit } from "../contract";
import type { Layout } from "../layout";

export type Conn = "connecting" | "live" | "reconnecting";

interface WorldState {
  conn: Conn;
  layout: Layout | null;
  units: Record<string, Unit>;
  /** Server receive time (performance.now) of each unit's latest update, for interpolation. */
  unitStamp: Record<string, number>;
  gateway: Gateway | null;
  selected: string | null;
  autoMode: boolean;
  events: Event[];
  acks: CommandAck[];
  setConn: (c: Conn) => void;
  setLayout: (l: Layout) => void;
  apply: (m: ServerMessage) => void;
}

const MAX_LOG = 200;

export const useWorld = create<WorldState>((set) => ({
  conn: "connecting",
  layout: null,
  units: {},
  unitStamp: {},
  gateway: null,
  selected: null,
  autoMode: false,
  events: [],
  acks: [],
  setConn: (conn) => set({ conn }),
  setLayout: (layout) => set({ layout }),
  apply: (m) =>
    set((s) => {
      const now = performance.now();
      switch (m.type) {
        case "world_snapshot": {
          const units: Record<string, Unit> = {};
          const unitStamp: Record<string, number> = {};
          for (const u of m.units) {
            units[u.id] = u;
            unitStamp[u.id] = now;
          }
          return { units, unitStamp, gateway: m.gateway, selected: m.selected_unit_id ?? null, autoMode: m.auto_mode };
        }
        case "unit_update": {
          const units = { ...s.units };
          const unitStamp = { ...s.unitStamp };
          for (const u of m.units) {
            units[u.id] = u;
            unitStamp[u.id] = now;
          }
          for (const id of m.removed ?? []) delete units[id];
          return { units, unitStamp, ...(m.auto_mode !== undefined ? { autoMode: m.auto_mode } : {}) };
        }
        case "gateway_update":
          return { gateway: m.gateway };
        case "selection_changed":
          return { selected: m.selected_unit_id ?? null };
        case "command_ack":
          return { acks: [...s.acks, m].slice(-MAX_LOG) };
        case "event":
          return { events: [...s.events, m].slice(-MAX_LOG) };
      }
    }),
}));

/** Purely local view state (not shared): hover and camera. */
interface ViewState {
  hovered: string | null;
  setHovered: (id: string | null) => void;
  /** Number of 90° steps from the default south-east view. */
  rotation: number;
  /** Multiplier on the fit-to-site zoom, clamped to 0.6–2 (CLAUDE.md). */
  zoom: number;
  /** Bumped to ask the camera to recenter on homeTarget. */
  homeNonce: number;
  focus: { x: number; z: number; nonce: number } | null;
  rotate: (dir: 1 | -1) => void;
  zoomBy: (f: number) => void;
  setZoom: (z: number) => void;
  home: () => void;
  focusOn: (x: number, z: number) => void;
}

export const ZOOM_MIN = 0.6;
export const ZOOM_MAX = 2;
const clampZoom = (z: number) => Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, z));

export const useView = create<ViewState>((set) => ({
  hovered: null,
  setHovered: (hovered) => set({ hovered }),
  rotation: 0,
  zoom: 1,
  homeNonce: 0,
  focus: null,
  rotate: (dir) => set((s) => ({ rotation: s.rotation + dir })),
  zoomBy: (f) => set((s) => ({ zoom: clampZoom(s.zoom * f) })),
  setZoom: (z) => set({ zoom: clampZoom(z) }),
  home: () => set((s) => ({ homeNonce: s.homeNonce + 1, zoom: 1 })),
  focusOn: (x, z) => set((s) => ({ focus: { x, z, nonce: (s.focus?.nonce ?? 0) + 1 } })),
}));
