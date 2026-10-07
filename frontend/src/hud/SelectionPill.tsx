// Floating pill above the selected unit ("FL-01 · Loading PL-03 onto TR-01"). The 3D scene moves
// it each frame (PillTracker in scene/Selection.tsx); content comes from the server's unit state.
import { useEffect, useRef } from "react";
import { pillAnchor } from "../scene/Selection";
import { stateLabel, toneColor, toneOf } from "../status";
import { useWorld } from "../store/world";

export function SelectionPill() {
  const u = useWorld((s) => (s.selected ? s.units[s.selected] : undefined));
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    pillAnchor.el = ref.current;
    if (ref.current) ref.current.style.visibility = "hidden"; // until the tracker positions it
    return () => { pillAnchor.el = null; };
  }, [u?.id]);
  if (!u) return null;
  const tone = toneColor[toneOf(u)];
  return (
    <div ref={ref} className="pointer-events-none absolute left-0 top-0 z-10 -mt-2 flex items-center gap-1.5 whitespace-nowrap rounded-full border border-[var(--card-border)] bg-[var(--card)] px-2.5 py-1 text-[12px] font-medium text-ink shadow-[var(--card-shadow)]">
      <span className="h-2 w-2 rounded-full" style={{ background: tone.fg }} />
      <span className="font-semibold">{u.label ?? u.id}</span>
      <span className="text-ink-2">·</span>
      <span>{u.task ?? stateLabel(u.state)}</span>
      {u.source === "device" && <span className="ml-1 rounded-full bg-[#F3EDFF] px-1.5 text-[11px] font-semibold text-live">LIVE</span>}
    </div>
  );
}
