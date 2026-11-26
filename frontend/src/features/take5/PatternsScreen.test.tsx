import { screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { GroupCounts, Patterns } from "../../api/take5";
import { renderWithApi, stubApi } from "../../test-utils";
import { PatternsScreen } from "./PatternsScreen";

const ZONE = Intl.DateTimeFormat().resolvedOptions().timeZone;
const PATTERNS_URL = `GET /api/patterns?zone=${encodeURIComponent(ZONE)}`;
const WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];
const TIMES_OF_DAY = [
  "Midnight to 6 am",
  "6 am to noon",
  "Noon to 6 pm",
  "6 pm to midnight",
];

afterEach(() => {
  vi.unstubAllGlobals();
});

function counts(
  group: string,
  changed: Partial<GroupCounts> = {},
): GroupCounts {
  return {
    group,
    take5_count: 0,
    high_risk_count: 0,
    rushed_count: 0,
    thought_gaps_count: 0,
    stopped_count: 0,
    ...changed,
  };
}

function patterns(changed: Partial<Patterns> = {}): Patterns {
  return {
    take5_count: 10,
    sentences: [],
    by_month: [counts("November 2026", { take5_count: 10 })],
    by_weekday: WEEKDAYS.map((weekday) => counts(weekday)),
    by_time_of_day: TIMES_OF_DAY.map((time) => counts(time)),
    no_time_of_day_count: 0,
    ...changed,
  };
}

it("asks in the phone's time zone, and says when nothing is saved (S1)", async () => {
  const calls = stubApi({
    [PATTERNS_URL]: {
      status: 200,
      body: patterns({ take5_count: 0, by_month: [] }),
    },
  });
  renderWithApi(<PatternsScreen />);
  expect(
    await screen.findByRole("heading", { name: "Patterns over time" }),
  ).toBeTruthy();
  expect(calls).toEqual([PATTERNS_URL]);
  expect(screen.getByText("No Take 5s have been saved yet.")).toBeTruthy();
  expect(screen.queryByRole("table")).toBeNull();
});

it("says when no pattern stands out, and that small numbers can be chance (S4)", async () => {
  stubApi({ [PATTERNS_URL]: { status: 200, body: patterns() } });
  renderWithApi(<PatternsScreen />);
  expect(
    await screen.findByText("No pattern stands out yet in 10 saved Take 5s."),
  ).toBeTruthy();
  expect(screen.getByText(/Small numbers can be chance/)).toBeTruthy();
});

it("shows each sentence with a link to its Take 5s in the table (S4)", async () => {
  stubApi({
    [PATTERNS_URL]: {
      status: 200,
      body: patterns({
        sentences: [
          {
            text: "3 of 5 Take 5s on Mondays were high risk, and none of 5 on other days.",
            table_filters: { weekday: "Monday" },
          },
          {
            text: "3 of 5 Take 5s in November 2026 were rushed, and none of 5 in other months.",
            table_filters: { from: "2026-11-01", to: "2026-11-30" },
          },
        ],
      }),
    },
  });
  renderWithApi(<PatternsScreen />);
  const items = within(await screen.findByRole("list")).getAllByRole(
    "listitem",
  );
  expect(items).toHaveLength(2);
  expect(items[0]?.textContent).toContain("on Mondays were high risk");
  const links = screen.getAllByRole("link", { name: "See these Take 5s" });
  expect(links.map((link) => link.getAttribute("href"))).toEqual([
    "/take5-table?weekday=Monday",
    "/take5-table?from=2026-11-01&to=2026-11-30",
  ]);
});

it("counts each month, weekday and time of day in its own table (S5)", async () => {
  stubApi({
    [PATTERNS_URL]: {
      status: 200,
      body: patterns({
        by_weekday: WEEKDAYS.map((weekday) =>
          weekday === "Monday"
            ? counts(weekday, {
                take5_count: 5,
                high_risk_count: 3,
                rushed_count: 1,
                thought_gaps_count: 2,
                stopped_count: 4,
              })
            : counts(weekday),
        ),
        no_time_of_day_count: 2,
      }),
    },
  });
  renderWithApi(<PatternsScreen />);
  const byWeekday = await screen.findByRole("region", { name: "By weekday" });
  const monday = within(byWeekday).getByRole("row", { name: /^Monday/ });
  expect(
    within(monday)
      .getAllByRole("cell")
      .map((cell) => cell.textContent),
  ).toEqual(["5", "3", "1", "2", "4"]);
  expect(within(byWeekday).getAllByRole("row")).toHaveLength(8);
  expect(screen.getByRole("region", { name: "By month" })).toBeTruthy();
  expect(screen.getByRole("region", { name: "By time of day" })).toBeTruthy();
  expect(
    screen.getByText(
      "2 paper cards have no time written on them, so they aren’t counted here.",
    ),
  ).toBeTruthy();
});

it("offers to try again when the patterns can't be worked out", async () => {
  stubApi({ [PATTERNS_URL]: { status: 500, body: {} } });
  renderWithApi(<PatternsScreen />);
  expect(
    await screen.findByRole("heading", {
      name: "Patterns couldn’t be worked out",
    }),
  ).toBeTruthy();
  expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
});
