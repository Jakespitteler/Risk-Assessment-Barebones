import { useCallback, useEffect, useRef, useState } from "react";
import type { Take5Summary } from "../../api/take5";
import { useFindSaved, useSavedTake5List } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Screen } from "../../components/Screen";
import { UndoBar } from "../../components/UndoBar";
import { formatDateTime } from "./formatDateTime";
import { KeptDraftCard } from "./KeptDraftCard";
import { VerdictTag } from "./VerdictTag";
import type { StoredDraft } from "./useTake5Draft";
import { forgetKeptDraft, keptDraft } from "./useTake5Draft";

const HEADING = "text-3xl font-extrabold focus:outline-none";
// The way to today's ranking (spec W7, decision D93), quieter than starting a Take 5.
const TODAY_LINK =
  "flex min-h-14 items-center justify-center rounded-xl border-2 border-ink bg-surface px-5 text-lg font-bold text-ink hover:bg-surface-hover focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus";
const NEW_TAKE5_LINK =
  "flex min-h-14 items-center justify-center rounded-xl bg-action px-5 text-lg font-bold text-on-action hover:bg-action-hover focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus";

/** Marks a Don't start yet that a newer Take 5 fixes, so it isn't taken as still open. */
function FixedTag() {
  return (
    <span className="rounded-lg border-2 border-success px-2 py-0.5 text-sm font-bold text-success uppercase">
      Fixed
    </span>
  );
}

/** One saved Take 5 in the list. The whole card is the link, for a gloved thumb. */
function SavedTake5Item({ take5 }: { take5: Take5Summary }) {
  return (
    <li>
      <a
        href={`/take5s/${take5.id}`}
        className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-4 [overflow-wrap:anywhere] hover:bg-surface-subtle focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus"
      >
        <span className="flex items-center justify-between gap-2">
          <span className="flex flex-wrap items-center gap-2">
            <VerdictTag canStart={take5.can_start} />
            {take5.fixed && <FixedTag />}
          </span>
          <span aria-hidden="true" className="text-3xl leading-none">
            ›
          </span>
        </span>
        <span className="line-clamp-2 text-lg font-bold">{take5.job}</span>
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

/**
 * The button under the list that loads the next 50 (spec D18 and D84). While they load
 * it says so and can't be pressed again; if the signal drops it says so and tries again.
 */
function ShowMore({
  loading,
  failed,
  onShowMore,
}: {
  loading: boolean;
  failed: boolean;
  onShowMore: () => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      {failed && !loading && (
        <p role="status" className="font-semibold text-danger">
          Couldn’t load more. Check your signal and try again.
        </p>
      )}
      <Button variant="secondary" disabled={loading} onClick={onShowMore}>
        {loading ? "Loading…" : failed ? "Try again" : "Show more"}
      </Button>
    </div>
  );
}

/**
 * Every saved Take 5, newest first, 50 at a time, with its date, worker, job and
 * verdict, and whether a Don't start yet has been fixed. Opening one shows its result
 * screen, exactly as it was saved. The phone's unfinished Take 5, if it keeps one, is
 * at the top in place of "Start a new Take 5", since there is only ever one. A draft
 * just thrown away can be put back with Undo, until another one is started.
 */
export function SavedTake5sScreen({
  thrownAway = null,
  onUndoThrowAway,
  onDismissUndo,
}: {
  thrownAway?: StoredDraft | null;
  onUndoThrowAway?: (draft: StoredDraft) => void;
  onDismissUndo?: () => void;
}) {
  const list = useSavedTake5List();
  const take5s = list.data?.pages.flatMap((page) => page.take5s) ?? [];
  const [kept, setKept] = useState(keptDraft);
  const [ranOut, setRanOut] = useState<string | null>(null);
  const [savedAlready, setSavedAlready] = useState<string | null>(null);
  const findSaved = useFindSaved();
  const refetchList = list.refetch;
  // A draft that ran out may have been saved, with the answer lost on its way back.
  const throwAwayRunOut = useCallback(
    async (message: string) => {
      const saved = kept ? await findSaved(kept.submissionId) : null;
      forgetKeptDraft();
      setKept(null);
      if (saved) {
        setSavedAlready(saved.take5.id);
        void refetchList();
      } else setRanOut(message);
    },
    [kept, findSaved, refetchList],
  );
  const page = useRef<HTMLDivElement>(null);
  // Only a new heading moves the focus. A failed refresh keeps the list, so the
  // focus stays where the worker left it.
  const shown = list.data ? "list" : list.isLoadingError ? "error" : "loading";
  useEffect(() => {
    page.current?.querySelector("h1")?.focus();
  }, [shown]);

  return (
    <Screen subtitle="Look back">
      <div ref={page} className="flex flex-col gap-6">
        {list.isPending && (
          <h1 tabIndex={-1} className={HEADING}>
            Loading saved Take 5s…
          </h1>
        )}
        {list.isLoadingError && (
          <>
            <h1 tabIndex={-1} className={HEADING}>
              The saved Take 5s couldn’t be loaded
            </h1>
            <p>Check your signal and try again.</p>
            <Button onClick={() => void list.refetch()}>Try again</Button>
          </>
        )}
        {/* A failed refresh keeps the list it already has. */}
        {list.data && (
          <>
            <h1 tabIndex={-1} className={HEADING}>
              Saved Take 5s
            </h1>
            <p>Newest first. Everyone using this app can see them.</p>
            {/* Undo would take the place of a draft started since, so it ends. */}
            {thrownAway && !kept && (
              <UndoBar
                message="Take 5 thrown away."
                onUndo={() => onUndoThrowAway?.(thrownAway)}
                onDismiss={() => onDismissUndo?.()}
              />
            )}
            {/* These appear once the back end answers, so a screen reader announces them. */}
            {savedAlready && (
              <div role="status">
                <Card>
                  <h2 className="text-xl font-bold">
                    Your unfinished Take 5 was saved
                  </h2>
                  <p>
                    It was saved before the signal dropped, so it’s in the list.
                  </p>
                  <a
                    className={NEW_TAKE5_LINK}
                    href={`/take5s/${savedAlready}`}
                  >
                    Open it
                  </a>
                </Card>
              </div>
            )}
            {ranOut && (
              <div role="status">
                <Card>
                  <h2 className="text-xl font-bold">
                    Your unfinished Take 5 has run out
                  </h2>
                  <p>{ranOut}</p>
                </Card>
              </div>
            )}
            {kept ? (
              <KeptDraftCard
                draft={kept.draft}
                onRunOut={(message) => void throwAwayRunOut(message)}
              />
            ) : (
              <a className={NEW_TAKE5_LINK} href="/">
                Start a new Take 5
              </a>
            )}
            {take5s.length > 0 && (
              <>
                <a className={TODAY_LINK} href="/review-today">
                  Today’s review
                </a>
                <a className={TODAY_LINK} href="/risk-by-area">
                  Risk by area
                </a>
              </>
            )}
            {take5s.length === 0 ? (
              <Card>
                <p>No Take 5s have been saved yet.</p>
              </Card>
            ) : (
              <ul className="flex flex-col gap-3">
                {take5s.map((take5) => (
                  <SavedTake5Item key={take5.id} take5={take5} />
                ))}
              </ul>
            )}
            {list.hasNextPage && (
              <ShowMore
                loading={list.isFetchingNextPage}
                failed={list.isFetchNextPageError}
                onShowMore={() => void list.fetchNextPage()}
              />
            )}
          </>
        )}
      </div>
    </Screen>
  );
}
