import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { Notice } from "./Notice";

it("is announced to screen readers", () => {
  render(<Notice>Your answers are still here.</Notice>);
  expect(screen.getByRole("alert").textContent).toBe(
    "Your answers are still here.",
  );
});
