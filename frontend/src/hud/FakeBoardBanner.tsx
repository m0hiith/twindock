import { useWorld } from "../store/world";

/** Required whenever data comes from tools/fake_board.py (hello.fw_version == "fake"). */
export function FakeBoardBanner() {
  const fake = useWorld((s) => s.gateway?.fake ?? false);
  if (!fake) return null;
  return (
    <div role="alert" className="pointer-events-auto rounded-full border border-crit bg-crit-bg px-4 py-1.5 text-[13px] font-semibold text-crit shadow-[var(--card-shadow)]">
      FAKE BOARD · board data comes from tools/fake_board.py, not the SiWx917
    </div>
  );
}
