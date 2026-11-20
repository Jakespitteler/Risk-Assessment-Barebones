import type { ReactNode } from "react";

/** Help that stays folded away until the worker opens it, so their answer stays in view. */
export function Guidance({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <details className="rounded-xl border border-line bg-surface-subtle">
      <summary className="flex min-h-12 cursor-pointer items-center rounded-xl px-4 font-semibold underline underline-offset-4 hover:decoration-2 hover:bg-surface-hover focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus">
        {title}
      </summary>
      <div className="flex flex-col gap-3 px-4 pb-4">{children}</div>
    </details>
  );
}
