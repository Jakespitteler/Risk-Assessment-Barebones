import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { SaveProblem } from "./SaveProblem";

it("links to the saved Take 5 when the ID was used for other answers", () => {
  render(<SaveProblem problem="conflict" submissionId="abc" />);
  expect(
    screen
      .getByRole("link", { name: "Open the saved Take 5" })
      .getAttribute("href"),
  ).toBe("/take5s/abc");
});

it("says the answers are kept when the save couldn't be confirmed", () => {
  render(<SaveProblem problem="unsent" submissionId="abc" />);
  expect(screen.getByRole("alert").textContent).toContain(
    "Your answers are still here",
  );
});
