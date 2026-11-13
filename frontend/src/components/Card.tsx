import type { ReactNode } from "react";

/** A white panel that groups one part of a screen. */
export function Card({ children }: { children: ReactNode }) {
  return (
    <section className="flex flex-col gap-4 rounded-2xl border border-stone-300 bg-white p-4 [overflow-wrap:anywhere]">
      {children}
    </section>
  );
}
