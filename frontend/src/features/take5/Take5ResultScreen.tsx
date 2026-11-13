import { useEffect, useRef } from "react";
import type { SavedTake5 } from "../../api/take5";
import { ApiError, useSavedTake5 } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { RiskBadge } from "../../components/RiskBadge";
import { Screen } from "../../components/Screen";
import { FixPanel } from "./FixPanel";
import { HazardSummary } from "./HazardSummary";
import { VerdictPanel } from "./VerdictPanel";

const NEW_TAKE5_LINK =
  "flex min-h-14 items-center justify-center rounded-xl bg-slate-900 px-5 text-lg font-bold text-white";

/**
 * A saved Take 5 exactly as it was saved: the verdict, the ratings and the controls,
 * and its link to the Take 5 that fixes it or that it fixes.
 */
export function Take5ResultScreen({
  id,
  onFix,
}: {
  id: string;
  onFix: (take5: SavedTake5) => void;
}) {
  const result = useSavedTake5(id);
  const page = useRef<HTMLDivElement>(null);
  useEffect(() => {
    page.current?.querySelector("h1")?.focus();
  }, [result.status]);

  if (result.isPending)
    return (
      <Screen subtitle="Saved Take 5">
        <h1 className="text-3xl font-extrabold">Opening your Take 5…</h1>
      </Screen>
    );
  if (result.isError) {
    const missing =
      result.error instanceof ApiError && result.error.status < 500;
    return (
      <Screen subtitle="Saved Take 5">
        <h1 className="text-3xl font-extrabold">
          {missing
            ? "This Take 5 couldn’t be found"
            : "This Take 5 couldn’t be opened"}
        </h1>
        <p>
          {missing
            ? "Check the address you were given."
            : "Check your signal and try again."}
        </p>
        {!missing && (
          <Button onClick={() => void result.refetch()}>Try again</Button>
        )}
        <a className={NEW_TAKE5_LINK} href="/">
          Start a new Take 5
        </a>
      </Screen>
    );
  }
  const { take5, rating, fixed_by } = result.data;
  const details = [
    { term: "Worker", value: take5.worker_name },
    { term: "Job", value: take5.job },
    { term: "Location", value: take5.location },
  ];
  return (
    <Screen subtitle="Saved Take 5">
      <div ref={page} className="flex flex-col gap-6">
        <VerdictPanel verdict={take5.verdict} />
        <FixPanel
          take5={take5}
          fixedBy={fixed_by}
          onFix={() => {
            onFix(take5);
          }}
        />
        <Card>
          <h2 className="text-xl font-bold">Overall risk after controls</h2>
          <RiskBadge score={rating.score} band={rating.band} />
          <dl className="flex flex-col gap-2">
            {details.map(({ term, value }) => (
              <div key={term}>
                <dt className="font-bold">{term}</dt>
                <dd>{value}</dd>
              </div>
            ))}
            <div>
              <dt className="font-bold">Finished</dt>
              <dd>
                <time dateTime={take5.finished_at}>
                  {new Date(take5.finished_at).toLocaleString()}
                </time>
              </dd>
            </div>
          </dl>
        </Card>
        {take5.hazards.map((hazard, index) => (
          <HazardSummary key={index} hazard={hazard} number={index + 1} />
        ))}
        <p>
          Filled in on the {take5.template.name}. It is kept as it was saved.
        </p>
        <a className={NEW_TAKE5_LINK} href="/">
          Start a new Take 5
        </a>
      </div>
    </Screen>
  );
}
