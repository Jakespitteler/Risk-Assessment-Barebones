import type { ReactNode } from "react";
import type { Answer, Hazard, Question } from "../../api/take5";
import { Card } from "../../components/Card";

const GROUPS = [
  { role: "stop", title: "Thinking it through" },
  { role: "hazard", title: "Hazard check" },
] as const;

/**
 * Each of the card's questions with the worker's answer, in the card's order. A Take 5
 * saved before the card had questions has none, so nothing is drawn. Anything to say
 * about one answer, such as a warning, comes from `noteFor` and goes under it. Under a
 * hazard question goes the hazard on the list the worker linked to it (spec T5).
 */
export function AnswerSummary({
  questions,
  answers,
  hazards,
  noteFor,
}: {
  questions: Question[];
  answers: Partial<Record<string, Answer>>;
  hazards: Hazard[];
  /** Anything to say under one answer, or null for nothing. */
  noteFor?: (questionId: string) => ReactNode;
}) {
  return GROUPS.map(({ role, title }) => {
    const asked = questions.filter((question) => question.role === role);
    if (!asked.length) return null;
    return (
      <Card key={role}>
        <h2 className="text-xl font-bold">{title}</h2>
        <dl className="flex flex-col divide-y divide-stone-300">
          {asked.map((question) => {
            const note = noteFor?.(question.id);
            const linked = hazards.filter((hazard) =>
              hazard.covers.includes(question.id),
            );
            return (
              <div
                key={question.id}
                className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-2 py-2"
              >
                <dt>{question.text}</dt>
                <dd className="min-w-12 text-right font-bold">
                  {answers[question.id]}
                </dd>
                {linked.map((hazard, index) => (
                  <dd key={index} className="col-span-2 text-green-800">
                    On your list: {hazard.description}
                  </dd>
                ))}
                {note && <dd className="col-span-2">{note}</dd>}
              </div>
            );
          })}
        </dl>
      </Card>
    );
  });
}
