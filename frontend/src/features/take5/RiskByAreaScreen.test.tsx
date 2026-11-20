import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { AreaRisk } from "../../api/take5";
import { renderWithApi, stubApi } from "../../test-utils";
import { RiskByAreaScreen } from "./RiskByAreaScreen";

// 2:30 pm on 21 Nov 2026 where the tests run; the 30 days count back from that midnight.
const NOW = new Date(2026, 10, 21, 14, 30);
const MIDNIGHT = new Date(2026, 10, 21).toISOString();
const AREAS_URL = `GET /api/risk-by-area?today=${encodeURIComponent(MIDNIGHT)}`;
const SINCE = new Date(2026, 9, 23).toISOString();

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
    dont_start_count: 0,
    thought_gap_count: 2,
    highest_score: 18,
    highest_band: "Extreme",
    common_yes: [],
    ...changed,
  };
}

it("asks from midnight where the phone is, and says when there is nothing (A2)", async () => {
  const calls = stubApi({
    [AREAS_URL]: { status: 200, body: { since: SINCE, areas: [] } },
  });
  renderWithApi(<RiskByAreaScreen />);
  expect(
    await screen.findByRole("heading", { name: "Risk by area" }),
  ).toBeTruthy();
  expect(calls).toEqual([AREAS_URL]);
  expect(
    screen.getByText("No Take 5s have been started in the last 30 days."),
  ).toBeTruthy();
});

it("lists the areas hottest first, each with what its Take 5s show (A4, A5)", async () => {
  stubApi({
    [AREAS_URL]: {
      status: 200,
      body: {
        since: SINCE,
        areas: [
          area("Crusher", {
            high_risk_count: 2,
            dont_start_count: 1,
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
      "Highest risk 18 Extreme. 1 “Don’t start yet”, 2 thought gaps.",
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
      "Highest risk 8 Moderate. 0 “Don’t start yet”, 1 thought gap.",
    ),
  ).toBeTruthy();
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
    [AREAS_URL]: { status: 200, body: { since: SINCE, areas: [] } },
  });
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(
    await screen.findByRole("heading", { name: "Risk by area" }),
  ).toBeTruthy();
});
