// Silicon Labs logo + product name. The logo is a 437×48 PNG whose swirl mark spans the left 133 px;
// `compact` crops to that mark so phone headers keep room for their controls.
// `tight` keeps only the mark below 1800 px, where the twin's top bar runs out of room.
export function Brand({ compact = false, tight = false, title = "TwinDock" }: { compact?: boolean; tight?: boolean; title?: string }) {
  const crop = compact ? "block h-5 w-[55px] overflow-hidden sm:w-auto" : tight ? "block h-5 w-[55px] overflow-hidden min-[1800px]:w-auto" : "block h-5";
  return (
    <div className="flex shrink-0 items-center gap-2.5">
      <span className={crop}>
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
