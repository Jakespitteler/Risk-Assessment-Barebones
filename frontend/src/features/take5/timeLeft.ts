const MINUTE_MS = 60_000;
const MINUTES_IN_AN_HOUR = 60;

/**
 * How long a draft has left before it runs out, in words such as "1 hr 42 min left".
 * The back end says when it runs out; this only counts down to that time.
 */
export function timeLeft(runsOutAt: string, now: Date): string {
  const minutesLeft = Math.floor(
    (new Date(runsOutAt).getTime() - now.getTime()) / MINUTE_MS,
  );
  if (minutesLeft < 1) return "Under 1 min left";
  const hours = Math.floor(minutesLeft / MINUTES_IN_AN_HOUR);
  const minutes = minutesLeft % MINUTES_IN_AN_HOUR;
  if (!hours) return `${String(minutes)} min left`;
  return minutes
    ? `${String(hours)} hr ${String(minutes)} min left`
    : `${String(hours)} hr left`;
}
