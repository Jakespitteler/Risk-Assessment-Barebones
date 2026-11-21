import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { AreaRisk } from "../../api/take5";
import { renderWithApi, stubApi } from "../../test-utils";
import { RiskByAreaScreen } from "./RiskByAreaScreen";

// 2:30 pm on 21 Nov 2026 where the tests run; the 30 days count back from that midnight.
const NOW = new Date(2026, 10, 21, 14, 30);
const MIDNIGHT = new Date(2026, 10, 21).toISOString();
const AREAS_URL = `GET /api/risk-by-area?today=${encodeURIComponent(MIDNIGHT)}`;

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function area(name: string, changed: Partial<AreaRisk> = {}): AreaRisk {
  return {
    name,
    take5_count: 3,
    high_risk_count: 1,
    stopped_count: 0,
    thought_gap_count: 2,
    highest_score: 18,
    highest_band: "Extreme",
    common_yes: [],
    ...changed,
  };
}

it("asks from midnight where the phone is, and says when there is nothing (A2)", async () => {
  const calls = stubApi({
    [AREAS_URL]: { status: 200, body: { areas: [], last_30_days_only: true } },
  });
  renderWithApi(<RiskByAreaScreen />);
  expect(
    await screen.findByRole("heading", { name: "Risk by area" }),
  ).toBeTruthy();
  expect(calls).toEqual([AREAS_URL]);
  expect(
    screen.getByText("No Take 5s with a location in the last 30 days."),
  ).toBeTruthy();
});

it("says there is no time limit when every saved Take 5 counts (D119)", async () => {
  stubApi({
    [AREAS_URL]: { status: 200, body: { areas: [], last_30_days_only: false } },
  });
  renderWithApi(<RiskByAreaScreen />);
  await screen.findByRole("heading", { name: "Risk by area" });
  expect(
    screen.getByText("No saved Take 5s with a location yet."),
  ).toBeTruthy();
});

it.each([
  { lastThirtyDaysOnly: false, period: "in every saved Take 5" },
  { lastThirtyDaysOnly: true, period: "in the last 30 days" },
])(
  "names the time counted above the areas: $period (A2, D119)",
  async ({ lastThirtyDaysOnly, period }) => {
    stubApi({
      [AREAS_URL]: {
        status: 200,
        body: {
          areas: [area("Crusher")],
          last_30_days_only: lastThirtyDaysOnly,
        },
      },
    });
    renderWithApi(<RiskByAreaScreen />);
    await screen.findByRole("heading", { name: "Risk by area" });
    expect(
      screen.getByText(new RegExp(`^Where the jobs were ${period},`)),
    ).toBeTruthy();
  },
);

it("lists the areas hottest first, each with what its Take 5s show (A4, A5)", async () => {
  stubApi({
    [AREAS_URL]: {
      status: 200,
      body: {
        areas: [
          area("Crusher", {
            high_risk_count: 2,
            stopped_count: 1,
            common_yes: [
              { question: "Will I be working at heights?", count: 2 },
            ],
          }),
          area("Light vehicle workshop", {
            take5_count: 1,
            high_risk_count: 0,
            thought_gap_count: 1,
            highest_score: 8,
            highest_band: "Moderate",
          }),
        ],
        last_30_days_only: true,
      },
    },
  });
  renderWithApi(<RiskByAreaScreen />);
  await screen.findByRole("heading", { name: "Risk by area" });

  const headings = screen
    .getAllByRole("heading", { level: 2 })
    .map((heading) => heading.textContent);
  expect(headings).toEqual(["Crusher", "Light vehicle workshop"]);
  const crusher = screen
    .getByRole("heading", { name: "Crusher" })
    .closest("li") as HTMLElement;
  expect(
    within(crusher).getByRole("heading", { name: "Crusher" }),
  ).toBeTruthy();
  expect(within(crusher).getByText("2 of 3 Take 5s high risk")).toBeTruthy();
  expect(
    within(crusher).getByText(
      "Highest risk before controls 18 Extreme. 1 “Don’t start yet”, 2 thought gaps.",
    ),
  ).toBeTruthy();
  expect(
    within(crusher).getByText("Will I be working at heights? (2)"),
  ).toBeTruthy();
  expect(
    screen.getByRole("heading", { name: "Light vehicle workshop" }),
  ).toBeTruthy();
  expect(screen.getByText("0 of 1 Take 5 high risk")).toBeTruthy();
  expect(
    screen.getByText(
      "Highest risk before controls 8 Moderate. 0 “Don’t start yet”, 1 thought gap.",
    ),
  ).toBeTruthy();
});

it("draws each bar beside the hottest area's high-risk count (A4)", async () => {
  stubApi({
    [AREAS_URL]: {
      status: 200,
      body: {
        areas: [
          area("Crusher", { high_risk_count: 4 }),
          area("Workshop", { high_risk_count: 2 }),
        ],
        last_30_days_only: true,
      },
    },
  });
  const { container } = renderWithApi(<RiskByAreaScreen />);
  await screen.findByRole("heading", { name: "Risk by area" });
  const widths = Array.from(
    container.querySelectorAll<HTMLElement>("[aria-hidden='true'] > div"),
  ).map((bar) => bar.style.width);
  expect(widths).toEqual(["100%", "50%"]);
});

it("asks only once when the back end answers with an error", async () => {
  const answered = stubApi({ [AREAS_URL]: { status: 422, body: {} } });
  renderWithApi(<RiskByAreaScreen />);
  await screen.findByRole("heading", {
    name: "Risk by area couldn’t be worked out",
  });
  expect(answered).toHaveLength(1);
});

it("offers to try again when the areas can't be loaded", async () => {
  stubApi({ [AREAS_URL]: { status: 500, body: {} } });
  renderWithApi(<RiskByAreaScreen />);
  expect(
    await screen.findByRole("heading", {
      name: "Risk by area couldn’t be worked out",
    }),
  ).toBeTruthy();
  stubApi({
    [AREAS_URL]: { status: 200, body: { areas: [], last_30_days_only: true } },
  });
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(
    await screen.findByRole("heading", { name: "Risk by area" }),
  ).toBeTruthy();
});

it("says no risk was rated in an area of unrated paper cards (P4)", async () => {
  stubApi({
    [AREAS_URL]: {
      status: 200,
      body: {
        areas: [
          area("Crusher", {
            high_risk_count: 0,
            highest_score: null,
            highest_band: null,
          }),
        ],
        last_30_days_only: false,
      },
    },
  });
  renderWithApi(<RiskByAreaScreen />);
  expect(await screen.findByText(/No risk rated\./)).toBeTruthy();
});
