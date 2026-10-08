// Stand-in for /control until the Control Room is built (PROMPTS.md, prompt 6).
export function ControlPlaceholder() {
  return (
    <div className="grid h-full place-items-center p-4">
      <div className="card max-w-sm p-5">
        <div className="text-[15px] font-semibold">Control Room</div>
        <div className="mt-1 text-ink-2">Not built yet. <a className="text-info underline" href="/twin">Back to the twin</a></div>
      </div>
    </div>
  );
}
