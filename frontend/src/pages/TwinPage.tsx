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
import { ProductionKpis } from "../hud/ProductionKpis";
import { SafetyPanel } from "../hud/SafetyPanel";
import { AlertsCard } from "../hud/AlertsPanel";
import { MiniMap } from "../hud/MiniMap";
import { useView, useWorld } from "../store/world";

// The scene fills the viewport; HUD cards float over it. The overlay itself ignores the pointer
// so dragging between cards still pans the map; each card opts back in.
export function TwinPage() {
  // KPIs, shipments and the fleet table describe the warehouse; FAC-01 gets its own cards.
  const warehouse = useView((s) => s.site) === "WH-01";
  const building = useView((s) => s.building);
  const selected = useWorld((s) => s.selected);
  const inspecting = building !== null || selected !== null;
  return (
    <div className="relative h-full w-full">
      <Scene />
      <SelectionPill />
      <div className="pointer-events-none absolute inset-4 z-20 flex flex-col gap-3">
        <TopBar />
        <div className="flex justify-center empty:hidden"><FakeBoardBanner /></div>
        {/* Two columns between the top bar and the bottom edge, each never taller than the screen: on the left the
            KPIs and the shipment or safety panel; on the right the inspect card (scrolls inside), the alerts (fold up
            while something is inspected), the mini-map (steps aside while inspecting) and the fleet table. */}
        <div className="flex min-h-0 flex-1 justify-between gap-3">
          <div className="flex min-h-0 min-w-0 flex-col justify-between gap-3">
            {warehouse ? <KpiCards /> : <div className="flex shrink-0 items-start gap-3"><ProductionKpis /><SiteDevicesCard /></div>}
            <div className="flex min-h-0 flex-col justify-end">
              {warehouse ? <ShipmentPanel /> : <SafetyPanel className="min-h-0 w-[420px] overflow-y-auto [&>*]:shrink-0" />}
            </div>
          </div>
          <div className="flex min-h-0 items-start gap-3">
            <div className="pointer-events-auto shrink-0"><MapControls /></div>
            <div className="flex h-full min-h-0 flex-col items-end gap-3">
              <InspectCard />
              <div className="shrink-0"><AlertsCard collapsed={inspecting} /></div>
              {!inspecting && <MiniMap className="shrink-0" />}
              {warehouse && <div className="mt-auto shrink-0"><FleetTable /></div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
