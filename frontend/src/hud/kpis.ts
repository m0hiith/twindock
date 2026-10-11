// KPI numbers, computed only from the server's unit list. On-time dispatch comes from the server's logistics
// event log (logistics_update, R3) once an order has shipped; until then dock utilisation stands in.
import type { Unit } from "../contract";

export interface KpiCounts {
  /** Pallets in the building: in racks, staged in zones, or on a forklift (not on a truck). */
  stock: number;
  stockInRacks: number;
  stockStaged: number;
  trucksOnSite: number;
  trucksDocked: number;
  docksInUse: number;
  docksUsable: number;
  docksMaintenance: number;
}

export function kpiCounts(units: Record<string, Unit>): KpiCounts {
  const c: KpiCounts = { stock: 0, stockInRacks: 0, stockStaged: 0, trucksOnSite: 0, trucksDocked: 0, docksInUse: 0, docksUsable: 0, docksMaintenance: 0 };
  for (const u of Object.values(units)) {
    switch (u.kind) {
      case "pallet":
        if (u.state === "loaded") break;
        c.stock++;
        if (u.state === "stored") c.stockInRacks++;
        if (u.state === "staged") c.stockStaged++;
        break;
      case "truck":
        if (u.state === "gone") break;
        c.trucksOnSite++;
        if (u.docked_at) c.trucksDocked++;
        break;
      case "dock":
        if (u.state === "maintenance") c.docksMaintenance++;
        else c.docksUsable++;
        if (u.state === "occupied") c.docksInUse++;
        break;
    }
  }
  return c;
}
