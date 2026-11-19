import { useState } from "react";
import { useTemplate } from "../../api/take5";
import type { RatingChoice } from "../../api/take5";
import { RatingPicker } from "../../components/RatingPicker";
import { useColourScheme } from "../../theme/useColourScheme";

/**
 * The walking skeleton's one screen: rate a risk on the matrix the back end sends. It has
 * no top bar, so no switch, but it still follows the phone into light or dark.
 */
export function RateRiskScreen() {
  useColourScheme();
  const template = useTemplate();
  const [rating, setRating] = useState<RatingChoice>({
    likelihood: null,
    consequence: null,
  });

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 bg-surface px-4 py-6">
      <h1 className="text-3xl font-bold text-ink">Rate a risk</h1>
      {template.isPending && (
        <p className="text-lg text-ink-muted">Loading the card…</p>
      )}
      {template.isError && (
        <div className="flex flex-col gap-3">
          <p className="text-lg text-ink">
            The card couldn’t be loaded. Check your signal and try again.
          </p>
          <button
            type="button"
            onClick={() => void template.refetch()}
            className="min-h-14 rounded-xl bg-action px-4 text-lg font-semibold text-on-action"
          >
            Try again
          </button>
        </div>
      )}
      {template.isSuccess && (
        <RatingPicker
          matrix={template.data.matrix}
          rating={rating}
          onChange={setRating}
        />
      )}
    </main>
  );
}
