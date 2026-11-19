import { useEffect } from "react";
import type { Take5Draft } from "../../api/take5";
import { useOpeningCheck } from "../../api/take5";
import { Card } from "../../components/Card";
import { formatDateTime } from "./formatDateTime";
import { runOutMessage } from "./runOut";
import { TimeLeft } from "./TimeLeft";

const CARRY_ON_LINK =
  "flex min-h-14 items-center justify-center rounded-xl bg-action px-5 text-lg font-bold text-on-action focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus";

/**
 * The phone's unfinished Take 5, at the top of the saved list, with a button to carry on
 * where the worker left it. The back end checks it first; one that has run out is
 * reported to the screen, which throws it away (spec K2).
 */
export function KeptDraftCard({
  draft,
  onRunOut,
}: {
  draft: Take5Draft;
  onRunOut: (message: string) => void;
}) {
  const check = useOpeningCheck(draft, true);
  const ranOut = runOutMessage(check.data?.errors);
  useEffect(() => {
    if (ranOut) onRunOut(ranOut);
  }, [ranOut, onRunOut]);

  const job = draft.job.trim();
  return (
    <Card>
      <h2 className="text-xl font-bold">Your unfinished Take 5</h2>
      <p className="line-clamp-2 text-lg font-bold [overflow-wrap:anywhere]">
        {job || "No job written yet"}
      </p>
      {draft.started_at && (
        <p>
          Started{" "}
          <time dateTime={draft.started_at}>
            {formatDateTime(draft.started_at)}
          </time>
        </p>
      )}
      <TimeLeft runsOutAt={check.data?.runs_out_at} />
      {/* It appears once the check fails, so a screen reader announces it (spec D27). */}
      {check.isError && (
        <p role="status" className="font-semibold">
          No signal: it couldn’t be checked to see if it’s still in time. If it
          has run out, it can’t be saved.
        </p>
      )}
      <a className={CARRY_ON_LINK} href="/">
        Carry on
      </a>
    </Card>
  );
}
