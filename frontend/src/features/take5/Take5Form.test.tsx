import type { Take5Draft } from "../../api/take5";
import { onlineManager } from "@tanstack/react-query";
import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  COMPLETE_DRAFT,
  HAZARD_DRAFT,
  PASSING_CHECK,
  SAVED,
  SMALL_TEMPLATE,
  UNANSWERED,
  renderWithApi,
  stubApi,
  stubPointer,
} from "../../test-utils";
import type { Stage } from "./stage";
import { Take5Form } from "./Take5Form";
import { answersHere } from "./unanswered";
import type { StoredDraft } from "./useTake5Draft";

const onSaved = vi.fn<(id: string) => void>();
// Each page the form moved to, and whether it replaced the page before it.
let moves: { page: string; replace: boolean }[] = [];

// Stands in for the router: the stage is kept in state instead of the URL.
const onLeave = vi.fn<(thrownAway: StoredDraft | null) => void>();
const onStartAfresh = vi.fn<() => void>();
// A start time a few minutes before the tests run, so a kept draft hasn't run out.
const STARTED_AT = new Date(Date.now() - 5 * 60_000).toISOString();

function FormAt({ start }: { start: Stage }) {
  const [stage, setStage] = useState(start);
  return (
    <Take5Form
      template={SMALL_TEMPLATE}
      stage={stage}
      onStageChange={(to, options) => {
        moves.push({ page: to.page, replace: options?.replace ?? false });
        setStage(to);
      }}
      onBack={setStage}
      onSaved={onSaved}
      onLeave={onLeave}
      onStartAfresh={onStartAfresh}
    />
  );
}

function storeDraft(draft = COMPLETE_DRAFT, keptWording?: string[]) {
  localStorage.setItem(
    "take5-draft",
    JSON.stringify({
      version: 4,
      draft: { started_at: STARTED_AT, ...draft },
      submissionId: SAVED.take5.id,
      keptWording,
    }),
  );
}

/** Press Submit once the review's check has come back and enabled it. */
async function clickSubmit() {
  const button = await screen.findByRole<HTMLButtonElement>("button", {
    name: "Submit Take 5",
  });
  await waitFor(() => {
    expect(button.disabled).toBe(false);
  });
  fireEvent.click(button);
}

beforeEach(() => {
  localStorage.clear();
  onSaved.mockReset();
  onLeave.mockReset();
  onStartAfresh.mockReset();
  moves = [];
});
afterEach(() => {
  vi.unstubAllGlobals();
  onlineManager.setOnline(true);
});

it("starts with nothing filled in but the remembered name, and the heading focused", () => {
  localStorage.setItem("take5-worker-name", "Sam Example");
  stubApi({});
  renderWithApi(<FormAt start={{ page: "job" }} />);
  expect(screen.getByLabelText<HTMLInputElement>("Your name").value).toBe(
    "Sam Example",
  );
  expect(
    screen.getByLabelText<HTMLTextAreaElement>("What is the job?").value,
  ).toBe("");
  expect(document.activeElement).toBe(
    screen.getByRole("heading", { level: 1 }),
  );
});

it("on a computer, puts the cursor in the first empty box as a page opens", () => {
  stubPointer("fine");
  localStorage.setItem("take5-worker-name", "Sam Example");
  stubApi({});
  renderWithApi(<FormAt start={{ page: "job" }} />);
  expect(document.activeElement).toBe(
    screen.getByLabelText("What is the job?"),
  );
});

it("on a computer, opens control 1 with the cursor in it", () => {
  stubPointer("fine");
  storeDraft({
    ...COMPLETE_DRAFT,
    hazards: [{ ...HAZARD_DRAFT, controls: [] }],
  });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "controls", hazard: 0 }} />);
  expect(document.activeElement).toBe(
    screen.getByLabelText("What will you do?"),
  );
});

it("leaves control 1 open and empty when the only control is removed, and Undo puts it back", () => {
  storeDraft();
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "controls", hazard: 0 }} />);
  fireEvent.click(screen.getByRole("button", { name: "Remove control 1" }));
  expect(
    screen.getByLabelText<HTMLTextAreaElement>("What will you do?").value,
  ).toBe("");
  expect(screen.queryByRole("button", { name: "Remove control 1" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Undo" }));
  expect(
    screen.getByLabelText<HTMLTextAreaElement>("What will you do?").value,
  ).toBe("Chock the wheel");
  expect(screen.getByRole("button", { name: "Remove control 1" })).toBeTruthy();
});

it("on a computer, focuses the heading when every box is filled in", () => {
  stubPointer("fine");
  storeDraft();
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "job" }} />);
  expect(document.activeElement).toBe(
    screen.getByRole("heading", { level: 1 }),
  );
});

it("on a phone, focuses the heading so the keyboard stays down", () => {
  stubPointer("coarse");
  stubApi({});
  renderWithApi(<FormAt start={{ page: "job" }} />);
  expect(document.activeElement).toBe(
    screen.getByRole("heading", { level: 1 }),
  );
});

