// Auto mode: the warehouse works on its own (random jobs, waits and bays, chosen by the server).
// Shared by every screen; the switch shows the server's state, never the click.
import { useState } from "react";
import { useControl } from "../control/state";
import { useWorld } from "../store/world";

export function AutoModeToggle() {
  const auto = useWorld((s) => s.autoMode);
  const run = useControl((s) => s.run);
  const [waiting, setWaiting] = useState(false);
  const toggle = async () => {
    setWaiting(true);
    await run({ type: "set_auto_mode", enabled: !auto }, `Auto mode ${auto ? "off" : "on"}`);
    setWaiting(false);
  };
  return (
    <button type="button" role="switch" aria-checked={auto} onClick={toggle} disabled={waiting}
      title={auto ? "The warehouse is working on its own. Click to stop." : "Let the warehouse work on its own"}
      className={`flex h-9 items-center gap-2 rounded-xl border px-3 text-[13px] font-medium transition-colors ${auto ? "border-warn bg-warn-bg text-warn" : "border-[var(--card-border)] bg-white text-ink"}`}>
      <span className={`relative h-4 w-7 rounded-full transition-colors ${auto ? "bg-warn" : "bg-[#D5DAE5]"}`}>
        <span className={`absolute top-0.5 h-3 w-3 rounded-full bg-white transition-[left] ${auto ? "left-3.5" : "left-0.5"}`} />
      </span>
      Auto{waiting ? "…" : auto ? " on" : " off"}
    </button>
  );
}
