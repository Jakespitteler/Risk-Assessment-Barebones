import type { ReactNode } from "react";
import type { Answer, Question } from "../../api/take5";
import { Card } from "../../components/Card";

const GROUPS = [
  { role: "stop", title: "Thinking it through" },
  { role: "hazard", title: "Hazard check" },
] as const;

/**
 * Each of the card's questions with the worker's answer, in the card's order. A Take 5
 * saved before the card had questions has none, so nothing is drawn. Anything to say
 * about one answer, such as a warning, comes from `noteFor` and goes under it.
 */
export function AnswerSummary({
  questions,
  answers,
  noteFor,
}: {
  questions: Question[];
  answers: Partial<Record<string, Answer>>;
  noteFor?: (questionId: string) => ReactNode;
}) {
  return GROUPS.map(({ role, title }) => {
    const asked = questions.filter((question) => question.role === role);
    if (!asked.length) return null;
    return (
      <Card key={role}>
        <h2 className="text-xl font-bold">{title}</h2>
        <dl className="flex flex-col divide-y divide-stone-300">
          {asked.map((question) => (
            <div key={question.id} className="flex flex-col gap-2 py-2">
              <div className="flex items-start justify-between gap-4">
                <dt>{question.text}</dt>
                <dd className="min-w-12 shrink-0 text-right font-bold">
                  {answers[question.id]}
                </dd>
              </div>
              {noteFor?.(question.id)}
            </div>
          ))}
        </dl>
      </Card>
    );
  });
}
