import { useEffect, useRef } from "react";
import type { GroupCounts, PatternSentence } from "../../api/take5";
import { usePatterns } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Screen } from "../../components/Screen";
import { SavedListLink } from "./SavedListLink";

const HEADING = "text-3xl font-extrabold focus:outline-none";
const TABLE_LINK =
  "inline-flex min-h-12 items-center font-semibold underline underline-offset-4 hover:decoration-2 focus-visible:outline-4 focus-visible:outline-focus";
const COUNT_HEADINGS = [
  "Take 5s",
  "High risk",
  "Rushed",
  "Thought gaps",
  "Don’t start yet",
];

/** "1 saved Take 5" or "3 saved Take 5s". */
function savedTake5s(count: number): string {
  return `${String(count)} saved Take 5${count === 1 ? "" : "s"}`;
}

/** The All Take 5s table's address, showing the group a sentence is about (S4). */
function tableLink(sentence: PatternSentence): string {
  return `/take5-table?${new URLSearchParams(sentence.table_filters).toString()}`;
}

/** One pattern: its sentence, with a link to the Take 5s behind it. */
function SentenceItem({ sentence }: { sentence: PatternSentence }) {
  return (
    <li className="flex flex-col gap-1 rounded-2xl border border-l-4 border-line border-l-caution-line bg-surface p-4 [overflow-wrap:anywhere]">
      <p className="text-lg font-bold">{sentence.text}</p>
      <a className={TABLE_LINK} href={tableLink(sentence)}>
        See these Take 5s
      </a>
    </li>
  );
}

/**
 * One grouping's counts as a table: each group's Take 5s and how many showed each main
 * sign (S5). It scrolls sideways inside its box on a narrow phone.
 */
function CountsTable({
  title,
  groupHeading,
  counts,
}: {
  title: string;
  groupHeading: string;
  counts: GroupCounts[];
}) {
  return (
    <div
      className="overflow-x-auto rounded-2xl border border-line bg-surface focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus"
      tabIndex={0}
      role="region"
      aria-label={title}
    >
      <table className="w-full min-w-[34rem] border-collapse text-left">
        <thead className="bg-surface-subtle">
          <tr>
            <th scope="col" className="px-3 py-2 font-bold">
              {groupHeading}
            </th>
            {COUNT_HEADINGS.map((heading) => (
              <th
                key={heading}
                scope="col"
                className="px-3 py-2 text-right font-bold"
              >
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {counts.map((group) => (
            <tr key={group.group} className="border-t border-line">
              <th
                scope="row"
                className="px-3 py-2 font-semibold whitespace-nowrap"
              >
                {group.group}
              </th>
              {[
                group.take5_count,
                group.high_risk_count,
                group.rushed_count,
                group.thought_gaps_count,
                group.stopped_count,
              ].map((count, column) => (
                <td
                  key={COUNT_HEADINGS[column]}
                  className="px-3 py-2 text-right tabular-nums"
                >
                  {count}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** A heading and its counts table. */
function CountsSection({
  title,
  groupHeading,
  counts,
  note,
}: {
  title: string;
  groupHeading: string;
  counts: GroupCounts[];
  note?: string;
}) {
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-xl font-extrabold">{title}</h2>
      <CountsTable title={title} groupHeading={groupHeading} counts={counts} />
      {note && <p className="text-ink-muted">{note}</p>}
    </section>
  );
}

/**
 * When Take 5s go wrong, by month, weekday and time of day (spec S1 to S5): plain
 * sentences found by fixed rules, each with its numbers, and the counts beneath. The
 * back end finds the patterns; this page only draws them.
 */
export function PatternsScreen() {
  const patterns = usePatterns();
  const data = patterns.data;

  const page = useRef<HTMLDivElement>(null);
  const shown = data ? "patterns" : patterns.isError ? "error" : "loading";
  useEffect(() => {
    page.current?.querySelector("h1")?.focus();
  }, [shown]);

  const noTime = data?.no_time_of_day_count ?? 0;

  return (
    <Screen subtitle="Look back" aside={<SavedListLink />}>
      <div ref={page} className="flex flex-col gap-6">
        {patterns.isPending && (
          <h1 tabIndex={-1} className={HEADING}>
            Looking for patterns…
          </h1>
        )}
        {patterns.isError && (
          <>
            <h1 tabIndex={-1} className={HEADING}>
              Patterns couldn’t be worked out
            </h1>
            <p>Check your signal and try again.</p>
            <Button onClick={() => void patterns.refetch()}>Try again</Button>
          </>
        )}
        {data && (
          <>
            <h1 tabIndex={-1} className={HEADING}>
              Patterns over time
            </h1>
            {data.take5_count === 0 ? (
              <Card>
                <p>No Take 5s have been saved yet.</p>
              </Card>
            ) : (
              <>
                <p>
                  When Take 5s go wrong, by month, weekday and time of day, in
                  every saved Take 5. A pattern is shown when something happens
                  much more often in one group than in the rest, with its
                  numbers. Small numbers can be chance, so look at the Take 5s
                  before acting on one.
                </p>
                {data.sentences.length === 0 ? (
                  <Card>
                    <p>
                      No pattern stands out yet in{" "}
                      {savedTake5s(data.take5_count)}.
                    </p>
                  </Card>
                ) : (
                  <ul className="flex flex-col gap-3">
                    {data.sentences.map((sentence) => (
                      <SentenceItem key={sentence.text} sentence={sentence} />
                    ))}
                  </ul>
                )}
                <CountsSection
                  title="By month"
                  groupHeading="Month"
                  counts={data.by_month}
                />
                <CountsSection
                  title="By weekday"
                  groupHeading="Weekday"
                  counts={data.by_weekday}
                />
                <CountsSection
                  title="By time of day"
                  groupHeading="Time of day"
                  counts={data.by_time_of_day}
                  note={
                    noTime > 0
                      ? `${String(noTime)} paper card${noTime === 1 ? " has" : "s have"} no time written on ${noTime === 1 ? "it" : "them"}, so ${noTime === 1 ? "it isn’t" : "they aren’t"} counted here.`
                      : undefined
                  }
                />
              </>
            )}
          </>
        )}
      </div>
    </Screen>
  );
}
