// Guided tour overlay: everything except the current step's element is dimmed and blurred, and a card beside it says
// what it is. Opens by itself on a visitor's first visit (or with ?tour=1; ?tour=0 keeps it closed) and from the Tour
// tab in the page header.
import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from "react";
import { navigate } from "../hud/PageTabs";
import { useWorld } from "../store/world";
import { STEPS, type TourStep } from "./steps";
import { tourSeen, useTour } from "./store";

const PAD = 6; // between the element and the spotlight's edge
const GAP = 14; // between the spotlight and the card
const EDGE = 12; // closest the card comes to the window edge
const CARD_W = 360;
// A target that hasn't rendered by then (no data yet, or the screen is too narrow for it) gets a centred card instead.
const GIVE_UP_MS = 3000;
const SHADE: CSSProperties = { background: "rgba(17,17,17,0.5)", backdropFilter: "blur(4px)", WebkitBackdropFilter: "blur(4px)" };
const MOVE = "top 220ms ease, left 220ms ease, width 220ms ease, height 220ms ease";

type Rect = { top: number; left: number; width: number; height: number };

function findTarget(sel: string): Element | null {
  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) return el;
  }
  return null;
}

/** The element's box plus padding, clipped to the window (some targets are taller than the screen). */
function spotlight(el: Element): Rect {
  const r = el.getBoundingClientRect();
  const top = Math.max(4, r.top - PAD), left = Math.max(4, r.left - PAD);
  const bottom = Math.min(innerHeight - 4, r.bottom + PAD), right = Math.min(innerWidth - 4, r.right + PAD);
  return { top: Math.round(top), left: Math.round(left), width: Math.round(right - left), height: Math.round(bottom - top) };
}

const sameRect = (a: Rect | null, b: Rect) =>
  a !== null && a.top === b.top && a.left === b.left && a.width === b.width && a.height === b.height;

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

/** Below the spotlight if it fits, else above, right, left; a target that fills the screen gets the card inside it. */
function placeCard(r: Rect | null, w: number, h: number, look: boolean): { left: number; top: number } {
  const vw = innerWidth, vh = innerHeight;
  const cx = (x: number) => clamp(x, EDGE, vw - w - EDGE);
  const cy = (y: number) => clamp(y, EDGE, vh - h - EDGE);
  if (!r) return look ? { left: cx((vw - w) / 2), top: cy(vh - h - 96) } : { left: cx((vw - w) / 2), top: cy((vh - h) / 2) };
  const midX = r.left + r.width / 2 - w / 2, midY = r.top + r.height / 2 - h / 2;
  if (r.top + r.height + GAP + h <= vh - EDGE) return { left: cx(midX), top: r.top + r.height + GAP };
  if (r.top - GAP - h >= EDGE) return { left: cx(midX), top: r.top - GAP - h };
  if (r.left + r.width + GAP + w <= vw - EDGE) return { left: r.left + r.width + GAP, top: cy(midY) };
  if (r.left - GAP - w >= EDGE) return { left: r.left - GAP - w, top: cy(midY) };
  return { left: cx(midX), top: cy(r.top + r.height - h - 24) };
}

export function Tour() {
  const step = useTour((s) => s.step);
  const ready = useWorld((s) => s.layout !== null);
  // Wait for the app to load so the first thing a visitor sees isn't the tour over a "Can't reach the backend" card.
  useEffect(() => {
    if (!ready) return;
    const q = new URLSearchParams(location.search).get("tour");
    if (q === "1" || (q !== "0" && !tourSeen())) useTour.getState().start();
  }, [ready]);
  const s = step === null ? undefined : STEPS[step];
  return step === null || !s ? null : <Overlay key={step} index={step} s={s} />;
}

