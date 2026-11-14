import type { Answer, Question } from "../../api/take5";
import { AnswerPicker } from "../../components/AnswerPicker";
import { Card } from "../../components/Card";

/** Step 2: the card's think-through questions, whatever the template holds. */
export function ThinkPage({
  questions,
  choices,
  answers,
  errorFor,
  onAnswer,
}: {
  questions: Question[];
  choices: Answer[];
  answers: Partial<Record<string, Answer>>;
  errorFor: (path: string) => string | undefined;
  onAnswer: (questionId: string, answer: Answer) => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <p>
        Before you look for hazards, check you’re ready. A No means sort it out
        before you start.
      </p>
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
          </Card>
        );
      })}
    </div>
  );
}
