/**
 * Light or dark: which one the screen shows, and the worker's own choice of it.
 *
 * The app follows the phone's light or dark setting. The switch in the top bar can override
 * that, but only until the phone's own setting next changes (spec F7, decision D66). So the
 * choice is kept with the phone's setting at the moment it was made: once the phone has
 * changed, the choice is stale and the phone wins again.
 *
 * The choice is kept on the phone, never sent to the server. `index.html` repeats
 * `schemeToShow` in a few lines that run before the app draws, so a dark phone never flashes a
 * white page; the two must read the same key and the same shape.
 */

export type ColourScheme = "light" | "dark";

/** The worker's choice from the switch, with the phone's setting when it was made. */
export type SchemeChoice = {
  readonly chosen: ColourScheme;
  readonly phoneWhenChosen: ColourScheme;
};

export const SCHEME_CHOICE_KEY = "take5-colour-scheme";

/** The colour of each page, for the phone browser's address bar. Matches `--color-page`. */
const ADDRESS_BAR_COLOURS: Record<ColourScheme, string> = {
  light: "#f5f5f4",
  dark: "#0f172b",
};

const PHONE_IS_DARK = "(prefers-color-scheme: dark)";

/** The scheme to show: the worker's choice while the phone hasn't changed, else the phone's. */
export function schemeToShow(
  phone: ColourScheme,
  choice: SchemeChoice | null,
): ColourScheme {
  return choice?.phoneWhenChosen === phone ? choice.chosen : phone;
}

/**
 * What pressing the switch saves: the other scheme, or no choice at all when the other scheme
 * is the phone's own, so the app simply follows the phone again.
 */
export function choiceAfterSwitch(
  phone: ColourScheme,
  showing: ColourScheme,
): SchemeChoice | null {
  const chosen: ColourScheme = showing === "dark" ? "light" : "dark";
  return chosen === phone ? null : { chosen, phoneWhenChosen: phone };
}

/** The phone's own light or dark setting. A browser that can't say counts as light. */
export function phoneScheme(): ColourScheme {
  return window.matchMedia(PHONE_IS_DARK).matches ? "dark" : "light";
}

/** Calls `onChange` whenever the phone's setting changes; returns how to stop. */
export function watchPhoneScheme(onChange: () => void): () => void {
  const query = window.matchMedia(PHONE_IS_DARK);
  query.addEventListener("change", onChange);
  return () => {
    query.removeEventListener("change", onChange);
  };
}

/** The saved choice, or null if there is none, it can't be read, or it isn't one. */
export function readChoice(): SchemeChoice | null {
  try {
    const stored: unknown = JSON.parse(
      localStorage.getItem(SCHEME_CHOICE_KEY) ?? "null",
    );
    return isSchemeChoice(stored) ? stored : null;
  } catch {
    return null;
  }
}

/**
 * The saved choice if the phone hasn't changed since it was made. A stale one, from a phone
 * that changed while the app was closed, is forgotten here.
 */
export function readFreshChoice(phone: ColourScheme): SchemeChoice | null {
  const choice = readChoice();
  if (choice === null || choice.phoneWhenChosen === phone) return choice;
  saveChoice(null);
  return null;
}

/** Saves the choice, or forgets it when given null. */
export function saveChoice(choice: SchemeChoice | null): void {
  try {
    if (choice === null) localStorage.removeItem(SCHEME_CHOICE_KEY);
    else localStorage.setItem(SCHEME_CHOICE_KEY, JSON.stringify(choice));
  } catch {
    /* Storage is switched off: the switch still works until the page reloads. */
  }
}

/** Draws the page in the scheme, and tells the browser so its own parts match. */
export function showScheme(scheme: ColourScheme): void {
  const page = document.documentElement;
  page.dataset.theme = scheme;
  page.style.colorScheme = scheme;
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", ADDRESS_BAR_COLOURS[scheme]);
}

function isColourScheme(value: unknown): value is ColourScheme {
  return value === "light" || value === "dark";
}

function isSchemeChoice(value: unknown): value is SchemeChoice {
  if (typeof value !== "object" || value === null) return false;
  const { chosen, phoneWhenChosen } = value as Record<string, unknown>;
  return isColourScheme(chosen) && isColourScheme(phoneWhenChosen);
}
