// Board controls. LED switches show only the board's confirmed state (pending in between);
// button lamps light only on real twin/gateway/button messages. Nothing here is defaulted.
import { ago, Icon, LiveBadge, useTick } from "../hud/ui";
import type { Gateway } from "../contract";
import { useWorld } from "../store/world";
import { useControl } from "./state";

// HARDWARE.md: LED0 and LED1 are the green and blue channels of the single RGB LED.
const LED_INFO: Record<string, { colour: string; name: string; rule?: string }> = {
  LED0: { colour: "#22C55E", name: "Green", rule: "Automatic: on while a truck is docked at Bay 1" },
  LED1: { colour: "#3B82F6", name: "Blue" },
};
// Buttons TwinDock exposes (HARDWARE.md); the board's hello decides which are actually present.
const BUTTON_INFO: Record<string, string> = {
  BTN0: "Selected forklift runs its next step",
  BTN1: "Select the next forklift",
};

function Switch({ on, pending, disabled, onClick, label }: { on: boolean; pending: boolean; disabled: boolean; onClick: () => void; label: string }) {
  return (
    <button type="button" role="switch" aria-checked={on} aria-label={label} disabled={disabled} onClick={onClick}
      className={`relative h-8 w-14 shrink-0 rounded-full transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${on ? "bg-info" : "bg-[#D5DAE5]"}`}>
      <span className={`absolute top-1 grid h-6 w-6 place-items-center rounded-full bg-white shadow transition-[left] ${on ? "left-7" : "left-1"}`}>
        {pending && <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-info border-t-transparent" />}
      </span>
    </button>
  );
}

export function GatewayPanel() {
  const gw = useWorld((s) => s.gateway);
  useTick(1000);

  if (!gw || (!gw.hello && !gw.status)) {
    return <div className="rounded-xl bg-idle-bg px-4 py-6 text-center text-ink-2">Waiting for device</div>;
  }
  const online = gw.online;
  const hello = gw.hello?.data;

  return (
    <div className={online ? "" : "opacity-80"}>
      <div className="flex items-center gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#F3EDFF] text-live"><Icon name="gateway" size={20} /></span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-[17px] font-semibold">{hello?.board ?? "Board"}<LiveBadge /></div>
          <div className="text-[12px] text-ink-2">
            {online ? "Online" : "Offline"} · last seen {gw.last_seen_ms ? ago(gw.last_seen_ms) : "never"}
          </div>
        </div>
        <span className={`rounded-full px-2 py-0.5 text-[12px] font-medium ${online ? "bg-[#F3EDFF] text-live" : "bg-crit-bg text-crit"}`}>{online ? "Online" : "Offline"}</span>
      </div>

      {gw.status && (
        <div className={`mt-3 grid grid-cols-3 gap-2 text-[12px] ${online ? "" : "text-idle"}`}>
          {([["Wi-Fi", gw.status.data.wifi_rssi_dbm, " dBm"], ["Reconnects", gw.status.data.reconnects, ""], ["Flushed", gw.status.data.buffered, " msgs"]] as const).map(([k, val, unit]) => (
            <div key={k} className="rounded-lg bg-idle-bg px-2.5 py-1.5">
              <div className="text-ink-2">{k}</div>
              <div className="tabular font-semibold">{val === undefined ? "Not reported" : `${val}${unit}`}</div>
            </div>
          ))}
          <div className="col-span-3 text-ink-2">From the board's status message, {ago(gw.status.received_ms)}{online ? "" : " (stale)"}</div>
        </div>
      )}

      <LedSection gw={gw} />
      <ButtonSection gw={gw} />
    </div>
  );
}

/** LED rows: confirmed state, pending spinner, switch (LED0 is rule-driven and locked). */
export function LedSection({ gw }: { gw: Gateway }) {
  const run = useControl((s) => s.run);
  const online = gw.online;
  const leds = Object.entries(gw.leds);
  // Mixed colour of the one physical RGB LED, from confirmed states only.
  const g = gw.leds.LED0?.on === true, b = gw.leds.LED1?.on === true;
  const mix = g && b ? "#22D3EE" : g ? LED_INFO.LED0!.colour : b ? LED_INFO.LED1!.colour : null;
  return (
    <>
  <div className="mt-4 flex items-baseline justify-between">
    <span className="text-[13px] font-semibold">RGB LED</span>
    <span className="flex items-center gap-1.5 text-[12px] text-ink-2">
      <span className="h-3 w-3 rounded-full ring-1 ring-[var(--card-border)]" style={{ background: mix ?? "#E5E8EF", boxShadow: mix && online ? `0 0 8px ${mix}` : undefined }} />
      {mix ? "Lit" : "Off or unknown"}
    </span>
  </div>
  <div className="mt-1 divide-y divide-[var(--card-border)]">
    {leds.length === 0 && <div className="py-3 text-ink-2">The board hasn't listed any LEDs</div>}
    {leds.map(([name, st]) => {
      if (!st) return null;
      const info = LED_INFO[name];
      const pending = st.pending !== null;
      const want = st.pending?.on ?? st.on;
      return (
        <div key={name} className="flex items-center gap-3 py-2.5">
          <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: st.on ? info?.colour ?? "var(--live)" : "#D5DAE5" }} />
          <div className="min-w-0 flex-1">
            <div className="font-medium">{name}{info && <span className="font-normal text-ink-2"> · {info.name}</span>}</div>
            <div className="truncate text-[12px] text-ink-2">
              {pending ? `Waiting for the board to switch it ${st.pending!.on ? "on" : "off"}…`
                : st.on === null ? "State not reported yet"
                : `${st.on ? "On" : "Off"} · confirmed ${st.received_ms ? ago(st.received_ms) : ""}`}
            </div>
            {info?.rule && <div className="text-[12px] text-ink-2">{info.rule}</div>}
          </div>
          <Switch on={want === true} pending={pending} label={`${name} ${st.on ? "on" : "off"}`}
            disabled={Boolean(info?.rule) || pending || !online}
            onClick={() => run({ type: "led_command", led: name, on: !(st.on === true) }, `${name} ${st.on ? "off" : "on"}`)} />
        </div>
      );
    })}
  </div>
    </>
  );
}

/** Button lamps, lit only by real twin/gateway/button messages. */
export function ButtonSection({ gw }: { gw: Gateway }) {
  const hello = gw.hello?.data;
  return (
    <>
  <div className="mt-4 text-[13px] font-semibold">Buttons</div>
  <div className="mt-2 grid grid-cols-2 gap-2">
    {(hello?.buttons ?? []).filter((n) => n in BUTTON_INFO).map((name) => {
      const st = gw.buttons[name];
      const pressed = st?.state === "pressed";
      return (
        <div key={name} className={`rounded-xl border p-3 transition-colors ${pressed ? "border-live bg-[#F3EDFF]" : "border-[var(--card-border)] bg-white"}`}>
          <div className="flex items-center justify-between">
            <span className="font-semibold">{name}</span>
            <span className={`h-3 w-3 rounded-full transition-all ${pressed ? "bg-live shadow-[0_0_10px_var(--live)]" : "bg-[#D5DAE5]"}`} aria-label={pressed ? "pressed" : "released"} />
          </div>
          <div className="mt-1 text-[12px] text-ink-2">{st ? `${pressed ? "Pressed" : "Released"} · ${ago(st.received_ms)}` : "No press yet"}</div>
          <div className="mt-1 text-[12px] leading-snug text-ink-2">{BUTTON_INFO[name] ?? ""}</div>
        </div>
      );
    })}
  </div>
    </>
  );
}
