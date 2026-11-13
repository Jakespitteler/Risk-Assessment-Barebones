import { useEffect, useState } from "react";
import type { HazardDraft, Take5Draft } from "../../api/take5";
import { newSubmissionId } from "../../api/submissionId";

const WORKER_NAME_KEY = "take5-worker-name";
const DRAFT_KEY = "take5-draft";

interface StoredDraft {
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
  const stored = read(() => sessionStorage, DRAFT_KEY);
  return stored ? (JSON.parse(stored) as StoredDraft) : null;
}

/**
 * The Take 5 being filled in, kept in this tab's session storage so a reload or a slip
 * of the back gesture loses nothing. Its submission ID is kept with it, so a retry after
 * a lost answer sends the same ID. A removal can be undone.
 */
export function useTake5Draft() {
  const [stored] = useState(storedDraft);
  const [draft, setDraft] = useState<Take5Draft>(
    () =>
      stored?.draft ?? {
        worker_name: read(() => localStorage, WORKER_NAME_KEY) ?? "",
        job: "",
        location: "",
        hazards: [blankHazard()],
      },
  );
  const [submissionId] = useState(
    () => stored?.submissionId ?? newSubmissionId(),
  );
  const [removal, setRemoval] = useState<Removal | null>(null);

  useEffect(() => {
    const value: StoredDraft = { draft, submissionId };
    write(() => sessionStorage, DRAFT_KEY, JSON.stringify(value));
  }, [draft, submissionId]);

  return {
    draft,
    submissionId,
    removal,
    change: (update: (current: Take5Draft) => Take5Draft) => {
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
      write(() => sessionStorage, DRAFT_KEY, null);
      write(() => localStorage, WORKER_NAME_KEY, workerName);
    },
  };
}

/** Everything `useTake5Draft` gives a component. */
export type Take5DraftState = ReturnType<typeof useTake5Draft>;
