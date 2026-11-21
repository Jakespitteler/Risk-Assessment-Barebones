import { expect, test } from "@playwright/test";
import {
  answerQuestion,
  capture,
  controlledDraft,
  finish,
  heading,
  submit,
} from "./helpers";

test("the saved list opens today's best, then all worst first, each with why (W1, W7, W8)", async ({
  page,
}) => {
  await controlledDraft(page);
  await finish(page);
  await expect(heading(page, "Good to go")).toBeVisible();
  // A careful one: a specific hazard and a full answer, so it can be the best (W8).
  await controlledDraft(
    page,
    ["Possible", "Minor"],
    ["Unlikely", "Minor"],
    {},
    "Wheel rolls off the hub and crushes a foot",
  );
  await submit(page);
  await answerQuestion(page, "Wheels chocked both sides and the nuts torqued");
  await expect(heading(page, "Good to go")).toBeVisible();

  await page.goto("/take5s");
  await page.getByRole("link", { name: "Today’s review", exact: true }).click();
  await expect(heading(page, "Review of all saved")).toBeVisible();
  const ranking = page.getByRole("list");
  const first = ranking.getByRole("listitem").first();
  await expect(first.getByText("1.", { exact: true })).toBeVisible();
  await expect(first.getByText(/^Highest risk \d+ /)).toBeVisible();
  const best = page.getByRole("region", { name: "Best of all saved" });
  await expect(
    best.getByText(/^Highest risk \d+ \w+, with specific hazards/),
  ).toBeVisible();
  await capture(page, "review-today");
});
