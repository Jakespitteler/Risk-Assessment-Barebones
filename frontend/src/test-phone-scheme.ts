import type { ColourScheme } from "./theme/colourScheme";

/**
 * A stand-in for the phone's light or dark setting. Vitest's pretend browser (jsdom) has no
 * `window.matchMedia`, which is how the app reads it. Every test starts on a light phone.
 */
let phone: ColourScheme = "light";
const listeners = new Set<() => void>();

/** Sets the pretend phone to light or dark, telling the app as a real phone would. */
export function setPhoneScheme(scheme: ColourScheme): void {
  phone = scheme;
  listeners.forEach((listener) => {
    listener();
  });
}

/** Puts back a light phone with nobody listening. */
export function resetPhoneScheme(): void {
  phone = "light";
  listeners.clear();
}

/** Answers only the one question the app asks: is the phone set to dark? */
export function fakeMatchMedia(query: string): MediaQueryList {
  return {
    media: query,
    get matches() {
      return query === "(prefers-color-scheme: dark)" && phone === "dark";
    },
    addEventListener: (_type: string, listener: () => void) => {
      listeners.add(listener);
    },
    removeEventListener: (_type: string, listener: () => void) => {
      listeners.delete(listener);
    },
  } as unknown as MediaQueryList;
}
