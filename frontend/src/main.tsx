import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { HostedBanner } from "./hud/HostedBanner";
import { Tour } from "./tour/Tour";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
    <HostedBanner />
    <Tour />
  </StrictMode>,
);
