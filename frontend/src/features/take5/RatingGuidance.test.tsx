import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { SMALL_TEMPLATE } from "../../test-utils";
import { RatingGuidance } from "./RatingGuidance";

it("lists each level with what it means, from the template", () => {
  render(<RatingGuidance template={SMALL_TEMPLATE} />);
  expect(screen.getByText("Often").nextElementSibling?.textContent).toBe(
    "Every week.",
  );
  expect(screen.getByText("Serious").nextElementSibling?.textContent).toBe(
    "Hospital.",
  );
});
