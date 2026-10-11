// Shared pieces for kits: the picker (grouped by asset type), the status banner and kit URLs.
import { ASSET_LABEL, type KitInfo, type KitSummary } from "./model";
import { navigate } from "../hud/PageTabs";

export const kitPath = (id: string) => `/wiring/${encodeURIComponent(id)}`;

/** Order the asset groups the same way everywhere. */
export function groupKits(kits: KitSummary[]): [KitInfo["asset_type"], KitSummary[]][] {
  const order = Object.keys(ASSET_LABEL) as KitInfo["asset_type"][];
  return order
    .map((t) => [t, kits.filter((k) => k.asset_type === t)] as [KitInfo["asset_type"], KitSummary[]])
    .filter(([, list]) => list.length > 0);
}

export function KitPicker({ kits, current }: { kits: KitSummary[]; current: string }) {
  return (
    <label className="flex items-center gap-2 text-[13px] text-ink-2">
      Kit
      <select value={current} aria-label="Kit"
        onChange={(e) => { navigate(kitPath(e.target.value)); }}
        className="h-9 max-w-[260px] rounded-xl border border-[var(--card-border)] bg-white px-2 text-[14px] text-ink">
        {kits.length === 0 && <option value={current}>{current}</option>}
        {groupKits(kits).map(([type, list]) => (
          <optgroup key={type} label={ASSET_LABEL[type]}>
            {list.map((k) => <option key={k.id} value={k.id}>{k.name}{k.status === "reference" ? " (simulated)" : ""}</option>)}
          </optgroup>
        ))}
      </select>
    </label>
  );
}

export function StatusBadge({ status }: { status: KitInfo["status"] }) {
  // Not violet: that colour is reserved for real device data, and a kit's status is not a reading.
  return status === "built"
    ? <span className="rounded-full bg-ok-bg px-1.5 py-px text-[11px] font-semibold tracking-wide text-ok">BUILT</span>
    : <span className="rounded-full bg-idle-bg px-1.5 py-px text-[11px] font-semibold tracking-wide text-ink-2">SIM</span>;
}

/** Built kits are real hardware; the others are real parts with simulated data. Never blurred. */
export function KitBanner({ kit, devices }: { kit: KitInfo; devices: string[] }) {
  const built = kit.status === "built";
  return (
    <div role="status" data-testid="kit-banner"
      className={`flex flex-wrap items-center gap-x-3 gap-y-1 rounded-xl px-4 py-2 text-[13px] ${built ? "bg-ok-bg text-ok" : "bg-idle-bg text-ink"}`}>
      <b className="text-[14px]">{built ? "Built and verified" : "Simulated kit"}</b>
      <span className={built ? "text-ink" : "text-ink-2"}>
        {built
          ? "Real hardware on the bench. Its readings come from the board itself."
          : "Real, buyable parts with a correct wiring plan. The readings shown come from the simulator (SIM)."}
      </span>
      {devices.length > 0 && <span className="ml-auto text-ink-2">Used by {devices.join(", ")}</span>}
    </div>
  );
}
