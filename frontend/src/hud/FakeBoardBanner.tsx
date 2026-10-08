import { useWorld } from "../store/world";

/** Required whenever data comes from tools/fake_board.py (hello.fw_version == "fake"). */
export function FakeBoardBanner() {
  const fake = useWorld((s) => s.gateway?.fake ?? false);
  if (!fake) return null;
  return (
    <div role="alert" className="pointer-events-auto rounded-full border border-crit bg-crit-bg px-3 py-1 text-[12px] font-semibold sm:px-4 sm:py-1.5 sm:text-[13px] text-crit shadow-[var(--card-shadow)]">
      FAKE BOARD<span className="hidden sm:inline"> · board data comes from tools/fake_board.py, not the SiWx917</span><span className="sm:hidden"> · not the SiWx917</span>
    </div>
  );
}
