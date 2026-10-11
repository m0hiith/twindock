// Colours of real materials seen from above. Part artwork uses these, never the UI theme, so a
// green PCB looks green and gold pads look gold. (Wires have their own table in ../model.ts.)
export const PCB_MASK = {
  green: { base: "#1F6B3A", dark: "#14502A", light: "#2A8049" },
  blue: { base: "#1F4E96", dark: "#163A72", light: "#2D63B3" },
  black: { base: "#1C1C1E", dark: "#0E0E10", light: "#2C2C30" },
  red: { base: "#B3202A", dark: "#85161E", light: "#CC3039" },
  white: { base: "#E6E6E2", dark: "#C7C7C2", light: "#F4F4F1" },
  yellow: { base: "#D2A92A", dark: "#A98414", light: "#E6C04C" },
  none: { base: "#00000000", dark: "#00000000", light: "#00000000" },
} as const;
export type PcbColor = keyof typeof PCB_MASK;

export const GOLD = "#D8B45A";
export const GOLD_DARK = "#9C7A35";
export const TIN = "#C9CDD2";
export const TIN_DARK = "#8E949B";
export const PLASTIC_BLACK = "#1A1A1C";
export const SILK = "#F2F2EE";
export const CREAM = "#EDE4CC";
export const CREAM_DARK = "#B9AD8A";

/** Pixels per millimetre of the breadboard view. */
export const PX_PER_MM = 10;
