import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { SMALL_TEMPLATE } from "../../test-utils";
import { ThinkPage } from "./ThinkPage";

const STOP_QUESTIONS = SMALL_TEMPLATE.questions.filter(
  (question) => question.role === "stop",
);

it("draws whatever stop questions the template holds, none answered", () => {
  render(
    <ThinkPage
      questions={STOP_QUESTIONS}
      choices={SMALL_TEMPLATE.answer_choices}
      answers={{}}
      errorFor={() => undefined}
      onAnswer={vi.fn()}
    />,
  );
  const groups = screen.getAllByRole("group");
  expect(
    groups.map((group) => group.querySelector("legend")?.textContent),
  ).toEqual(["Have you got the gate keys?"]);
  expect(screen.queryByRole("radio", { checked: true })).toBeNull();
});

it("sends the question's ID with the picked answer, and shows its error", () => {
  const onAnswer = vi.fn();
  render(
    <ThinkPage
      questions={STOP_QUESTIONS}
      choices={SMALL_TEMPLATE.answer_choices}
      answers={{}}
      errorFor={(path) =>
        path === "answers.keys" ? "Pick Yes, No or N/A." : undefined
      }
      onAnswer={onAnswer}
    />,
  );
  expect(screen.getByText("Pick Yes, No or N/A.")).toBeTruthy();
  fireEvent.click(
    within(
      screen.getByRole("group", { name: "Have you got the gate keys?" }),
    ).getByRole("radio", { name: "No" }),
  );
  expect(onAnswer).toHaveBeenCalledWith("keys", "No");
});
