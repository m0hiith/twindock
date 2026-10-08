import { serverClock, useWorld } from "../store/world";
import { useTick } from "./ui";

/** WebSocket link state. Grey "Reconnecting" as soon as the socket drops. The clock is the
 *  server's (from server_ts_ms), the same clock every age and timestamp in the app uses. */
export function LivePill() {
  const conn = useWorld((s) => s.conn);
  const now = useTick(1000);
  const live = conn === "live";
  return (
    <div role="status" className={`flex h-9 items-center gap-2 rounded-xl px-3 text-[13px] font-medium ${live ? "bg-ok-bg text-ok" : "bg-idle-bg text-idle"}`}>
      <span className={`h-2 w-2 rounded-full ${live ? "bg-ok animate-pulse" : "bg-idle"}`} />
      {live ? "Live" : conn === "connecting" ? "Connecting" : "Reconnecting"}
      <span className="tabular text-ink-2">{new Date(now + serverClock.offsetMs).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
    </div>
  );
}
