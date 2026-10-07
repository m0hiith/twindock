import { useView, useWorld, ZOOM_MAX, ZOOM_MIN } from "../store/world";

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
  const { zoomBy, rotate, home } = useView.getState();
  const focusSelected = () => {
    const { selected, units } = useWorld.getState();
    const u = selected ? units[selected] : undefined;
    if (u) useView.getState().focusOn(u.x, u.z);
    else home();
  };
  return (
    <div className="card flex flex-col overflow-hidden !rounded-xl divide-y divide-[var(--card-border)]">
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
      <Btn label="Center on selection" onClick={focusSelected}>
        <svg viewBox="0 0 24 24" {...icon}><path d="M4 11 12 4l8 7v8a1 1 0 0 1-1 1h-4v-6h-6v6H5a1 1 0 0 1-1-1z" /></svg>
      </Btn>
    </div>
  );
}
