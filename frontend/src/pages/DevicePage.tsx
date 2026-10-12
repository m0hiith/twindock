// /device: the board's own page. For now it holds the BLE calibration helper; the board twin and
// status panels join it once the board photo and hotspot positions are in HARDWARE.md.
import { useState } from "react";
import { BleCalibration } from "../device/BleCalibration";
import { RangeBar, useHistory, type HistoryRange } from "../fleet/DevicePanel";
import { Sparkline } from "../fleet/ui";
import { LiveBadge } from "../hud/ui";
import { FakeBoardBanner } from "../hud/FakeBoardBanner";
import { LivePill } from "../hud/LivePill";
import { useWorld } from "../store/world";
import { Brand } from "../hud/Brand";
import { PageTabs } from "../hud/PageTabs";

/** The board's Wi-Fi signal over time, from the historian (its own status messages: real data). */
function BoardTrend() {
  const id = useWorld((s) => s.layout?.gateway.id ?? "GW-01");
  const [range, setRange] = useState<HistoryRange>("1h");
  const points = useHistory(id, "wifi_rssi_dbm", range);
  return (
    <section className="card p-4" aria-label="Board signal history">
      <div className="flex items-center gap-2">
        <h2 className="text-[15px] font-semibold">{id} Wi-Fi signal</h2><LiveBadge />
        <span className="ml-auto text-[12px] text-ink-2">From the board's status messages; empty until the board reports</span>
      </div>
      <div className="mt-2"><RangeBar id={id} channel="wifi_rssi_dbm" range={range} onRange={setRange} /></div>
      <div className="mt-1.5"><Sparkline points={points} unit="dBm" /></div>
    </section>
  );
}

export function DevicePage() {
  const site = useWorld((s) => s.layout?.site.short);
  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-4 p-4">
        <header className="flex items-center gap-3">
          <Brand compact title="" />
          <div className="min-w-0 flex-1">
            <div className="text-[15px] font-semibold leading-tight">Device · BLE calibration</div>
            <div className="text-[12px] text-ink-2">{site}</div>
          </div>
          <LivePill />
          <PageTabs className="hidden sm:flex" />
        </header>
        <div className="flex justify-center empty:hidden"><FakeBoardBanner /></div>
        <BoardTrend />
        <BleCalibration />
      </div>
    </div>
  );
}
