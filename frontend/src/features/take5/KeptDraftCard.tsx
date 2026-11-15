import { useEffect } from "react";
import type { Take5Draft } from "../../api/take5";
import { useDraftCheck } from "../../api/take5";
import { Card } from "../../components/Card";
import { formatDateTime } from "./formatDateTime";
import { runOutMessage } from "./runOut";

const CARRY_ON_LINK =
  "flex min-h-14 items-center justify-center rounded-xl bg-slate-900 px-5 text-lg font-bold text-white focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-blue-700";

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
  const check = useDraftCheck(draft);
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
      <a className={CARRY_ON_LINK} href="/">
        Carry on
      </a>
    </Card>
  );
}
