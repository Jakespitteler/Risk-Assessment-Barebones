import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { RankedTake5Line } from "../../api/take5";
import { renderWithApi, stubApi } from "../../test-utils";
import { WorstOfTodayScreen } from "./WorstOfTodayScreen";

// 2:30 pm on 20 Nov 2026 where the tests run; the ranking starts at that midnight.
const NOW = new Date(2026, 10, 20, 14, 30);
const MIDNIGHT = new Date(2026, 10, 20).toISOString();
const RANKING_URL = `GET /api/ranked-take5s?since=${encodeURIComponent(MIDNIGHT)}`;

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function ranked(
  number: number,
  changed: Partial<RankedTake5Line> = {},
): RankedTake5Line {
  return {
    id: `00000000-0000-4000-8000-${String(number).padStart(12, "0")}`,
    created_at: "2026-11-20T01:15:00Z",
    worker_name: `Worker ${String(number)}`,
    job: `Job ${String(number)}`,
    can_start: true,
    line: `Reason ${String(number)}.`,
    ranked_by_ai: false,
    ...changed,
  };
}

it("asks for today's Take 5s from midnight where the phone is (W7)", async () => {
  const calls = stubApi({
    [RANKING_URL]: { status: 200, body: { take5s: [] } },
  });
  renderWithApi(<WorstOfTodayScreen />);
  expect(
    await screen.findByRole("heading", { name: "Worst of today" }),
  ).toBeTruthy();
  expect(calls).toEqual([RANKING_URL]);
  expect(screen.getByText("No Take 5s have been started today.")).toBeTruthy();
});

it("lists them worst first with place, verdict, job, reason and worker (W1)", async () => {
  stubApi({
    [RANKING_URL]: {
      status: 200,
      body: { take5s: [ranked(1, { can_start: null }), ranked(2)] },
    },
  });
  renderWithApi(<WorstOfTodayScreen />);
  await screen.findByRole("heading", { name: "Worst of today" });
  const [worst, next] = screen
    .getAllByRole("listitem")
    .map((item) => within(item));
  expect(worst?.getByText("1.")).toBeTruthy();
  expect(worst?.getByText("Not finished")).toBeTruthy();
  expect(worst?.getByText("Job 1")).toBeTruthy();
  expect(worst?.getByText("Reason 1.")).toBeTruthy();
  expect(worst?.getByText("Worker 1")).toBeTruthy();
  expect(next?.getByText("2.")).toBeTruthy();
  expect(
    screen.getAllByRole("link", { name: /Job 2/ })[0]?.getAttribute("href"),
  ).toBe(`/take5s/${ranked(2).id}`);
  expect(screen.queryByText(/An AI ordered/)).toBeNull();
});

it("shows the worst 5, then the rest in order on Show all", async () => {
  stubApi({
    [RANKING_URL]: {
      status: 200,
      body: { take5s: [1, 2, 3, 4, 5, 6, 7].map((number) => ranked(number)) },
    },
  });
  renderWithApi(<WorstOfTodayScreen />);
  await screen.findByRole("heading", { name: "Worst of today" });
  expect(screen.getAllByRole("listitem")).toHaveLength(5);
  fireEvent.click(screen.getByRole("button", { name: "Show all 7" }));
  expect(screen.getAllByRole("listitem")).toHaveLength(7);
  expect(screen.getByText("7.")).toBeTruthy();
  expect(screen.queryByRole("button", { name: /Show all/ })).toBeNull();
});

it("says when an AI ordered them, and that names aren't sent (W6)", async () => {
  stubApi({
    [RANKING_URL]: {
      status: 200,
      body: { take5s: [ranked(1, { ranked_by_ai: true }), ranked(2)] },
    },
  });
  renderWithApi(<WorstOfTodayScreen />);
  expect(
    await screen.findByText(
      "An AI ordered the worst and wrote their reasons. Names aren’t sent to it.",
    ),
  ).toBeTruthy();
});
