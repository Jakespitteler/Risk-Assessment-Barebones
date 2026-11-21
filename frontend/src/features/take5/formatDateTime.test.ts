import { expect, it } from "vitest";
import { formatAsWritten, formatDateTime } from "./formatDateTime";

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

it("writes the day, a three-letter month, the year and the time with am or pm", () => {
  // The hour depends on the time zone the tests run in, so only its shape is fixed.
  expect(formatDateTime("2026-11-14T10:52:00Z")).toMatch(
    /^\d{1,2} Nov 2026, \d{1,2}:52 [ap]m$/,
  );
});

it.each(MONTHS.map((month, index) => [month, index + 1] as const))(
  "writes month %s with three letters",
  (month, number) => {
    // Midday on the 15th is the 15th in every time zone, so the month can't shift.
    const iso = `2026-${String(number).padStart(2, "0")}-15T12:00:00Z`;
    expect(formatDateTime(iso)).toMatch(new RegExp(`^15 ${month} 2026, `));
  },
);

it("writes a paper card's date and time as written, whatever the phone's zone (P5)", () => {
  expect(formatAsWritten("2026-04-03T00:00:00+08:00")).toBe("3 Apr 2026");
  expect(formatAsWritten("2026-04-03T06:40:00+11:00")).toBe(
    "3 Apr 2026, 6:40 am",
  );
  expect(formatAsWritten("2026-09-30T18:05:00-04:00")).toBe(
    "30 Sep 2026, 6:05 pm",
  );
});
