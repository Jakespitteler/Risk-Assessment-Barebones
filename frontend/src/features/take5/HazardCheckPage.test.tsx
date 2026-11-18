import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { Answer, HazardDraft } from "../../api/take5";
import { HAZARD_DRAFT, SMALL_TEMPLATE } from "../../test-utils";
import { HazardCheckPage } from "./HazardCheckPage";

const HAZARD_QUESTIONS = SMALL_TEMPLATE.questions.filter(
  (question) => question.role === "hazard",
);
const BITTEN: HazardDraft = {
  ...HAZARD_DRAFT,
  description: "Bitten by the guard dog",
};

function renderPage(
  answer: Answer | undefined,
  hazards: HazardDraft[] = [HAZARD_DRAFT, BITTEN],
  error?: string,
) {
  const handlers = { onAddHazard: vi.fn(), onLink: vi.fn(), onUnlink: vi.fn() };
  render(
    <HazardCheckPage
      hazards={hazards}
      questions={HAZARD_QUESTIONS}
      choices={SMALL_TEMPLATE.answer_choices}
      answers={answer ? { dogs: answer } : {}}
      errorFor={(path) => (path === "answers.dogs" ? error : undefined)}
      onAnswer={vi.fn()}
      {...handlers}
    />,
  );
  return handlers;
}

it("shows the worker's own list above whatever hazard questions the template holds", () => {
  renderPage(undefined);
  expect(
    screen.getAllByRole("listitem").map((item) => item.textContent),
  ).toEqual(["Moving wheel", "Bitten by the guard dog"]);
  expect(
    screen.getByRole("group", { name: "Are there dogs on site?" }),
  ).toBeTruthy();
  expect(screen.getAllByRole("group")).toHaveLength(1);
});

it.each<Answer>(["No", "N/A"])("asks nothing more after %s", (answer) => {
  renderPage(answer);
  expect(screen.queryByText("Which hazard on your list is this?")).toBeNull();
});

it("after a Yes, asks which hazard it is, with a button to add a hazard", () => {
  const { onAddHazard } = renderPage("Yes");
  expect(screen.getByText("Which hazard on your list is this?")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Add a hazard" }));
  expect(onAddHazard).toHaveBeenCalledWith("dogs");
});

it("“It’s on my list” shows the list to pick from, and moves the focus to it", () => {
  const { onLink } = renderPage("Yes");
  fireEvent.click(screen.getByRole("button", { name: "It’s on my list" }));
  const picker = screen.getByRole("group", {
    name: "Which one on your list is it?",
  });
  expect(
    within(picker)
      .getAllByRole("button")
      .map((choice) => choice.textContent),
  ).toEqual([
    "Moving wheel",
    "Bitten by the guard dog",
    "It’s not there: add a hazard",
  ]);
  expect(document.activeElement?.textContent).toBe(
    "Which one on your list is it?",
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Bitten by the guard dog" }),
  );
  expect(onLink).toHaveBeenCalledWith("dogs", 1);
});

it("the picker says when a hazard already answers another question", () => {
  renderPage("Yes", [{ ...BITTEN, covers: ["fences"] }]);
  fireEvent.click(screen.getByRole("button", { name: "It’s on my list" }));
  expect(
    screen.getByRole("button", {
      name: /^Bitten by the guard dog\s*Already on another question$/,
    }),
  ).toBeTruthy();
});

it("the picker can still add a hazard when it isn't on the list", () => {
  const { onAddHazard } = renderPage("Yes");
  fireEvent.click(screen.getByRole("button", { name: "It’s on my list" }));
  fireEvent.click(
    screen.getByRole("button", { name: "It’s not there: add a hazard" }),
  );
  expect(onAddHazard).toHaveBeenCalledWith("dogs");
});

it("once linked, shows the hazard, a way to unlink it and a way to add another", () => {
  const { onAddHazard, onUnlink } = renderPage("Yes", [
    HAZARD_DRAFT,
    { ...BITTEN, covers: ["dogs"] },
  ]);
  expect(
    screen.getByText("On your list: Bitten by the guard dog", { exact: false }),
  ).toBeTruthy();
  expect(screen.queryByText("Which hazard on your list is this?")).toBeNull();
  fireEvent.click(
    screen.getByRole("button", {
      name: "Not this one: Bitten by the guard dog",
    }),
  );
  expect(onUnlink).toHaveBeenCalledWith("dogs", 1);
  fireEvent.click(screen.getByRole("button", { name: "Add another" }));
  expect(onAddHazard).toHaveBeenCalledWith("dogs");
});

it("shows the back end's gap beside a Yes with no hazard linked", () => {
  renderPage(
    "Yes",
    undefined,
    "Pick the hazard on your list that this is, or add it.",
  );
  expect(
    screen.getByText("Pick the hazard on your list that this is, or add it."),
  ).toBeTruthy();
});

it("never offers or shows a hazard with nothing written in it", () => {
  const blank = { ...HAZARD_DRAFT, description: " ", covers: ["dogs"] };
  renderPage("Yes", [HAZARD_DRAFT, blank]);
  expect(screen.queryByText("On your list:", { exact: false })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "It’s on my list" }));
  const picker = screen.getByRole("group", {
    name: "Which one on your list is it?",
  });
  expect(within(picker).getAllByRole("button")).toHaveLength(2);
});
