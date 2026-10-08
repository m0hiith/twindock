import { useWorld } from "../store/world";
import { useTick } from "./ui";

/** WebSocket link state. Grey "Reconnecting" as soon as the socket drops. */
export function LivePill() {
  const conn = useWorld((s) => s.conn);
  const now = useTick(1000);
  const live = conn === "live";
  return (
    <div role="status" className={`flex h-9 items-center gap-2 rounded-xl px-3 text-[13px] font-medium ${live ? "bg-ok-bg text-ok" : "bg-idle-bg text-idle"}`}>
      <span className={`h-2 w-2 rounded-full ${live ? "bg-ok animate-pulse" : "bg-idle"}`} />
      {live ? "Live" : conn === "connecting" ? "Connecting" : "Reconnecting"}
      <span className="tabular text-ink-2">{new Date(now).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
    </div>
  );
}
