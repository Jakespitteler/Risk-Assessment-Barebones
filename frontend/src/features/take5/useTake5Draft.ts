import { useEffect, useState } from "react";
import type {
  Hazard,
  HazardDraft,
  SavedTake5,
  Take5Draft,
} from "../../api/take5";
import { newSubmissionId } from "../../api/submissionId";
import type { Stage } from "./stage";
import { sameStage } from "./stage";

const WORKER_NAME_KEY = "take5-worker-name";
const DRAFT_KEY = "take5-draft";

// Bump this when the draft's shape changes, so a phone left open across an update starts
// afresh instead of loading answers in the old shape.
const DRAFT_VERSION = 3;

/** The one unfinished Take 5 the phone keeps, until it is saved or thrown away. */
export interface StoredDraft {
  version: number;
  draft: Take5Draft;
  submissionId: string;
  /** The hazard questions a hazard was added from, so their Yes shows it was done. */
  addedFor?: string[];
  /** The page the worker was on, so carrying on opens where they left it. */
  stage?: Stage;
}

export interface Removal {
  message: string;
  before: Take5Draft;
  addedForBefore: string[];
}

const NOTHING_PICKED = { likelihood: null, consequence: null };

export function blankHazard(): HazardDraft {
  return {
    description: "",
    weak_controls_reason: "",
    before: { ...NOTHING_PICKED },
    controls: [],
    after: { ...NOTHING_PICKED },
  };
}

/** A saved hazard as a draft again. With no controls it was never rated after them. */
function hazardDraftOf(hazard: Hazard): HazardDraft {
  const { likelihood, consequence } = hazard.after;
  return {
    description: hazard.description,
    weak_controls_reason: hazard.weak_controls_reason,
    before: {
      likelihood: hazard.before.likelihood,
      consequence: hazard.before.consequence,
    },
    controls: hazard.controls.map(({ description, kind }) => ({
      description,
      kind,
    })),
    after: hazard.controls.length
      ? { likelihood, consequence }
      : { ...NOTHING_PICKED },
  };
}

/** A new draft holding a saved Take 5's answers, which says it fixes that Take 5. */
export function fixDraftOf(saved: SavedTake5): Take5Draft {
  return {
    worker_name: saved.worker_name,
    job: saved.job,
    location: saved.location,
    answers: { ...saved.answers },
    hazards: saved.hazards.map(hazardDraftOf),
    fixes: saved.id,
  };
}

// Storage can be switched off on a phone, so every read and write may fail.
function read(storage: () => Storage, key: string): string | null {
  try {
    return storage().getItem(key);
  } catch {
    return null;
  }
}

function write(storage: () => Storage, key: string, value: string | null) {
  try {
    if (value === null) storage().removeItem(key);
    else storage().setItem(key, value);
  } catch {
    /* The draft still works; it just won't survive a reload. */
  }
}

/** The time now, as the phone's clock says, in the form the back end reads. */
function now(): string {
  return new Date().toISOString();
}

/**
 * The unfinished Take 5 the phone is keeping, or null. A draft only counts once the
 * worker has changed something, which is when its clock starts.
 */
export function keptDraft(): StoredDraft | null {
  try {
    const stored = JSON.parse(
      read(() => localStorage, DRAFT_KEY) ?? "null",
    ) as Partial<StoredDraft> | null;
    const usable =
      stored?.version === DRAFT_VERSION &&
      typeof stored.submissionId === "string" &&
      Array.isArray(stored.draft?.hazards) &&
      typeof stored.draft.started_at === "string";
    return usable ? (stored as StoredDraft) : null;
  } catch {
    return null;
  }
}

/** Keep this draft as the phone's unfinished Take 5, in place of any other. */
export function keepDraft(stored: StoredDraft) {
  write(() => localStorage, DRAFT_KEY, JSON.stringify(stored));
}

/** Stop keeping the phone's unfinished Take 5. */
export function forgetKeptDraft() {
  write(() => localStorage, DRAFT_KEY, null);
}

/**
 * Keep a copy of a saved Take 5's answers as the phone's draft, with a new submission ID,
 * so the form opens on it. Its clock starts now. The saved Take 5 itself is never changed.
 */
