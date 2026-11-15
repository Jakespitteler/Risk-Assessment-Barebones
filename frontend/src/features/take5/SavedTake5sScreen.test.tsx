import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Take5Summary } from "../../api/take5";
import { quickClient, renderWithApi, stubApi } from "../../test-utils";
import { SavedTake5sScreen } from "./SavedTake5sScreen";

afterEach(() => {
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
