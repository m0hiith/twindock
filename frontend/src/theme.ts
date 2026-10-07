// Design tokens from CLAUDE.md. CSS variables in index.css carry the same values for the HUD;
// the 3D scene reads them from here because three.js materials need plain colours.
export const color = {
  ground: "#E9EDF6",
  road: "#DCE2EE",
  laneMark: "#FFFFFF",
  structure: "#2F5FE0",
  structureDark: "#2349B8",
  card: "#FFFFFF",
  cardBorder: "#E6E9F0",
  ink: "#1B2333",
  ink2: "#6B7385",
  ok: "#16A34A",
  okBg: "#E8F7EE",
  info: "#2F5FE0",
  infoBg: "#EAF0FF",
  warn: "#D97706",
  warnBg: "#FFF4E0",
  crit: "#DC2626",
  critBg: "#FDECEC",
  idle: "#8A93A6",
  idleBg: "#F1F3F7",
  live: "#7C3AED", // reserved for real board/device data only
  marking: "#F2C230",
  box: "#D9B48A",
  boxDark: "#C79A6B",
  pallet: "#B98A5A",
  tree: "#6BBF8A",
} as const;

// Model colours derived from the palette (not separate design tokens).
export const model = {
  floor: "#F5F7FC",
  wallTop: "#5A80EA",
  forkliftBody: color.marking,
  forkliftMast: color.structure,
  tyre: "#2B3242",
  metal: "#9AA3B5",
  cabGlass: "#BFD3FF",
  trailer: "#FFFFFF",
  trailerTrim: "#E3E8F2",
  door: "#E9EDF5",
  doorSlat: "#D3DAE7",
  skin: "#F0C7A0",
  hiVis: "#F97316",
  rackUpright: color.structureDark,
  rackBeam: color.warn,
  pole: "#B7BFCE",
  trunk: "#A07A55",
  fence: "#C9D0DD",
} as const;

export const font = {
  family: '"Inter", system-ui, sans-serif',
  size: { xs: 12, sm: 13, md: 15, lg: 20, xl: 28 },
} as const;

export const shadow = "0 8px 24px rgba(30,45,90,0.08)";
