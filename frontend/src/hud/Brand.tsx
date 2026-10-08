// Silicon Labs logo + product name. The logo is a 437×48 PNG whose swirl mark spans the left 133 px;
// `compact` crops to that mark so phone headers keep room for their controls.
export function Brand({ compact = false, title = "TwinDock" }: { compact?: boolean; title?: string }) {
  return (
    <div className="flex shrink-0 items-center gap-2.5">
      <span className={compact ? "block h-5 w-[55px] overflow-hidden sm:w-auto" : "block h-5"}>
        <img src="/brand/silicon-labs.png" alt="Silicon Labs" className="h-5 w-auto max-w-none" />
      </span>
      {title && (
        <>
          <span className="h-5 w-px bg-[var(--card-border)]" aria-hidden />
          <span className="text-[17px] font-semibold tracking-tight">{title}</span>
        </>
      )}
    </div>
  );
}
