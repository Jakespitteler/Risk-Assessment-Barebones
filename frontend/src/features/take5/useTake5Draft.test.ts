import { beforeEach, expect, it } from "vitest";
import { SAVED, STOPPED } from "../../test-utils";
import {
  fixDraftOf,
  keepFixDraft,
  keptDraft,
  putBackDraft,
} from "./useTake5Draft";

beforeEach(() => {
  localStorage.clear();
});

it("copies every answer of a saved Take 5 and says which one it fixes", () => {
  expect(fixDraftOf(SAVED.take5)).toEqual({
    worker_name: "Sam Example",
    job: "Change tyre",
    location: "Example workshop",
    answers: { keys: "Yes", dogs: "No" },
    hazards: [
      {
        description: "Moving wheel",
        weak_controls_reason: "",
        before: { likelihood: "Often", consequence: "Serious" },
        controls: [
          { description: "Chock the wheel", kind: "Isolate the hazard" },
        ],
        after: { likelihood: "Seldom", consequence: "Scratch" },
        covers: [],
      },
    ],
    fixes: SAVED.take5.id,
  });
});

it("leaves the after rating unpicked for a hazard that had no controls", () => {
  expect(fixDraftOf(STOPPED.take5).hazards[0]?.after).toEqual({
    likelihood: null,
    consequence: null,
  });
});

it("copies each hazard's links to the card's questions into a correction", () => {
  const saved = {
    ...SAVED.take5,
    hazards: SAVED.take5.hazards.map((hazard) => ({
      ...hazard,
      covers: ["dogs"],
    })),
  };
  expect(fixDraftOf(saved).hazards[0]?.covers).toEqual(["dogs"]);
});

it("copies the weak-controls answer into a correction", () => {
  const reason = "Live testing, so the panel can't be isolated";
  const saved = {
    ...SAVED.take5,
    hazards: SAVED.take5.hazards.map((hazard) => ({
      ...hazard,
      weak_controls_reason: reason,
    })),
  };
  expect(fixDraftOf(saved).hazards[0]?.weak_controls_reason).toBe(reason);
});

it("keeps the copy as the phone's draft, with a new submission ID and a start time", () => {
  keepFixDraft(STOPPED.take5);
  const stored = JSON.parse(localStorage.getItem("take5-draft") ?? "{}") as {
    draft: { fixes: string };
    submissionId: string;
  };
  expect(stored.draft.fixes).toBe(STOPPED.take5.id);
  expect(stored.submissionId).not.toBe(STOPPED.take5.id);
  expect(stored.submissionId).toMatch(/^[0-9a-f-]{36}$/);
  expect(keptDraft()?.draft.started_at).toMatch(/^\d{4}-\d\d-\d\dT.*Z$/);
});

it("starts the copy with no hazard question marked as added to the list", () => {
  localStorage.setItem(
    "take5-draft",
    JSON.stringify({
      version: 4,
      draft: { ...fixDraftOf(SAVED.take5), started_at: "2026-11-15T12:12:00Z" },
      submissionId: SAVED.take5.id,
      addedFor: ["dogs"],
    }),
  );
  keepFixDraft(STOPPED.take5);
  const stored = JSON.parse(localStorage.getItem("take5-draft") ?? "{}") as {
    addedFor?: string[];
  };
  expect(stored.addedFor).toBeUndefined();
});

it("puts a thrown-away draft back for Undo, but never over a newer one", () => {
  const thrownAway = {
    version: 4,
    draft: { ...fixDraftOf(SAVED.take5), started_at: "2026-11-15T09:12:00Z" },
    submissionId: SAVED.take5.id,
  };
  putBackDraft(thrownAway);
  expect(keptDraft()).toEqual(thrownAway);

  const newer = {
    ...thrownAway,
    draft: { ...thrownAway.draft, job: "Grease the conveyor" },
    submissionId: STOPPED.take5.id,
  };
  localStorage.setItem("take5-draft", JSON.stringify(newer));
  putBackDraft(thrownAway);
  expect(keptDraft()).toEqual(newer);
});
