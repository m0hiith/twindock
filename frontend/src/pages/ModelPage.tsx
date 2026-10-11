// /model: how the simulation works. Every model with its equations in plain language, every parameter with its
// value, unit and source, every simulated sensor (part, report period, noise, resolution, range) and every random
// distribution. Served by GET /api/model from the same params the simulator runs on (backend/sim/params/*.yaml).
import { useEffect, useState } from "react";
import { Brand } from "../hud/Brand";
import { LivePill } from "../hud/LivePill";
import { PageTabs } from "../hud/PageTabs";
import { Pill } from "../hud/ui";
import type { Tone } from "../status";

type SourceKind = "datasheet" | "standard" | "typical" | "assumption";

interface Param {
  path: string;
  value: unknown;
  unit: string;
  source: string;
  kind: SourceKind;
  dist?: string;
  note?: string;
}

interface ModelInfo {
  key: string;
  title: string;
  equations: string[];
  reads: string[];
  writes: string[];
  parameters: Param[];
  distributions: Param[];
}

interface Channel {
  channel: string;
  unit: string | null;
  period_s: number;
  sigma: number;
  resolution: number;
  range: [number, number] | null;
  dropout_p: number;
  part: string;
  source: string;
  kind: SourceKind;
}

interface ModelCard {
  models: ModelInfo[];
  sensors: { device_type: string; kit: string; devices: string[]; channels: Channel[] }[];
  counts: { parameters: number; by_source: Partial<Record<SourceKind, number>> };
  core: Param[];
  devices: Param[];
  run: { mode: "embedded" | "external"; seed: number | null; t_s: number | null; recent_events: { t: number; name: string; cause: string }[] };
}

const KIND: Record<SourceKind, { label: string; tone: Tone }> = {
  datasheet: { label: "Datasheet", tone: "ok" },
  standard: { label: "Standard", tone: "ok" },
  typical: { label: "Typical value", tone: "info" },
  assumption: { label: "Assumption", tone: "idle" },
};

function fmt(v: unknown): string {
  if (Array.isArray(v)) return v.join(", ");
  if (v !== null && typeof v === "object") return Object.entries(v as Record<string, unknown>).map(([k, x]) => `${k} ${fmt(x)}`).join(" · ");
  return String(v);
}

function short(path: string): string {
  return path.split(".").slice(1).join(".");
}

