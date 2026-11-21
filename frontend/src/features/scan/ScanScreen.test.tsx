import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ScannedCardResponse } from "../../api/take5";
import {
  HAZARD_DRAFT,
  renderWithApi,
  SAVED,
  SMALL_TEMPLATE,
  stubApi,
} from "../../test-utils";
import { UNREADABLE_MARK } from "./PaperCardForm";
import { ScanScreen } from "./ScanScreen";

const TEMPLATE = {
  "GET /api/take5/template": { status: 200, body: SMALL_TEMPLATE },
};
const READ: ScannedCardResponse = {
  draft: {
    worker_name: "Sam Example",
    job: "",
    location: "Workshop bay 2",
    answers: { keys: "Yes" },
    hazards: [{ ...HAZARD_DRAFT, controls: [] }],
  },
  filled_in_at: "2026-04-03",
  unreadable: ["job"],
};

beforeEach(() => {
  vi.stubGlobal("URL", {
    ...URL,
    createObjectURL: () => "blob:photo",
    revokeObjectURL: vi.fn(),
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function choosePhotos(count: number) {
  const files = Array.from(
    { length: count },
    (_, index) =>
      new File(["photo"], `card-${String(index)}.jpg`, { type: "image/jpeg" }),
  );
  fireEvent.change(screen.getByLabelText("Choose photos"), {
    target: { files },
  });
}

it("reads every photo, then shows each card to check with what couldn't be read (F10)", async () => {
  const calls = stubApi({
    ...TEMPLATE,
    "POST /api/scans": { status: 200, body: READ },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(2);
  expect(
    await screen.findByRole("heading", { name: "Check card 1 of 2" }),
  ).toBeTruthy();
  expect(calls.filter((call) => call === "POST /api/scans")).toHaveLength(2);
  expect(screen.getByRole("img", { name: "The paper card" })).toBeTruthy();
  expect(screen.getByLabelText("Name")).toHaveProperty("value", "Sam Example");
  expect(screen.getByLabelText("Date on the card")).toHaveProperty(
    "value",
    "2026-04-03",
  );
  expect(screen.getByText(UNREADABLE_MARK)).toBeTruthy();
  expect(screen.getByRole("heading", { name: "Hazard 1" })).toBeTruthy();
});

it("saves a checked card as written with the checker's time zone, then shows the next (P1, P5)", async () => {
  const saves: unknown[] = [];
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": { status: 200, body: READ },
    "POST /api/take5s/paper": { status: 200, body: SAVED },
  });
  const fetchStub = vi.mocked(fetch);
  renderWithApi(<ScanScreen />);
  choosePhotos(2);
  fireEvent.change(await screen.findByLabelText("Job"), {
    target: { value: "Change tyre" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save as written" }));
  expect(
    await screen.findByRole("heading", { name: "Check card 2 of 2" }),
  ).toBeTruthy();
  for (const [input, init] of fetchStub.mock.calls)
    if (input === "/api/take5s/paper" && typeof init?.body === "string")
      saves.push(JSON.parse(init.body));
  expect(saves).toHaveLength(1);
  expect(saves[0]).toMatchObject({
    draft: { job: "Change tyre", worker_name: "Sam Example" },
    filled_in_at: "2026-04-03",
    time_zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });
  fireEvent.click(screen.getByRole("button", { name: "Skip this card" }));
  expect(await screen.findByText("1 card saved, 1 skipped.")).toBeTruthy();
});

it("shows the back end's problem beside its field when a save is refused", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": { status: 200, body: READ },
    "POST /api/take5s/paper": {
      status: 422,
      body: {
        detail: "This time zone isn't known.",
        errors: [
          { path: "filled_in_at", message: "Give the card's date as written." },
        ],
      },
    },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  fireEvent.click(
    await screen.findByRole("button", { name: "Save as written" }),
  );
  expect(
    await screen.findByText("Give the card's date as written."),
  ).toBeTruthy();
  expect(screen.getByRole("alert").textContent).toBe(
    "This time zone isn't known.",
  );
});

it("says why a photo couldn't be read, and reads it again on Try again", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": [
      {
        status: 422,
        body: {
          detail: "This photo couldn't be read as a Take 5 card.",
          errors: [],
        },
      },
      { status: 200, body: READ },
    ],
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  expect(
    await screen.findByText("This photo couldn't be read as a Take 5 card."),
  ).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(await screen.findByLabelText("Name")).toBeTruthy();
});

it("says when scanning needs an AI that isn't set up", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": {
      status: 503,
      body: { detail: "Scanning paper cards needs an AI, and none is set up." },
    },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  const card = await screen.findByRole("heading", {
    name: "Check card 1 of 1",
  });
  expect(card).toBeTruthy();
  expect(
    within(document.body).getByText(
      "Scanning paper cards needs an AI, and none is set up.",
    ),
  ).toBeTruthy();
});

/** The bodies sent to save paper cards, in order. */
function savedBodies(): unknown[] {
  return vi
    .mocked(fetch)
    .mock.calls.filter(([input]) => input === "/api/take5s/paper")
    .map(([, init]) =>
      typeof init?.body === "string"
        ? (JSON.parse(init.body) as unknown)
        : null,
    );
}

it("sends the card exactly as read when nothing is changed (P1)", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": { status: 200, body: READ },
    "POST /api/take5s/paper": { status: 200, body: SAVED },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  fireEvent.click(
    await screen.findByRole("button", { name: "Save as written" }),
  );
  await screen.findByText("1 card saved.");
  expect(savedBodies()).toEqual([
    {
      id: expect.any(String) as unknown,
      draft: READ.draft,
      filled_in_at: "2026-04-03",
      time_zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    },
  ]);
});

it("sets a misread answer and rating back to blank, as on the card (P1)", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": { status: 200, body: READ },
    "POST /api/take5s/paper": { status: 200, body: SAVED },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  fireEvent.click(
    await screen.findByRole("button", {
      name: "Leave blank, as on the card: Have you got the gate keys?",
    }),
  );
  fireEvent.click(
    screen.getByRole("button", {
      name: "Leave this rating blank, as on the card: hazard 1, before controls",
    }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Save as written" }));
  await screen.findByText("1 card saved.");
  expect(savedBodies()[0]).toMatchObject({
    draft: {
      answers: {},
      hazards: [{ before: { likelihood: null, consequence: null } }],
    },
  });
});

it("saves a card once when the first reply was lost", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": { status: 200, body: READ },
    "POST /api/take5s/paper": ["offline", { status: 200, body: SAVED }],
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  fireEvent.click(
    await screen.findByRole("button", { name: "Save as written" }),
  );
  await screen.findByText("1 card saved.");
  const [first, second] = savedBodies() as { id: string }[];
  expect(second?.id).toBe(first?.id);
});

it("stops reading the batch when no AI is set up", async () => {
  const calls = stubApi({
    ...TEMPLATE,
    "POST /api/scans": {
      status: 503,
      body: { detail: "Scanning paper cards needs an AI, and none is set up." },
    },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(3);
  await screen.findByRole("heading", { name: "Check card 1 of 3" });
  expect(calls.filter((call) => call === "POST /api/scans")).toHaveLength(1);
});

it("reads a retaken photo in place of one that couldn't be read", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": [
      {
        status: 422,
        body: { detail: "Try a clearer photo of the whole card.", errors: [] },
      },
      { status: 200, body: READ },
    ],
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  fireEvent.change(await screen.findByLabelText("Take this photo again"), {
    target: {
      files: [new File(["clearer"], "again.jpg", { type: "image/jpeg" })],
    },
  });
  expect(await screen.findByLabelText("Name")).toBeTruthy();
});

it("says when the card couldn't be loaded, and loads it again", async () => {
  stubApi({
    "GET /api/take5/template": [
      { status: 500, body: { detail: "Down." } },
      { status: 500, body: { detail: "Down." } },
      { status: 500, body: { detail: "Down." } },
      { status: 200, body: SMALL_TEMPLATE },
    ],
    "POST /api/scans": { status: 200, body: READ },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
  expect(await screen.findByLabelText("Name")).toBeTruthy();
});

it("keeps each mark beside its own hazard when one is removed", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": {
      status: 200,
      body: {
        ...READ,
        draft: {
          ...READ.draft,
          hazards: [HAZARD_DRAFT, { ...HAZARD_DRAFT, description: "Second" }],
        },
        unreadable: ["hazards.1.description"],
      },
    },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  fireEvent.click(
    await screen.findByRole("button", { name: "Remove hazard 1" }),
  );
  const hazard = screen.getByRole("heading", { name: "Hazard 1" })
    .parentElement as HTMLElement;
  expect(within(hazard).getByText(UNREADABLE_MARK)).toBeTruthy();
});

it("takes more photos while a card is being checked, and reads them next", async () => {
  const calls = stubApi({
    ...TEMPLATE,
    "POST /api/scans": { status: 200, body: READ },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  await screen.findByRole("heading", { name: "Check card 1 of 1" });
  fireEvent.change(screen.getByLabelText("Add more photos"), {
    target: {
      files: [new File(["photo"], "next.jpg", { type: "image/jpeg" })],
    },
  });
  expect(
    await screen.findByRole("heading", { name: "Check card 1 of 2" }),
  ).toBeTruthy();
  expect(calls.filter((call) => call === "POST /api/scans")).toHaveLength(2);
});

it("counts a card as saved when a retry finds it already saved", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": { status: 200, body: READ },
    "POST /api/take5s/paper": {
      status: 409,
      body: { detail: "This Take 5 was already saved with different answers." },
    },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  fireEvent.click(
    await screen.findByRole("button", { name: "Save as written" }),
  );
  expect(await screen.findByText("1 card saved.")).toBeTruthy();
  expect(
    screen.getByText(/^One card was already saved, as it was first sent/),
  ).toBeTruthy();
});

it("keeps the edits to the card being checked when more photos are added", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": { status: 200, body: READ },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  fireEvent.change(await screen.findByLabelText("Job"), {
    target: { value: "Change tyre" },
  });
  fireEvent.change(screen.getByLabelText("Add more photos"), {
    target: {
      files: [new File(["photo"], "next.jpg", { type: "image/jpeg" })],
    },
  });
  await screen.findByRole("heading", { name: "Check card 1 of 2" });
  expect(screen.getByLabelText("Job")).toHaveProperty("value", "Change tyre");
});

