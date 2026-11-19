import { expect, it } from "vitest";
import { timeLeftText } from "./timeLeftText";

const NOW = new Date("2026-11-16T03:00:00Z");

it.each([
  ["2026-11-16T05:00:00Z", "2 hr left"],
  ["2026-11-16T04:42:30Z", "1 hr 42 min left"],
  ["2026-11-16T03:42:00Z", "42 min left"],
  ["2026-11-16T03:01:00Z", "1 min left"],
  ["2026-11-16T03:00:59Z", "Under 1 min left"],
  ["2026-11-16T02:50:00Z", "Under 1 min left"],
])("counts down to %s as %s", (runsOutAt, expected) => {
  expect(timeLeftText(runsOutAt, NOW)).toBe(expected);
});
