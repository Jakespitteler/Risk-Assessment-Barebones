import { useEffect, useState } from "react";
import type {
  Hazard,
  HazardDraft,
  SavedTake5,
  Take5Draft,
} from "../../api/take5";
import { newSubmissionId } from "../../api/submissionId";

const WORKER_NAME_KEY = "take5-worker-name";
const DRAFT_KEY = "take5-draft";

// Bump this when the draft's shape changes, so a tab left open across an update starts
// afresh instead of loading answers in the old shape.
const DRAFT_VERSION = 2;

interface StoredDraft {
  version: number;
  draft: Take5Draft;
  submissionId: string;
}

export interface Removal {
  message: string;
  before: Take5Draft;
}

const NOTHING_PICKED = { likelihood: null, consequence: null };

export function blankHazard(): HazardDraft {
  return {
    description: "",
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

function storedDraft(): StoredDraft | null {
  try {
    const stored = JSON.parse(
      read(() => sessionStorage, DRAFT_KEY) ?? "null",
    ) as Partial<StoredDraft> | null;
    const usable =
      stored?.version === DRAFT_VERSION &&
      typeof stored.submissionId === "string" &&
      Array.isArray(stored.draft?.hazards);
    return usable ? (stored as StoredDraft) : null;
  } catch {
    return null;
  }
}

/**
 * Keep a copy of a saved Take 5's answers as this tab's draft, with a new submission ID,
 * so the form opens on it. The saved Take 5 itself is never changed.
 */
export function keepFixDraft(saved: SavedTake5) {
  const value: StoredDraft = {
    version: DRAFT_VERSION,
    draft: fixDraftOf(saved),
    submissionId: newSubmissionId(),
  };
  write(() => sessionStorage, DRAFT_KEY, JSON.stringify(value));
}

/**
 * The Take 5 being filled in, kept in this tab's session storage so a reload or a slip
 * of the back gesture loses nothing. Its submission ID is kept with it, so a retry after
 * a lost answer sends the same ID. A removal can be undone until the next edit.
 */
export function useTake5Draft() {
  const [stored] = useState(storedDraft);
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
  const [removal, setRemoval] = useState<Removal | null>(null);
  const [kept, setKept] = useState(true);

  useEffect(() => {
    if (!kept) return;
    const value: StoredDraft = { version: DRAFT_VERSION, draft, submissionId };
    write(() => sessionStorage, DRAFT_KEY, JSON.stringify(value));
  }, [draft, submissionId, kept]);

  return {
    draft,
    submissionId,
    removal,
    // An edit after a removal ends its undo, so Undo can never wipe newer answers.
    change: (update: (current: Take5Draft) => Take5Draft) => {
      setRemoval(null);
      setDraft(update);
    },
    remove: (message: string, update: (current: Take5Draft) => Take5Draft) => {
      setRemoval({ message, before: draft });
      setDraft(update);
    },
    undoRemoval: () => {
      if (removal) setDraft(removal.before);
      setRemoval(null);
    },
    dismissRemoval: () => {
      setRemoval(null);
    },
    /** Forget the draft once it is saved, and remember the name for next time. */
    saved: (workerName: string) => {
      setKept(false);
      write(() => sessionStorage, DRAFT_KEY, null);
      write(() => localStorage, WORKER_NAME_KEY, workerName);
    },
    /**
     * Stop keeping the draft once its ID belongs to another saved Take 5, so the next
     * Take 5 in this tab starts afresh with a new ID.
     */
    discard: () => {
      setKept(false);
      write(() => sessionStorage, DRAFT_KEY, null);
    },
  };
}

/** Everything `useTake5Draft` gives a component. */
export type Take5DraftState = ReturnType<typeof useTake5Draft>;
