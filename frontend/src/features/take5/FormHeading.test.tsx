import { render, screen } from "@testing-library/react";
import { createRef } from "react";
import { expect, it } from "vitest";
import { FormHeading } from "./FormHeading";

it("shows the step, the hazard and a focusable heading", () => {
  const heading = createRef<HTMLHeadingElement>();
  render(
    <FormHeading
      stage={{ page: "after", hazard: 1 }}
      hazardCount={3}
      hazardDescription="Dust"
      headingRef={heading}
    />,
  );
  expect(screen.getByText("Step 4 of 5 · Hazard 2 of 3")).toBeTruthy();
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
    "After your controls",
  );
  expect(heading.current?.tabIndex).toBe(-1);
  expect(screen.getByText("Dust")).toBeTruthy();
  expect(screen.getByText("Assess").getAttribute("aria-current")).toBe("step");
});
