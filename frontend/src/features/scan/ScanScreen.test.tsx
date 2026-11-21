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
import { COULDNT_READ } from "./PaperCardForm";
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
  expect(screen.getByText(COULDNT_READ)).toBeTruthy();
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
