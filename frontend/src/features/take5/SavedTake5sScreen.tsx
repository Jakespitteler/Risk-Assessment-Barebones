import { useCallback, useEffect, useRef, useState } from "react";
import type { Take5Summary } from "../../api/take5";
import { useSavedTake5List } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Screen } from "../../components/Screen";
import { UndoBar } from "../../components/UndoBar";
import { formatDateTime } from "./formatDateTime";
import { KeptDraftCard } from "./KeptDraftCard";
import type { StoredDraft } from "./useTake5Draft";
import { forgetKeptDraft, keptDraft } from "./useTake5Draft";

const HEADING = "text-3xl font-extrabold focus:outline-none";
const NEW_TAKE5_LINK =
  "flex min-h-14 items-center justify-center rounded-xl bg-slate-900 px-5 text-lg font-bold text-white focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-blue-700";

/** The verdict as a tag, in the same strong colours as the result screen. */
function VerdictTag({ canStart }: { canStart: boolean }) {
  return (
    <span
      className={`rounded-lg px-2 py-1 text-sm font-bold text-white uppercase ${
        canStart ? "bg-green-800" : "bg-red-800"
      }`}
    >
      {canStart ? "Good to go" : "Don’t start yet"}
    </span>
  );
}

/** Marks a Don't start yet that a newer Take 5 fixes, so it isn't taken as still open. */
function FixedTag() {
  return (
    <span className="rounded-lg border-2 border-green-800 px-2 py-0.5 text-sm font-bold text-green-800 uppercase">
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
        className="flex flex-col gap-2 rounded-2xl border border-stone-300 bg-white p-4 [overflow-wrap:anywhere] hover:bg-stone-50 focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
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
          <time dateTime={take5.created_at} className="text-slate-700">
            {formatDateTime(take5.created_at)}
          </time>
        </span>
      </a>
    </li>
  );
}

/**
 * Every saved Take 5, newest first, with its date, worker, job and verdict, and whether a
 * Don't start yet has been fixed. Opening one shows its result screen, exactly as it was
 * saved. The phone's unfinished Take 5, if it keeps one, is at the top in place of
 * "Start a new Take 5", since there is only ever one. A draft just thrown away can be
 * put back with Undo.
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
  const [kept, setKept] = useState(keptDraft);
  const [ranOut, setRanOut] = useState<string | null>(null);
  const throwAwayRunOut = useCallback((message: string) => {
    forgetKeptDraft();
    setKept(null);
    setRanOut(message);
  }, []);
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
            {thrownAway && (
              <UndoBar
                message="Take 5 thrown away."
                onUndo={() => onUndoThrowAway?.(thrownAway)}
                onDismiss={() => onDismissUndo?.()}
              />
            )}
            {ranOut && (
              <Card>
                <h2 className="text-xl font-bold">
                  Your unfinished Take 5 has run out
                </h2>
                <p>{ranOut}</p>
              </Card>
            )}
            {kept ? (
              <KeptDraftCard draft={kept.draft} onRunOut={throwAwayRunOut} />
            ) : (
              <a className={NEW_TAKE5_LINK} href="/">
                Start a new Take 5
              </a>
            )}
            {list.data.length === 0 ? (
              <Card>
                <p>No Take 5s have been saved yet.</p>
              </Card>
            ) : (
              <ul className="flex flex-col gap-3">
                {list.data.map((take5) => (
                  <SavedTake5Item key={take5.id} take5={take5} />
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </Screen>
  );
}
