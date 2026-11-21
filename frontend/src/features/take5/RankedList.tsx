import { useState } from "react";
import type { RankedTake5Line } from "../../api/take5";
import { Button } from "../../components/Button";
import { formatDateTime } from "./formatDateTime";
import { VerdictTag } from "./VerdictTag";

// The worst few show first; the rest wait for "Show all" (decision D92).
const FIRST_SHOWN = 5;

/**
 * Take 5s worst first, numbered from 1, each with one line saying why (spec W1 to W7).
 * The worst 5 show first, then "Show all" for the rest in order. Today's review and
 * a scanned batch (F10) both draw it.
 */
export function RankedList({ take5s }: { take5s: RankedTake5Line[] }) {
  const [showAll, setShowAll] = useState(false);
  const shown = showAll ? take5s : take5s.slice(0, FIRST_SHOWN);
  return (
    <>
      <ol className="flex flex-col gap-3">
        {shown.map((take5, index) => (
          <RankedItem key={take5.id} take5={take5} place={index + 1} />
        ))}
      </ol>
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
  );
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
