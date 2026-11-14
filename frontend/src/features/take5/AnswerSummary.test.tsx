import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { ANSWERS, SMALL_TEMPLATE } from "../../test-utils";
import { AnswerSummary } from "./AnswerSummary";

it("shows each question with its answer, grouped by what kind of question it is", () => {
  render(
    <AnswerSummary questions={SMALL_TEMPLATE.questions} answers={ANSWERS} />,
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
  const { container } = render(<AnswerSummary questions={[]} answers={{}} />);
  expect(container.childElementCount).toBe(0);
});
