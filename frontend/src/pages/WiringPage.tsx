// /wiring/:kit_id: how one device kit is connected, generated entirely from GET /api/kits/:id
// (hardware/kits/<id>.json). Three views, hover and click details, Export PNG / PDF, kit picker.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Wiring } from "../contract";
import { Brand } from "../hud/Brand";
import { FakeBoardBanner } from "../hud/FakeBoardBanner";
import { LivePill } from "../hud/LivePill";
import { PageTabs } from "../hud/PageTabs";
import { TabButton } from "../hud/ui";
import { useWorld } from "../store/world";
import { BreadboardView } from "../wiring/BreadboardView";
import { useBoardPhoto } from "../wiring/photo";
import { exportPdf, exportPng, renderView } from "../wiring/export";
import { DEFAULT_KIT, fetchKits, fetchWiring, statusLabel, WiringIndex, type KitSummary, type Status } from "../wiring/model";
import { KitBanner, KitPicker, kitPath } from "../wiring/kits";
import { PartPanel } from "../wiring/PartPanel";
import { PartsList } from "../wiring/PartsList";
import { useAllReadings } from "../wiring/readings";
import { SchematicView } from "../wiring/SchematicView";

type View = "breadboard" | "schematic" | "parts";
const VIEWS: { id: View; label: string }[] = [
  { id: "breadboard", label: "Breadboard" },
  { id: "schematic", label: "Schematic" },
  { id: "parts", label: "Parts list" },
];

function initialView(): View {
  const v = new URLSearchParams(location.search).get("view");
  return v === "schematic" || v === "parts" ? v : "breadboard";
}

/** /wiring/<kit_id> -> kit_id; bare /wiring is the FL-01 sensor pack. */
function kitFromPath(): string {
  const id = location.pathname.split("/")[2];
  return id ? decodeURIComponent(id) : DEFAULT_KIT;
}

export function WiringPage() {
  const [kitId, setKitId] = useState(kitFromPath);
  const [kits, setKits] = useState<KitSummary[]>([]);
  const [wiring, setWiring] = useState<Wiring | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setViewState] = useState<View>(initialView);
  const [selected, setSelected] = useState<string | null>(null);
  const [busy, setBusy] = useState<"png" | "pdf" | null>(null);
  const svg = useRef<SVGSVGElement | null>(null);
  const photo = useBoardPhoto();
  const online = useWorld((s) => s.gateway?.online ?? false);

  useEffect(() => {
    const onNav = () => { setKitId(kitFromPath()); setSelected(null); };
    addEventListener("popstate", onNav);
    return () => removeEventListener("popstate", onNav);
  }, []);
  useEffect(() => {
    fetchKits().then(setKits).catch((e: unknown) => setError(String(e)));
  }, []);
  useEffect(() => {
    setWiring(null);
    setError(null);
    fetchWiring(kitId).then(setWiring).catch((e: unknown) => setError(String(e)));
  }, [kitId]);

  const setView = (v: View) => {
    setViewState(v);
    const q = new URLSearchParams(location.search);
    if (v === "breadboard") q.delete("view");
    else q.set("view", v);
    history.replaceState(null, "", `${kitPath(kitId)}${q.size ? `?${q}` : ""}`);
  };

  const ix = useMemo(() => (wiring ? new WiringIndex(wiring) : null), [wiring]);
  const readings = useAllReadings(wiring?.parts ?? EMPTY);
  const registerSvg = useCallback((el: SVGSVGElement | null) => { svg.current = el; }, []);

  const doExport = async (kind: "png" | "pdf") => {
    if (!svg.current || !wiring) return;
    setBusy(kind);
    try {
      const label = VIEWS.find((v) => v.id === view)!.label;
      const stamp = new Date().toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
      const k = wiring.kit;
      const canvas = await renderView(svg.current, `${k.name} wiring · ${label}`,
        `${k.status === "built" ? "Built and verified" : "Reference design · simulated"} · ${wiring.board} · from hardware/kits/${k.id}.json · exported ${stamp}`, view === "breadboard");
      const name = `twindock-wiring-${k.id}-${view}`;
      if (kind === "png") await exportPng(canvas, `${name}.png`);
      else exportPdf(canvas, `${name}.pdf`);
    } catch (e) {
      setError(`Export failed: ${String(e)}`);
    } finally {
      setBusy(null);
    }
  };

  const counts = useMemo(() => {
    const c: Record<Status, number> = { planned: 0, wired: 0, verified: 0 };
    for (const p of wiring?.parts ?? []) c[p.status] += 1;
    return c;
  }, [wiring]);
  const part = selected ? ix?.part(selected) : undefined;

  return (
    <div className="flex h-full flex-col gap-3 p-3 sm:p-4">
      <header className="flex flex-wrap items-center gap-3">
        <Brand compact title="" />
        <div className="min-w-0 flex-1">
          <div className="text-[20px] font-semibold leading-tight">{wiring ? `${wiring.kit.name} wiring` : "Wiring"}</div>
          <div className="text-[13px] text-ink-2">{wiring ? wiring.kit.purpose : "Loading the kit…"}</div>
        </div>
        <KitPicker kits={kits} current={kitId} />
        <LivePill />
        {wiring?.kit.status === "built" && <span className={`flex h-9 items-center gap-2 rounded-xl px-3 text-[13px] font-medium ${online ? "bg-[#F3EDFF] text-live" : "bg-idle-bg text-idle"}`}>
          <span className={`h-2 w-2 rounded-full ${online ? "bg-live" : "bg-idle"}`} />
          {online ? "Board online" : "Board offline"}
        </span>}
        <PageTabs />
      </header>
      <div className="flex justify-center empty:hidden"><FakeBoardBanner /></div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="card flex gap-1 p-1" role="tablist">
          {VIEWS.map((v) => (
            <TabButton key={v.id} active={view === v.id} onClick={() => setView(v.id)}>
              <span className="px-1 text-[14px]">{v.label}</span>
            </TabButton>
          ))}
        </div>
        <div className="hidden items-center gap-3 px-2 text-[13px] text-ink-2 md:flex">
          {(Object.keys(counts) as Status[]).map((s) => <span key={s}><b className="tabular text-ink">{counts[s]}</b> {statusLabel[s].toLowerCase()}</span>)}
        </div>
        <div className="flex-1" />
        <button type="button" onClick={() => void doExport("png")} disabled={!wiring || busy !== null}
          className="h-10 rounded-xl border border-[var(--card-border)] bg-white px-4 text-[14px] font-medium hover:bg-idle-bg disabled:opacity-50">
          {busy === "png" ? "Exporting…" : "Export PNG"}
        </button>
        <button type="button" onClick={() => void doExport("pdf")} disabled={!wiring || busy !== null}
          className="h-10 rounded-xl bg-accent px-4 text-[14px] font-medium text-white hover:brightness-95 disabled:opacity-50">
          {busy === "pdf" ? "Exporting…" : "Export PDF"}
        </button>
      </div>

      {wiring && <KitBanner kit={wiring.kit} devices={kits.find((k) => k.id === wiring.kit.id)?.devices ?? []} />}

      {error && <div role="alert" className="rounded-xl bg-crit-bg px-4 py-2 text-[13px] text-crit">{error}</div>}

      <div className="flex min-h-0 flex-1 gap-3">
        <main className="card relative min-w-0 flex-1 overflow-hidden">
          {!ix ? (
            <div className="grid h-full place-items-center text-ink-2">{error ? "Wiring data unavailable" : "Loading wiring…"}</div>
          ) : view === "breadboard" ? (
            photo === "checking" ? null : (
              <BreadboardView key={kitId} ix={ix} photo={photo} readings={readings.byPart} online={readings.online}
                selected={selected} onSelect={setSelected} svgRef={registerSvg} />
            )
          ) : view === "schematic" ? (
            <SchematicView ix={ix} selected={selected} onSelect={setSelected} svgRef={registerSvg} />
          ) : (
            <PartsList ix={ix} selected={selected} onSelect={setSelected} svgRef={registerSvg} />
          )}
        </main>
        <aside className="card hidden w-[360px] shrink-0 overflow-hidden lg:block">
          {ix && part ? (
            <PartPanel ix={ix} part={part} readings={readings.byPart[part.id]} online={readings.online} onClose={() => setSelected(null)} />
          ) : (
            <Intro wiring={wiring} />
          )}
        </aside>
      </div>
    </div>
  );
}

