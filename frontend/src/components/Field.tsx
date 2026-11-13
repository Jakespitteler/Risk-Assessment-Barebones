import type { ReactNode } from "react";

/** A labelled field, with the back end's error for it shown underneath. */
export function Field({
  name,
  label,
  error,
  children,
}: {
  name: string;
  label: string;
  error?: string | undefined;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={name} className="text-lg font-bold">
        {label}
      </label>
      {children}
      {error && (
        <p id={`${name}-error`} className="font-semibold text-red-800">
          {error}
        </p>
      )}
    </div>
  );
}
