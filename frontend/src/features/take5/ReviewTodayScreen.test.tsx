import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { BestTake5Line, RankedTake5Line } from "../../api/take5";
import { renderWithApi, stubApi } from "../../test-utils";
import { ReviewTodayScreen } from "./ReviewTodayScreen";

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
    [RANKING_URL]: {
      status: 200,
      body: { take5s: [], best: null, typical_minutes: null },
    },
  });
  renderWithApi(<ReviewTodayScreen />);
  expect(
    await screen.findByRole("heading", { name: "Today’s review" }),
  ).toBeTruthy();
  expect(calls).toEqual([RANKING_URL]);
  expect(screen.getByText("No Take 5s have been started today.")).toBeTruthy();
});

it("lists them worst first with place, verdict, job, reason and worker (W1)", async () => {
  stubApi({
    [RANKING_URL]: {
      status: 200,
      body: {
        take5s: [ranked(1, { can_start: null }), ranked(2)],
        best: null,
        typical_minutes: null,
      },
    },
  });
  renderWithApi(<ReviewTodayScreen />);
  await screen.findByRole("heading", { name: "Today’s review" });
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
      body: {
        take5s: [1, 2, 3, 4, 5, 6, 7].map((number) => ranked(number)),
        best: null,
        typical_minutes: null,
      },
    },
  });
  renderWithApi(<ReviewTodayScreen />);
  await screen.findByRole("heading", { name: "Today’s review" });
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
      body: {
        take5s: [ranked(1, { ranked_by_ai: true }), ranked(2)],
        best: null,
        typical_minutes: null,
      },
    },
  });
  renderWithApi(<ReviewTodayScreen />);
  expect(
    await screen.findByText(
      "An AI helped choose these and wrote their reasons. Names aren’t sent to it.",
    ),
  ).toBeTruthy();
});

it("says while it ranks, and offers Try again when it can't (W6)", async () => {
  stubApi({
    [RANKING_URL]: [
      "offline",
      {
        status: 200,
        body: { take5s: [ranked(1)], best: null, typical_minutes: null },
      },
    ],
  });
  renderWithApi(<ReviewTodayScreen />);
  expect(
    screen.getByRole("heading", { name: "Ranking today’s Take 5s…" }),
  ).toBeTruthy();
  expect(
    await screen.findByRole("heading", {
      name: "Today’s Take 5s couldn’t be ranked",
    }),
  ).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(
    await screen.findByRole("heading", { name: "Today’s review" }),
  ).toBeTruthy();
  expect(screen.getByText("Reason 1.")).toBeTruthy();
});

const BEST: BestTake5Line = {
  id: "00000000-0000-4000-8000-000000000099",
  created_at: "2026-11-20T01:15:00Z",
  worker_name: "Worker 9",
  job: "Job 9",
  can_start: true,
  line: "Names the exact chock points.",
  picked_by_ai: true,
  minutes_taken: 9,
};

it("shows the best of today with why and how long it took (W8, W9)", async () => {
  stubApi({
    [RANKING_URL]: {
      status: 200,
      body: { take5s: [ranked(1)], best: BEST, typical_minutes: 3 },
    },
  });
  renderWithApi(<ReviewTodayScreen />);
  const best = within(
    await screen.findByRole("region", { name: "Best of today" }),
  );
  expect(best.getByText("Names the exact chock points.")).toBeTruthy();
  expect(best.getByText("Worker 9")).toBeTruthy();
  expect(
    best.getByText("Took 9 minutes. Today’s typical Take 5 took 3 minutes."),
  ).toBeTruthy();
  expect(best.getByRole("link", { name: /Job 9/ }).getAttribute("href")).toBe(
    `/take5s/${BEST.id}`,
  );
  expect(screen.getByText(/An AI helped choose/)).toBeTruthy();
});

it("says under a minute rather than 0 minutes (W9)", async () => {
  stubApi({
    [RANKING_URL]: {
      status: 200,
      body: {
        take5s: [ranked(1)],
        best: { ...BEST, minutes_taken: 0 },
        typical_minutes: 1,
      },
    },
  });
  renderWithApi(<ReviewTodayScreen />);
  expect(
    await screen.findByText(
      "Took under a minute. Today’s typical Take 5 took 1 minute.",
    ),
  ).toBeTruthy();
});

it("says when no Take 5 today was careful enough to be the best (W8)", async () => {
  stubApi({
    [RANKING_URL]: {
      status: 200,
      body: { take5s: [ranked(1)], best: null, typical_minutes: null },
    },
  });
  renderWithApi(<ReviewTodayScreen />);
  expect(
    await screen.findByText(
      "No Take 5 today was free of signs of little thought.",
    ),
  ).toBeTruthy();
});
