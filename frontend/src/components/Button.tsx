import type { ButtonHTMLAttributes } from "react";

// Every button is at least 56 px high: big enough for a gloved thumb.
const VARIANTS = {
  primary:
    "min-h-14 rounded-xl bg-action px-5 text-lg font-bold text-on-action hover:bg-action-hover",
  secondary:
    "min-h-14 rounded-xl border-2 border-ink bg-surface px-5 text-lg font-bold text-ink hover:bg-surface-hover",
  quiet:
    "min-h-12 self-start rounded-lg px-2 text-base font-semibold text-ink underline underline-offset-4 hover:decoration-2 hover:bg-surface-hover",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof VARIANTS;
};

/** A button in one of the app's three styles. */
export function Button({
  variant = "primary",
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`${VARIANTS[variant]} focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:cursor-wait disabled:opacity-60 ${className}`}
      {...props}
    />
  );
}