it("starts afresh instead of loading a draft kept before the card had questions", () => {
  // JSON leaves out an undefined field, so this is the old shape, with no answers.
  const oldDraft = { ...COMPLETE_DRAFT, answers: undefined };
  localStorage.setItem(
    "take5-draft",
    JSON.stringify({
      version: 1,
      draft: oldDraft,
      submissionId: SAVED.take5.id,
    }),
  );
  stubApi({});
  renderWithApi(<FormAt start={{ page: "job" }} />);
  expect(
    screen.getByLabelText<HTMLTextAreaElement>("What is the job?").value,
  ).toBe("");
});

it("keeps the worker on a page with gaps, shows them, and focuses the first", async () => {
  stubApi({
    "POST /api/take5s/check": {
      status: 200,
      body: {
        errors: [
          { path: "job", message: "Fill in this field." },
          { path: "hazards.0.description", message: "Fill in this field." },
        ],
        assessment: null,
        can_submit: false,
      },
    },
  });
  renderWithApi(<FormAt start={{ page: "job" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  const job = screen.getByLabelText("What is the job?");
  await waitFor(() => {
    expect(document.activeElement).toBe(job);
  });
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
    "The job in front of you",
  );
  // Only this page's gaps are shown here.
  expect(screen.getAllByText("Fill in this field.")).toHaveLength(1);
});

it("moves on when the page has no gaps", async () => {
  storeDraft();
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "job" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(
    await screen.findByRole("heading", { name: "Think it through" }),
  ).toBeTruthy();
});

it("moves on when the page is submitted, as Enter in a box does", async () => {
  storeDraft();
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "job" }} />);
  const location = screen.getByLabelText<HTMLInputElement>(
    "Where will you do it?",
  );
  fireEvent.submit(location.form as HTMLFormElement);
  expect(
    await screen.findByRole("heading", { name: "Think it through" }),
  ).toBeTruthy();
});

it("puts a removed hazard back on Undo", () => {
  storeDraft();
  stubApi({});
  renderWithApi(<FormAt start={{ page: "hazards" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Remove hazard 1" }));
  expect(screen.queryByLabelText("Hazard 1")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Undo" }));
  expect(screen.getByLabelText<HTMLTextAreaElement>("Hazard 1").value).toBe(
    "Moving wheel",
  );
});

it("saves, forgets the draft, remembers the name and opens the result", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
    "POST /api/take5s": { status: 200, body: SAVED },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  await clickSubmit();
  await waitFor(() => {
    expect(onSaved).toHaveBeenCalledWith(SAVED.take5.id);
  });
  expect(localStorage.getItem("take5-draft")).toBeNull();
  expect(localStorage.getItem("take5-worker-name")).toBe("Sam Example");
  // A retry that finds it already answered has no question left to go back to.
  expect(answersHere(SAVED.take5.id)).toBe(false);
});

it("remembers an unanswered Take 5, so only this phone answers it", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
    "POST /api/take5s": { status: 200, body: UNANSWERED },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  await clickSubmit();
  await waitFor(() => {
    expect(onSaved).toHaveBeenCalledWith(UNANSWERED.take5.id);
  });
  expect(answersHere(UNANSWERED.take5.id)).toBe(true);
});

it("sends the worker to the gap the back end found on Submit", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
    "POST /api/take5s": {
      status: 422,
      body: {
        detail: "Fill in the highlighted fields before you submit.",
        errors: [
          {
            path: "hazards.0.controls.0.kind",
            message: "Pick a control kind.",
          },
        ],
      },
    },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  await clickSubmit();
  expect(
    await screen.findByRole("heading", { name: "What will stop it?" }),
  ).toBeTruthy();
  expect(screen.getByText("Pick a control kind.")).toBeTruthy();
});

it("offers the saved Take 5 when its ID was used for other answers", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
    "POST /api/take5s": {
      status: 409,
      body: { detail: "This Take 5 was already saved with different answers." },
    },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  await clickSubmit();
  expect(
    await screen.findByRole("link", { name: "Open the saved Take 5" }),
  ).toBeTruthy();
});

