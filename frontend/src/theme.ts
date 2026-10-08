// Design tokens from CLAUDE.md. CSS variables in index.css carry the same values for the HUD;
// the 3D scene reads them from here because three.js materials need plain colours.
export const color = {
  ground: "#EDEDED",
  road: "#DEDEDE",
  laneMark: "#FFFFFF",
  structure: "#D91E2A",
  structureDark: "#A8141F",
  card: "#FFFFFF",
  cardBorder: "#E6E6E6",
  ink: "#111111",
  ink2: "#6B6B6B",
  ok: "#16A34A",
  okBg: "#E8F7EE",
  info: "#111111",
  infoBg: "#EFEFEF",
  warn: "#D97706",
  warnBg: "#FFF4E0",
  crit: "#DC2626",
  critBg: "#FDECEC",
  idle: "#8C8C8C",
  idleBg: "#F2F2F2",
  accent: "#D91E2A", // Silicon Labs red: selection, map pins, routes, hover
  live: "#7C3AED", // reserved for real board/device data only
  marking: "#F2C230",
  box: "#D9B48A",
  boxDark: "#C79A6B",
  pallet: "#B98A5A",
  tree: "#6BBF8A",
} as const;

// Model colours derived from the palette (not separate design tokens).
export const model = {
  floor: "#F6F6F6",
  wallTop: "#E5545D",
  forkliftBody: color.marking,
  forkliftMast: color.ink,
  tyre: "#2B2B2B",
  metal: "#A0A0A0",
  cabGlass: "#D4D8DC",
  trailer: "#FFFFFF",
  trailerTrim: "#E6E6E6",
  door: "#EBEBEB",
  doorSlat: "#D6D6D6",
  skin: "#F0C7A0",
  hiVis: "#F97316",
  rackUpright: color.structureDark,
  rackBeam: color.warn,
  pole: "#BDBDBD",
  trunk: "#A07A55",
  fence: "#CCCCCC",
} as const;

export const font = {
  family: '"Inter", system-ui, sans-serif',
  size: { xs: 12, sm: 13, md: 15, lg: 20, xl: 28 },
} as const;

export const shadow = "0 8px 24px rgba(0,0,0,0.08)";
