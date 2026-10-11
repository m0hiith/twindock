// Read-only helpers over hardware/wiring.json (GET /api/wiring). Nothing about parts, pins or
// wires is hard-coded in the /wiring page: every view derives from these.
import type { Wiring, WiringPin, WiringStatus } from "../contract";
import { checkWiring } from "../contract/validate";
import type { Tone } from "../status";

export type Part = Wiring["parts"][number];
export type Connection = Wiring["connections"][number];
export type Bus = Wiring["buses"][number];
export type BoardDrawing = NonNullable<Wiring["board_drawing"]>;
export type Feature = BoardDrawing["features"][number];
export type PadColumn = BoardDrawing["pad_columns"][number];
export type KitInfo = Wiring["kit"];
/** One entry of GET /api/kits. */
export interface KitSummary extends KitInfo {
  board: string;
  part_count: number;
  bom_lines: number;
  bom_cost_usd: number | null;
  bom_cost_complete: boolean;
  devices: string[];
}

export const DEFAULT_KIT = "fl01_sensor_pack";
export const ASSET_LABEL: Record<KitInfo["asset_type"], string> = {
  forklift: "Forklifts", truck: "Trucks", dock: "Docks", pallet: "Pallets", machine: "Machines", conveyor: "Conveyors",
  utility: "Utilities", worker: "People", building: "Buildings", environment: "Environment", energy: "Energy", fire: "Fire safety",
};
export const RADIO_LABEL: Record<KitInfo["radio"]["protocol"], string> = {
  wifi: "Wi-Fi", ble: "Bluetooth LE", thread: "Thread", matter: "Matter", zigbee: "Zigbee", wired: "Wired",
};
export const POWER_LABEL: Record<KitInfo["power_source"]["type"], string> = {
  mains: "Mains", vehicle: "Vehicle supply", battery: "Battery", din_rail: "DIN rail", usb: "USB",
};

export async function fetchKits(): Promise<KitSummary[]> {
  const r = await fetch("/api/kits");
  if (!r.ok) throw new Error(`GET /api/kits: ${r.status}`);
  return (await r.json()) as KitSummary[];
}
export type Pin = WiringPin;
export type Status = WiringStatus;

export async function fetchWiring(kitId: string = DEFAULT_KIT): Promise<Wiring> {
  const r = await fetch(`/api/kits/${encodeURIComponent(kitId)}`);
  if (!r.ok) throw new Error(r.status === 404 ? `No kit called ${kitId}` : `GET /api/kits/${kitId}: ${r.status}`);
  return checkWiring(await r.json());
}

/** "vl53l1x.qwiic_in.SDA" -> { part: "vl53l1x", pin: "qwiic_in.SDA" } */
export function splitRef(ref: string): { part: string; pin: string } {
  const i = ref.indexOf(".");
  return { part: ref.slice(0, i), pin: ref.slice(i + 1) };
}

/** "qwiic_in.SDA" -> "qwiic_in"; pins without a prefix share the group "". */
export const pinGroup = (pin: string) => (pin.includes(".") ? pin.slice(0, pin.lastIndexOf(".")) : "");
export const pinShort = (pin: string) => pin.slice(pin.lastIndexOf(".") + 1);

export class WiringIndex {
  readonly parts = new Map<string, Part>();
  readonly buses = new Map<string, Bus>();
  /** Distance from the board in connections (on-board parts = 0), for laying out external modules. */
  readonly depth = new Map<string, number>();

  readonly w: Wiring;

  constructor(w: Wiring) {
    this.w = w;
    for (const p of w.parts) this.parts.set(p.id, p);
    for (const b of w.buses) this.buses.set(b.id, b);
    // Distance from the processor: on-board parts when the kit has a photographed board, else the SoC/module itself.
    const queue = w.parts.filter((p) => (w.board_drawing ? p.location === "on-board" : p.kind === "soc")).map((p) => p.id);
    for (const id of queue) this.depth.set(id, 0);
    while (queue.length) {
      const id = queue.shift()!;
      for (const c of this.connectionsOf(id)) {
        const other = this.otherEnd(c, id);
        if (!this.depth.has(other)) {
          this.depth.set(other, this.depth.get(id)! + 1);
          queue.push(other);
        }
      }
    }
  }

