// "Hosted demo" banner (D2): on the public deploy every value comes from the simulator, so the page says so on every
// screen. The real SiWx917 board is shown in the live demo (laptop + board). Grey, never violet: nothing here is live.
import { useEffect, useState } from "react";

export function HostedBanner() {
  const [hosted, setHosted] = useState(false);
  useEffect(() => {
    let alive = true;
    fetch("/api/health").then((r) => (r.ok ? r.json() : null)).then((j: { hosted?: boolean } | null) => { if (alive && j?.hosted) setHosted(true); }).catch(() => undefined);
    return () => { alive = false; };
  }, []);
  if (!hosted) return null;
  return (
    <div role="note" className="pointer-events-none fixed inset-x-0 bottom-3 z-50 flex justify-center px-4">
      <div className="pointer-events-auto rounded-full border border-[var(--card-border)] bg-white/95 px-4 py-1.5 text-[12px] text-ink shadow-[0_8px_24px_rgba(0,0,0,0.08)]">
        <span className="font-semibold">Hosted demo</span> · Simulated factory · the real SiWx917 board is shown in the live demo
      </div>
    </div>
  );
}
