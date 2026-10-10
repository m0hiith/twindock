import { FakeBoardBanner } from "../hud/FakeBoardBanner";
import { FleetTable } from "../hud/FleetTable";
import { InspectCard } from "../hud/InspectCard";
import { KpiCards } from "../hud/KpiCards";
import { MapControls } from "../hud/MapControls";
import { SelectionPill } from "../hud/SelectionPill";
import { ShipmentPanel } from "../hud/ShipmentPanel";
import { TopBar } from "../hud/TopBar";
import { Scene } from "../scene/Scene";
import { SiteDevicesCard } from "../hud/SiteDevicesCard";
import { useView } from "../store/world";

// The scene fills the viewport; HUD cards float over it. The overlay itself ignores the pointer
// so dragging between cards still pans the map; each card opts back in.
export function TwinPage() {
  // KPIs, shipments and the fleet table describe the warehouse; FAC-01 gets its own cards.
  const warehouse = useView((s) => s.site) === "WH-01";
  return (
    <div className="relative h-full w-full">
      <Scene />
      <SelectionPill />
      <div className="pointer-events-none absolute inset-4 z-20 flex flex-col gap-3">
        <TopBar />
        <div className="flex justify-center empty:hidden"><FakeBoardBanner /></div>
        <div className="flex items-start justify-between gap-3">
          {warehouse ? <KpiCards /> : <SiteDevicesCard />}
          <div className="flex items-start gap-3">
            <div className="pointer-events-auto"><MapControls /></div>
            <InspectCard />
          </div>
        </div>
        <div className="mt-auto flex items-end justify-between gap-3">
          {warehouse && <ShipmentPanel />}
          {warehouse && <FleetTable />}
        </div>
      </div>
    </div>
  );
}
