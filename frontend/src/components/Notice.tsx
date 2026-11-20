import type { ReactNode } from "react";

/** A message the worker must see, such as a failed save. Screen readers announce it. */
export function Notice({ children }: { children: ReactNode }) {
  return (
    <div
      role="alert"
      className="flex flex-col gap-2 rounded-xl border-2 border-danger bg-danger-soft p-4 font-semibold text-on-danger-soft"
    >
      {children}
    </div>
  );
}