function Overlay({ index, s }: { index: number; s: TourStep }) {
  const next = STEPS[index + 1];
  const { go, stop } = useTour.getState();
  const [rect, setRect] = useState<Rect | null>(null);
  const [missing, setMissing] = useState(false);
  const [size, setSize] = useState({ w: CARD_W, h: 220 });
  const card = useRef<HTMLDivElement>(null);
  const primary = useRef<HTMLButtonElement>(null);

  // Go to the step's page, run its setup, then follow its element every frame (cards resize and move as data arrives).
  // Overlay is keyed by step, so each step starts with no spotlight.
  useEffect(() => {
    if (s.page && location.pathname !== s.page) navigate(s.page);
    s.enter?.();
    if (!s.target) return;
    const sel = s.target;
    const t0 = performance.now();
    let el: Element | null = null;
    let scrolled = false;
    let raf = 0;
    const tick = () => {
      if (el) {
        const r = el.getBoundingClientRect();
        if (!el.isConnected || r.width === 0 || r.height === 0) el = null;
      }
      el ??= findTarget(sel);
      if (el) {
        if (!scrolled) {
          scrolled = true;
          const r = el.getBoundingClientRect();
          // Only when its top is off screen: a tall table that starts on screen stays put, with its page summary above.
          if (r.top < 0 || r.top > innerHeight - 120) el.scrollIntoView({ block: r.height > innerHeight ? "start" : "center" });
        }
        const next = spotlight(el);
        setRect((prev) => (sameRect(prev, next) ? prev : next));
      } else {
        setRect(null);
        if (performance.now() - t0 > GIVE_UP_MS) setMissing(true);
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [s]);

  const showing = !s.target || rect !== null || missing;

  useLayoutEffect(() => {
    const el = card.current;
    if (!el) return;
    const next = { w: el.offsetWidth, h: el.offsetHeight };
    setSize((prev) => (prev.w === next.w && prev.h === next.h ? prev : next));
  }, [rect, missing, showing]);

  useEffect(() => { if (showing) primary.current?.focus({ preventScroll: true }); }, [showing, index]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") stop();
      else if (e.key === "ArrowRight") { if (next) go(index + 1); else stop(); }
      else if (e.key === "ArrowLeft") go(index - 1);
      else return;
      e.preventDefault();
      e.stopPropagation();
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [index, next, go, stop]);

  const first = index === 0, last = index === STEPS.length - 1;
  const width = Math.min(CARD_W, innerWidth - 2 * EDGE);
  const pos = placeCard(rect, size.w, size.h, Boolean(s.look));
  const counted = STEPS.length - 2; // the welcome and closing cards aren't numbered
  const vw = innerWidth, vh = innerHeight;

  return (
    <div className={`fixed inset-0 z-[1000] ${s.look ? "pointer-events-none" : ""}`}>
      {/* Four shaded panels around the spotlight, so only the element itself stays sharp. A clear blocker over the
          hole keeps clicks from leaving the tour; `look` steps drop both so the visitor can use the page. */}
      {!s.look && (rect ? (
        <>
          <div className="absolute" style={{ ...SHADE, transition: MOVE, top: 0, left: 0, width: vw, height: rect.top }} />
          <div className="absolute" style={{ ...SHADE, transition: MOVE, top: rect.top + rect.height, left: 0, width: vw, height: Math.max(0, vh - rect.top - rect.height) }} />
          <div className="absolute" style={{ ...SHADE, transition: MOVE, top: rect.top, left: 0, width: rect.left, height: rect.height }} />
          <div className="absolute" style={{ ...SHADE, transition: MOVE, top: rect.top, left: rect.left + rect.width, width: Math.max(0, vw - rect.left - rect.width), height: rect.height }} />
          <div className="absolute rounded-2xl" style={{ transition: MOVE, ...rect, boxShadow: "0 0 0 2px var(--accent), 0 0 0 7px rgba(217,30,42,0.22)" }} />
        </>
      ) : <div className="absolute inset-0" style={SHADE} />)}

      {showing && (
        <div ref={card} role="dialog" aria-modal={!s.look} aria-labelledby="tour-title" aria-describedby="tour-body"
          className="card pointer-events-auto absolute p-5"
          style={{ width, left: pos.left, top: pos.top, background: "#FFFFFF", transition: rect ? "top 220ms ease, left 220ms ease" : undefined }}>
          {first ? (
            <img src="/brand/silicon-labs.png" alt="Silicon Labs" className="mb-3 h-5 w-auto" />
          ) : (
            <div className="flex items-center justify-between text-[12px] text-ink-2">
              <span>{s.chapter}</span>
              {!last && <span className="tabular">{index} of {counted}</span>}
            </div>
          )}
          <h2 id="tour-title" className={`font-semibold leading-tight text-ink ${first ? "text-[20px]" : "mt-1 text-[15px]"}`}>{s.title}</h2>
          <p id="tour-body" className="mt-1.5 text-[13px] leading-relaxed text-ink-2">{s.body}</p>
          {missing && <p className="mt-1.5 text-[12px] text-ink-2">(It isn't on screen right now; it appears once there is data, or on a wider window.)</p>}
          {!first && !last && (
            <div className="mt-4 h-1 overflow-hidden rounded-full bg-idle-bg">
              <div className="h-1 rounded-full bg-accent transition-[width]" style={{ width: `${(index / counted) * 100}%` }} />
            </div>
          )}
          {first ? (
            <div className="mt-4 flex flex-col gap-2">
              <button ref={primary} type="button" onClick={() => go(1)}
                className="h-10 rounded-xl bg-accent px-4 text-[13px] font-medium text-white outline-none hover:brightness-95 focus-visible:ring-2 focus-visible:ring-accent/40 focus-visible:ring-offset-2">I'm new, show me around</button>
              <button type="button" onClick={stop}
                className="h-10 rounded-xl border border-[var(--card-border)] bg-white px-4 text-[13px] font-medium text-ink hover:bg-idle-bg">Skip, I'll explore on my own</button>
              <p className="mt-1 text-center text-[12px] text-ink-2">Use ← → to move through the tour and Esc to leave it.</p>
            </div>
          ) : (
            <div className="mt-4 flex items-center gap-2">
              {!last && <button type="button" onClick={stop} className="text-[13px] text-ink-2 hover:text-ink">Skip tour</button>}
              <div className="flex-1" />
              <button type="button" onClick={() => go(index - 1)}
                className="h-9 rounded-xl border border-[var(--card-border)] bg-white px-3.5 text-[13px] font-medium text-ink hover:bg-idle-bg">Back</button>
              <button ref={primary} type="button" onClick={() => (last ? stop() : go(index + 1))}
                className="h-9 rounded-xl bg-accent px-4 text-[13px] font-medium text-white outline-none hover:brightness-95 focus-visible:ring-2 focus-visible:ring-accent/40 focus-visible:ring-offset-2">
                {!next ? "Start exploring" : next === STEPS.at(-1) ? "Finish" : next.page !== s.page ? `Next: ${next.chapter}` : "Next"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
