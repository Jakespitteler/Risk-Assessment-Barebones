import { render, screen } from "@testing-library/react";
import { createRef } from "react";
import { expect, it } from "vitest";
import { FormHeading } from "./FormHeading";

it("shows the step, the hazard's card and a focusable heading", () => {
  const heading = createRef<HTMLHeadingElement>();
  render(
    <FormHeading
      stage={{ page: "after", hazard: 1 }}
      hazardCount={3}
      hazardDescription="Dust"
      headingRef={heading}
      furthestStep={4}
      busy={false}
      onPickStep={() => undefined}
    />,
  );
  expect(screen.getByText("Step 4 of 5")).toBeTruthy();
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
    "After your controls",
  );
  expect(heading.current?.tabIndex).toBe(-1);
  const hazardLabel = screen.getByText("Hazard 2 of 3");
  expect(hazardLabel.nextElementSibling?.textContent).toBe("Dust");
  expect(
    screen.getByRole("button", { name: "Assess" }).getAttribute("aria-current"),
  ).toBe("step");
});

it("names a hazard with no words yet by its number in the card", () => {
  render(
    <FormHeading
      stage={{ page: "controls", hazard: 0 }}
      hazardCount={2}
      hazardDescription=""
      headingRef={createRef<HTMLHeadingElement>()}
      furthestStep={4}
      busy={false}
      onPickStep={() => undefined}
    />,
  );
  expect(screen.getByText("Hazard 1 of 2")).toBeTruthy();
  expect(screen.getByText("Hazard 1")).toBeTruthy();
});

it("shows no hazard card on a page that is not about one hazard", () => {
  render(
    <FormHeading
      stage={{ page: "job" }}
      hazardCount={2}
      hazardDescription=""
      headingRef={createRef<HTMLHeadingElement>()}
      furthestStep={1}
      busy={false}
      onPickStep={() => undefined}
    />,
  );
  expect(screen.queryByText(/^Hazard \d+ of \d+$/)).toBeNull();
});
