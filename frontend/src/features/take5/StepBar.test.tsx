import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { Stage } from "./stage";
import { StepBar } from "./StepBar";

function renderBar(stage: Stage, furthestStep: number, busy = false) {
  const onPickStep = vi.fn<(step: number) => void>();
  render(
    <StepBar
      stage={stage}
      furthestStep={furthestStep}
      busy={busy}
      onPickStep={onPickStep}
    />,
  );
  return onPickStep;
}

it("lets the worker tap each step reached, and no step after it", () => {
  renderBar({ page: "think" }, 3);
  for (const name of ["Job", "Hazards"])
    expect(screen.getByRole("button", { name })).toBeTruthy();
  for (const name of ["Think", "Assess", "Review"])
    expect(screen.queryByRole("button", { name })).toBeNull();
  expect(screen.getAllByText(", not reached yet")).toHaveLength(2);
});

it("hands over the step tapped", () => {
  const onPickStep = renderBar({ page: "review" }, 5);
  fireEvent.click(screen.getByRole("button", { name: "Hazards" }));
  expect(onPickStep).toHaveBeenCalledWith(3);
});

it("marks the current step, and lets it be tapped away from its first page", () => {
  const onPickStep = renderBar({ page: "controls", hazard: 1 }, 4);
  const assess = screen.getByRole("button", { name: "Assess" });
  expect(assess.getAttribute("aria-current")).toBe("step");
  fireEvent.click(assess);
  expect(onPickStep).toHaveBeenCalledWith(4);
});

it("counts the step showing as reached, even before it is remembered", () => {
  renderBar({ page: "hazards" }, 1);
  expect(screen.getByRole("button", { name: "Think" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Assess" })).toBeNull();
});

it("makes the steps wait while a check or a save is under way", () => {
  renderBar({ page: "review" }, 5, true);
  expect(
    screen.getByRole<HTMLButtonElement>("button", { name: "Job" }).disabled,
  ).toBe(true);
});
