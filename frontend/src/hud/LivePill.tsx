import { useEffect, useState } from "react";
import { useWorld } from "../store/world";

export function LivePill() {
  const conn = useWorld((s) => s.conn);
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  const live = conn === "live";
  return (
    <div className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-[13px] font-medium ${live ? "bg-ok-bg text-ok" : "bg-idle-bg text-idle"}`}>
      <span className={`h-2 w-2 rounded-full ${live ? "bg-ok animate-pulse" : "bg-idle"}`} />
      {live ? "Live" : conn === "connecting" ? "Connecting" : "Reconnecting"}
      <span className="tabular text-ink-2">{now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
    </div>
  );
}
