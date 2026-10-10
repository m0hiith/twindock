// Runtime validation of WebSocket messages against /shared/schemas (the same files the backend uses).
import Ajv2020, { type ValidateFunction } from "ajv/dist/2020";
import type { ClientMessage, ServerMessage, Wiring } from "./index";

const files = import.meta.glob<{ default: Record<string, unknown> }>("../../../shared/schemas/*/*.json", { eager: true });

const ajv = new Ajv2020({ allErrors: false, strict: false });
for (const mod of Object.values(files)) ajv.addSchema(mod.default);

const cache = new Map<string, ValidateFunction>();
function validatorFor(type: string): ValidateFunction | undefined {
  let v = cache.get(type);
  if (!v) {
    v = ajv.getSchema(`twindock/ws/${type}.json`);
    if (v) cache.set(type, v);
  }
  return v;
}

const SERVER_TYPES = new Set(["world_snapshot", "unit_update", "gateway_update", "selection_changed", "command_ack", "event", "ble_tracks", "device_update", "production_update"]);

/** Parse and validate a server message. Returns null (and logs) if it violates the contract. */
export function parseServerMessage(text: string): ServerMessage | null {
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    console.warn("[contract] server sent non-JSON");
    return null;
  }
  const type = (data as { type?: unknown })?.type;
  if (typeof type !== "string" || !SERVER_TYPES.has(type)) {
    console.warn("[contract] unknown server message type", type);
    return null;
  }
  const v = validatorFor(type);
  if (!v || !v(data)) {
    console.warn(`[contract] invalid ${type}`, v?.errors);
    return null;
  }
  return data as ServerMessage;
}

/** Validate an outgoing client message; throws in development so contract drift is loud. */
export function checkClientMessage(msg: ClientMessage): void {
  const v = validatorFor(msg.type);
  if (!v || !v(msg)) throw new Error(`[contract] invalid ${msg.type}: ${ajv.errorsText(v?.errors)}`);
}

/** Check GET /api/wiring against shared/schemas/hardware/wiring.json. Throws with the first error. */
export function checkWiring(data: unknown): Wiring {
  const v = ajv.getSchema("twindock/hardware/wiring.json");
  if (!v) throw new Error("[contract] wiring schema not loaded");
  if (!v(data)) throw new Error(`[contract] invalid /api/wiring: ${ajv.errorsText(v.errors)}`);
  return data as Wiring;
}
