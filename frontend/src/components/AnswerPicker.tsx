import type { Answer } from "../api/take5";

interface AnswerPickerProps {
  /** The field's dotted path, such as `answers.permits`. It ties the error to the group. */
  name: string;
  question: string;
  choices: Answer[];
  picked: Answer | undefined;
  onPick: (answer: Answer) => void;
  error?: string | undefined;
}

/**
 * One question with a big button for each answer, side by side. Nothing is picked to
 * begin with, so every answer is a choice the worker made.
 */
export function AnswerPicker({
  name,
  question,
  choices,
  picked,
  onPick,
  error,
}: AnswerPickerProps) {
  return (
    <fieldset
      className="flex flex-col gap-3"
      aria-invalid={Boolean(error)}
      aria-describedby={error ? `${name}-error` : undefined}
    >
      <legend className="mb-3 text-lg font-bold">{question}</legend>
      {error && (
        <p id={`${name}-error`} className="font-semibold text-danger">
          {error}
        </p>
      )}
      <div className="grid grid-cols-3 gap-2">
        {choices.map((answer) => (
          <label
            key={answer}
            className="flex min-h-14 cursor-pointer items-center justify-center rounded-xl border-2 border-line-strong bg-surface px-2 text-lg font-bold has-checked:border-action has-checked:bg-action has-checked:text-on-action hover:not-has-checked:bg-surface-hover has-focus-visible:outline-4 has-focus-visible:outline-focus"
          >
            <input
              type="radio"
              name={name}
              value={answer}
              checked={picked === answer}
              onChange={() => {
                onPick(answer);
              }}
              className="sr-only"
            />
            {answer}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
