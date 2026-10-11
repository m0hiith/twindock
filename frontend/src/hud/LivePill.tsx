import { useState } from "react";
import { useControl } from "../control/state";
import { serverNow, useWorld } from "../store/world";
import { useTick } from "./ui";

/** WebSocket link state and the simulation clock. Grey "Reconnecting" as soon as the socket drops. The time is the
 *  server's simulated time (server_ts_ms), the same clock every age and timestamp in the app uses; x5 and x20 show
 *  the speed so a fast clock is never mistaken for real time. */
export function LivePill() {
  const conn = useWorld((s) => s.conn);
  const clock = useWorld((s) => s.simClock);
  useTick(1000);
  const live = conn === "live";
  const speed = clock?.speed ?? 1;
  return (
    <div className="flex items-center gap-1">
      <div role="status" className={`flex h-9 items-center gap-2 rounded-xl px-3 text-[13px] font-medium ${live ? "bg-ok-bg text-ok" : "bg-idle-bg text-idle"}`}
        title={clock?.warm_start ? `Simulation warm-started: ${Math.round(clock.warm_start.sim_s / 60)} simulated minutes in ${clock.warm_start.wall_s.toFixed(1)} s (seed ${clock.warm_start.seed})` : "Server clock"}>
        <span className={`h-2 w-2 rounded-full ${live ? "bg-ok animate-pulse" : "bg-idle"}`} />
        {live ? "Live" : conn === "connecting" ? "Connecting" : "Reconnecting"}
        <span className="tabular text-ink-2">{new Date(serverNow()).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", ...(speed > 1 ? { second: "2-digit" } : {}) })}</span>
      </div>
      {clock && <SpeedControl />}
    </div>
  );
}

function SpeedControl() {
  const clock = useWorld((s) => s.simClock);
  const run = useControl((s) => s.run);
  const [waiting, setWaiting] = useState(false);
  if (!clock) return null;
  const set = async (speed: 1 | 5 | 20) => {
    setWaiting(true);
    await run({ type: "set_sim_speed", speed }, `Simulation speed x${speed}`);
    setWaiting(false);
  };
  return (
    <div role="group" aria-label="Simulation speed" title={clock.speed_locked ?? "Simulation speed (x1 is real time)"}
      className="flex h-9 items-center rounded-xl border border-[var(--card-border)] p-0.5 text-[12px] font-medium">
      {clock.speeds.map((s) => (
        <button key={s} type="button" aria-pressed={clock.speed === s} disabled={waiting || (s !== 1 && clock.speed_locked !== null)}
          onClick={() => set(s)}
          className={`tabular h-7 rounded-lg px-2 transition-colors disabled:opacity-40 ${clock.speed === s ? (s === 1 ? "bg-info-bg text-ink" : "bg-warn-bg text-warn") : "text-ink-2 hover:bg-idle-bg"}`}>
          ×{s}
        </button>
      ))}
    </div>
  );
}