export function keepFixDraft(saved: SavedTake5) {
  keepDraft({
    version: DRAFT_VERSION,
    draft: { ...fixDraftOf(saved), started_at: now() },
    submissionId: newSubmissionId(),
  });
}

/**
 * The Take 5 being filled in. Once the worker changes anything it is kept on the phone,
 * so a reload, a slip of the back gesture or closing the app loses nothing, until it is
 * saved or thrown away. Its submission ID is kept with it, so a retry after a lost answer
 * sends the same ID. A removal can be undone until the next edit.
 */
export function useTake5Draft() {
  const [stored] = useState(keptDraft);
  const [draft, setDraft] = useState<Take5Draft>(
    () =>
      stored?.draft ?? {
        worker_name: read(() => localStorage, WORKER_NAME_KEY) ?? "",
        job: "",
        location: "",
        answers: {},
        hazards: [blankHazard()],
      },
  );
  const [submissionId] = useState(
    () => stored?.submissionId ?? newSubmissionId(),
  );
  const [addedFor, setAddedFor] = useState<string[]>(
    () => stored?.addedFor ?? [],
  );
  const [stage, setStage] = useState(stored?.stage);
  const [removal, setRemoval] = useState<Removal | null>(null);
  const [kept, setKept] = useState(true);

  const current = (): StoredDraft => ({
    version: DRAFT_VERSION,
    draft,
    submissionId,
    addedFor,
    stage,
  });
  const started = draft.started_at != null;

  useEffect(() => {
    if (!kept || !started) return;
    keepDraft({ version: DRAFT_VERSION, draft, submissionId, addedFor, stage });
  }, [draft, submissionId, addedFor, stage, kept, started]);

  return {
    draft,
    submissionId,
    removal,
    addedFor,
    /** True once the worker has changed anything, so there is something to keep. */
    started,
    /** Remember the page the worker is on, so carrying on later opens it. */
    keepStage: (shown: Stage) => {
      setStage((previous) =>
        previous && sameStage(previous, shown) ? previous : shown,
      );
    },
    /** Remember that a hazard was added from this hazard question. */
    markAdded: (questionId: string) => {
      setAddedFor((current) =>
        current.includes(questionId) ? current : [...current, questionId],
      );
    },
    // An edit after a removal ends its undo, so Undo can never wipe newer answers.
    // The first change starts the draft's clock (spec K2).
    change: (update: (current: Take5Draft) => Take5Draft) => {
      setRemoval(null);
      setDraft((previous) => {
        const changed = update(previous);
        return changed.started_at ? changed : { ...changed, started_at: now() };
      });
    },
    // A hazard isn't tied to the question it came from, so removing any hazard forgets
    // every mark: each Yes then reminds the worker again until Undo puts them back.
    remove: (message: string, update: (current: Take5Draft) => Take5Draft) => {
      const after = update(draft);
      setRemoval({ message, before: draft, addedForBefore: addedFor });
      if (after.hazards.length < draft.hazards.length) setAddedFor([]);
      setDraft(after);
    },
    undoRemoval: () => {
      if (removal) {
        setDraft(removal.before);
        setAddedFor(removal.addedForBefore);
      }
      setRemoval(null);
    },
    dismissRemoval: () => {
      setRemoval(null);
    },
    /** Forget the draft once it is saved, and remember the name for next time. */
    saved: (workerName: string) => {
      setKept(false);
      forgetKeptDraft();
      write(() => localStorage, WORKER_NAME_KEY, workerName);
    },
    /**
     * Stop keeping the draft: its ID belongs to another saved Take 5, or it has run out.
     * The next Take 5 starts afresh with a new ID.
     */
    discard: () => {
      setKept(false);
      forgetKeptDraft();
    },
    /** Throw the draft away, and return it so that Undo can keep it again. */
    throwAway: (): StoredDraft => {
      setKept(false);
      forgetKeptDraft();
      return current();
    },
  };
}

/** Everything `useTake5Draft` gives a component. */
export type Take5DraftState = ReturnType<typeof useTake5Draft>;