function ParamRows({ rows }: { rows: Param[] }) {
  return (
    <table className="mt-2 w-full text-[13px]">
      <tbody className="divide-y divide-[var(--card-border)]">
        {rows.map((p) => (
          <tr key={p.path} className="align-top">
            <td className="py-1.5 pr-3 font-medium">{short(p.path)}</td>
            <td className="tabular whitespace-nowrap py-1.5 pr-3">{p.dist ? `${p.dist}(${fmt(p.value)})` : fmt(p.value)} <span className="text-ink-2">{p.unit === "1" || p.unit === "-" ? "" : p.unit}</span></td>
            <td className="w-[110px] py-1.5 pr-3"><Pill tone={KIND[p.kind].tone}>{KIND[p.kind].label}</Pill></td>
            <td className="py-1.5 text-ink-2">{p.source.replace(/^(datasheet|standard): /, "").replace(/^(typical industry value|assumption): ?/, "")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function ModelPage() {
  const [card, setCard] = useState<ModelCard | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    fetch("/api/model").then((r) => (r.ok ? r.json() : Promise.reject(new Error(`GET /api/model: ${r.status}`))))
      .then((j: ModelCard) => setCard(j)).catch((e: unknown) => setError(String(e)));
  }, []);
  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-[1100px] flex-col gap-4 p-4">
        <header className="card flex h-[60px] items-center gap-4 px-4">
          <Brand />
          <PageTabs className="ml-2" />
          <div className="ml-auto"><LivePill /></div>
        </header>
        <section className="card p-4">
          <h1 className="text-[20px] font-semibold">How the simulation works</h1>
          <p className="mt-1 max-w-[820px] text-[13px] text-ink-2">
            Everything marked SIM comes from these models. Each number is a cause and effect: machines draw air and power
            because they run, the compressor loads because pressure fell, the generator starts because the grid failed.
            Randomness appears only where real plants are random (failures, arrival times, scrap, people), always through a
            named distribution and a seeded stream. Models hold the true state; every simulated sensor reads it with the
            noise, resolution, range and report period of the real part in its kit. The real SiWx917 board is never simulated.
          </p>
          {card && (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-[13px]">
              <span className="font-medium">{card.counts.parameters} parameters:</span>
              {(Object.keys(KIND) as SourceKind[]).map((k) => (
                <Pill key={k} tone={KIND[k].tone}>{card.counts.by_source[k] ?? 0} {KIND[k].label.toLowerCase()}</Pill>
              ))}
              <span className="text-ink-2">
                · {card.run.mode === "embedded" ? `running in the backend, seed ${card.run.seed}, ${Math.round((card.run.t_s ?? 0) / 60)} simulated min` : "running as tools/site_sim.py"}
              </span>
            </div>
          )}
          {error && <div className="mt-3 text-crit">{error}</div>}
        </section>
        {card?.models.map((m) => (
          <section key={m.key} className="card p-4" aria-label={m.title}>
            <div className="flex items-baseline justify-between gap-3">
              <h2 className="text-[15px] font-semibold">{m.title}</h2>
              <span className="text-[12px] text-ink-2">
                {m.reads.length > 0 && <>reads {m.reads.join(", ")}</>}
                {m.reads.length > 0 && m.writes.length > 0 && " · "}
                {m.writes.length > 0 && <>writes {m.writes.join(", ")}</>}
              </span>
            </div>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-[13px]">
              {m.equations.map((e) => <li key={e}>{e}</li>)}
            </ul>
            {m.parameters.length > 0 && <ParamRows rows={m.parameters} />}
            {m.distributions.length > 0 && (
              <>
                <div className="mt-3 text-[12px] font-semibold uppercase tracking-wide text-ink-2">Random, by distribution</div>
                <ParamRows rows={m.distributions} />
              </>
            )}
          </section>
        ))}
        {card && (
          <section className="card p-4" aria-label="Sensors">
            <h2 className="text-[15px] font-semibold">Simulated sensors</h2>
            <p className="mt-1 text-[13px] text-ink-2">reading = clip(round(true value + noise, resolution), range); a sample is lost with the dropout chance.</p>
            {card.sensors.map((s) => (
              <div key={s.device_type} className="mt-3">
                <div className="text-[13px] font-semibold">{s.device_type.replace(/_/g, " ")} <span className="font-normal text-ink-2">· kit {s.kit} · {s.devices.join(", ")}</span></div>
                <table className="mt-1 w-full text-[13px]">
                  <tbody className="divide-y divide-[var(--card-border)]">
                    {s.channels.map((c) => (
                      <tr key={c.channel} className="align-top">
                        <td className="w-[140px] py-1 pr-3 font-medium">{c.channel}</td>
                        <td className="tabular whitespace-nowrap py-1 pr-3 text-ink-2">every {c.period_s} s{c.sigma ? ` · σ ${c.sigma}` : ""}{c.resolution ? ` · step ${c.resolution}` : ""}{c.range ? ` · ${c.range[0]}…${c.range[1]}` : ""} {c.unit ?? ""}{c.dropout_p ? ` · ${c.dropout_p * 100}% lost` : ""}</td>
                        <td className="py-1 pr-3">{c.part}</td>
                        <td className="w-[110px] py-1"><Pill tone={KIND[c.kind].tone}>{KIND[c.kind].label}</Pill></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </section>
        )}
        {card && (
          <section className="card p-4" aria-label="Core">
            <h2 className="text-[15px] font-semibold">Core and devices</h2>
            <ParamRows rows={[...card.core, ...card.devices]} />
          </section>
        )}
        {card && card.run.recent_events.length > 0 && (
          <section className="card p-4" aria-label="Recent events">
            <h2 className="text-[15px] font-semibold">Recent simulated events, with their cause</h2>
            <div className="mt-2 divide-y divide-[var(--card-border)] text-[13px]">
              {card.run.recent_events.map((e) => (
                <div key={`${e.t}-${e.name}`} className="flex gap-3 py-1">
                  <span className="tabular w-[80px] shrink-0 text-ink-2">{Math.floor(e.t / 60)}:{String(Math.floor(e.t % 60)).padStart(2, "0")}</span>
                  <span className="min-w-0 flex-1 text-ink-2">{e.cause} →</span>
                  <span className="min-w-0 flex-1">{e.name}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
