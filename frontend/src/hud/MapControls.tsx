import { useView, useWorld, ZOOM_MAX, ZOOM_MIN } from "../store/world";
import { CameraMenu } from "./CameraMenu";

function Btn({ label, onClick, disabled, children }: { label: string; onClick: () => void; disabled?: boolean; children: React.ReactNode }) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick} disabled={disabled}
      className="grid h-9 w-9 place-items-center text-ink transition-colors hover:bg-info-bg hover:text-info disabled:opacity-35 disabled:hover:bg-transparent">
      {children}
    </button>
  );
}

const icon = { width: 18, height: 18, fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

export function MapControls() {
  const zoom = useView((s) => s.zoom);
  const showDevices = useView((s) => s.showDevices);
  const cutaway = useView((s) => s.cutaway);
  const { zoomBy, rotate, home } = useView.getState();
  const focusSelected = () => {
    const { selected, units } = useWorld.getState();
    const u = selected ? units[selected] : undefined;
    if (u) useView.getState().focusOn(u.x, u.z);
    else home();
  };
  return (
    <div data-tour="map-controls" className="card flex flex-col overflow-hidden !rounded-xl divide-y divide-[var(--card-border)]">
      <Btn label="Zoom in" onClick={() => zoomBy(1.25)} disabled={zoom >= ZOOM_MAX - 1e-6}>
        <svg viewBox="0 0 24 24" {...icon}><path d="M12 5v14M5 12h14" /></svg>
      </Btn>
      <Btn label="Zoom out" onClick={() => zoomBy(0.8)} disabled={zoom <= ZOOM_MIN + 1e-6}>
        <svg viewBox="0 0 24 24" {...icon}><path d="M5 12h14" /></svg>
      </Btn>
      <Btn label="Rotate left" onClick={() => rotate(-1)}>
        <svg viewBox="0 0 24 24" {...icon}><path d="M4 12a8 8 0 1 0 2.4-5.7" /><path d="M4 4v4h4" /></svg>
      </Btn>
      <Btn label="Rotate right" onClick={() => rotate(1)}>
        <svg viewBox="0 0 24 24" {...icon}><path d="M20 12a8 8 0 1 1-2.4-5.7" /><path d="M20 4v4h-4" /></svg>
      </Btn>
      <CameraMenu />
      <Btn label="Center on selection" onClick={focusSelected}>
        <svg viewBox="0 0 24 24" {...icon}><path d="M4 11 12 4l8 7v8a1 1 0 0 1-1 1h-4v-6h-6v6H5a1 1 0 0 1-1-1z" /></svg>
      </Btn>
      <button type="button" aria-label="Interiors" title={cutaway ? "Close the roofs" : "Show interiors (roofs off)"} aria-pressed={cutaway}
        onClick={() => useView.getState().setCutaway(!cutaway)}
        className={`grid h-9 w-9 place-items-center transition-colors ${cutaway ? "bg-[var(--accent)] text-white" : "text-ink hover:bg-info-bg"}`}>
        <svg viewBox="0 0 24 24" {...icon}><path d="M3 10 12 4l9 6M5 10v9h14v-9M9 19v-5h6v5" /></svg>
      </button>
      <button type="button" aria-label="Devices" title={showDevices ? "Hide devices" : "Show devices"} aria-pressed={showDevices}
        onClick={() => useView.getState().setShowDevices(!showDevices)}
        className={`grid h-9 w-9 place-items-center transition-colors ${showDevices ? "bg-[var(--accent)] text-white" : "text-ink hover:bg-info-bg"}`}>
        <svg viewBox="0 0 24 24" {...icon}><path d="M12 13a1 1 0 1 0 0-.01M8.5 9.5a5 5 0 0 0 0 7M15.5 9.5a5 5 0 0 1 0 7M6 7a8.5 8.5 0 0 0 0 12M18 7a8.5 8.5 0 0 1 0 12" /></svg>
      </button>
    </div>
  );
}
