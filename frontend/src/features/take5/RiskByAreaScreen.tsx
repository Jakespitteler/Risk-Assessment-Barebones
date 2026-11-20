import { useEffect, useRef, useState } from "react";
import type { AreaRisk } from "../../api/take5";
import { useRiskByArea } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Screen } from "../../components/Screen";
import { SavedListLink } from "./SavedListLink";

const HEADING = "text-3xl font-extrabold focus:outline-none";

/** Midnight today where the phone is, so the back end counts 30 days from there (A2). */
function midnightToday(): string {
  const midnight = new Date();
  midnight.setHours(0, 0, 0, 0);
  return midnight.toISOString();
}

/** "1 Take 5" or "3 Take 5s". */
function take5s(count: number): string {
  return `${String(count)} Take 5${count === 1 ? "" : "s"}`;
}

/** "1 thought gap" or "4 thought gaps". */
function gaps(count: number): string {
  return `${String(count)} thought gap${count === 1 ? "" : "s"}`;
}

/**
 * One area: its name, a bar as long as its high-risk count beside the hottest's, and
 * what its Take 5s show (A3 to A5). The bar only repeats the words, so it is hidden
 * from screen readers.
 */
function AreaItem({ area, hottest }: { area: AreaRisk; hottest: number }) {
  const share = hottest === 0 ? 0 : area.high_risk_count / hottest;
  return (
    <li className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-4 [overflow-wrap:anywhere]">
      <h2 className="text-xl font-extrabold">{area.name}</h2>
      <div
        aria-hidden="true"
        className="h-3 overflow-hidden rounded-full bg-surface-subtle"
      >
        <div
          className="h-full rounded-full bg-danger-fill"
          style={{ width: `${String(Math.round(share * 100))}%` }}
        />
      </div>
      <p className="text-lg font-bold">
        {area.high_risk_count} of {take5s(area.take5_count)} high risk
      </p>
      <p>
        Highest risk {area.highest_score} {area.highest_band}.{" "}
        {area.dont_start_count} “Don’t start yet”,{" "}
        {gaps(area.thought_gap_count)}.
      </p>
      {area.common_yes.length > 0 && (
        <div className="flex flex-col gap-1">
          <h3 className="font-bold">Answered Yes most often</h3>
          <ul className="flex flex-col gap-1">
            {area.common_yes.map((yes) => (
              <li key={yes.question}>
                {yes.question} ({yes.count})
              </li>
            ))}
          </ul>
        </div>
      )}
    </li>
  );
}

/**
 * Every area with a Take 5 in the last 30 days, hottest first: the most Take 5s with
 * a hazard that needed a JHA before controls (spec A1 to A5).
 */
export function RiskByAreaScreen() {
  const [today] = useState(midnightToday);
  const risk = useRiskByArea(today);
  const areas = risk.data?.areas ?? [];
  const hottest = Math.max(0, ...areas.map((area) => area.high_risk_count));

  const page = useRef<HTMLDivElement>(null);
  const shown = risk.data ? "list" : risk.isError ? "error" : "loading";
  useEffect(() => {
    page.current?.querySelector("h1")?.focus();
  }, [shown]);

  return (
    <Screen subtitle="Look back" aside={<SavedListLink />}>
      <div ref={page} className="flex flex-col gap-6">
        {risk.isPending && (
          <h1 tabIndex={-1} className={HEADING}>
            Grouping Take 5s by area…
          </h1>
        )}
        {risk.isError && (
          <>
            <h1 tabIndex={-1} className={HEADING}>
              Risk by area couldn’t be worked out
            </h1>
            <p>Check your signal and try again.</p>
            <Button onClick={() => void risk.refetch()}>Try again</Button>
          </>
        )}
        {risk.data && (
          <>
            <h1 tabIndex={-1} className={HEADING}>
              Risk by area
            </h1>
            {areas.length === 0 ? (
              <Card>
                <p>No Take 5s have been started in the last 30 days.</p>
              </Card>
            ) : (
              <>
                <p>
                  Where the jobs were in the last 30 days, as workers typed it,
                  hottest first. A Take 5 is high risk when a hazard needed a
                  JHA before controls.
                </p>
                <ol className="flex flex-col gap-3">
                  {areas.map((area) => (
                    <AreaItem key={area.name} area={area} hottest={hottest} />
                  ))}
                </ol>
              </>
            )}
          </>
        )}
      </div>
    </Screen>
  );
}
