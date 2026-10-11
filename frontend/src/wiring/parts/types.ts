import type { Wiring } from "../../contract";

export type PartDrawing = NonNullable<Wiring["parts"][number]["drawing"]>;
export type DrawingFeature = NonNullable<PartDrawing["features"]>[number];
export type Family = PartDrawing["family"];

/** What every family component draws: a box of w × h pixels at (0,0), `s` pixels per mm. */
export interface Spec {
  family: Family;
  variant?: string;
  label?: string;
  color?: string;
  w: number;
  h: number;
  s: number;
  pcb?: string;
}

/** Trailing count in a variant, "screw_3" -> 3. */
export const countOf = (variant: string | undefined, fallback: number): number => {
  const m = /_(\d+)$/.exec(variant ?? "");
  return m ? Number(m[1]) : fallback;
};
