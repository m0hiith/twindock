import { useEffect, useState, useSyncExternalStore } from "react";
import { fetchLayout } from "./layout";
import { ControlPage } from "./pages/ControlPage";
import { DevicePage } from "./pages/DevicePage";
import { FleetPage } from "./pages/FleetPage";
import { RulesPage } from "./pages/RulesPage";
import { TwinPage } from "./pages/TwinPage";
import { PartsGallery } from "./pages/PartsGallery";
import { MonitorPage } from "./pages/MonitorPage";
import { MePage } from "./pages/MePage";
import { KitsPage } from "./pages/KitsPage";
import { WiringPage } from "./pages/WiringPage";
import { connect } from "./store/ws";
import { useWorld } from "./store/world";

const subscribePath = (cb: () => void) => { addEventListener("popstate", cb); return () => removeEventListener("popstate", cb); };

export default function App() {
  const path = useSyncExternalStore(subscribePath, () => location.pathname);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    fetchLayout()
      .then((l) => {
        useWorld.getState().setLayout(l);
        connect();
      })
      .catch((e: unknown) => setError(String(e)));
  }, []);
  if (error) {
    return (
      <div className="grid h-full place-items-center">
        <div className="card max-w-md p-5">
          <div className="text-[15px] font-semibold">Can't reach the backend</div>
          <div className="mt-1 text-ink-2">{error}. Start it with ./scripts/run_backend.sh and reload.</div>
        </div>
      </div>
    );
  }
  // A handful of routes, so plain pathname matching is enough; "/" shows the twin.
  if (path.startsWith("/control")) return <ControlPage />;
  if (path.startsWith("/device")) return <DevicePage />;
  if (path.startsWith("/fleet")) return <FleetPage />;
  if (path.startsWith("/rules")) return <RulesPage />;
  if (path.startsWith("/wiring")) return <WiringPage />;
  if (path.startsWith("/kits")) return <KitsPage />;
  if (path.startsWith("/monitor")) return <MonitorPage />;
  if (path.startsWith("/me")) return <MePage />;
  if (path.startsWith("/parts")) return <PartsGallery />;
  if (path !== "/twin") history.replaceState(null, "", "/twin" + location.search);
  return <TwinPage />;
}
