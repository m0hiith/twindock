// Tabs between the app's pages, shown in every page header. Navigation is client-side
// (history.pushState) so the WebSocket and world state stay up when switching pages.
export const PAGES = [
  { path: "/twin", label: "Twin" },
  { path: "/monitor", label: "Monitor" },
  { path: "/energy", label: "Energy" },
  { path: "/control", label: "Control" },
  { path: "/fleet", label: "Fleet" },
  { path: "/rules", label: "Rules" },
  { path: "/device", label: "Device" },
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
    </nav>
  );
}
