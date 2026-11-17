import { Button } from "../../components/Button";
import { Warning } from "../../components/Warning";
import { formatDateTime } from "./formatDateTime";

/**
 * Shown on the form when a kept draft couldn't be checked as it opened, so the worker
 * knows it may have run out (spec K2) and that it can't be saved if it has. It goes once
 * any later check gets through.
 */
export function UncheckedNotice({
  startedAt,
  checking,
  onTryAgain,
}: {
  startedAt: string | null | undefined;
  checking: boolean;
  onTryAgain: () => void;
}) {
  return (
    <div role="status">
      <Warning>
        <p>
          No signal: this Take 5 couldn’t be checked to see if it’s still in
          time.
        </p>
        {startedAt && (
          <p>
            You started it{" "}
            <time dateTime={startedAt}>{formatDateTime(startedAt)}</time>. If it
            has run out, it can’t be saved and you’ll need to start a new one.
          </p>
        )}
        <Button variant="secondary" disabled={checking} onClick={onTryAgain}>
          {checking ? "Checking…" : "Try again"}
        </Button>
      </Warning>
    </div>
  );
}