const EMPTY: Wiring["parts"][number][] = [];

function Intro({ wiring }: { wiring: Wiring | null }) {
  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4 text-[14px]">
      <div>
        <div className="text-[20px] font-semibold leading-tight">Click a part</div>
        <p className="mt-1 text-ink-2">See what it does in this kit, how it is connected{wiring?.kit.status === "built" ? " and its latest reading" : ""}.</p>
      </div>
      <div className="flex flex-col gap-2.5">
        <div className="text-[13px] font-semibold">What the colours mean</div>
        <LegendRow swatch={<span className="block h-4 w-7 rounded border border-dashed border-idle bg-[#F1F1F1]" />}>Planned · not connected yet</LegendRow>
        <LegendRow swatch={<span className="block h-4 w-7 rounded border border-ink bg-[#2E2E2E]" />}>Wired · connected, not read yet</LegendRow>
        <LegendRow swatch={<span className="block h-4 w-7 rounded border-2 border-ok bg-white" />}>Verified · the firmware has read it</LegendRow>
        {wiring?.kit.status === "built" && <LegendRow swatch={<span className="block h-3 w-3 rounded-full bg-live" />}>Live reading from the board</LegendRow>}
      </div>
      {(wiring?.connections.some((c) => c.medium === "qwiic_cable") ?? true) && <div className="flex flex-col gap-2.5">
        <div className="text-[13px] font-semibold">Qwiic cable wires</div>
        {([["#D7262E", "Red", "3.3 V power"], ["#1C1C1C", "Black", "Ground"], ["#2463EB", "Blue", "SDA · data"], ["#F2C230", "Yellow", "SCL · clock"]] as const).map(([c, n, l]) => (
          <LegendRow key={n} swatch={<span className="block h-1.5 w-7 rounded-full" style={{ background: c }} />}>{n} · {l}</LegendRow>
        ))}
      </div>}
      {wiring && wiring.open_questions.length > 0 && (
        <div className="rounded-xl bg-warn-bg p-3 text-[13px]">
          <div className="font-semibold text-warn">Still open</div>
          <ul className="mt-1 list-disc space-y-1 pl-4">
            {wiring.open_questions.map((q) => <li key={q.id}>{q.question}</li>)}
          </ul>
        </div>
      )}
      <p className="mt-auto text-[12px] text-ink-2">
        {wiring?.kit.status === "reference"
          ? `Generated from hardware/kits/${wiring.kit.id}.json. Reference design: real parts, simulated data. Values marked unverified must be checked before building.`
          : "Generated from the kit file in hardware/kits. Readings appear only from real messages sent by the board; until then a part shows “Waiting for firmware”."}
      </p>
    </div>
  );
}

function LegendRow({ swatch, children }: { swatch: React.ReactNode; children: React.ReactNode }) {
  return <div className="flex items-center gap-3"><span className="flex w-7 justify-center">{swatch}</span><span>{children}</span></div>;
}
