import type { Answer, HazardDraft, Question } from "../../api/take5";
import { AnswerPicker } from "../../components/AnswerPicker";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Warning } from "../../components/Warning";

/**
 * Step 3, after the list: the card's hazard questions, as a check on what the worker
 * wrote. Their list is shown first, so a Yes can be checked against it.
 */
export function HazardCheckPage({
  hazards,
  questions,
  choices,
  answers,
  errorFor,
  onAnswer,
  onAddHazard,
}: {
  hazards: HazardDraft[];
  questions: Question[];
  choices: Answer[];
  answers: Partial<Record<string, Answer>>;
  errorFor: (path: string) => string | undefined;
  onAnswer: (questionId: string, answer: Answer) => void;
  onAddHazard: () => void;
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
            {answers[question.id] === "Yes" && (
              <Warning>
                <p>Make sure it’s on your list.</p>
                <Button variant="secondary" onClick={onAddHazard}>
                  Add a hazard
                </Button>
              </Warning>
            )}
          </Card>
        );
      })}
    </div>
  );
}
