import { useEffect, useRef, useState } from "react";
import type {
  Hazard,
  HazardDraft,
  SavedTake5,
  Take5Draft,
} from "../../api/take5";
import { newSubmissionId } from "../../api/submissionId";
import type { Stage } from "./stage";
import { FIRST_STAGE, sameStage, stepOf } from "./stage";

const WORKER_NAME_KEY = "take5-worker-name";
const DRAFT_KEY = "take5-draft";

// Bump this when the draft's shape changes, so a phone left open across an update starts
// afresh instead of loading answers in the old shape.
const DRAFT_VERSION = 4;

/** The one unfinished Take 5 the phone keeps, until it is saved or thrown away. */
export interface StoredDraft {
  version: number;
  draft: Take5Draft;
  submissionId: string;
  /** The page the worker was on, so carrying on opens where they left it. */
  stage?: Stage;
  /** The furthest of the five steps reached, so the step bar lets the worker jump back to it. */
  furthestStep?: number;
  /** Hazard wordings the worker chose to keep, so their nudge isn't asked again. */
  keptWording?: string[];
}

export interface Removal {
  message: string;
  before: Take5Draft;
}

const NOTHING_PICKED = { likelihood: null, consequence: null };

export function blankHazard(): HazardDraft {
  return {
    description: "",
    weak_controls_reason: "",
    before: { ...NOTHING_PICKED },
    controls: [],
    after: { ...NOTHING_PICKED },
    covers: [],
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
    covers: [...hazard.covers],
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
function keepDraft(stored: StoredDraft) {
  write(() => localStorage, DRAFT_KEY, JSON.stringify(stored));
}

/**
 * Keep a thrown-away draft again, for Undo. A draft started since then stays instead,
 * so Undo can never wipe newer answers.
 */
export function putBackDraft(thrownAway: StoredDraft) {
  if (!keptDraft()) keepDraft(thrownAway);
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
  const [stage, setStage] = useState(stored?.stage);
  // A draft kept before the step bar could be tapped has reached at least its own page.
  const [furthestStep, setFurthestStep] = useState(() =>
    typeof stored?.furthestStep === "number"
      ? stored.furthestStep
      : stepOf(stored?.stage ?? FIRST_STAGE),
  );
  const [keptWording, setKeptWording] = useState<string[]>(
    () => stored?.keptWording ?? [],
  );
  const [removal, setRemoval] = useState<Removal | null>(null);
  const [kept, setKept] = useState(true);
  // Set at once when the draft is saved or thrown away. The state above only changes on
  // the next render, so an effect from a render before then could keep the draft again.
  const forgotten = useRef(false);

  const forget = () => {
    forgotten.current = true;
    setKept(false);
    forgetKeptDraft();
  };

  const current = (): StoredDraft => ({
    version: DRAFT_VERSION,
    draft,
    submissionId,
    stage,
    furthestStep,
    keptWording,
  });
  const started = draft.started_at != null;

  useEffect(() => {
    if (!kept || !started || forgotten.current) return;
    keepDraft({
      version: DRAFT_VERSION,
      draft,
      submissionId,
      stage,
      furthestStep,
      keptWording,
    });
  }, [draft, submissionId, stage, furthestStep, keptWording, kept, started]);

  return {
    draft,
    submissionId,
    removal,
    /** True when the worker chose to keep this hazard wording as it is (spec T6). */
    keptAsIs: (description: string) => keptWording.includes(description.trim()),
    /** Remember that the worker chose to keep this wording, so it isn't asked again. */
    keepWording: (description: string) => {
      const wording = description.trim();
      setKeptWording((current) =>
        current.includes(wording) ? current : [...current, wording],
      );
    },
    /** True once the worker has changed anything, so there is something to keep. */
    started,
    /** The furthest of the five steps this Take 5 has reached, counting from 1. */
    furthestStep,
    /**
     * Remember the page the worker is on, so carrying on later opens it, and how far
     * they have got, so the step bar lets them jump back there.
     */
    keepStage: (shown: Stage) => {
      setStage((previous) =>
        previous && sameStage(previous, shown) ? previous : shown,
      );
      setFurthestStep((previous) => Math.max(previous, stepOf(shown)));
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
    // A hazard carries the questions it is linked to, so removing it removes its links, and
    // Undo puts the hazard and its links back together.
    remove: (message: string, update: (current: Take5Draft) => Take5Draft) => {
      setRemoval({ message, before: draft });
      setDraft(update(draft));
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
      forget();
      write(() => localStorage, WORKER_NAME_KEY, workerName);
    },
    /**
     * Stop keeping the draft: its ID belongs to another saved Take 5, or it has run out.
     * The next Take 5 starts afresh with a new ID.
     */
    discard: () => {
      forget();
    },
    /** Throw the draft away, and return it so that Undo can keep it again. */
    throwAway: (): StoredDraft => {
      forget();
      return current();
    },
  };
}

/** Everything `useTake5Draft` gives a component. */
export type Take5DraftState = ReturnType<typeof useTake5Draft>;
