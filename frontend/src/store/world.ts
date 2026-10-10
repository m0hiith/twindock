// Client mirror of server state. It only ever changes in response to server messages:
// the UI sends intents (ws.ts) and waits for the backend to broadcast the result.
import { create } from "zustand";
import type { BleTracks, CommandAck, Device, Event, Gateway, ProductionUpdate, ServerMessage, Site, Unit } from "../contract";
import type { Layout } from "../layout";
import { kpiCounts, type KpiCounts } from "../hud/kpis";

export type Conn = "connecting" | "live" | "reconnecting";

interface WorldState {
  conn: Conn;
  layout: Layout | null;
  units: Record<string, Unit>;
  /** Server receive time (performance.now) of each unit's latest update, for interpolation. */
  unitStamp: Record<string, number>;
  gateway: Gateway | null;
  /** Site twin: sites with zones (static per run) and every device, real (GW-01) and simulated. */
  sites: Site[];
  devices: Record<string, Device>;
  /** FAC-01 line analytics from the (simulated) machine monitors. */
  production: ProductionUpdate | null;
  selected: string | null;
  autoMode: boolean;
  events: Event[];
  acks: CommandAck[];
  ble: BleTracks | null;
  /** Smoothed RSSI per tag from successive ble_tracks messages (real scans only), oldest first. */
  bleHistory: Record<string, { t: number; avg: number; raw: number }[]>;
  /** KPI counts at the last world_snapshot, so KPI cards can show what changed since then. */
  baseline: { counts: KpiCounts; at_ms: number } | null;
  setConn: (c: Conn) => void;
  setLayout: (l: Layout) => void;
  apply: (m: ServerMessage) => void;
}

const MAX_LOG = 200;
const MAX_BLE_POINTS = 90; // 3 minutes of 2 s scans

/** Server time minus local time, from the latest server_ts_ms. Device ages are measured on the
 *  server clock, so a phone with a skewed clock still shows "12s ago" correctly. */
export const serverClock = { offsetMs: 0 };
export const serverNow = () => Date.now() + serverClock.offsetMs;

export const useWorld = create<WorldState>((set) => ({
  conn: "connecting",
  layout: null,
  units: {},
  unitStamp: {},
  gateway: null,
  sites: [],
  devices: {},
  production: null,
  selected: null,
  autoMode: false,
  events: [],
  acks: [],
  ble: null,
  bleHistory: {},
  baseline: null,
  setConn: (conn) => set({ conn }),
  setLayout: (layout) => set({ layout }),
  apply: (m) =>
    set((s) => {
      const now = performance.now();
      if ("server_ts_ms" in m) serverClock.offsetMs = m.server_ts_ms - Date.now();
      switch (m.type) {
        case "world_snapshot": {
          const units: Record<string, Unit> = {};
          const unitStamp: Record<string, number> = {};
          for (const u of m.units) {
            units[u.id] = u;
            unitStamp[u.id] = now;
          }
          const devices: Record<string, Device> = {};
          for (const d of m.devices) devices[d.id] = d;
          return {
            units, unitStamp, gateway: m.gateway, selected: m.selected_unit_id ?? null, autoMode: m.auto_mode,
            sites: m.sites, devices,
            baseline: { counts: kpiCounts(units), at_ms: m.server_ts_ms },
          };
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
        case "production_update":
          return { production: m };
        case "device_update": {
          const devices = { ...s.devices };
          for (const d of m.devices) devices[d.id] = d;
          for (const id of m.removed ?? []) delete devices[id];
          return { devices };
        }
        case "selection_changed":
          return { selected: m.selected_unit_id ?? null };
        case "command_ack":
          return { acks: [...s.acks, m].slice(-MAX_LOG) };
        case "event":
          return { events: [...s.events, m].slice(-MAX_LOG) };
        case "ble_tracks": {
          const bleHistory = { ...s.bleHistory };
          for (const t of m.tracks) {
            if (t.avg_rssi_dbm === null) continue;
            const h = bleHistory[t.name] ?? [];
            // A scan seen twice (lost-tag message re-sends tracks) adds no new point.
            if (h.at(-1)?.t === t.last_seen_ms) continue;
            bleHistory[t.name] = [...h, { t: t.last_seen_ms, avg: t.avg_rssi_dbm, raw: t.last_rssi_dbm }].slice(-MAX_BLE_POINTS);
          }
          return { ble: m, bleHistory };
        }
      }
    }),
}));

/** Purely local view state (not shared): hover, camera and which site this screen looks at. */
interface ViewState {
  hovered: string | null;
  /** Site shown on this screen (local, like the camera). */
  site: string;
  setSite: (id: string) => void;
  /** Site-twin device pucks in the 3D scene (hidden by default). */
  showDevices: boolean;
  setShowDevices: (v: boolean) => void;
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

const initialSite = new URLSearchParams(location.search).get("site") ?? "WH-01";

export const useView = create<ViewState>((set) => ({
  hovered: null,
  site: initialSite,
  setSite: (site) => set((s) => ({ site, homeNonce: s.homeNonce + 1, zoom: 1 })),
  showDevices: new URLSearchParams(location.search).has("devices"),
  setShowDevices: (showDevices) => set({ showDevices }),
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
