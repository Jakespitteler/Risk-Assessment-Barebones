import { beforeEach, expect, it } from "vitest";
import { SAVED, STOPPED } from "../../test-utils";
import { fixDraftOf, keepFixDraft } from "./useTake5Draft";

beforeEach(() => {
  sessionStorage.clear();
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
        before: { likelihood: "Often", consequence: "Serious" },
        controls: [
          { description: "Chock the wheel", kind: "Isolate the hazard" },
        ],
        after: { likelihood: "Seldom", consequence: "Scratch" },
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

it("keeps the copy as this tab's draft, with a new submission ID", () => {
  keepFixDraft(STOPPED.take5);
  const stored = JSON.parse(sessionStorage.getItem("take5-draft") ?? "{}") as {
    draft: { fixes: string };
    submissionId: string;
  };
  expect(stored.draft.fixes).toBe(STOPPED.take5.id);
  expect(stored.submissionId).not.toBe(STOPPED.take5.id);
  expect(stored.submissionId).toMatch(/^[0-9a-f-]{36}$/);
});

it("starts the copy with no hazard question marked as added to the list", () => {
  sessionStorage.setItem(
    "take5-draft",
    JSON.stringify({
      version: 2,
      draft: fixDraftOf(SAVED.take5),
      submissionId: SAVED.take5.id,
      addedFor: ["dogs"],
    }),
  );
  keepFixDraft(STOPPED.take5);
  const stored = JSON.parse(sessionStorage.getItem("take5-draft") ?? "{}") as {
    addedFor?: string[];
  };
  expect(stored.addedFor).toBeUndefined();
});
