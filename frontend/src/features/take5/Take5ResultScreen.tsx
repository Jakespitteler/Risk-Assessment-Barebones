import { useEffect, useRef, useState } from "react";
import type { SavedTake5 } from "../../api/take5";
import { ApiError, useSavedTake5 } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { RiskBadge } from "../../components/RiskBadge";
import { Screen } from "../../components/Screen";
import { AnswerSummary } from "./AnswerSummary";
import { ChallengeScreen } from "./ChallengeScreen";
import { ChallengeSummary } from "./ChallengeSummary";
import { FixPanel } from "./FixPanel";
import { formatDateTime } from "./formatDateTime";
import { FromPaperTag } from "./FromPaperTag";
import { HazardSummary } from "./HazardSummary";
import { SavedListLink } from "./SavedListLink";
import { answersHere, forgetUnanswered } from "./unanswered";
import { keptDraft } from "./useTake5Draft";
import { VerdictPanel } from "./VerdictPanel";

const NEW_TAKE5_LINK =
  "flex min-h-14 items-center justify-center rounded-xl bg-action px-5 text-lg font-bold text-on-action hover:bg-action-hover focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus";

/**
 * A saved Take 5 exactly as it was saved: the verdict, the ratings and the controls,
 * the challenge question with its answer, and its link to the Take 5 that fixes it or
 * that it fixes. An unfinished one shows its question instead (spec C6).
 */
export function Take5ResultScreen({
  id,
  onFix,
}: {
  id: string;
  onFix: (take5: SavedTake5) => void;
}) {
  const result = useSavedTake5(id);
  const [unfinished] = useState(() => keptDraft()?.draft ?? null);
  // The phone keeps one draft, which the form opens, so say so rather than "new".
  const newTake5Label = unfinished
    ? "Carry on your Take 5"
    : "Start a new Take 5";
  const page = useRef<HTMLDivElement>(null);
  // Answering the question only swaps the data, so a finished Take 5 moves the focus too.
  const finished = Boolean(result.data?.take5.verdict);
  useEffect(() => {
    page.current?.querySelector("h1")?.focus();
  }, [result.status, finished]);
  // A Take 5 that is finished, or was never saved, has no question left to go back to.
  const finishedOrMissing =
    finished ||
    (result.error instanceof ApiError && result.error.status === 404);
  useEffect(() => {
    if (finishedOrMissing) forgetUnanswered(id);
  }, [finishedOrMissing, id]);

  if (result.isPending)
    return (
      <Screen subtitle="Your Take 5">
        <h1 className="text-3xl font-extrabold">Opening your Take 5…</h1>
      </Screen>
    );
  if (result.isError) {
    const missing =
      result.error instanceof ApiError && result.error.status < 500;
    return (
      <Screen subtitle="Your Take 5">
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
          {newTake5Label}
        </a>
      </Screen>
    );
  }
  const { take5, rating, fixed_by, offers_fix } = result.data;
  if (!take5.verdict || !take5.finished_at)
    return (
      <ChallengeScreen
        key={take5.id}
        take5={take5}
        canAnswer={answersHere(take5.id)}
        onOutOfDate={() => void result.refetch()}
      />
    );
  const details = [
    { term: "Worker", value: take5.worker_name },
    { term: "Job", value: take5.job },
    { term: "Location", value: take5.location },
  ];
  return (
    <Screen subtitle="Your Take 5" aside={<SavedListLink />}>
      <div ref={page} className="flex flex-col gap-6">
        {take5.from_paper && (
          <p>
            <FromPaperTag />
          </p>
        )}
        <VerdictPanel verdict={take5.verdict} />
        <FixPanel
          take5={take5}
          fixedBy={fixed_by}
          offersFix={offers_fix}
          unfinished={unfinished}
          onFix={() => {
            onFix(take5);
          }}
        />
        <Card>
          <h2 className="text-xl font-bold">Overall risk after controls</h2>
          {rating ? (
            <RiskBadge score={rating.score} band={rating.band} />
          ) : (
            <p>Not rated</p>
          )}
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
                  {formatDateTime(take5.finished_at)}
                </time>
              </dd>
            </div>
          </dl>
        </Card>
        {take5.challenge && <ChallengeSummary challenge={take5.challenge} />}
        <AnswerSummary
          questions={take5.template.questions}
          answers={take5.answers}
          hazards={take5.hazards}
        />
        {take5.hazards.map((hazard, index) => (
          <HazardSummary key={index} hazard={hazard} number={index + 1} />
        ))}
        <p>
          Filled in on the {take5.template.name}. It is kept as it was saved.
        </p>
        <a className={NEW_TAKE5_LINK} href="/">
          {newTake5Label}
        </a>
      </div>
    </Screen>
  );
}
