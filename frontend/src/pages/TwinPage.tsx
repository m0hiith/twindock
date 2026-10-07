import { FakeBoardBanner } from "../hud/FakeBoardBanner";
import { LivePill } from "../hud/LivePill";
import { MapControls } from "../hud/MapControls";
import { SelectionPill } from "../hud/SelectionPill";
import { Scene } from "../scene/Scene";
import { useWorld } from "../store/world";

export function TwinPage() {
  const site = useWorld((s) => s.layout?.site);
  return (
    <div className="relative h-full w-full">
      <Scene />
      <SelectionPill />
      <div className="pointer-events-none absolute inset-x-4 top-4 flex items-start justify-between gap-4">
        <div className="card pointer-events-auto flex items-center gap-3 px-3 py-2">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-structure text-white">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinejoin="round"><path d="M4 15 12 7l8 8" /><path d="M9 15h6v4H9z" /></svg>
          </span>
          <span className="text-[15px] font-semibold">TwinDock</span>
          {site && <span className="text-ink-2">{site.short}</span>}
          <LivePill />
        </div>
        <FakeBoardBanner />
        <div className="pointer-events-auto"><MapControls /></div>
      </div>
    </div>
  );
}
