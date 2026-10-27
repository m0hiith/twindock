// Which tour step is showing (null: no tour). Kept apart from the overlay so the page tabs can start the tour
// without importing it.
import { create } from "zustand";
import { STEPS } from "./steps";

const SEEN_KEY = "twindock.tour.seen";

export function tourSeen(): boolean {
  try { return localStorage.getItem(SEEN_KEY) === "1"; } catch { return false; }
}

function markSeen(): void {
  try { localStorage.setItem(SEEN_KEY, "1"); } catch { /* private window: the tour just offers itself again next visit */ }
}

type TourState = {
  step: number | null;
  start: () => void;
  go: (i: number) => void;
  stop: () => void;
};

export const useTour = create<TourState>((set) => ({
  step: null,
  start: () => set({ step: 0 }),
  go: (i) => set({ step: Math.max(0, Math.min(STEPS.length - 1, i)) }),
  stop: () => { markSeen(); set({ step: null }); },
}));
