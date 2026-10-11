// /kits: one card per device kit (asset type, radio, power, parts, cost, status). A click opens its wiring page.
import { useEffect, useState } from "react";
import { Brand } from "../hud/Brand";
import { LivePill } from "../hud/LivePill";
import { navigate, PageTabs } from "../hud/PageTabs";
import { ASSET_LABEL, fetchKits, POWER_LABEL, RADIO_LABEL, type KitSummary } from "../wiring/model";
import { groupKits, kitPath, StatusBadge } from "../wiring/kits";

export function KitsPage() {
  const [kits, setKits] = useState<KitSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { fetchKits().then(setKits).catch((e: unknown) => setError(String(e))); }, []);
  const built = kits?.filter((k) => k.status === "built").length ?? 0;
  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-4 p-4">
        <header className="card flex h-[60px] items-center gap-4 px-4">
          <Brand />
          <PageTabs className="ml-2" />
          <div className="ml-auto"><LivePill /></div>
        </header>
        <div>
          <h1 className="text-[20px] font-semibold">Device kits</h1>
          <p className="mt-1 text-[13px] text-ink-2">
            One kit design per kind of asset. {built} {built === 1 ? "kit is" : "kits are"} built on real hardware; every other kit is a
            reference design: real parts and a correct wiring plan, with simulated data.
          </p>
        </div>
        {error && <div role="alert" className="rounded-xl bg-crit-bg px-4 py-2 text-[13px] text-crit">{error}</div>}
        {!kits && !error && <div className="text-ink-2">Loading kits…</div>}
        {kits && groupKits(kits).map(([type, list]) => (
          <section key={type} aria-label={ASSET_LABEL[type]}>
            <h2 className="mb-2 text-[15px] font-semibold">{ASSET_LABEL[type]}</h2>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {list.map((k) => <KitCard key={k.id} k={k} />)}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function KitCard({ k }: { k: KitSummary }) {
  const cost = k.bom_cost_usd === null ? "Cost unknown" : `${k.bom_cost_complete ? "≈" : "≥"} $${k.bom_cost_usd.toFixed(0)}`;
  return (
    <a href={kitPath(k.id)} data-testid={`kit-${k.id}`}
      onClick={(e) => { if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return; e.preventDefault(); navigate(kitPath(k.id)); }}
      className="card flex flex-col gap-2 p-4 transition-shadow hover:shadow-[0_8px_24px_rgba(0,0,0,0.14)]">
      <div className="flex items-start justify-between gap-2">
        <div className="text-[15px] font-semibold leading-tight">{k.name}</div>
        <StatusBadge status={k.status} />
      </div>
      <p className="text-[13px] text-ink-2">{k.purpose}</p>
      <dl className="mt-1 grid grid-cols-[88px_1fr] gap-y-1 text-[13px]">
        <dt className="text-ink-2">Radio</dt><dd>{RADIO_LABEL[k.radio.protocol]} · {k.radio.chip}</dd>
        <dt className="text-ink-2">Power</dt><dd>{POWER_LABEL[k.power_source.type]}</dd>
        <dt className="text-ink-2">Parts</dt><dd className="tabular">{k.part_count} in {k.bom_lines} lines</dd>
        <dt className="text-ink-2">Bill of materials</dt><dd className="tabular">{cost}</dd>
        <dt className="text-ink-2">Used by</dt><dd>{k.devices.length ? k.devices.join(", ") : "No device yet"}</dd>
      </dl>
    </a>
  );
}
