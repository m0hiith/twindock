// The guided tour, page by page. Each step spotlights one element (a CSS selector, usually a data-tour attribute) and
// explains it in a sentence or two. Steps without a target show a centred card; `look` steps leave the page visible
// and usable so the visitor can try the 3D scene.
import { send } from "../store/ws";
import { useView, useWorld } from "../store/world";

export type TourStep = {
  chapter: string;
  title: string;
  body: string;
  /** Path to show for this step; the tour navigates there first. */
  page?: string;
  target?: string;
  look?: boolean;
  enter?: () => void;
};

const WAREHOUSE = "WH-01";

function showWarehouse(): void {
  if (useView.getState().site !== WAREHOUSE) useView.getState().setSite(WAREHOUSE);
}

/** Selects a forklift so the inspect card and the Control Room have something to show. Keeps the current one. */
function selectForklift(): void {
  const { units, selected } = useWorld.getState();
  if (selected && units[selected]?.kind === "forklift") return;
  const fl = Object.values(units).filter((u) => u.kind === "forklift").sort((a, b) => a.id.localeCompare(b.id))[0];
  if (fl) send({ type: "select_unit", unit_id: fl.id });
}

function clearSelection(): void {
  if (useWorld.getState().selected) send({ type: "select_unit", unit_id: null });
}

