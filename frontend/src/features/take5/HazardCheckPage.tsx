import type { ReactNode } from "react";
import type { Answer, HazardDraft, Question } from "../../api/take5";
import { AnswerPicker } from "../../components/AnswerPicker";
import { Card } from "../../components/Card";
import { HazardLink } from "./HazardLink";

/**
 * Step 3, after the list: the card's hazard questions, as a check on what the worker
 * wrote. Their list is shown first, so a Yes can be checked against it. Each Yes then
 * needs a hazard linked to it: one picked from the list, or a new one (spec T5).
 */
export function HazardCheckPage({
  hazards,
  questions,
  choices,
  answers,
  errorFor,
  onAnswer,
  onLink,
  onUnlink,
  onAddHazard,
  nudgeFor,
  aiNotice,
}: {
  hazards: HazardDraft[];
  questions: Question[];
  choices: Answer[];
  answers: Partial<Record<string, Answer>>;
  errorFor: (path: string) => string | undefined;
  onAnswer: (questionId: string, answer: Answer) => void;
  onLink: (questionId: string, hazardIndex: number) => void;
  onUnlink: (questionId: string, hazardIndex: number) => void;
  onAddHazard: (questionId: string) => void;
  /** Anything to ask about the wording of a hazard linked to this question (T6). */
  nudgeFor?: (questionId: string, hazardIndex: number) => ReactNode;
  /** That linked hazards are checked by an AI, when one is set up (decision D63). */
  aiNotice?: string | null;
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
      <p>
        Did you miss any of these? For each Yes, say which hazard on your list
        it is, or add it.
      </p>
      {aiNotice && <p className="text-ink-muted">{aiNotice}</p>}
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
              <HazardLink
                questionId={question.id}
                hazards={hazards}
                onLink={(hazardIndex) => {
                  onLink(question.id, hazardIndex);
                }}
                onUnlink={(hazardIndex) => {
                  onUnlink(question.id, hazardIndex);
                }}
                onAddHazard={() => {
                  onAddHazard(question.id);
                }}
                nudgeFor={(hazardIndex) => nudgeFor?.(question.id, hazardIndex)}
              />
            )}
          </Card>
        );
      })}
    </div>
  );
}
