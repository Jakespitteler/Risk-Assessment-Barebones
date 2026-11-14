import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { Answer } from "../../api/take5";
import { HAZARD_DRAFT, SMALL_TEMPLATE } from "../../test-utils";
import { HazardCheckPage } from "./HazardCheckPage";

const HAZARD_QUESTIONS = SMALL_TEMPLATE.questions.filter(
  (question) => question.role === "hazard",
);

function renderPage(
  answer: Answer | undefined,
  onAddHazard = vi.fn(),
  addedFor: string[] = [],
) {
  render(
    <HazardCheckPage
      hazards={[HAZARD_DRAFT]}
      questions={HAZARD_QUESTIONS}
      choices={SMALL_TEMPLATE.answer_choices}
      answers={answer ? { dogs: answer } : {}}
      addedFor={addedFor}
      errorFor={() => undefined}
      onAnswer={vi.fn()}
      onAddHazard={onAddHazard}
    />,
  );
}

it("shows the worker's own list above whatever hazard questions the template holds", () => {
  renderPage(undefined);
  expect(screen.getByRole("listitem").textContent).toBe("Moving wheel");
  expect(
    screen.getByRole("group", { name: "Are there dogs on site?" }),
  ).toBeTruthy();
  expect(screen.getAllByRole("group")).toHaveLength(1);
});

it.each<Answer>(["No", "N/A"])("asks nothing more after %s", (answer) => {
  renderPage(answer);
  expect(screen.queryByText("Make sure it’s on your list.")).toBeNull();
});

it("after a Yes, reminds the worker to list it, with a button to add a hazard", () => {
  const onAddHazard = vi.fn();
  renderPage("Yes", onAddHazard);
  expect(screen.getByText("Make sure it’s on your list.")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Add a hazard" }));
  expect(onAddHazard).toHaveBeenCalledWith("dogs");
});

it("once a hazard was added from a Yes, shows a tick and a way to add another", () => {
  const onAddHazard = vi.fn();
  renderPage("Yes", onAddHazard, ["dogs"]);
  expect(screen.getByText("Added to your list")).toBeTruthy();
  expect(screen.queryByText("Make sure it’s on your list.")).toBeNull();
  expect(screen.queryByRole("button", { name: "Add a hazard" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Add another" }));
  expect(onAddHazard).toHaveBeenCalledWith("dogs");
});
