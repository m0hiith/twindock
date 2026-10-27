// /device: the board's own page. Board status and controls, its Wi-Fi history and the BLE calibration helper; the
// board twin joins it once the board photo and hotspot positions are in HARDWARE.md.
import { useState } from "react";
import { GatewayPanel } from "../control/GatewayPanel";
import { BleCalibration } from "../device/BleCalibration";
import { RangeBar, useHistory, type HistoryRange } from "../fleet/DevicePanel";
import { Sparkline } from "../fleet/ui";
import { LiveBadge } from "../hud/ui";
import { FakeBoardBanner } from "../hud/FakeBoardBanner";
import { LivePill } from "../hud/LivePill";
import { useWorld } from "../store/world";
import { Brand } from "../hud/Brand";
import { PageTabs } from "../hud/PageTabs";

/** True once the board has sent anything (hello or status). Until then every board panel says "Waiting for device". */
function useBoardSeen(): boolean {
  return useWorld((s) => Boolean(s.gateway?.hello || s.gateway?.status));
}

/** The board's Wi-Fi signal over time, from the historian (its own status messages: real data). */
function BoardTrend() {
  const id = useWorld((s) => s.layout?.gateway.id ?? "GW-01");
  const seen = useBoardSeen();
  const [range, setRange] = useState<HistoryRange>("1h");
  const points = useHistory(id, "wifi_rssi_dbm", range);
  return (
    <section className="card p-4" aria-label="Board signal history">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-[15px] font-semibold">{id} Wi-Fi signal</h2><LiveBadge />
        <span className="ml-auto text-[12px] text-ink-2">From the board's status messages</span>
      </div>
      <div className="mt-2"><RangeBar id={id} channel="wifi_rssi_dbm" range={range} onRange={setRange} /></div>
      <div className="mt-1.5">
        {seen || points.length > 0
          ? <Sparkline points={points} unit="dBm" />
          : <div className="grid h-24 place-items-center rounded-lg bg-[#F8F8F8] text-[12px] text-ink-2">Waiting for device</div>}
      </div>
    </section>
  );
}

export function DevicePage() {
  const site = useWorld((s) => s.layout?.site.short);
  const seen = useBoardSeen();
  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-4 p-4">
        <header className="card flex h-[60px] items-center gap-4 px-4">
          <Brand tight />
          <PageTabs className="ml-2" />
          <div className="ml-auto"><LivePill /></div>
        </header>
        <div className="flex justify-center empty:hidden"><FakeBoardBanner /></div>
        <div>
          <h1 className="text-[20px] font-semibold">Device</h1>
          <p className="mt-1 text-[13px] text-ink-2">
            The real SiWx917 board (GW-01){site ? ` at ${site}` : ""}. Everything on this page comes from its own MQTT messages.
          </p>
        </div>
        <div className="grid items-start gap-4 lg:grid-cols-[360px_minmax(0,1fr)]">
          <section className="card p-4" aria-label="Board"><GatewayPanel /></section>
          <BoardTrend />
        </div>
        {seen ? <BleCalibration /> : (
          <section className="card p-4" aria-label="BLE calibration">
            <h2 className="text-[15px] font-semibold">BLE calibration</h2>
            <p className="mt-1 text-ink-2">
              Calibrates forklift zones from the board's BLE scans of TD- tags. It opens once the board is connected and reporting.
            </p>
          </section>
        )}
      </div>
    </div>
  );
}
