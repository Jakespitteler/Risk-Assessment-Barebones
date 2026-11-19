import type { ReactNode } from "react";
import { ThemeSwitch } from "./ThemeSwitch";

/**
 * The page every screen sits on, with the app's name at the top. `aside` goes at the
 * right of the top bar, for a link away from the screen, beside the light or dark switch.
 */
export function Screen({
  subtitle,
  aside,
  children,
}: {
  subtitle: string;
  aside?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="min-h-dvh bg-page text-base text-ink">
      <main className="mx-auto flex w-full max-w-2xl flex-col gap-6 px-4 py-6">
        <header className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className="grid size-12 shrink-0 place-items-center rounded-xl bg-brand text-3xl font-black text-on-brand"
          >
            5
          </span>
          <p className="flex flex-col">
            <span className="text-sm font-bold tracking-wide text-ink-muted uppercase">
              Take 5
            </span>
            <span className="font-semibold text-balance">{subtitle}</span>
          </p>
          <div className="-mr-2 ml-auto flex shrink-0 items-center">
            {aside}
            <ThemeSwitch />
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