it("keeps a control's mark beside it when an earlier control is removed", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": {
      status: 200,
      body: {
        ...READ,
        draft: {
          ...READ.draft,
          hazards: [
            {
              ...HAZARD_DRAFT,
              controls: [
                { description: "First", kind: "Wear PPE" },
                { description: "Second", kind: null },
              ],
            },
          ],
        },
        unreadable: ["hazards.0.controls.1.kind"],
      },
    },
  });
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  fireEvent.click(
    await screen.findByRole("button", { name: "Remove control 1" }),
  );
  const control = screen.getByRole("heading", { name: "Control 1" })
    .parentElement as HTMLElement;
  expect(within(control).getByText(UNREADABLE_MARK)).toBeTruthy();
});

it("ranks the saved cards worst first once the batch is done (F10)", async () => {
  stubApi({
    ...TEMPLATE,
    "POST /api/scans": { status: 200, body: READ },
    "POST /api/take5s/paper": { status: 200, body: SAVED },
    "POST /api/ranked-take5s/batch": {
      status: 200,
      body: {
        take5s: [
          {
            id: SAVED.take5.id,
            created_at: SAVED.take5.created_at,
            worker_name: "Sam Example",
            job: "Change tyre",
            can_start: false,
            line: "No risk rated. “Moving wheel” has no rating.",
            ranked_by_ai: false,
          },
        ],
        best: null,
        typical_minutes: null,
        today_only: false,
      },
    },
  });
  const fetchStub = vi.mocked(fetch);
  renderWithApi(<ScanScreen />);
  choosePhotos(1);
  fireEvent.click(
    await screen.findByRole("button", { name: "Save as written" }),
  );
  expect(
    await screen.findByRole("heading", { name: "This batch, worst first" }),
  ).toBeTruthy();
  expect(
    await screen.findByText("No risk rated. “Moving wheel” has no rating."),
  ).toBeTruthy();
  const batch = fetchStub.mock.calls.find(
    ([input]) => input === "/api/ranked-take5s/batch",
  );
  expect(
    typeof batch?.[1]?.body === "string" && JSON.parse(batch[1].body),
  ).toEqual({ ids: [expect.any(String)] });
});