export const STEPS: TourStep[] = [
  {
    chapter: "Welcome",
    title: "Welcome to TwinDock",
    body: "A live digital twin of Riverside, a warehouse and factory campus. A real Silicon Labs SiWx917 board feeds it over Wi-Fi and MQTT; everything else comes from a simulator, and every value says which one it is. The tour takes about two minutes.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[aria-label="Pages"]', enter: showWarehouse,
    title: "Pages",
    body: "Each tab is a different view of the same live world: the 3D twin, a wall-display monitor, energy, the operator's control room, the device fleet, alert rules, hardware kits, wiring, and how the simulation works.",
  },
  {
    chapter: "3D twin", page: "/twin", look: true,
    title: "The 3D world",
    body: "Forklifts, trucks, workers and machines move only when the server says so. Drag to pan, scroll to zoom, and click any vehicle, building or device to inspect it. Try it now.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[data-tour="kpis"]',
    title: "Live KPIs",
    body: "Stock on hand, trucks on site and on-time dispatch, calculated from the server's world state as it changes. The small pill shows the change since the session started.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[data-tour="map-controls"]',
    title: "Map controls",
    body: "Zoom, rotate in 90° steps, jump to preset camera views, centre on the selection, take the roofs off to look inside, and show every sensor on the map.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[data-tour="alerts"]',
    title: "Open alerts",
    body: "Raised by the rules engine, most severe first. Click one and the camera flies to where it happened. Acknowledging an alert here shows on every open screen.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[aria-label="Mini-map"]',
    title: "Mini-map",
    body: "The whole campus from above, with the area you are looking at. Click or drag on it to jump there.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[data-tour="fleet-table"]',
    title: "Docks, forklifts and trucks",
    body: "Every unit with its job, status and progress. Click a row to select it. The selection is shared, so every open screen follows it.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[data-tour="shipments"]',
    title: "Shipment tracking",
    body: "Follows one truck from arrival through docking and loading to departure. The arrows step through the trucks on site.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[data-tour="inspect"]', enter: selectForklift,
    title: "Inspect card",
    body: "We selected a forklift for you. Its card shows the task, battery and details, and the red brackets mark it in the scene. \"Open in Control Room\" lets you drive it.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[data-tour="site"]', enter: clearSelection,
    title: "Sites",
    body: "Switch between WH-01, the warehouse, and FAC-01, the factory next door with two production lines, machine monitoring and worker safety.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[data-tour="search"]',
    title: "Search",
    body: "Find any building, device, vehicle, worker or alert. Press / from anywhere, pick a result, and the camera flies to it.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[data-tour="auto"]',
    title: "Auto mode",
    body: "Off by default. Turn it on and the warehouse runs itself: the server creates jobs, sends forklifts and docks trucks.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[data-tour="live"]',
    title: "Live clock and speed",
    body: "Green means connected to the server. The time is the simulation clock, and ×5 or ×20 speeds it up. Speed stays at ×1 while the real board is online, so its data stays real time.",
  },
  {
    chapter: "3D twin", page: "/twin", target: '[data-tour="notifications"]',
    title: "Event log",
    body: "Every notable event: board button presses, auto mode, LED timeouts and dropped device messages. The badge counts new warnings.",
  },
  {
    chapter: "Control Room", page: "/control", target: '[data-tour="control-map"]', enter: selectForklift,
    title: "Control Room",
    body: "The operator's page, built for a phone. With a forklift selected, the server checks every place it can go. Tap one to see the planned route, then confirm. The move shows up in the 3D twin on every screen.",
  },
  {
    chapter: "Control Room", page: "/control", target: '[data-tour="unit-chips"]',
    title: "Pick a unit",
    body: "Choose the forklift or truck you want to control.",
  },
  {
    chapter: "Control Room", page: "/control", target: '[data-tour="control-tabs"]',
    title: "Control tabs",
    body: "Move units, see the real board on the Gateway tab, run the factory and approve maintenance recommendations. Anything that stops production waits for a person. There are also logistics, scripted demo scenarios such as a grid failure, alerts and the event log.",
  },
  {
    chapter: "Control Room", page: "/control", target: '[data-tour="reset"]', enter: clearSelection,
    title: "Reset world",
    body: "Puts the world back to where it started, for everyone, if a demo leaves things messy.",
  },
  {
    chapter: "Monitor", page: "/monitor", target: '[aria-label="Campus map"]',
    title: "Monitoring centre",
    body: "Built for a wall display in a control room. Pulsing rings on the campus mark open alerts. Click any unit, worker or device to inspect it.",
  },
  {
    chapter: "Monitor", page: "/monitor", target: '[aria-label="Alerts"]',
    title: "Alerts and incidents",
    body: "Open alerts, the incident timeline and PDF shift reports. Worker safety and evacuation are below.",
  },
  {
    chapter: "Monitor", page: "/monitor", target: '[aria-label="Campus status"]',
    title: "Campus status",
    body: "Production, logistics, energy, environment, device health and the real board. Each tile is marked LIVE (real board) or SIM (simulated).",
  },
  {
    chapter: "Energy", page: "/energy", target: '[data-tour="energy-cards"]',
    title: "Energy",
    body: "Where the campus's power comes from and where it goes: demand, rooftop solar, grid import, the backup generator and today's cost on a time-of-day tariff. All from simulated meters, and labelled that way.",
  },
  {
    chapter: "Fleet", page: "/fleet", target: '[data-tour="fleet-devices"]',
    title: "Device fleet",
    body: "Every device on the campus with protocol, battery, signal, firmware and when it was last heard from. GW-01 is the real SiWx917 board (violet LIVE badge); everything else is simulated (grey SIM). Click a row to see its history.",
  },
  {
    chapter: "Rules", page: "/rules", target: '[aria-label="Rules"]',
    title: "Alert rules",
    body: "Every rule in plain language. A rule fires only when its condition holds for its whole duration, and never on values that did not arrive.",
  },
  {
    chapter: "Kits", page: "/kits", target: '[data-tour="kits"]',
    title: "Device kits",
    body: "One sensor pack for each kind of asset, built from real, buyable Silicon Labs radios and parts, with a bill of materials. The forklift pack is built on the real board; the others are simulated designs.",
  },
  {
    chapter: "Wiring", page: "/wiring/fl01_sensor_pack", target: '[data-tour="wiring-views"]',
    title: "Wiring",
    body: "How a kit is wired, as a breadboard drawing, a schematic or a parts list. Click any part to see what it does and its latest reading, and export the drawing as PNG or PDF.",
  },
  {
    chapter: "Model", page: "/model", target: '[data-tour="model-intro"]',
    title: "How the simulation works",
    body: "Every model, equation, parameter and simulated sensor, with the source of each number and a validation run.",
  },
  {
    chapter: "Done", page: "/twin", enter: showWarehouse,
    title: "You're all set",
    body: "That's TwinDock. To replay this tour, click Tour in the page tabs.",
  },
];
