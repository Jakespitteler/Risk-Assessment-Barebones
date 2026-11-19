import { useEffect, useState } from "react";
import { formatDateTime } from "./formatDateTime";
import { timeLeftText } from "./timeLeftText";

// Often enough that the minutes shown are never more than half a minute out.
const REFRESH_MS = 30_000;

/**
 * How long the draft has left before it runs out (spec K2), counting down while it
 * shows. Nothing shows when the back end hasn't said, or the time limit is off.
 */
export function TimeLeft({
  runsOutAt,
}: {
  runsOutAt: string | null | undefined;
}) {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, REFRESH_MS);
    return () => {
      clearInterval(timer);
    };
  }, []);
  if (!runsOutAt) return null;
  return (
    <p className="self-start rounded-lg border-2 border-ink bg-surface px-3 py-1 font-semibold">
      {timeLeftText(runsOutAt, now)}{" "}
      <span className="font-normal text-ink-muted">
        to finish, until{" "}
        <time dateTime={runsOutAt}>{formatDateTime(runsOutAt)}</time>
      </span>
    </p>
  );
}
