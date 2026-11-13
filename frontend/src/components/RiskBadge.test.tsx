import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { RiskBadge } from "./RiskBadge";

it("always shows the score with its band", () => {
  render(<RiskBadge score={12} band="High" />);
  expect(screen.getByText("12").parentElement?.textContent).toBe("12High");
});

it("draws a band from another company's matrix in the plain style", () => {
  render(<RiskBadge score={3} band="Medium" />);
  expect(screen.getByText("Medium").parentElement?.className).toContain(
    "bg-slate-800",
  );
});
