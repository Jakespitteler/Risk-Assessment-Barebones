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

it("shows the saved reason without changing or summarising it", () => {
  const reason = "Live testing, so the panel can't be isolated";
  render(
    <HazardSummary
      hazard={{ ...RATED_HAZARD, weak_controls_reason: reason }}
      number={1}
    />,
  );
  expect(
    screen.getByRole("heading", {
      name: "Why stronger controls weren't possible",
    }),
  ).toBeTruthy();
  expect(screen.getByText(reason)).toBeTruthy();
});

it("says a rating a paper card left blank is not rated (P1)", () => {
  const hazard = {
    ...RATED_HAZARD,
    before: null,
    after: null,
    controls: [{ description: "Chock the wheel", kind: null }],
  };
  render(<HazardSummary hazard={hazard} number={1} />);
  expect(screen.getAllByText("Not rated")).toHaveLength(2);
  expect(screen.getByText("No kind given")).toBeTruthy();
  expect(screen.getByText("Chock the wheel")).toBeTruthy();
});
