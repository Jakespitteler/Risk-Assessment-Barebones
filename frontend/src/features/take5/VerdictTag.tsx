/**
 * The verdict as a tag, in the same strong colours as the result screen, or "Not
 * finished" while its question is unanswered (spec F5).
 */
export function VerdictTag({ canStart }: { canStart: boolean | null }) {
  if (canStart === null)
    return (
      <span className="rounded-lg bg-brand px-2 py-1 text-sm font-bold text-on-brand uppercase">
        Not finished
      </span>
    );
  return (
    <span
      className={`rounded-lg px-2 py-1 text-sm font-bold text-on-fill uppercase ${
        canStart ? "bg-success-fill" : "bg-danger-fill"
      }`}
    >
      {canStart ? "Good to go" : "Don’t start yet"}
    </span>
  );
}
