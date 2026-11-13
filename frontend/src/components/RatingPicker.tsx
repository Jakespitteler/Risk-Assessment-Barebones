import { useId } from "react";
import type { RiskMatrix, RatingChoice } from "../api/take5";
import { RiskBadge } from "./RiskBadge";

/** What the worker has picked so far. Nothing is picked to begin with (spec F2). */
export type PickedRating = RatingChoice;

export const NOTHING_PICKED: PickedRating = {
  likelihood: null,
  consequence: null,
};

interface RatingPickerProps {
  matrix: RiskMatrix;
  rating: PickedRating;
  onChange: (rating: PickedRating) => void;
  errors?: { likelihood?: string; consequence?: string };
}

/** Pick a likelihood and a consequence, and see the score and band as soon as both are picked. */
export function RatingPicker({
  matrix,
  rating,
  onChange,
  errors,
}: RatingPickerProps) {
  const cell = lookUpCell(matrix, rating);
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
          <p className="text-lg text-slate-700">Pick both to see the score.</p>
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
  error?: string;
}

function ScalePicker({
  question,
  levels,
  picked,
  onPick,
  error,
}: ScalePickerProps) {
  // Its own name, so two pickers on one screen (before and after controls) never share a group.
  const groupName = useId();
  return (
    <fieldset
      className="flex flex-col gap-2"
      aria-invalid={Boolean(error)}
      aria-describedby={error ? `${groupName}-error` : undefined}
    >
      <legend className="mb-2 text-xl font-semibold text-slate-900">
        {question}
      </legend>
      {error && (
        <p className="field-error" id={`${groupName}-error`}>
          {error}
        </p>
      )}
      {levels.map((level) => (
        <label
          key={level}
          className="flex min-h-14 cursor-pointer items-center rounded-xl border-2 border-slate-400 bg-white px-4 text-lg font-medium text-slate-900 has-checked:border-slate-900 has-checked:bg-slate-900 has-checked:text-white has-focus-visible:outline-4 has-focus-visible:outline-blue-600"
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

/** Find the matrix cell for what has been picked, or nothing until both are picked. */
export function lookUpCell(matrix: RiskMatrix, rating: PickedRating) {
  if (rating.likelihood == null || rating.consequence == null) {
    return undefined;
  }
  const row = matrix.likelihoods.indexOf(rating.likelihood);
  const column = matrix.consequences.indexOf(rating.consequence);
  return matrix.cells[row]?.[column];
}
