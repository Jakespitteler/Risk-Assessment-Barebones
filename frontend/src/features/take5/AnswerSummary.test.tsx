import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { ANSWERS, RATED_HAZARD, SMALL_TEMPLATE } from "../../test-utils";
import { AnswerSummary } from "./AnswerSummary";

it("shows each question with its answer, grouped by what kind of question it is", () => {
  render(
    <AnswerSummary
      questions={SMALL_TEMPLATE.questions}
      answers={ANSWERS}
      hazards={[RATED_HAZARD]}
    />,
  );
  expect(
    screen.getAllByRole("heading").map((heading) => heading.textContent),
  ).toEqual(["Thinking it through", "Hazard check"]);
  const terms = screen.getAllByRole("term").map((term) => term.textContent);
  const answers = screen
    .getAllByRole("definition")
    .map((answer) => answer.textContent);
  expect(terms).toEqual([
    "Have you got the gate keys?",
    "Are there dogs on site?",
  ]);
  expect(answers).toEqual(["Yes", "No"]);
});

it("draws nothing for a Take 5 saved before the card had questions", () => {
  const { container } = render(
    <AnswerSummary questions={[]} answers={{}} hazards={[]} />,
  );
  expect(container.childElementCount).toBe(0);
});

it("shows the hazard on the list that a Yes was linked to, under that answer", () => {
  render(
    <AnswerSummary
      questions={SMALL_TEMPLATE.questions}
      answers={{ keys: "Yes", dogs: "Yes" }}
      hazards={[{ ...RATED_HAZARD, description: "Bitten", covers: ["dogs"] }]}
    />,
  );
  const dogs = screen.getByText("Are there dogs on site?").parentElement;
  expect(dogs?.textContent).toBe(
    "Are there dogs on site?YesOn your list: Bitten",
  );
});
