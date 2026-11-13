import type { ReactNode } from "react";

/** Keep a server-provided error beside the field and connected to assistive technology. */
export function Field({
  name,
  label,
  error,
  children,
}: {
  name: string;
  label: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      {children}
      {error && (
        <p className="field-error" id={`${name}-error`}>
          {error}
        </p>
      )}
    </div>
  );
}

/** Expandable supporting text leaves the worker's own answers in focus. */
export function Guidance({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <details className="guidance">
      <summary>{title}</summary>
      <div>{children}</div>
    </details>
  );
}
