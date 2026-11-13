import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { RATED_HAZARD } from "../../test-utils";
import { HazardSummary } from "./HazardSummary";

it("shows the ratings the back end worked out, with their levels and controls", () => {
  render(<HazardSummary hazard={RATED_HAZARD} number={1} />);
  expect(screen.getByRole("heading", { name: "Moving wheel" })).toBeTruthy();
  expect(screen.getByText("Often · Serious")).toBeTruthy();
  expect(screen.getByText("4").parentElement?.textContent).toBe("4Severe");
  expect(screen.getByText("1").parentElement?.textContent).toBe("1Minimal");
  expect(screen.getByText("Chock the wheel")).toBeTruthy();
});

it("says when a hazard has no controls", () => {
  const hazard = { ...RATED_HAZARD, controls: [] };
  render(<HazardSummary hazard={hazard} number={2} />);
  expect(screen.getByText("No controls listed.")).toBeTruthy();
  expect(screen.getByText("Hazard 2")).toBeTruthy();
});