it("moves on with no signal, even when the phone says it is offline", async () => {
  storeDraft();
  stubApi({ "POST /api/take5s/check": "offline" });
  onlineManager.setOnline(false);
  renderWithApi(<FormAt start={{ page: "job" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(
    await screen.findByRole("heading", { name: "Think it through" }),
  ).toBeTruthy();
});

it("keeps Submit disabled when the review couldn't be checked", async () => {
  storeDraft();
  stubApi({ "POST /api/take5s/check": "offline" });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  expect(await screen.findByRole("button", { name: "Try again" })).toBeTruthy();
  expect(
    screen.getByRole<HTMLButtonElement>("button", { name: "Submit Take 5" })
      .disabled,
  ).toBe(true);
});

it("ends the undo at the next edit, so Undo can't wipe newer answers", () => {
  storeDraft();
  stubApi({});
  renderWithApi(<FormAt start={{ page: "hazards" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Add another hazard" }));
  fireEvent.click(screen.getByRole("button", { name: "Remove hazard 1" }));
  fireEvent.change(screen.getByLabelText("Hazard 1"), {
    target: { value: "Dust" },
  });
  expect(screen.queryByRole("button", { name: "Undo" })).toBeNull();
});

it("forgets the draft after a 409, so the next Take 5 in the tab starts afresh", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
    "POST /api/take5s": {
      status: 409,
      body: { detail: "This Take 5 was already saved with different answers." },
    },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  await clickSubmit();
  await screen.findByRole("link", { name: "Open the saved Take 5" });
  expect(localStorage.getItem("take5-draft")).toBeNull();
});

it("returns to the review once a gap is fixed, in place of the fixed page", async () => {
  storeDraft();
  const gap = {
    errors: [{ path: "job", message: "Fill in this field." }],
    assessment: null,
    can_submit: false,
  };
  stubApi({
    "POST /api/take5s/check": [
      { status: 200, body: gap },
      { status: 200, body: PASSING_CHECK },
    ],
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  expect(
    await screen.findByRole("heading", { name: "The job in front of you" }),
  ).toBeTruthy();
  fireEvent.change(screen.getByLabelText("What is the job?"), {
    target: { value: "Change tyre again" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(
    await screen.findByRole("heading", { name: "One last look" }),
  ).toBeTruthy();
  expect(moves).toEqual([
    { page: "job", replace: true },
    { page: "review", replace: true },
  ]);
});

it("focuses the heading on returning to a page that once had errors", async () => {
  stubApi({
    "POST /api/take5s/check": [
      {
        status: 200,
        body: {
          errors: [{ path: "job", message: "Fill in this field." }],
          assessment: null,
          can_submit: false,
        },
      },
      { status: 200, body: PASSING_CHECK },
    ],
  });
  renderWithApi(<FormAt start={{ page: "job" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  const job = screen.getByLabelText("What is the job?");
  await waitFor(() => {
    expect(document.activeElement).toBe(job);
  });
  fireEvent.change(job, { target: { value: "Change tyre" } });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  await screen.findByRole("heading", { name: "Think it through" });
  fireEvent.click(screen.getByRole("button", { name: "Back" }));
  await waitFor(() => {
    expect(document.activeElement).toBe(
      screen.getByRole("heading", { level: 1 }),
    );
  });
  expect(
    screen.queryByText("Fill in the highlighted answers to carry on."),
  ).toBeNull();
});

it("opens a warning's controls page, then goes on to rate and back to the review", async () => {
  const hazard = {
    ...HAZARD_DRAFT,
    controls: [],
    after: { likelihood: null, consequence: null },
  };
  storeDraft({ ...COMPLETE_DRAFT, hazards: [hazard] });
  const warned = {
    ...PASSING_CHECK,
    warnings: [
      {
        path: "hazards.0.controls",
        message: "No controls: you'll be told not to start.",
      },
    ],
  };
  const needsAfter = {
    errors: [
      { path: "hazards.0.after.likelihood", message: "Pick a likelihood." },
    ],
    warnings: [],
    assessment: null,
    can_submit: false,
  };
  // Controls are checked while editing as well as on Continue: reply from the
  // submitted draft, not from how many requests happened before it.
  vi.stubGlobal(
    "fetch",
    vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
      if (typeof init?.body !== "string")
        throw new Error("Expected a JSON draft");
      const draft = JSON.parse(init.body) as Take5Draft;
      const current = draft.hazards[0];
      const body = !current?.controls.length
        ? warned
        : !current.after?.likelihood
          ? needsAfter
          : PASSING_CHECK;
      return Promise.resolve(
        new Response(JSON.stringify(body), { status: 200 }),
      );
    }),
  );
  renderWithApi(<FormAt start={{ page: "review" }} />);
  fireEvent.click(await screen.findByRole("button", { name: "Add a control" }));
  expect(
    await screen.findByRole("heading", { name: "What will stop it?" }),
  ).toBeTruthy();
  fireEvent.change(screen.getByLabelText("What will you do?"), {
    target: { value: "Chock the wheel" },
  });
  fireEvent.change(screen.getByLabelText("Kind of control"), {
    target: { value: "Isolate the hazard" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  // The new control's after rating opens as the next page, not marked as a mistake.
  expect(
    await screen.findByRole("heading", { name: "After your controls" }),
  ).toBeTruthy();
  expect(screen.queryByText("Pick a likelihood.")).toBeNull();
  for (const [group, level] of [
    ["How likely is it?", "Seldom"],
    ["How bad would it be?", "Scratch"],
  ] as const)
    fireEvent.click(
      within(screen.getByRole("group", { name: group })).getByRole("radio", {
        name: level,
      }),
    );
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));

  expect(
    await screen.findByRole("heading", { name: "One last look" }),
  ).toBeTruthy();
  expect(moves).toEqual([
    { page: "controls", replace: true },
    { page: "after", replace: false },
    { page: "review", replace: true },
  ]);
});

it("lets the worker submit with a warning showing", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": {
      status: 200,
      body: {
        ...PASSING_CHECK,
        warnings: [
          {
            path: "hazards.0.controls",
            message: "No controls: you'll be told not to start.",
          },
        ],
      },
    },
    "POST /api/take5s": { status: 200, body: SAVED },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  await screen.findByText("No controls: you'll be told not to start.");
  await clickSubmit();
  await waitFor(() => {
    expect(onSaved).toHaveBeenCalledWith(SAVED.take5.id);
  });
});

it("a Yes to a hazard question adds a hazard, then comes back to the questions", async () => {
  storeDraft({ ...COMPLETE_DRAFT, answers: { keys: "Yes" } });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "check" }} />);
  const dogs = screen.getByRole("group", { name: "Are there dogs on site?" });
  expect(screen.queryByText("Which hazard on your list is this?")).toBeNull();
  fireEvent.click(within(dogs).getByRole("radio", { name: "Yes" }));
  expect(screen.getByText("Which hazard on your list is this?")).toBeTruthy();

  fireEvent.click(screen.getByRole("button", { name: "Add a hazard" }));

  expect(
    await screen.findByRole("heading", { name: "What could hurt someone?" }),
  ).toBeTruthy();
  const newHazard = screen.getByLabelText<HTMLTextAreaElement>("Hazard 2");
  await waitFor(() => {
    expect(document.activeElement).toBe(newHazard);
  });
  fireEvent.change(newHazard, { target: { value: "Dog near the gate" } });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(
    await screen.findByRole("heading", { name: "Did you miss any?" }),
  ).toBeTruthy();
  expect(screen.getByText("Dog near the gate")).toBeTruthy();
  expect(
    screen.getByText("On your list: Dog near the gate", { exact: false }),
  ).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Add a hazard" })).toBeNull();
  expect(
    within(
      screen.getByRole("group", { name: "Are there dogs on site?" }),
    ).getByRole<HTMLInputElement>("radio", { name: "Yes" }).checked,
  ).toBe(true);
});

it("still shows the hazard linked to a Yes after a reload", async () => {
  storeDraft({ ...COMPLETE_DRAFT, answers: { keys: "Yes", dogs: "Yes" } });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  const beforeReload = renderWithApi(<FormAt start={{ page: "check" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Add a hazard" }));
  const newHazard = await screen.findByLabelText("Hazard 2");
  fireEvent.change(newHazard, { target: { value: "Dog near the gate" } });
  beforeReload.unmount();

  renderWithApi(<FormAt start={{ page: "check" }} />);
  expect(screen.getByText("Dog near the gate")).toBeTruthy();
  expect(
    screen.getByText("On your list: Dog near the gate", { exact: false }),
  ).toBeTruthy();
  expect(screen.getByRole("button", { name: "Add another" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Add a hazard" })).toBeNull();
});

it("asks again about a Yes once the hazard linked to it is removed", async () => {
  storeDraft({ ...COMPLETE_DRAFT, answers: { keys: "Yes", dogs: "Yes" } });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "check" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Add a hazard" }));
  await screen.findByLabelText("Hazard 2");

  fireEvent.click(screen.getByRole("button", { name: "Remove hazard 2" }));
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));

  expect(
    await screen.findByRole("heading", { name: "Did you miss any?" }),
  ).toBeTruthy();
  expect(screen.queryByText("On your list:", { exact: false })).toBeNull();
  expect(screen.getByText("Which hazard on your list is this?")).toBeTruthy();
});

it("links the hazard to its Yes again when its removal is undone", async () => {
  storeDraft({ ...COMPLETE_DRAFT, answers: { keys: "Yes", dogs: "Yes" } });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "check" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Add a hazard" }));
  const newHazard = await screen.findByLabelText("Hazard 2");
  fireEvent.change(newHazard, { target: { value: "Dog near the gate" } });

  fireEvent.click(screen.getByRole("button", { name: "Remove hazard 2" }));
  fireEvent.click(screen.getByRole("button", { name: "Undo" }));
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));

  expect(
    await screen.findByRole("heading", { name: "Did you miss any?" }),
  ).toBeTruthy();
  expect(
    screen.getByText("On your list: Dog near the gate", { exact: false }),
  ).toBeTruthy();
});

it("“It’s on my list” links a Yes to the hazard picked, and it stays linked", () => {
  storeDraft({ ...COMPLETE_DRAFT, answers: { keys: "Yes", dogs: "Yes" } });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  const beforeReload = renderWithApi(<FormAt start={{ page: "check" }} />);
  fireEvent.click(screen.getByRole("button", { name: "It’s on my list" }));
  fireEvent.click(screen.getByRole("button", { name: "Moving wheel" }));
  expect(
    screen.getByText("On your list: Moving wheel", { exact: false }),
  ).toBeTruthy();
  beforeReload.unmount();

  renderWithApi(<FormAt start={{ page: "check" }} />);
  expect(
    screen.getByText("On your list: Moving wheel", { exact: false }),
  ).toBeTruthy();
  fireEvent.click(screen.getByRole("radio", { name: "No" }));
  fireEvent.click(screen.getByRole("radio", { name: "Yes" }));
  expect(
    screen.getByText("On your list: Moving wheel", { exact: false }),
  ).toBeTruthy();
  fireEvent.click(
    screen.getByRole("button", { name: "Not this one: Moving wheel" }),
  );
  expect(screen.getByText("Which hazard on your list is this?")).toBeTruthy();
  expect(document.activeElement?.textContent).toBe(
    "Which hazard on your list is this?",
  );
});

const NUDGE =
  'Make it specific: say what could hurt you, and where. For example: "Bitten by the guard dog at the side gate"';
const NUDGED_CHECK = {
  ...PASSING_CHECK,
  nudges: [
    { path: "hazards.0.description", message: NUDGE, question_id: "dogs" },
  ],
};
const DOG: typeof HAZARD_DRAFT = {
  ...HAZARD_DRAFT,
  description: "Dog",
  covers: ["dogs"],
};

it("nudges a short hazard linked to a Yes, and keeping it stops the nudge for good", async () => {
  storeDraft({
    ...COMPLETE_DRAFT,
    answers: { keys: "Yes", dogs: "Yes" },
    hazards: [DOG],
  });
  stubApi({ "POST /api/take5s/check": { status: 200, body: NUDGED_CHECK } });
  const beforeReload = renderWithApi(<FormAt start={{ page: "check" }} />);
  expect(await screen.findByText(NUDGE)).toBeTruthy();
  expect(screen.getByLabelText<HTMLTextAreaElement>("Hazard 1").value).toBe(
    "Dog",
  );

  fireEvent.click(
    screen.getByRole("button", { name: "Keep it as it is: hazard 1" }),
  );
  expect(screen.queryByText(NUDGE)).toBeNull();
  expect(document.activeElement?.textContent).toContain("On your list: Dog");
  beforeReload.unmount();

  renderWithApi(<FormAt start={{ page: "check" }} />);
  expect(screen.getByText("On your list: Dog", { exact: false })).toBeTruthy();
  await new Promise((resolve) => setTimeout(resolve, 500));
  expect(screen.queryByText(NUDGE)).toBeNull();
});

it("rewording in the nudge changes the hazard on the list as the worker types", async () => {
  storeDraft({
    ...COMPLETE_DRAFT,
    answers: { keys: "Yes", dogs: "Yes" },
    hazards: [DOG],
  });
  stubApi({ "POST /api/take5s/check": { status: 200, body: NUDGED_CHECK } });
  renderWithApi(<FormAt start={{ page: "check" }} />);
  const box = await screen.findByLabelText("Hazard 1");

  fireEvent.focus(box);
  fireEvent.change(box, {
    target: { value: "Bitten by the guard dog at the side gate" },
  });

  const yourList = screen.getByRole("heading", { name: "Your list" });
  expect(
    within(yourList.parentElement ?? document.body).getByRole("listitem")
      .textContent,
  ).toBe("Bitten by the guard dog at the side gate");
  expect(screen.getByLabelText("Hazard 1")).toBe(box);
});

it("keeps the nudge's box while the worker types words they kept before", async () => {
  storeDraft(
    {
      ...COMPLETE_DRAFT,
      answers: { keys: "Yes", dogs: "Yes" },
      hazards: [{ ...DOG, description: "Cat" }],
    },
    ["Dog"],
  );
  stubApi({ "POST /api/take5s/check": { status: 200, body: NUDGED_CHECK } });
  renderWithApi(<FormAt start={{ page: "check" }} />);
  const box = await screen.findByLabelText("Hazard 1");

  fireEvent.focus(box);
  fireEvent.change(box, { target: { value: "Dog" } });

  expect(screen.getByLabelText("Hazard 1")).toBe(box);
  expect(screen.queryByText(NUDGE)).toBeNull();
  fireEvent.blur(box);
  expect(screen.queryByLabelText("Hazard 1")).toBeNull();
});

it("shows a nudge only under the question the back end names", async () => {
  storeDraft({
    ...COMPLETE_DRAFT,
    answers: { keys: "Yes", dogs: "Yes" },
    hazards: [DOG],
  });
  stubApi({
    "POST /api/take5s/check": {
      status: 200,
      body: {
        ...NUDGED_CHECK,
        nudges: [{ ...NUDGED_CHECK.nudges[0], question_id: "other" }],
      },
    },
  });
  renderWithApi(<FormAt start={{ page: "check" }} />);
  await new Promise((resolve) => setTimeout(resolve, 500));
  expect(screen.queryByText(NUDGE)).toBeNull();
});

it("shows no nudge for a hazard the back end doesn't nudge", async () => {
  storeDraft({
    ...COMPLETE_DRAFT,
    answers: { keys: "Yes", dogs: "Yes" },
    hazards: [DOG],
  });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "check" }} />);
  await new Promise((resolve) => setTimeout(resolve, 500));
  expect(screen.getByText("On your list: Dog", { exact: false })).toBeTruthy();
  expect(screen.queryByLabelText("Hazard 1")).toBeNull();
  expect(
    screen.queryByRole("button", { name: "Keep it as it is: hazard 1" }),
  ).toBeNull();
});

it("sends an unanswered question found at the review to the page for its role", async () => {
  storeDraft({ ...COMPLETE_DRAFT, answers: { keys: "Yes" } });
  stubApi({
    "POST /api/take5s/check": {
      status: 200,
      body: {
        errors: [{ path: "answers.dogs", message: "Pick Yes, No or N/A." }],
        warnings: [],
        assessment: null,
        can_submit: false,
      },
    },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  expect(
    await screen.findByRole("heading", { name: "Did you miss any?" }),
  ).toBeTruthy();
  expect(screen.getByText("Pick Yes, No or N/A.")).toBeTruthy();
});

it("sends an empty hazard left on the list back there from the questions", async () => {
  const blank = { ...HAZARD_DRAFT, description: "" };
  storeDraft({ ...COMPLETE_DRAFT, hazards: [HAZARD_DRAFT, blank] });
  stubApi({
    "POST /api/take5s/check": {
      status: 200,
      body: {
        errors: [
          { path: "hazards.1.description", message: "Fill in this field." },
        ],
        warnings: [],
        assessment: null,
        can_submit: false,
      },
    },
  });
  renderWithApi(<FormAt start={{ page: "check" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(
    await screen.findByRole("heading", { name: "What could hurt someone?" }),
  ).toBeTruthy();
  const emptyHazard = screen.getByLabelText("Hazard 2");
  await waitFor(() => {
    expect(document.activeElement).toBe(emptyHazard);
  });
  expect(screen.getByText("Fill in this field.")).toBeTruthy();
});

it("never renders the hazard questions for a direct link with a blank hazard", () => {
  storeDraft({
    ...COMPLETE_DRAFT,
    hazards: [{ ...HAZARD_DRAFT, description: "  " }],
  });
  stubApi({});
  renderWithApi(<FormAt start={{ page: "check" }} />);
  expect(screen.getByLabelText("Hazard 1")).toBeTruthy();
  expect(
    screen.queryByRole("heading", { name: "Did you miss any?" }),
  ).toBeNull();
  expect(moves).toEqual([{ page: "hazards", replace: true }]);
});

const RUN_OUT_MESSAGE =
  "This Take 5 was started more than 2 hours ago. Start a new one at the job.";
const RUN_OUT_CHECK = {
  ...PASSING_CHECK,
  errors: [{ path: "started_at", message: RUN_OUT_MESSAGE }],
  assessment: null,
  can_submit: false,
};

it("links to the saved Take 5s until something is typed, then offers Leave", () => {
  stubApi({});
  renderWithApi(<FormAt start={{ page: "job" }} />);
  expect(screen.getByRole("link", { name: "Saved Take 5s" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Leave" })).toBeNull();
  expect(localStorage.getItem("take5-draft")).toBeNull();

  fireEvent.change(screen.getByLabelText("What is the job?"), {
    target: { value: "Change the front left tyre" },
  });

  expect(screen.getByRole("button", { name: "Leave" })).toBeTruthy();
  expect(screen.queryByRole("link", { name: "Saved Take 5s" })).toBeNull();
  const kept = JSON.parse(localStorage.getItem("take5-draft") ?? "{}") as {
    draft: Take5Draft;
    stage: Stage;
  };
  expect(kept.draft.job).toBe("Change the front left tyre");
  expect(kept.draft.started_at).toMatch(/^\d{4}-\d\d-\d\dT.*Z$/);
  expect(kept.stage).toEqual({ page: "job" });
});

it("asks before leaving, and Keep going goes back to the same page", async () => {
  storeDraft();
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "think" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Leave" }));
  const heading = screen.getByRole("heading", { name: "Leave this Take 5?" });
  expect(document.activeElement).toBe(heading);

  fireEvent.click(screen.getByRole("button", { name: "Keep going" }));

  // The panel's buttons are gone, so the focus goes back to the page's heading.
  const page = screen.getByRole("heading", { name: "Think it through" });
  await waitFor(() => {
    expect(document.activeElement).toBe(page);
  });
  expect(onLeave).not.toHaveBeenCalled();
});

it("makes Leave wait while Continue is being checked, as Back does", async () => {
  storeDraft();
  // The draft's check as it opens is answered; the Continue's check never is.
  const unanswered = new Promise<Response>(() => undefined);
  const fetchStub = vi
    .fn<() => Promise<Response>>()
    .mockResolvedValueOnce(
      new Response(JSON.stringify(PASSING_CHECK), { status: 200 }),
    )
    .mockReturnValue(unanswered);
  vi.stubGlobal("fetch", fetchStub);
  renderWithApi(<FormAt start={{ page: "job" }} />);
  const leave = screen.getByRole<HTMLButtonElement>("button", {
    name: "Leave",
  });
  expect(leave.disabled).toBe(false);
  fireEvent.change(screen.getByLabelText("Where will you do it?"), {
    target: { value: "Workshop bay 2" },
  });

  fireEvent.click(screen.getByRole("button", { name: "Continue" }));

  await screen.findByRole("button", { name: "Checking…" });
  expect(leave.disabled).toBe(true);
});

it("keeps the draft on the phone when the worker leaves to finish it later", () => {
  storeDraft();
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "think" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Leave" }));
  fireEvent.click(screen.getByRole("button", { name: "Keep it for later" }));
  expect(onLeave).toHaveBeenCalledWith(null);
  const kept = JSON.parse(localStorage.getItem("take5-draft") ?? "{}") as {
    draft: Take5Draft;
    stage: Stage;
  };
  expect(kept.draft.job).toBe(COMPLETE_DRAFT.job);
  expect(kept.stage).toEqual({ page: "think" });
});

it("throws the draft away and hands it over, so Undo can keep it again", () => {
  storeDraft();
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "think" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Leave" }));
  fireEvent.click(screen.getByRole("button", { name: "Throw it away" }));
  expect(localStorage.getItem("take5-draft")).toBeNull();
  const thrownAway = onLeave.mock.calls[0]?.[0];
  expect(thrownAway?.draft.job).toBe(COMPLETE_DRAFT.job);
  expect(thrownAway?.submissionId).toBe(SAVED.take5.id);
  expect(thrownAway?.stage).toEqual({ page: "think" });
});

it("throws away a kept draft that has run out as it opens, and says why", async () => {
  storeDraft();
  stubApi({ "POST /api/take5s/check": { status: 200, body: RUN_OUT_CHECK } });
  renderWithApi(<FormAt start={{ page: "think" }} />);
  const heading = await screen.findByRole("heading", {
    name: "This Take 5 has run out",
  });
  await waitFor(() => {
    expect(document.activeElement).toBe(heading);
  });
  expect(screen.getByText(RUN_OUT_MESSAGE)).toBeTruthy();
  expect(
    screen.getByText(/^\d{1,2} \w{3} \d{4}, \d{1,2}:\d\d [ap]m$/),
  ).toBeTruthy();
  expect(localStorage.getItem("take5-draft")).toBeNull();
  expect(screen.queryByRole("button", { name: "Leave" })).toBeNull();

  fireEvent.click(screen.getByRole("button", { name: "Start a new Take 5" }));

  expect(onStartAfresh).toHaveBeenCalled();
  expect(moves.at(-1)).toEqual({ page: "job", replace: true });
});

it("stops at the run-out screen when Continue finds the draft has run out", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": [
      { status: 200, body: PASSING_CHECK },
      { status: 200, body: RUN_OUT_CHECK },
    ],
  });
  renderWithApi(<FormAt start={{ page: "job" }} />);
  await waitFor(() => {
    expect(screen.getByRole("button", { name: "Continue" })).toBeTruthy();
  });
  fireEvent.change(screen.getByLabelText("Where will you do it?"), {
    target: { value: "Workshop bay 2" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(
    await screen.findByRole("heading", { name: "This Take 5 has run out" }),
  ).toBeTruthy();
  expect(localStorage.getItem("take5-draft")).toBeNull();
});

it("stops at the run-out screen when Submit is refused for running out", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
    "POST /api/take5s": {
      status: 422,
      body: {
        detail: "Fill in the highlighted fields before you submit.",
        errors: [{ path: "started_at", message: RUN_OUT_MESSAGE }],
      },
    },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  await clickSubmit();
  expect(
    await screen.findByRole("heading", { name: "This Take 5 has run out" }),
  ).toBeTruthy();
  expect(onSaved).not.toHaveBeenCalled();
});

/** Keep a complete draft on the phone that has already reached the given step. */
function storeDraftThatReached(furthestStep: number | undefined, stage: Stage) {
  localStorage.setItem(
    "take5-draft",
    JSON.stringify({
      version: 4,
      draft: { started_at: STARTED_AT, ...COMPLETE_DRAFT },
      submissionId: SAVED.take5.id,
      stage,
      furthestStep,
    }),
  );
}

it("lets a new Take 5 tap no step it hasn't reached", () => {
  stubApi({});
  renderWithApi(<FormAt start={{ page: "job" }} />);
  const steps = screen.getByRole("navigation", { name: "Take 5 steps" });
  expect(within(steps).queryAllByRole("button")).toHaveLength(0);
});

it("goes back to an earlier step with no check, as Back does", async () => {
  storeDraftThatReached(5, { page: "review" });
  const calls = stubApi({
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
  });
  renderWithApi(<FormAt start={{ page: "think" }} />);
  await waitFor(() => {
    expect(calls).toContain("POST /api/take5s/check");
  });
  const checksBefore = calls.length;
  fireEvent.click(screen.getByRole("button", { name: "Job" }));
  expect(
    await screen.findByRole("heading", { name: "The job in front of you" }),
  ).toBeTruthy();
  expect(calls).toHaveLength(checksBefore);
  expect(moves.at(-1)).toEqual({ page: "job", replace: false });
});

it("checks this page before jumping forward, and keeps the worker on a gap", async () => {
  storeDraftThatReached(5, { page: "review" });
  stubApi({
    "POST /api/take5s/check": {
      status: 200,
      body: {
        errors: [{ path: "job", message: "Fill in this field." }],
        assessment: null,
        can_submit: false,
      },
    },
  });
  renderWithApi(<FormAt start={{ page: "job" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Review" }));
  const job = screen.getByLabelText("What is the job?");
  await waitFor(() => {
    expect(document.activeElement).toBe(job);
  });
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
    "The job in front of you",
  );
});

it("jumps forward to a step already reached when this page has no gaps", async () => {
  storeDraftThatReached(5, { page: "review" });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "job" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Review" }));
  expect(
    await screen.findByRole("heading", { name: "One last look" }),
  ).toBeTruthy();
  expect(moves.at(-1)).toEqual({ page: "review", replace: false });
});

it("opens the assess step on the first hazard's before rating", async () => {
  storeDraftThatReached(5, { page: "review" });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  fireEvent.click(await screen.findByRole("button", { name: "Assess" }));
  expect(
    await screen.findByRole("heading", { name: "Before any controls" }),
  ).toBeTruthy();
  expect(screen.getByText("Step 4 of 5 · Hazard 1 of 1")).toBeTruthy();
});

it("counts the page a draft kept before the step bar was left on as reached", () => {
  storeDraftThatReached(undefined, { page: "review" });
  stubApi({});
  renderWithApi(<FormAt start={{ page: "job" }} />);
  expect(screen.getByRole("button", { name: "Review" })).toBeTruthy();
});

it("opens a kept draft with the steps it reached, not only the page it was left on", () => {
  storeDraftThatReached(4, { page: "job" });
  stubApi({});
  renderWithApi(<FormAt start={{ page: "job" }} />);
  expect(screen.getByRole("button", { name: "Assess" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Review" })).toBeNull();
});

it("keeps how far the worker got with the draft on the phone", async () => {
  storeDraftThatReached(2, { page: "think" });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  await waitFor(() => {
    const kept = JSON.parse(localStorage.getItem("take5-draft") ?? "{}") as {
      furthestStep?: number;
    };
    expect(kept.furthestStep).toBe(5);
  });
});

it("opens the saved result, not the run-out screen, when the draft was saved already", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": { status: 200, body: RUN_OUT_CHECK },
    [`GET /api/take5s/${SAVED.take5.id}`]: { status: 200, body: SAVED },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  await waitFor(() => {
    expect(onSaved).toHaveBeenCalledWith(SAVED.take5.id);
  });
  expect(
    screen.queryByRole("heading", { name: "This Take 5 has run out" }),
  ).toBeNull();
  expect(localStorage.getItem("take5-draft")).toBeNull();
  expect(localStorage.getItem("take5-worker-name")).toBe("Sam Example");
});

it("says when a kept draft couldn't be checked, until a check gets through", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": ["offline", { status: 200, body: PASSING_CHECK }],
  });
  renderWithApi(<FormAt start={{ page: "think" }} />);
  const notice = await screen.findByText(
    "No signal: this Take 5 couldn’t be checked to see if it’s still in time.",
  );
  expect(notice.closest("[role=status]")).toBeTruthy();
  expect(screen.getByText(/^You started it/)).toBeTruthy();

  fireEvent.click(screen.getByRole("button", { name: "Try again" }));

  await waitFor(() => {
    expect(
      screen.queryByText(
        "No signal: this Take 5 couldn’t be checked to see if it’s still in time.",
      ),
    ).toBeNull();
  });
  expect(
    screen.getByRole("heading", { name: "Think it through" }),
  ).toBeTruthy();
});

it("shows how long a kept draft has left, as the back end says", async () => {
  storeDraft();
  const runsOutAt = new Date(Date.now() + 42.5 * 60_000).toISOString();
  stubApi({
    "POST /api/take5s/check": {
      status: 200,
      body: { ...PASSING_CHECK, runs_out_at: runsOutAt },
    },
  });
  renderWithApi(<FormAt start={{ page: "think" }} />);
  expect(await screen.findByText("42 min left")).toBeTruthy();
});
