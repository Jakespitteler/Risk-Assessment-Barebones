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
  renderWithApi,
  stubApi,
} from "../../test-utils";
import type { Stage } from "./stage";
import { Take5Form } from "./Take5Form";

const onSaved = vi.fn<(id: string) => void>();
// Each page the form moved to, and whether it replaced the page before it.
let moves: { page: string; replace: boolean }[] = [];

// Stands in for the router: the stage is kept in state instead of the URL.
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
    />
  );
}

function storeDraft(draft = COMPLETE_DRAFT) {
  sessionStorage.setItem(
    "take5-draft",
    JSON.stringify({ version: 2, draft, submissionId: SAVED.take5.id }),
  );
}

/** Press Finish once the review's check has come back and enabled it. */
async function clickFinish() {
  const button = await screen.findByRole<HTMLButtonElement>("button", {
    name: "Finish Take 5",
  });
  await waitFor(() => {
    expect(button.disabled).toBe(false);
  });
  fireEvent.click(button);
}

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  onSaved.mockReset();
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

it("starts afresh instead of loading a draft kept before the card had questions", () => {
  // JSON leaves out an undefined field, so this is the old shape, with no answers.
  const oldDraft = { ...COMPLETE_DRAFT, answers: undefined };
  sessionStorage.setItem(
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
  await clickFinish();
  await waitFor(() => {
    expect(onSaved).toHaveBeenCalledWith(SAVED.take5.id);
  });
  expect(sessionStorage.getItem("take5-draft")).toBeNull();
  expect(localStorage.getItem("take5-worker-name")).toBe("Sam Example");
});

it("sends the worker to the gap the back end found on Finish", async () => {
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
  await clickFinish();
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
  await clickFinish();
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

it("keeps Finish disabled when the review couldn't be checked", async () => {
  storeDraft();
  stubApi({ "POST /api/take5s/check": "offline" });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  expect(await screen.findByRole("button", { name: "Try again" })).toBeTruthy();
  expect(
    screen.getByRole<HTMLButtonElement>("button", { name: "Finish Take 5" })
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
  await clickFinish();
  await screen.findByRole("link", { name: "Open the saved Take 5" });
  expect(sessionStorage.getItem("take5-draft")).toBeNull();
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
  fireEvent.click(screen.getByRole("button", { name: "Add a control" }));
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

it("lets the worker finish with a warning showing", async () => {
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
  await clickFinish();
  await waitFor(() => {
    expect(onSaved).toHaveBeenCalledWith(SAVED.take5.id);
  });
});

it("a Yes to a hazard question adds a hazard, then comes back to the questions", async () => {
  storeDraft({ ...COMPLETE_DRAFT, answers: { keys: "Yes" } });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "check" }} />);
  const dogs = screen.getByRole("group", { name: "Are there dogs on site?" });
  expect(screen.queryByText("Make sure it’s on your list.")).toBeNull();
  fireEvent.click(within(dogs).getByRole("radio", { name: "Yes" }));
  expect(screen.getByText("Make sure it’s on your list.")).toBeTruthy();

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
  expect(screen.getByText("Added to your list")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Add a hazard" })).toBeNull();
  expect(
    within(
      screen.getByRole("group", { name: "Are there dogs on site?" }),
    ).getByRole<HTMLInputElement>("radio", { name: "Yes" }).checked,
  ).toBe(true);
});

it("still shows a hazard was added from a Yes after a reload", async () => {
  storeDraft({ ...COMPLETE_DRAFT, answers: { keys: "Yes", dogs: "Yes" } });
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  const beforeReload = renderWithApi(<FormAt start={{ page: "check" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Add a hazard" }));
  const newHazard = await screen.findByLabelText("Hazard 2");
  fireEvent.change(newHazard, { target: { value: "Dog near the gate" } });
  beforeReload.unmount();

  renderWithApi(<FormAt start={{ page: "check" }} />);
  expect(screen.getByText("Dog near the gate")).toBeTruthy();
  expect(screen.getByText("Added to your list")).toBeTruthy();
  expect(screen.getByRole("button", { name: "Add another" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Add a hazard" })).toBeNull();
});

it("reminds again about a Yes once the hazard added from it is removed", async () => {
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
  expect(screen.queryByText("Added to your list")).toBeNull();
  expect(screen.getByText("Make sure it’s on your list.")).toBeTruthy();
});

it("shows the hazard as added again when its removal is undone", async () => {
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
  expect(screen.getByText("Added to your list")).toBeTruthy();
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
