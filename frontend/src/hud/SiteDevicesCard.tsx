// Device health for the site on screen (used where the warehouse KPIs don't apply).
import { useShallow } from "zustand/react/shallow";
import { summarize } from "../fleet/logic";
import { useView, useWorld } from "../store/world";
import { navigate } from "./PageTabs";
import { Icon } from "./ui";

export function SiteDevicesCard() {
  const site = useView((s) => s.site);
  const devices = useWorld(useShallow((s) => Object.values(s.devices).filter((d) => d.site_id === site)));
  const sum = summarize(devices);
  return (
    <button type="button" onClick={() => navigate("/fleet")}
      className="card pointer-events-auto flex w-[220px] flex-col gap-1 p-4 text-left hover:brightness-[0.99]">
      <span className="flex items-center gap-2 text-[13px] text-ink-2">
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-idle-bg text-ink"><Icon name="sensor" size={16} /></span>
        Devices online
      </span>
      <span className="tabular text-[28px] font-semibold leading-none">{sum.online}/{sum.total}</span>
      <span className="text-[12px] text-ink-2">
        {sum.attention ? <span className="font-medium text-warn">{sum.attention} need attention</span> : "All healthy"} · {sum.real ? `${sum.real} LIVE, ${sum.total - sum.real} SIM` : "all SIM"}
      </span>
    </button>
  );
}
