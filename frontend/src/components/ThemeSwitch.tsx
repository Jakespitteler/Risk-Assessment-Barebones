import { useColourScheme } from "../theme/useColourScheme";

/**
 * The sun or moon button in the top bar, which switches between light and dark. It shows the
 * scheme it switches to: a moon on a light page, a sun on a dark one.
 */
export function ThemeSwitch() {
  const { showing, switchScheme } = useColourScheme();
  const switchingTo = showing === "dark" ? "light" : "dark";
  return (
    <button
      type="button"
      aria-label={`Switch to ${switchingTo}`}
      onClick={switchScheme}
      className="grid h-12 w-11 shrink-0 place-items-center rounded-lg text-ink hover:bg-surface-hover focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus"
    >
      {switchingTo === "dark" ? <MoonPicture /> : <SunPicture />}
    </button>
  );
}

const PICTURE_PROPS = {
  "aria-hidden": true,
  viewBox: "0 0 24 24",
  className: "size-7",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
} as const;

function MoonPicture() {
  return (
    <svg {...PICTURE_PROPS}>
      <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z" />
    </svg>
  );
}

function SunPicture() {
  return (
    <svg {...PICTURE_PROPS}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  );
}
