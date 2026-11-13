import type { ReactNode } from "react";

/** A message the worker must see, such as a failed save. Screen readers announce it. */
export function Notice({ children }: { children: ReactNode }) {
  return (
    <div
      role="alert"
      className="flex flex-col gap-2 rounded-xl border-2 border-red-800 bg-red-50 p-4 font-semibold text-red-900"
    >
      {children}
    </div>
  );
}
