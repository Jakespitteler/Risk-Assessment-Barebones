import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { SMALL_TEMPLATE } from "../../test-utils";
import { RatingPage } from "./RatingPage";

it("shows the whole rating's error, such as controls raising the risk", () => {
  render(
    <RatingPage
      when="after"
      path="hazards.0.after"
      rating={{ likelihood: "Often", consequence: "Serious" }}
      template={SMALL_TEMPLATE}
      errorFor={(path) =>
        path === "hazards.0.after"
          ? "Controls cannot make the after risk higher than before."
          : undefined
      }
      onChange={vi.fn()}
    />,
  );
  expect(
    screen.getByText("Controls cannot make the after risk higher than before."),
  ).toBeTruthy();
  expect(
    screen.getByText(
      "Think about what could still happen with your controls in place.",
    ),
  ).toBeTruthy();
});

it("shows the card's guidance and reports a pick", () => {
  const onChange = vi.fn();
  render(
    <RatingPage
      when="before"
      path="hazards.0.before"
      rating={{ likelihood: null, consequence: null }}
      template={SMALL_TEMPLATE}
      errorFor={() => undefined}
      onChange={onChange}
    />,
  );
  expect(screen.getByText("Every week.")).toBeTruthy();
  expect(screen.getByText("Hospital.")).toBeTruthy();
  const group = screen.getByRole("group", { name: "How likely is it?" });
  fireEvent.click(within(group).getByRole("radio", { name: "Seldom" }));
  expect(onChange).toHaveBeenCalledWith({
    likelihood: "Seldom",
    consequence: null,
  });
});
