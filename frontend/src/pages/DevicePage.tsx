// /device: the board's own page. For now it holds the BLE calibration helper; the board twin and
// status panels join it once the board photo and hotspot positions are in HARDWARE.md.
import { BleCalibration } from "../device/BleCalibration";
import { FakeBoardBanner } from "../hud/FakeBoardBanner";
import { LivePill } from "../hud/LivePill";
import { useWorld } from "../store/world";
import { Brand } from "../hud/Brand";

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
          <a href="/twin" className="hidden h-9 items-center rounded-xl border border-[var(--card-border)] bg-white px-3 text-[13px] font-medium sm:flex">Twin</a>
          <a href="/control" className="hidden h-9 items-center rounded-xl border border-[var(--card-border)] bg-white px-3 text-[13px] font-medium sm:flex">Control</a>
          <a href="/wiring" className="hidden h-9 items-center rounded-xl border border-[var(--card-border)] bg-white px-3 text-[13px] font-medium sm:flex">Wiring</a>
        </header>
        <div className="flex justify-center empty:hidden"><FakeBoardBanner /></div>
        <BleCalibration />
      </div>
    </div>
  );
}
