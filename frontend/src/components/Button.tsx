import type { ButtonHTMLAttributes } from "react";

// Every button is at least 56 px high: big enough for a gloved thumb.
const VARIANTS = {
  primary:
    "min-h-14 rounded-xl bg-slate-900 px-5 text-lg font-bold text-white hover:bg-slate-700",
  secondary:
    "min-h-14 rounded-xl border-2 border-slate-900 bg-white px-5 text-lg font-bold text-slate-900 hover:bg-stone-100",
  quiet:
    "min-h-12 self-start rounded-lg px-2 text-base font-semibold text-slate-900 underline underline-offset-4",
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
      className={`${VARIANTS[variant]} focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-wait disabled:opacity-60 ${className}`}
      {...props}
    />
  );
}
