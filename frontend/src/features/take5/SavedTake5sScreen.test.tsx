import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Take5Summary } from "../../api/take5";
import {
  COMPLETE_DRAFT,
  PASSING_CHECK,
  SAVED,
  keepSampleDraft,
  quickClient,
  renderWithApi,
  stubApi,
} from "../../test-utils";
import { SavedTake5sScreen } from "./SavedTake5sScreen";

afterEach(() => {
  localStorage.clear();
  vi.unstubAllGlobals();
});

// Newest first, as the back end sends them.
const LIST: Take5Summary[] = [
  {
    id: "22222222-2222-4222-8222-222222222222",
    created_at: "2026-11-14T01:15:00Z",
    worker_name: "Alex Example",
    job: "Replace conveyor idler",
    can_start: false,
    fixed: true,
  },
  {
    id: "11111111-1111-4111-8111-111111111111",
    created_at: "2026-11-13T07:30:00Z",
    worker_name: "Sam Example",
    job: "Change tyre",
    can_start: true,
    fixed: false,
  },
];

it("lists each saved Take 5 in the order sent, with its verdict, job, worker and date", async () => {
  stubApi({ "GET /api/take5s": { status: 200, body: LIST } });
  renderWithApi(<SavedTake5sScreen />);
  expect(
    await screen.findByRole("heading", { name: "Saved Take 5s" }),
  ).toBeTruthy();
  const items = screen.getAllByRole("listitem");
  expect(items).toHaveLength(2);
  const [newest, oldest] = items.map((item) => within(item));
  expect(newest?.getByText("Don’t start yet")).toBeTruthy();
  expect(newest?.getByText("Replace conveyor idler")).toBeTruthy();
  expect(newest?.getByText("Alex Example")).toBeTruthy();
  expect(items[0]?.querySelector("time")?.getAttribute("dateTime")).toBe(
    "2026-11-14T01:15:00Z",
  );
  expect(newest?.getByText("Fixed")).toBeTruthy();
  expect(oldest?.getByText("Good to go")).toBeTruthy();
  expect(oldest?.queryByText("Fixed")).toBeNull();
  expect(oldest?.getByText("Change tyre")).toBeTruthy();
});

it("moves the focus to the heading, so a screen reader starts there", async () => {
  stubApi({ "GET /api/take5s": { status: 200, body: LIST } });
  renderWithApi(<SavedTake5sScreen />);
  const heading = await screen.findByRole("heading", { name: "Saved Take 5s" });
  expect(document.activeElement).toBe(heading);
});

it("keeps showing the list when a refresh fails", async () => {
  stubApi({ "GET /api/take5s": [{ status: 200, body: LIST }, "offline"] });
  const client = quickClient();
  renderWithApi(<SavedTake5sScreen />, client);
  expect(await screen.findByText("Replace conveyor idler")).toBeTruthy();
  await client.refetchQueries({ queryKey: ["take5s"] });
  expect(screen.getByRole("heading", { name: "Saved Take 5s" })).toBeTruthy();
  expect(screen.getByText("Replace conveyor idler")).toBeTruthy();
});

it("leaves the focus where it was when a refresh fails", async () => {
  stubApi({ "GET /api/take5s": [{ status: 200, body: LIST }, "offline"] });
  const client = quickClient();
  renderWithApi(<SavedTake5sScreen />, client);
  const link = await screen.findByRole("link", {
    name: /Replace conveyor idler/,
  });
  link.focus();
  await client.refetchQueries({ queryKey: ["take5s"] });
  await waitFor(() => {
    expect(client.getQueryState(["take5s"])?.status).toBe("error");
  });
  expect(document.activeElement).toBe(link);
});

it("opens a saved Take 5's result screen from its card", async () => {
  stubApi({ "GET /api/take5s": { status: 200, body: LIST } });
  renderWithApi(<SavedTake5sScreen />);
  const link = await screen.findByRole("link", {
    name: /Replace conveyor idler/,
  });
  expect(link.getAttribute("href")).toBe(
    "/take5s/22222222-2222-4222-8222-222222222222",
  );
});

it("says when nothing has been saved yet, and offers a new Take 5", async () => {
  stubApi({ "GET /api/take5s": { status: 200, body: [] } });
  renderWithApi(<SavedTake5sScreen />);
  expect(
    await screen.findByText("No Take 5s have been saved yet."),
  ).toBeTruthy();
  expect(screen.queryByRole("list")).toBeNull();
  expect(
    screen
      .getByRole("link", { name: "Start a new Take 5" })
      .getAttribute("href"),
  ).toBe("/");
});

it("offers to try again when the list can't be loaded", async () => {
  const calls = stubApi({
    "GET /api/take5s": [
      "offline",
      "offline",
      "offline",
      { status: 200, body: LIST },
    ],
  });
  renderWithApi(<SavedTake5sScreen />);
  fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
  expect(
    await screen.findByRole("heading", { name: "Saved Take 5s" }),
  ).toBeTruthy();
  expect(calls).toHaveLength(4);
});

const RUN_OUT_MESSAGE =
  "This Take 5 was started more than 2 hours ago. Start a new one at the job.";

