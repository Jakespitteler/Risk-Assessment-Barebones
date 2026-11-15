import { expect, it } from "vitest";
import { formatDateTime } from "./formatDateTime";

it("writes the short month, the year and the time with am or pm", () => {
  // The day and hour depend on the time zone the tests run in, so only the shape is fixed.
  expect(formatDateTime("2026-11-14T10:52:00Z")).toMatch(
    /^\d{1,2}\sNov\s2026,\s\d{1,2}:52\s[ap]m$/,
  );
});
