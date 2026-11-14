import { useEffect, useEffectEvent } from "react";
import type { FieldError, FieldWarning, Take5Draft } from "../../api/take5";
import { useDraftCheck } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Notice } from "../../components/Notice";
import { Warning } from "../../components/Warning";
import { HazardSummary } from "./HazardSummary";

/**
 * Step 4: the worker's answers, rated by the back end. If anything is missing, the
 * worker is sent to the page where it is. Each warning the back end sends is shown on
 * its hazard. The only kind for now is a hazard with no controls, so its button opens
 * that hazard's controls. A warning never stops the worker finishing.
 */
export function ReviewPage({
  draft,
  onGaps,
  onOpenWarning,
}: {
  draft: Take5Draft;
  onGaps: (errors: FieldError[]) => void;
  onOpenWarning: (warning: FieldWarning) => void;
}) {
  const check = useDraftCheck(draft);
  const gaps = check.data && !check.data.can_submit ? check.data.errors : null;
  const reportGaps = useEffectEvent(onGaps);
  useEffect(() => {
    if (gaps) reportGaps(gaps);
  }, [gaps]);

  if (check.isError)
    return (
      <Notice>
        <p>
          Your answers couldn’t be checked. Check your signal and try again.
        </p>
        <Button onClick={() => void check.refetch()}>Try again</Button>
      </Notice>
    );
  const assessment = check.data?.assessment;
  if (!assessment) return <p role="status">Checking your answers…</p>;
  const warnings = check.data?.warnings ?? [];
  const details = [
    { term: "Name", value: draft.worker_name },
    { term: "Job", value: draft.job },
    { term: "Location", value: draft.location },
  ];
  return (
    <div className="flex flex-col gap-4">
      {draft.fixes && (
        <p className="rounded-xl border-2 border-slate-400 bg-white p-4">
          This is a copy of a Take 5 that said Don’t start yet. Fix what it
          said, then finish. The first one stays saved as it was.
        </p>
      )}
      <Card>
        <h2 className="text-xl font-bold">The job</h2>
        <dl className="flex flex-col gap-2">
          {details.map(({ term, value }) => (
            <div key={term}>
              <dt className="font-bold">{term}</dt>
              <dd>{value.trim()}</dd>
            </div>
          ))}
        </dl>
      </Card>
      {assessment.hazards.map((hazard, index) => (
        <HazardSummary key={index} hazard={hazard} number={index + 1}>
          {warnings
            .filter((warning) =>
              warning.path.startsWith(`hazards.${String(index)}.`),
            )
            .map((warning) => (
              <Warning key={warning.path}>
                <p>{warning.message}</p>
                <Button
                  variant="secondary"
                  onClick={() => {
                    onOpenWarning(warning);
                  }}
                >
                  Add a control
                </Button>
              </Warning>
            ))}
        </HazardSummary>
      ))}
      <p>
        Read your answers against the job in front of you. Go back if anything
        needs changing.
      </p>
    </div>
  );
}
