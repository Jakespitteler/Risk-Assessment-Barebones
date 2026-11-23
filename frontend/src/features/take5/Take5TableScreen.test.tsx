import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Take5Row, Take5TablePage } from "../../api/take5";
import { renderWithApi, stubApi } from "../../test-utils";
import { Take5TableScreen } from "./Take5TableScreen";

const ZONE = Intl.DateTimeFormat().resolvedOptions().timeZone;

afterEach(() => {
  vi.unstubAllGlobals();
});

function tableUrl(filters = "") {
  const query = new URLSearchParams(filters);
  query.set("zone", ZONE);
  return `GET /api/take5-table?${query.toString()}`;
}

function row(changed: Partial<Take5Row> = {}): Take5Row {
  return {
    id: "11111111-1111-4111-8111-111111111111",
    started_at: "2026-11-21T07:00:00+08:00",
    saved_at: "2026-11-20T23:10:00Z",
    started_on: "2026-11-21",
    month: "2026-11",
    weekday: "Saturday",
    time_of_day: "6 am to noon",
    worker_name: "Sam Example",
    job: "Change tyre on LV12",
    location: "Example workshop",
    verdict: "Good to go",
    importance: 8,
    highest_score: 8,
    highest_band: "Moderate",
    needs_jha: false,
    why: "Highest risk 8 Moderate. No signs of a rushed Take 5.",
    thought_gaps: [],
    rushed: false,
    minutes_taken: 10,
    hazard_count: 1,
    control_count: 1,
    strong_control: true,
    answers: { keys: "Yes" },
    from_paper: false,
    ...changed,
  };
}

const PAGE: Take5TablePage = {
  rows: [
    row({
      id: "22222222-2222-4222-8222-222222222222",
      importance: 23,
      highest_score: 18,
      highest_band: "Extreme",
      needs_jha: true,
      verdict: "Don't start yet",
      thought_gaps: ["it was filled in in under 2 minutes"],
      rushed: true,
    }),
    row(),
  ],
  areas: ["Example workshop"],
  bands: ["Low", "Moderate", "High", "Extreme"],
};

function open(filters = "", onFilters = vi.fn()) {
  renderWithApi(
    <Take5TableScreen
      filters={new URLSearchParams(filters)}
      onFilters={onFilters}
    />,
  );
  return onFilters;
}

it("lists every Take 5, the most important first, as the back end sends them (E1, E2)", async () => {
  const calls = stubApi({ [tableUrl()]: { status: 200, body: PAGE } });
  open();
  expect(await screen.findByText("2 Take 5s match.")).toBeTruthy();
  expect(calls).toEqual([tableUrl()]);
  const table = screen.getByRole("region", {
    name: "Take 5s, the most important first",
  });
  const [, first, second] = within(table).getAllByRole("row");
  expect(within(first as HTMLElement).getByText("23")).toBeTruthy();
  expect(within(first as HTMLElement).getByText("18 Extreme")).toBeTruthy();
  expect(within(first as HTMLElement).getByText("Needs a JHA")).toBeTruthy();
  expect(within(first as HTMLElement).getByText("Rushed")).toBeTruthy();
  expect(within(second as HTMLElement).getByText("8")).toBeTruthy();
  expect(
    within(second as HTMLElement)
      .getByRole("link", { name: "Change tyre on LV12" })
      .getAttribute("href"),
  ).toBe("/take5s/11111111-1111-4111-8111-111111111111");
});

it("asks the back end for the filters in the address, and downloads the same rows (E4, E5)", async () => {
  const filters = "verdict=Don%27t+start+yet&band=Extreme";
  const calls = stubApi({ [tableUrl(filters)]: { status: 200, body: PAGE } });
  open(filters);
  await screen.findByText("2 Take 5s match.");
  expect(calls).toEqual([tableUrl(filters)]);
  expect(screen.getByLabelText("Verdict")).toHaveProperty(
    "value",
    "Don't start yet",
  );
  expect(
    screen.getByRole("link", { name: "Download CSV" }).getAttribute("href"),
  ).toBe(
    tableUrl(filters).replace("GET /api/take5-table?", "/api/take5-table.csv?"),
  );
});

it("puts a chosen filter in the address, and clears them all (F11)", async () => {
  stubApi({ [tableUrl("band=Extreme")]: { status: 200, body: PAGE } });
  const onFilters = open("band=Extreme");
  await screen.findByText("2 Take 5s match.");
  fireEvent.change(screen.getByLabelText("Weekday"), {
    target: { value: "Monday" },
  });
  expect((onFilters.mock.calls[0]?.[0] as URLSearchParams).toString()).toBe(
    "band=Extreme&weekday=Monday",
  );
  fireEvent.click(screen.getByRole("button", { name: "Clear the filters" }));
  expect((onFilters.mock.calls[1]?.[0] as URLSearchParams).toString()).toBe("");
});

it("offers the areas and bands the back end sends", async () => {
  stubApi({ [tableUrl()]: { status: 200, body: PAGE } });
  open();
  await screen.findByText("2 Take 5s match.");
  const area = screen.getByLabelText("Area");
  expect(
    within(area)
      .getAllByRole("option")
      .map((option) => option.textContent),
  ).toEqual(["Any", "Example workshop"]);
});

it("shows a paper card's own date, with no time of day (E3, P5)", async () => {
  stubApi({
    [tableUrl()]: {
      status: 200,
      body: {
        ...PAGE,
        rows: [
          row({
            from_paper: true,
            started_at: "2026-04-03T00:00:00+08:00",
            time_of_day: null,
            weekday: "Friday",
          }),
        ],
      },
    },
  });
  open();
  expect(await screen.findByText("3 Apr 2026")).toBeTruthy();
  const table = screen.getByRole("region", {
    name: "Take 5s, the most important first",
  });
  expect(within(table).getByText("From paper")).toBeTruthy();
  expect(within(table).getByText("Friday")).toBeTruthy();
});

it("says when nothing matches, with no download", async () => {
  stubApi({
    [tableUrl("search=crusher")]: { status: 200, body: { ...PAGE, rows: [] } },
  });
  open("search=crusher");
  expect(await screen.findByText("0 Take 5s match.")).toBeTruthy();
  expect(screen.queryByRole("link", { name: "Download CSV" })).toBeNull();
});
