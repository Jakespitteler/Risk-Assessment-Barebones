import type { ReactNode } from "react";

/**
 * Something the worker is allowed to do but should know about before going on, such
 * as a hazard with no controls. Amber, so it reads apart from an error in bright sun.
 */
export function Warning({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border-2 border-caution-line bg-caution-soft p-4 font-semibold text-on-caution-soft">
      {children}
    </div>
  );
}