  part(id: string): Part | undefined {
    return this.parts.get(id);
  }

  pin(ref: string): { part: Part; pin: Pin } | undefined {
    const { part, pin } = splitRef(ref);
    const p = this.parts.get(part);
    const q = p?.pins.find((x) => x.name === pin);
    return p && q ? { part: p, pin: q } : undefined;
  }

  connectionsOf(partId: string): Connection[] {
    return this.w.connections.filter((c) => splitRef(c.from).part === partId || splitRef(c.to).part === partId);
  }

  otherEnd(c: Connection, partId: string): string {
    const a = splitRef(c.from).part;
    return a === partId ? splitRef(c.to).part : a;
  }

  feature(partId: string): Feature | undefined {
    return this.w.board_drawing?.features.find((f) => f.part === partId);
  }

  busName(id: string | null | undefined): string {
    if (!id) return "—";
    return this.buses.get(id)?.name ?? id;
  }

  /** Address as shown to people: "0x29 → 0x30 at boot" when firmware re-addresses the part. */
  address(p: Part): string {
    if (!p.address) return "—";
    return p.runtime_address ? `${p.address} → ${p.runtime_address} at boot` : p.address;
  }

  /** Open questions that keep this part (or the whole pack) unverified. */
  openQuestions(partId: string) {
    return this.w.open_questions.filter((q) => q.blocks.includes(partId));
  }

  /**
   * Connections a reading travels from `partId` back to the board, following the data line
   * (SDA on I2C, MISO on SPI). Each step says whether to walk the connection backwards.
   */
  dataPath(partId: string): { conn: Connection; reverse: boolean }[] {
    const DATA = new Set(["SDA", "MISO"]);
    const path: { conn: Connection; reverse: boolean }[] = [];
    let at = partId;
    const seen = new Set([at]);
    while ((this.depth.get(at) ?? 0) > 0 || path.length === 0) {
      const here = this.depth.get(at) ?? 0;
      const step = this.connectionsOf(at).find((c) => {
        const other = this.otherEnd(c, at);
        return DATA.has(c.signal) && !seen.has(other) && (this.depth.get(other) ?? 0) <= here;
      });
      if (!step) break;
      const reverse = splitRef(step.to).part === at;
      path.push({ conn: step, reverse });
      at = this.otherEnd(step, at);
      seen.add(at);
      if ((this.depth.get(at) ?? 0) === 0 && this.parts.get(at)?.location === "on-board") break;
    }
    return path;
  }
}

export const statusLabel: Record<Status, string> = { planned: "Planned", wired: "Wired", verified: "Verified" };
export const statusTone: Record<Status, Tone> = { planned: "idle", wired: "info", verified: "ok" };
export const statusHelp: Record<Status, string> = {
  planned: "Not connected yet",
  wired: "Connected, not read by firmware yet",
  verified: "Firmware has read real values from it",
};

/** Physical wire colours. Blue is used here only because the real Qwiic SDA wire is blue. */
export const WIRE_HEX: Record<string, string> = {
  red: "#D7262E",
  black: "#1C1C1C",
  blue: "#2463EB",
  yellow: "#F2C230",
  white: "#FFFFFF",
  green: "#22A355",
};

export const WIRE_SIGNAL: Record<string, string> = { red: "3.3 V", black: "GND", blue: "SDA (data)", yellow: "SCL (clock)" };

export const kindLabel: Record<Part["kind"], string> = {
  soc: "Processor", sensor: "Sensor", connector: "Connector", module: "Sensor module", transducer: "Transducer",
};
