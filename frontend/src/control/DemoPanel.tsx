// Demo runner (SITE_PROMPTS.md S10): the 5-minute site demo beat by beat. The real-board beats are
// done by hand on the board (nothing here can fake them); the site beats are triggered on cue and
// only drive the simulator and the movement engine.
import { useState } from "react";
import type { ScenarioCommand } from "../contract";
import { ago, LiveBadge, Pill, SimBadge, useTick } from "../hud/ui";
import { request } from "../store/ws";
import { useWorld } from "../store/world";

type Beat = ScenarioCommand["beat"];

// The projector shows /twin on FAC-01; camera and site are per-screen, so the phone can't move them.
const SITE_BEATS: { beat: Exclude<Beat, "reset">; title: string; watch: string }[] = [
  { beat: "degrade", title: "Degrade M-01",
    watch: "M-01's vibration climbs; within ~1 min it is flagged abnormal compared with its baseline and an alert opens. Acknowledge it here." },
  { beat: "near_miss", title: "Worker near a moving forklift",
    watch: "A forklift drives to the factory outbound while WK-02 walks that lane: amber/red rings and a proximity alert." },
  { beat: "visitor", title: "Visitor walks into the press area",
    watch: "WK-04 (visitor) enters the restricted press area: critical alert, resolves when they leave." },
  { beat: "cold_door", title: "Cold room door left open",
    watch: "After 60 s the door alert opens; the cold room warms past 5 °C and a temperature alert follows." },
  { beat: "stale", title: "A sensor stops reporting",
    watch: "AQ-01 goes stale after 15 s and offline after 60 s: /fleet shows it under Needs attention." },
];

function RunButton({ beat, label, primary = false }: { beat: Beat; label: string; primary?: boolean }) {
  const [state, setState] = useState<"idle" | "busy" | "done" | string>("idle");
  const run = async () => {
    setState("busy");
    const r = await request({ type: "scenario_command", beat }).ack;
    setState(r.type === "local_failure" ? r.reason : r.ok ? "done" : r.reason ?? "Rejected");
  };
  const cls = primary
    ? "h-9 whitespace-nowrap rounded-xl bg-[var(--accent)] px-3 text-[13px] font-semibold text-white hover:brightness-95 disabled:opacity-50"
    : "h-9 whitespace-nowrap rounded-xl border border-[var(--card-border)] px-3 text-[13px] font-medium hover:bg-idle-bg disabled:opacity-50";
  return (
    <span className="flex flex-col items-end gap-0.5">
      <button type="button" className={cls} disabled={state === "busy"} onClick={() => void run()}>{state === "busy" ? "Sending…" : label}</button>
      {state !== "idle" && state !== "busy" && <span className={`text-[11px] ${state === "done" ? "text-ok" : "text-crit"}`}>{state === "done" ? "Sent" : state}</span>}
    </span>
  );
}

export function DemoPanel() {
  const gw = useWorld((s) => s.gateway);
  const fake = gw?.fake ?? false;
  useTick(1000);
  return (
    <div className="flex flex-col gap-3">
      <div className="text-[12px] text-ink-2">The 5-minute site demo (full script in DEMO.md). Keep the projector on /twin with FAC-01 selected, run the beats in order, and watch for what each one describes.</div>

      <div className="card flex flex-col gap-2 p-3">
        <div className="flex items-center gap-2"><span className="font-semibold">1. Real board</span><LiveBadge /></div>
        <div className="flex items-center gap-2 text-[13px]">
          GW-01: <Pill tone={gw?.online ? "live" : "idle"}>{gw?.online ? "Online" : gw?.hello ? "Offline" : "Waiting for device"}</Pill>
          {gw?.status && <span className="text-[12px] text-ink-2">status {ago(gw.status.received_ms)}</span>}
          {fake && <span className="text-[12px] font-semibold text-crit">FAKE BOARD: stop tools/fake_board.py</span>}
        </div>
        <ol className="list-decimal pl-5 text-[13px] text-ink">
          <li>Press <b>BTN1</b> then <b>BTN0</b> on the board: FL-01 is selected and moves.</li>
          <li>Dock a truck at Bay 1 (Move tab): the real LED turns green after the board confirms.</li>
          <li>Unplug the router: GW-01 offline after 15 s, critical alert; it resolves on reconnect.</li>
        </ol>
        <div className="text-[12px] text-ink-2">Done by hand on the board: nothing here can trigger or fake these.</div>
      </div>

      <div className="flex items-center gap-2 px-1 pt-1"><span className="font-semibold">2. Factory (FAC-01)</span><SimBadge /></div>
      {SITE_BEATS.map((b, i) => (
        <div key={b.beat} className="card flex items-start gap-3 p-3">
          <div className="min-w-0 flex-1">
            <div className="font-medium">{String.fromCharCode(97 + i)}. {b.title}</div>
            <div className="mt-0.5 text-[12px] text-ink-2">{b.watch}</div>
          </div>
          <RunButton beat={b.beat} label="Run" />
        </div>
      ))}

      <div className="card flex flex-col gap-1 p-3">
        <div className="font-medium">3. Fleet and planning</div>
        <div className="text-[12px] text-ink-2">Open /fleet: GW-01 (LIVE) on top, AQ-01 under Needs attention. /plan (S8) is not built yet.</div>
      </div>

      <div className="flex items-center justify-between gap-3 pt-1">
        <span className="text-[12px] text-ink-2">Restores the seed world and the simulator's normal behaviour. The board is untouched.</span>
        <RunButton beat="reset" label="Reset demo" primary />
      </div>
    </div>
  );
}
