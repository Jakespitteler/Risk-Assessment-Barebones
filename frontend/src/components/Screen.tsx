import type { ReactNode } from "react";

/** The page every screen sits on, with the app's name at the top. */
export function Screen({
  subtitle,
  children,
}: {
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="min-h-dvh bg-stone-100 text-base text-slate-900">
      <main className="mx-auto flex w-full max-w-2xl flex-col gap-6 px-4 py-6">
        <header className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className="grid size-12 shrink-0 place-items-center rounded-xl bg-amber-400 text-3xl font-black"
          >
            5
          </span>
          <p className="flex flex-col">
            <span className="text-sm font-bold tracking-wide text-slate-700 uppercase">
              Take 5
            </span>
            <span className="font-semibold">{subtitle}</span>
          </p>
        </header>
        {children}
      </main>
    </div>
  );
}
