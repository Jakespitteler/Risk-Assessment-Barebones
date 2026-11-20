import { afterEach, expect, it } from "vitest";
import {
  choiceAfterSwitch,
  readChoice,
  readFreshChoice,
  saveChoice,
  SCHEME_CHOICE_KEY,
  schemeToShow,
  showScheme,
} from "./colourScheme";

afterEach(() => {
  localStorage.clear();
});

it("follows the phone when the worker hasn't chosen", () => {
  expect(schemeToShow("dark", null)).toBe("dark");
  expect(schemeToShow("light", null)).toBe("light");
});

it("shows the worker's choice while the phone hasn't changed since", () => {
  expect(
    schemeToShow("dark", { chosen: "light", phoneWhenChosen: "dark" }),
  ).toBe("light");
});

it("follows the phone again once the phone has changed since the choice", () => {
  expect(
    schemeToShow("light", { chosen: "light", phoneWhenChosen: "dark" }),
  ).toBe("light");
  expect(
    schemeToShow("dark", { chosen: "dark", phoneWhenChosen: "light" }),
  ).toBe("dark");
});

it("saves the other scheme with the phone's setting when the switch is pressed", () => {
  expect(choiceAfterSwitch("dark", "dark")).toEqual({
    chosen: "light",
    phoneWhenChosen: "dark",
  });
});

it("saves no choice when the switch goes back to the phone's own scheme", () => {
  expect(choiceAfterSwitch("dark", "light")).toBeNull();
});

it("reads back a saved choice", () => {
  saveChoice({ chosen: "dark", phoneWhenChosen: "light" });
  expect(readChoice()).toEqual({ chosen: "dark", phoneWhenChosen: "light" });
  saveChoice(null);
  expect(readChoice()).toBeNull();
});

it("forgets a choice made before the phone last changed", () => {
  saveChoice({ chosen: "light", phoneWhenChosen: "dark" });
  expect(readFreshChoice("dark")).toEqual({
    chosen: "light",
    phoneWhenChosen: "dark",
  });
  expect(readFreshChoice("light")).toBeNull();
  expect(readChoice()).toBeNull();
});

it("ignores a saved choice that isn't one", () => {
  localStorage.setItem(SCHEME_CHOICE_KEY, '{"chosen":"purple"}');
  expect(readChoice()).toBeNull();
  localStorage.setItem(SCHEME_CHOICE_KEY, "not json");
  expect(readChoice()).toBeNull();
});

it("marks the page with the scheme, for the colours and the browser's own parts", () => {
  showScheme("dark");
  expect(document.documentElement.dataset.theme).toBe("dark");
  expect(document.documentElement.style.colorScheme).toBe("dark");
});
