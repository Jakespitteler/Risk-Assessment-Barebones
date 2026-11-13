import { useState } from "react";
import { useTemplate } from "../../api/take5";
import { NOTHING_PICKED, RatingPicker } from "../../components/RatingPicker";

/** The walking skeleton's one screen: rate a risk on the matrix the back end sends. */
export function RateRiskScreen() {
  const template = useTemplate();
  const [rating, setRating] = useState(NOTHING_PICKED);

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 bg-white px-4 py-6">
      <h1 className="text-3xl font-bold text-slate-900">Rate a risk</h1>
      {template.isPending && (
        <p className="text-lg text-slate-700">Loading the card…</p>
      )}
      {template.isError && (
        <div className="flex flex-col gap-3">
          <p className="text-lg text-slate-900">
            The card couldn’t be loaded. Check your signal and try again.
          </p>
          <button
            type="button"
            onClick={() => void template.refetch()}
            className="min-h-14 rounded-xl bg-slate-900 px-4 text-lg font-semibold text-white"
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