it("shows the phone's unfinished Take 5 at the top, in place of Start a new Take 5", async () => {
  localStorage.clear();
  keepSampleDraft();
  stubApi({
    "GET /api/take5s": { status: 200, body: LIST },
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
  });
  renderWithApi(<SavedTake5sScreen />);
  const card = within(
    (await screen.findByRole("heading", { name: "Your unfinished Take 5" }))
      .parentElement as HTMLElement,
  );
  expect(card.getByText("Change tyre")).toBeTruthy();
  expect(
    card.getByText(/^\d{1,2} \w{3} \d{4}, \d{1,2}:\d\d [ap]m$/),
  ).toBeTruthy();
  expect(
    card.getByRole("link", { name: "Carry on" }).getAttribute("href"),
  ).toBe("/");
  expect(screen.queryByRole("link", { name: "Start a new Take 5" })).toBeNull();
  localStorage.clear();
});

it("throws away an unfinished Take 5 that has run out, and says why", async () => {
  localStorage.clear();
  keepSampleDraft();
  stubApi({
    "GET /api/take5s": { status: 200, body: LIST },
    "POST /api/take5s/check": {
      status: 200,
      body: {
        ...PASSING_CHECK,
        errors: [{ path: "started_at", message: RUN_OUT_MESSAGE }],
        assessment: null,
        can_submit: false,
      },
    },
  });
  renderWithApi(<SavedTake5sScreen />);
  expect(
    await screen.findByRole("heading", {
      name: "Your unfinished Take 5 has run out",
    }),
  ).toBeTruthy();
  // It appears after the list has loaded, so it is announced.
  expect(
    within(screen.getByRole("status")).getByText(RUN_OUT_MESSAGE),
  ).toBeTruthy();
  expect(screen.queryByRole("link", { name: "Carry on" })).toBeNull();
  expect(screen.getByRole("link", { name: "Start a new Take 5" })).toBeTruthy();
  expect(localStorage.getItem("take5-draft")).toBeNull();
});

it("offers Undo for a Take 5 just thrown away", async () => {
  localStorage.clear();
  const onUndo = vi.fn();
  const onDismiss = vi.fn();
  const thrownAway = {
    version: 3,
    draft: COMPLETE_DRAFT,
    submissionId: SAVED.take5.id,
  };
  stubApi({ "GET /api/take5s": { status: 200, body: LIST } });
  renderWithApi(
    <SavedTake5sScreen
      thrownAway={thrownAway}
      onUndoThrowAway={onUndo}
      onDismissUndo={onDismiss}
    />,
  );
  expect(await screen.findByText("Take 5 thrown away.")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Undo" }));
  expect(onUndo).toHaveBeenCalledWith(thrownAway);
  fireEvent.click(screen.getByRole("button", { name: "Close" }));
  expect(onDismiss).toHaveBeenCalled();
});

it("ends the Undo once another Take 5 has been started, so it can't be replaced", async () => {
  keepSampleDraft({ ...COMPLETE_DRAFT, job: "Grease the conveyor" });
  const thrownAway = {
    version: 3,
    draft: COMPLETE_DRAFT,
    submissionId: SAVED.take5.id,
  };
  stubApi({
    "GET /api/take5s": { status: 200, body: LIST },
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
  });
  renderWithApi(
    <SavedTake5sScreen
      thrownAway={thrownAway}
      onUndoThrowAway={vi.fn()}
      onDismissUndo={vi.fn()}
    />,
  );
  expect(await screen.findByText("Grease the conveyor")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Undo" })).toBeNull();
});

it("points to the saved Take 5 when a draft that ran out had been saved already", async () => {
  keepSampleDraft();
  stubApi({
    "GET /api/take5s": { status: 200, body: LIST },
    "POST /api/take5s/check": {
      status: 200,
      body: {
        ...PASSING_CHECK,
        errors: [{ path: "started_at", message: RUN_OUT_MESSAGE }],
        assessment: null,
        can_submit: false,
      },
    },
    [`GET /api/take5s/${SAVED.take5.id}`]: { status: 200, body: SAVED },
  });
  renderWithApi(<SavedTake5sScreen />);
  expect(
    await screen.findByRole("heading", {
      name: "Your unfinished Take 5 was saved",
    }),
  ).toBeTruthy();
  expect(
    screen.getByRole("link", { name: "Open it" }).getAttribute("href"),
  ).toBe(`/take5s/${SAVED.take5.id}`);
  expect(screen.queryByText(RUN_OUT_MESSAGE)).toBeNull();
  expect(localStorage.getItem("take5-draft")).toBeNull();
});

it("says when the unfinished Take 5 couldn't be checked", async () => {
  keepSampleDraft();
  stubApi({
    "GET /api/take5s": { status: 200, body: LIST },
    "POST /api/take5s/check": "offline",
  });
  renderWithApi(<SavedTake5sScreen />);
  expect(
    await screen.findByText(
      "No signal: it couldn’t be checked to see if it’s still in time.",
    ),
  ).toBeTruthy();
  expect(screen.getByRole("link", { name: "Carry on" })).toBeTruthy();
});

it("shows how long the unfinished Take 5 has left", async () => {
  keepSampleDraft();
  stubApi({
    "GET /api/take5s": { status: 200, body: LIST },
    "POST /api/take5s/check": {
      status: 200,
      body: {
        ...PASSING_CHECK,
        runs_out_at: new Date(Date.now() + 95.5 * 60_000).toISOString(),
      },
    },
  });
  renderWithApi(<SavedTake5sScreen />);
  expect(await screen.findByText("1 hr 35 min left")).toBeTruthy();
});
