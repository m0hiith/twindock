import { useEffect, useState } from "react";
import { fetchLayout } from "./layout";
import { TwinPage } from "./pages/TwinPage";
import { connect } from "./store/ws";
import { useWorld } from "./store/world";

export default function App() {
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
  return <TwinPage />;
}
