// Side panel for the selected part: plain-language caption first (non-engineers read this page),
// then what it measures, bus and address, status, and the reading area.
import type { ReactNode } from "react";
import { channelLabel, formatReading as formatDeviceReading, readingEntries } from "../fleet/format";
import { ago, Icon, LiveBadge, SimBadge, useTick } from "../hud/ui";
import { useWorld } from "../store/world";
import { kindLabel, statusHelp, type Part, type WiringIndex } from "./model";
import { formatReading, sensorLabel, WAITING, type PartReadings } from "./readings";
import { StatusBadge } from "./ui";

export function PartPanel({ ix, part, readings, online, onClose }: {
  ix: WiringIndex; part: Part; readings: PartReadings | undefined; online: boolean; onClose: () => void;
}) {
  const questions = ix.openQuestions(part.id);
  const supply = part.supply ? `${part.supply.min_v}–${part.supply.max_v} V` : null;
  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="flex items-start gap-3 border-b border-[var(--card-border)] p-4">
        <div className="min-w-0 flex-1">
          <div className="text-[12px] text-ink-2">{kindLabel[part.kind]} · {part.location === "on-board" ? "On board" : "External"}</div>
          <div className="text-[20px] font-semibold leading-tight">{part.name}</div>
          <div className="text-[13px] text-ink-2">{part.part_number}{part.quantity > 1 ? ` × ${part.quantity}` : ""}</div>
        </div>
        <button type="button" onClick={onClose} aria-label="Close" className="grid h-8 w-8 place-items-center rounded-lg text-ink-2 hover:bg-idle-bg">
          <Icon name="close" />
        </button>
      </div>

      <div className="flex flex-col gap-4 p-4">
        <p className="text-[15px] leading-snug">{part.caption}</p>
        <StatusBadge status={part.status} help />

        {ix.w.kit.status === "reference"
          ? <SimReadings kitId={ix.w.kit.id} />
          : <ReadingArea part={part} readings={readings} online={online} />}

        <dl className="grid grid-cols-[110px_1fr] gap-x-3 gap-y-2 text-[13px]">
          {part.measures && <Row k="Measures">{part.measures}</Row>}
          {part.forklift_use && <Row k="On the forklift">{part.forklift_use}</Row>}
          <Row k="Bus">{ix.busName(part.bus)}</Row>
          {part.address && <Row k="I2C address">{ix.address(part)}</Row>}
          <Row k="Power">{ix.busName(part.supplied_from)}{supply ? ` · accepts ${supply}` : ""}</Row>
          {part.enable_pin && <Row k="Enable pin">{part.enable_pin.split(".").slice(1).join(".")}</Row>}
          {part.sdk_driver && <Row k="SDK driver">{part.sdk_driver}</Row>}
          {(part.topics?.length ?? 0) > 0 && <Row k="MQTT topics">{part.topics!.map((t) => <div key={t} className="font-mono text-[12px] [overflow-wrap:anywhere]">{t}</div>)}</Row>}
        </dl>

        {part.pins.length > 0 && (
          <div>
            <div className="mb-1.5 text-[13px] font-semibold">Pins</div>
            <div className="flex flex-wrap gap-1.5">
              {part.pins.map((p) => (
                <span key={p.name} title={`${p.signal}${p.gpio ? ` · ${p.gpio}` : ""} · ${p.evidence}`}
                  className="rounded-md bg-idle-bg px-1.5 py-0.5 font-mono text-[11.5px]">{p.name}{p.gpio && p.gpio !== p.name ? ` · ${p.gpio}` : ""}</span>
              ))}
            </div>
          </div>
        )}

        {questions.length > 0 && (
          <div className="rounded-xl bg-warn-bg p-3 text-[13px]">
            <div className="font-semibold text-warn">Open question{questions.length > 1 ? "s" : ""}</div>
            {questions.map((q) => <p key={q.id} className="mt-1">{q.question}</p>)}
          </div>
        )}

        {part.notes && (
          <details className="text-[13px]">
            <summary className="cursor-pointer font-semibold">Engineering notes</summary>
            <p className="mt-1 text-ink-2">{part.notes}</p>
          </details>
        )}
      </div>
    </div>
  );
}

/** Real readings only: "Waiting for firmware" until a message arrives, greyed with age when the
 *  board is offline. W2 needs no change here: readings come through readings.ts. */
export function ReadingArea({ part, readings, online }: { part: Part; readings: PartReadings | undefined; online: boolean }) {
  useTick(1000);
  const topics = readings?.topics ?? [];
  if (topics.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--card-border)] p-3 text-[13px] text-ink-2">
        {part.kind === "transducer" ? "Read through the part it is wired to." : "Sends no readings of its own."}
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-[var(--card-border)] p-3">
      <div className="mb-2 flex items-center gap-2 text-[13px] font-semibold">
        Live reading
        {online && topics.some((t) => t.reading) && <LiveBadge />}
        {!online && topics.some((t) => t.reading) && <span className="text-[12px] font-medium text-idle">Board offline</span>}
      </div>
      <div className="flex flex-col gap-2">
        {topics.map(({ topic, name, reading }) => (
          <div key={topic} className="flex items-baseline justify-between gap-3">
            <span className="text-[13px] text-ink-2">{sensorLabel(name)}</span>
            {reading ? (
              <span className={`tabular text-right ${online ? "text-live" : "text-idle"}`}>
                <span className="text-[20px] font-semibold">{formatReading(reading)}</span>
                <span className="ml-2 text-[12px] text-ink-2">{ago(reading.received_ms)}</span>
              </span>
            ) : (
              <span className="text-[13px] font-medium text-ink-2">{WAITING}</span>
            )}
          </div>
        ))}
      </div>
      {part.status !== "verified" && (
        <div className="mt-2 text-[12px] text-ink-2">{statusHelp[part.status]}. It becomes verified once the firmware has read real values from it.</div>
      )}
    </div>
  );
}

function Row({ k, children }: { k: string; children: ReactNode }) {
  return (
    <>
      <dt className="text-ink-2">{k}</dt>
      <dd className="min-w-0">{children}</dd>
    </>
  );
}

/** A simulated kit: the latest readings of the SIM devices built from it (never violet, always with their age). */
function SimReadings({ kitId }: { kitId: string }) {
  useTick(1000);
  const devices = useWorld((s) => s.devices);
  const built = Object.values(devices).filter((d) => d.kit === kitId);
  return (
    <div className="rounded-xl border border-[var(--card-border)] p-3">
      <div className="mb-2 flex items-center gap-2 text-[13px] font-semibold">Readings <SimBadge /></div>
      {built.length === 0 && <div className="text-[13px] text-ink-2">No device uses this kit yet.</div>}
      <div className="flex flex-col gap-3">
        {built.map((d) => {
          const rs = readingEntries(d);
          return (
            <div key={d.id}>
              <div className="text-[12px] text-ink-2">{d.id} · {d.label}</div>
              {rs.length === 0 && <div className="text-[13px] text-ink-2">No reading yet</div>}
              {rs.map(([ch, r]) => (
                <div key={ch} className="flex items-baseline justify-between gap-3">
                  <span className="text-[13px] text-ink-2">{channelLabel(ch)}</span>
                  <span className="tabular text-right">
                    <span className="text-[15px] font-semibold">{formatDeviceReading(ch, r)}</span>
                    <span className="ml-2 text-[12px] text-ink-2">{ago(r.received_ms)}</span>
                  </span>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
