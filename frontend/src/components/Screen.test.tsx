import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { Screen } from "./Screen";

it("puts the page in one main landmark with the app's name", () => {
  render(
    <Screen subtitle="Before you start">
      <h1>The job</h1>
    </Screen>,
  );
  const main = screen.getByRole("main");
  expect(main.textContent).toContain("Take 5");
  expect(main.textContent).toContain("Before you start");
});

it("shows the aside in the top bar", () => {
  render(
    <Screen subtitle="Before you start" aside={<a href="/elsewhere">Away</a>}>
      <h1>The job</h1>
    </Screen>,
  );
  expect(
    screen.getByRole("link", { name: "Away" }).closest("header"),
  ).toBeTruthy();
});

it("makes the 5 a link to the start page, named for a screen reader", () => {
  render(
    <Screen subtitle="Look back">
      <h1>Saved Take 5s</h1>
    </Screen>,
  );
  const home = screen.getByRole("link", { name: "Take 5 home" });
  expect(home.getAttribute("href")).toBe("/");
  expect(home.closest("header")).toBeTruthy();
});
