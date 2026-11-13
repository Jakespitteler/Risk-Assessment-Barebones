import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { VerdictPanel } from "./VerdictPanel";

it("shows Don't start yet with every reason, in order", () => {
  const reasons = ["Say how you will control: Dust", "The risk is High (12)."];
  render(<VerdictPanel verdict={{ can_start: false, reasons }} />);
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
    "Don’t start yet",
  );
  expect(
    screen.getAllByRole("listitem").map((item) => item.textContent),
  ).toEqual(reasons);
});

it("shows Good to go with no reasons", () => {
  render(<VerdictPanel verdict={{ can_start: true, reasons: [] }} />);
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
    "Good to go",
  );
  expect(screen.queryByRole("list")).toBeNull();
});
