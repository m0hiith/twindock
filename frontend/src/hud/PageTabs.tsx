// Tabs between the app's pages, shown in every page header. Navigation is client-side
// (history.pushState) so the WebSocket and world state stay up when switching pages.
import { useTour } from "../tour/store";

export const PAGES = [
  { path: "/twin", label: "Twin" },
  { path: "/monitor", label: "Monitor" },
  { path: "/energy", label: "Energy" },
  { path: "/control", label: "Control" },
  { path: "/fleet", label: "Fleet" },
  { path: "/rules", label: "Rules" },
  { path: "/kits", label: "Kits" },
  { path: "/wiring", label: "Wiring" },
  { path: "/model", label: "Model" },
] as const;

export function navigate(path: string): void {
  if (location.pathname === path) return;
  history.pushState(null, "", path);
  dispatchEvent(new PopStateEvent("popstate"));
}

export function PageTabs({ className = "" }: { className?: string }) {
  const here = location.pathname;
  return (
    <nav aria-label="Pages" className={`flex min-w-0 items-center gap-0.5 overflow-x-auto rounded-xl bg-idle-bg p-1 [scrollbar-width:none] ${className}`}>
      {PAGES.map((p) => {
        const active = here.startsWith(p.path);
        return (
          <a key={p.path} href={p.path} aria-current={active ? "page" : undefined}
            onClick={(e) => {
              if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return; // let "open in new tab" work
              e.preventDefault();
              navigate(p.path);
            }}
            className={`flex h-7 shrink-0 items-center whitespace-nowrap rounded-lg px-2.5 text-[13px] min-[1800px]:px-3 font-medium transition-colors ${active ? "bg-white text-ink shadow-[0_1px_2px_rgba(0,0,0,0.08)]" : "text-ink-2 hover:text-ink"}`}>
            {p.label}
          </a>
        );
      })}
      <button type="button" onClick={() => useTour.getState().start()} title="A guided tour of every page"
        className="flex h-7 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-lg px-2.5 text-[13px] font-medium text-accent transition-colors hover:bg-white">
        <svg viewBox="0 0 24 24" width={14} height={14} fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <circle cx="12" cy="12" r="9" /><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .8-1 1.5v.2M12 17h.01" />
        </svg>
        Tour
      </button>
    </nav>
  );
}
