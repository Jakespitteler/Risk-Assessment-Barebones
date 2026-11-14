import type { Answer, HazardDraft, Question } from "../../api/take5";
import { AnswerPicker } from "../../components/AnswerPicker";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Warning } from "../../components/Warning";

/**
 * Step 3, after the list: the card's hazard questions, as a check on what the worker
 * wrote. Their list is shown first, so a Yes can be checked against it. Once a hazard
 * has been added from a Yes, the reminder becomes a tick, with a way to add another.
 */
export function HazardCheckPage({
  hazards,
  questions,
  choices,
  answers,
  addedFor,
  errorFor,
  onAnswer,
  onAddHazard,
}: {
  hazards: HazardDraft[];
  questions: Question[];
  choices: Answer[];
  answers: Partial<Record<string, Answer>>;
  addedFor: string[];
  errorFor: (path: string) => string | undefined;
  onAnswer: (questionId: string, answer: Answer) => void;
  onAddHazard: (questionId: string) => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <h2 className="text-xl font-bold">Your list</h2>
        <ol className="flex list-decimal flex-col gap-1 pl-6 text-lg">
          {hazards.map((hazard, index) => (
            <li key={index}>{hazard.description.trim()}</li>
          ))}
        </ol>
      </Card>
      <p>Did you miss any of these? A Yes means it belongs on your list.</p>
      {questions.map((question) => {
        const path = `answers.${question.id}`;
        return (
          <Card key={question.id}>
            <AnswerPicker
              name={path}
              question={question.text}
              choices={choices}
              picked={answers[question.id]}
              error={errorFor(path)}
              onPick={(answer) => {
                onAnswer(question.id, answer);
              }}
            />
            {answers[question.id] === "Yes" &&
              (addedFor.includes(question.id) ? (
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold text-green-800">
                    <span aria-hidden="true">✓ </span>Added to your list
                  </p>
                  <Button
                    variant="quiet"
                    onClick={() => {
                      onAddHazard(question.id);
                    }}
                  >
                    Add another
                  </Button>
                </div>
              ) : (
                <Warning>
                  <p>Make sure it’s on your list.</p>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      onAddHazard(question.id);
                    }}
                  >
                    Add a hazard
                  </Button>
                </Warning>
              ))}
          </Card>
        );
      })}
    </div>
  );
}
