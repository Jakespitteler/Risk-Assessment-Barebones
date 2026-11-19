import { useId } from "react";
import type { RatingChoice, RiskMatrix } from "../api/take5";
import { RiskBadge } from "./RiskBadge";

interface RatingPickerProps {
  matrix: RiskMatrix;
  rating: RatingChoice;
  onChange: (rating: RatingChoice) => void;
  errors?: {
    likelihood?: string | undefined;
    consequence?: string | undefined;
  };
}

/** Pick a likelihood and a consequence, and see the score and band once both are picked. */
export function RatingPicker({
  matrix,
  rating,
  onChange,
  errors,
}: RatingPickerProps) {
  const cell = cellFor(matrix, rating);
  return (
    <div className="flex flex-col gap-6">
      <ScalePicker
        question="How likely is it?"
        levels={matrix.likelihoods}
        picked={rating.likelihood ?? null}
        error={errors?.likelihood}
        onPick={(likelihood) => {
          onChange({ ...rating, likelihood });
        }}
      />
      <ScalePicker
        question="How bad would it be?"
        levels={matrix.consequences}
        picked={rating.consequence ?? null}
        error={errors?.consequence}
        onPick={(consequence) => {
          onChange({ ...rating, consequence });
        }}
      />
      <div role="status" aria-label="Risk score">
        {cell ? (
          <RiskBadge score={cell.score} band={cell.band} />
        ) : (
          <p className="text-lg text-ink-muted">Pick both to see the score.</p>
        )}
      </div>
    </div>
  );
}

interface ScalePickerProps {
  question: string;
  levels: string[];
  picked: string | null;
  onPick: (level: string) => void;
  error?: string | undefined;
}

function ScalePicker({
  question,
  levels,
  picked,
  onPick,
  error,
}: ScalePickerProps) {
  // Its own name, so two pickers on one screen never share a radio group.
  const groupName = useId();
  return (
    <fieldset
      className="flex flex-col gap-2"
      aria-invalid={Boolean(error)}
      aria-describedby={error ? `${groupName}-error` : undefined}
    >
      <legend className="mb-2 text-xl font-bold">{question}</legend>
      {error && (
        <p id={`${groupName}-error`} className="font-semibold text-danger">
          {error}
        </p>
      )}
      {levels.map((level) => (
        <label
          key={level}
          className="flex min-h-14 cursor-pointer items-center rounded-xl border-2 border-line-strong bg-surface px-4 text-lg font-medium has-checked:border-action has-checked:bg-action has-checked:text-on-action has-focus-visible:outline-4 has-focus-visible:outline-focus"
        >
          <input
            type="radio"
            name={groupName}
            value={level}
            checked={picked === level}
            onChange={() => {
              onPick(level);
            }}
            className="sr-only"
          />
          {level}
        </label>
      ))}
    </fieldset>
  );
}

/**
 * The matrix's cell for what is picked, or nothing until both halves are. This only
 * reads the matrix the back end sent; the back end checks the rating again on Continue.
 */
function cellFor(matrix: RiskMatrix, rating: RatingChoice) {
  if (rating.likelihood == null || rating.consequence == null) return undefined;
  const row = matrix.likelihoods.indexOf(rating.likelihood);
  const column = matrix.consequences.indexOf(rating.consequence);
  return matrix.cells[row]?.[column];
}
