// Live readings for the /wiring page, only from real board messages.
//
// A part lists the MQTT topics it feeds (wiring.json `topics`). The backend already keeps the last
// twin/gateway/sensor/<name> message per sensor in gateway.sensors (sent in gateway_update), limited
// to sensors the board's hello lists and HARDWARE.md exposes. So when W1/W2 add sensors, readings
// appear here without changes to this page. Nothing is defaulted: no message = no reading.
import { useMemo } from "react";
import type { Gateway } from "../contract";
import { useWorld } from "../store/world";
import type { Part } from "./model";

export interface Reading {
  topic: string;
  /** Sensor name: last topic segment ("temperature"). */
  name: string;
  value: number;
  unit: string;
  /** Board timestamp from the message. */
  ts_ms: number;
  /** When the backend received it (server clock), for "12s ago". */
  received_ms: number;
}

export interface PartReadings {
  /** One entry per topic of the part; null until a message has arrived. */
  topics: { topic: string; name: string; reading: Reading | null }[];
  /** Latest receive time across the part's readings, or null. */
  latest_ms: number | null;
}

const SENSOR_PREFIX = "twin/gateway/sensor/";

export function readingsFor(part: Part, gateway: Gateway | null): PartReadings {
  let latest: number | null = null;
  const topics = (part.topics ?? []).map((topic) => {
    const name = topic.slice(topic.lastIndexOf("/") + 1);
    const s = topic.startsWith(SENSOR_PREFIX) ? gateway?.sensors[name] : undefined;
    const reading: Reading | null = s
      ? { topic, name, value: s.data.value, unit: s.data.unit, ts_ms: s.data.ts_ms, received_ms: s.received_ms }
      : null;
    if (reading && (latest === null || reading.received_ms > latest)) latest = reading.received_ms;
    return { topic, name, reading };
  });
  return { topics, latest_ms: latest };
}

/** Readings for every part, plus whether the board is online (offline = show values greyed). */
export function useAllReadings(parts: readonly Part[]): { byPart: Record<string, PartReadings>; online: boolean } {
  const gateway = useWorld((s) => s.gateway);
  return useMemo(() => {
    const byPart: Record<string, PartReadings> = {};
    for (const p of parts) byPart[p.id] = readingsFor(p, gateway);
    return { byPart, online: gateway?.online ?? false };
  }, [parts, gateway]);
}

/** "21.4 °C". Precision follows the size of the number so lux and °C both read well. */
export function formatReading(r: Reading): string {
  const v = Math.abs(r.value) >= 100 ? r.value.toFixed(0) : Math.abs(r.value) >= 10 ? r.value.toFixed(1) : r.value.toFixed(2);
  return `${v} ${r.unit}`;
}

export const sensorLabel = (name: string) => (name.charAt(0).toUpperCase() + name.slice(1)).replace(/_/g, " ");

export const WAITING = "Waiting for firmware";
