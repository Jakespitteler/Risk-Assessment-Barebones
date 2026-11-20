import { useEffect, useRef, useState } from "react";
import type { BestTake5Line, RankedTake5Line } from "../../api/take5";
import { useRankedTake5s } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Screen } from "../../components/Screen";
import { formatDateTime } from "./formatDateTime";
import { SavedListLink } from "./SavedListLink";
import { VerdictTag } from "./VerdictTag";

const HEADING = "text-3xl font-extrabold focus:outline-none";
// The worst few show first; the rest wait for "Show all" (decision D92).
const FIRST_SHOWN = 5;

/** Midnight today where the phone is, as a moment the back end can compare (W7). */
function midnightToday(): string {
  const midnight = new Date();
  midnight.setHours(0, 0, 0, 0);
  return midnight.toISOString();
}

/** One ranked Take 5: its place, verdict, job, worker, time and why. The card is the link. */
function RankedItem({
  take5,
  place,
}: {
  take5: RankedTake5Line;
  place: number;
}) {
  return (
    <li>
      <a
        href={`/take5s/${take5.id}`}
        className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-4 [overflow-wrap:anywhere] hover:bg-surface-subtle focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus"
      >
        <span className="flex items-center justify-between gap-2">
          <span className="flex flex-wrap items-center gap-2">
            <span className="text-xl font-extrabold">{place}.</span>
            <VerdictTag canStart={take5.can_start} />
          </span>
          <span aria-hidden="true" className="text-3xl leading-none">
            ›
          </span>
        </span>
        <span className="line-clamp-2 text-lg font-bold">{take5.job}</span>
        <span className="rounded-lg border-l-4 border-caution-line bg-caution-soft px-3 py-2 text-on-caution-soft">
          {take5.line}
        </span>
        <span className="flex flex-col">
          <span>{take5.worker_name}</span>
          <time dateTime={take5.created_at} className="text-ink-muted">
            {formatDateTime(take5.created_at)}
          </time>
        </span>
      </a>
    </li>
  );
}

/** "Took 9 minutes. Today's typical Take 5 took 3 minutes." (spec W9). */
function timeTaken(minutes: number | null, typical: number | null): string {
  const plural = (count: number) =>
    count === 0
      ? "under a minute"
      : `${String(count)} minute${count === 1 ? "" : "s"}`;
  const took = minutes === null ? "" : `Took ${plural(minutes)}. `;
  const usual =
    typical === null ? "" : `Today’s typical Take 5 took ${plural(typical)}.`;
  return `${took}${usual}`.trim();
}

/** The best careful Take 5 of today, with what was good and how long it took (W8). */
function BestCard({
  best,
  typicalMinutes,
}: {
  best: BestTake5Line | null;
  typicalMinutes: number | null;
}) {
  return (
    <section aria-labelledby="best-heading" className="flex flex-col gap-3">
      <h2 id="best-heading" className="text-2xl font-extrabold">
        Best of today
      </h2>
      {best === null ? (
        <Card>
          <p>No Take 5 today was free of signs of little thought.</p>
        </Card>
      ) : (
        <a
          href={`/take5s/${best.id}`}
          className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-4 [overflow-wrap:anywhere] hover:bg-surface-subtle focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus"
        >
          <span className="flex items-center justify-between gap-2">
            <VerdictTag canStart={best.can_start} />
            <span aria-hidden="true" className="text-3xl leading-none">
              ›
            </span>
          </span>
          <span className="line-clamp-2 text-lg font-bold">{best.job}</span>
          <span className="rounded-lg border-l-4 border-success-line bg-success-soft px-3 py-2 text-on-success-soft">
            {best.line}
          </span>
          <span className="flex flex-col">
            <span>{best.worker_name}</span>
            <span className="text-ink-muted">
              {timeTaken(best.minutes_taken, typicalMinutes)}
            </span>
          </span>
        </a>
      )}
    </section>
  );
}

/**
 * Today's best Take 5, then all of them worst first, each with one line saying why
 * (spec W1 to W9). The worst 5 show first, then "Show all" for the rest in order.
 */
export function BestAndWorstScreen() {
  const [since] = useState(midnightToday);
  const ranking = useRankedTake5s(since);
  const [showAll, setShowAll] = useState(false);
  const take5s = ranking.data?.take5s ?? [];
  const shownTake5s = showAll ? take5s : take5s.slice(0, FIRST_SHOWN);
  const byAi =
    take5s.some((take5) => take5.ranked_by_ai) ||
    ranking.data?.best?.picked_by_ai === true;

  const page = useRef<HTMLDivElement>(null);
  const shown = ranking.data ? "list" : ranking.isError ? "error" : "loading";
  useEffect(() => {
    page.current?.querySelector("h1")?.focus();
  }, [shown]);

  return (
    <Screen subtitle="Look back" aside={<SavedListLink />}>
      <div ref={page} className="flex flex-col gap-6">
        {ranking.isPending && (
          <>
            <h1 tabIndex={-1} className={HEADING}>
              Ranking today’s Take 5s…
            </h1>
            <p>This can take up to half a minute.</p>
          </>
        )}
        {ranking.isError && (
          <>
            <h1 tabIndex={-1} className={HEADING}>
              Today’s Take 5s couldn’t be ranked
            </h1>
            <p>Check your signal and try again.</p>
            <Button onClick={() => void ranking.refetch()}>Try again</Button>
          </>
        )}
        {ranking.data && (
          <>
            <h1 tabIndex={-1} className={HEADING}>
              Best and worst of today
            </h1>
            {take5s.length === 0 ? (
              <Card>
                <p>No Take 5s have been started today.</p>
              </Card>
            ) : (
              <>
                <p>
                  The best of today’s Take 5s, to hold up as an example, then
                  all of them worst first: the riskiest jobs with the least
                  thought in the answers. Talk to each worker about the reason
                  given.
                </p>
                {byAi && (
                  <p className="text-ink-muted">
                    An AI helped choose these and wrote their reasons. Names
                    aren’t sent to it.
                  </p>
                )}
                <BestCard
                  best={ranking.data.best}
                  typicalMinutes={ranking.data.typical_minutes}
                />
                <h2 className="text-2xl font-extrabold">Worst first</h2>
              </>
            )}
            {take5s.length > 0 && (
              <ol className="flex flex-col gap-3">
                {shownTake5s.map((take5, index) => (
                  <RankedItem key={take5.id} take5={take5} place={index + 1} />
                ))}
              </ol>
            )}
            {!showAll && take5s.length > FIRST_SHOWN && (
              <Button
                variant="secondary"
                onClick={() => {
                  setShowAll(true);
                }}
              >
                Show all {take5s.length}
              </Button>
            )}
          </>
        )}
      </div>
    </Screen>
  );
}
