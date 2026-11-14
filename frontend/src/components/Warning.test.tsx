import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { Warning } from "./Warning";

it("shows its message without interrupting a screen reader", () => {
  render(<Warning>No controls: you'll be told not to start.</Warning>);
  expect(
    screen.getByText("No controls: you'll be told not to start."),
  ).toBeTruthy();
  expect(screen.queryByRole("alert")).toBeNull();
});
