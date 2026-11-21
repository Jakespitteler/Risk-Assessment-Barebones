import type { ReactNode } from "react";
import { ThemeSwitch } from "./ThemeSwitch";

/**
 * The page every screen sits on, with the app's name at the top. The "5" links to the start
 * page, where a new Take 5 begins or the kept draft carries on. `aside` goes at the right
 * of the top bar, for a link away from the screen, beside the light or dark switch.
 */
export function Screen({
  subtitle,
  aside,
  wide = false,
  children,
}: {
  subtitle: string;
  aside?: ReactNode;
  /** True for a screen with two columns on a desktop, such as a photo beside a form. */
  wide?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="min-h-dvh bg-page text-base text-ink">
      <main
        className={`mx-auto flex w-full flex-col gap-6 px-4 py-6 ${wide ? "max-w-6xl" : "max-w-2xl"}`}
      >
        <header className="flex items-center gap-3">
          <a
            href="/"
            aria-label="Take 5 home"
            className="grid size-12 shrink-0 place-items-center rounded-xl bg-brand text-3xl font-black text-on-brand hover:bg-brand-hover focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus"
          >
            5
          </a>
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
