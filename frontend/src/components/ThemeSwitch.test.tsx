import { act, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { setPhoneScheme } from "../test-phone-scheme";
import { readChoice } from "../theme/colourScheme";
import { ThemeSwitch } from "./ThemeSwitch";

afterEach(() => {
  localStorage.clear();
});

function pageScheme(): string | undefined {
  return document.documentElement.dataset.theme;
}

it("follows a light phone, and offers dark", () => {
  render(<ThemeSwitch />);
  expect(pageScheme()).toBe("light");
  expect(screen.getByRole("button", { name: "Switch to dark" })).toBeTruthy();
});

it("follows a dark phone, and offers light", () => {
  setPhoneScheme("dark");
  render(<ThemeSwitch />);
  expect(pageScheme()).toBe("dark");
  expect(screen.getByRole("button", { name: "Switch to light" })).toBeTruthy();
});

it("switches at once, and keeps the choice", () => {
  render(<ThemeSwitch />);
  act(() => {
    screen.getByRole("button", { name: "Switch to dark" }).click();
  });
  expect(pageScheme()).toBe("dark");
  expect(screen.getByRole("button", { name: "Switch to light" })).toBeTruthy();
  expect(readChoice()).toEqual({ chosen: "dark", phoneWhenChosen: "light" });
});

it("forgets the choice when switched back to the phone's own scheme", () => {
  render(<ThemeSwitch />);
  act(() => {
    screen.getByRole("button", { name: "Switch to dark" }).click();
  });
  act(() => {
    screen.getByRole("button", { name: "Switch to light" }).click();
  });
  expect(pageScheme()).toBe("light");
  expect(readChoice()).toBeNull();
});

it("follows the phone again, and forgets the choice, when the phone's setting changes", () => {
  render(<ThemeSwitch />);
  act(() => {
    screen.getByRole("button", { name: "Switch to dark" }).click();
  });
  act(() => {
    setPhoneScheme("dark");
  });
  act(() => {
    setPhoneScheme("light");
  });
  expect(pageScheme()).toBe("light");
  expect(readChoice()).toBeNull();
});
