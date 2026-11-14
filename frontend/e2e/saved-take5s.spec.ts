import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import {
  addControl,
  answerThinkThrough,
  capture,
  fillOneHazard,
  finish,
  heading,
  next,
  pick,
} from "./helpers";

// Other tests save Take 5s to the same database, so these two are found by their jobs.
const GOOD_JOB = "Check the lights on example water cart WC3";
const STOPPED_JOB = "Swap the screen deck on example crusher CR1";

/**
 * Fill in and save a Take 5 for this job, with one hazard. With a control it is Good to
 * go; without one it is Don't start yet.
 */
async function saveTake5(page: Page, job: string, controlled: boolean) {
  await page.goto("/");
  await page.getByLabel("Your name", { exact: true }).fill("Alex Example");
  await page.getByLabel("What is the job?").fill(job);
  await page.getByLabel("Where will you do it?").fill("Example plant");
  await next(page);
  await answerThinkThrough(page);
  await fillOneHazard(page);
  await pick(page, "Possible", "Minor");
  await next(page);
  if (controlled) {
    await addControl(page);
    await next(page);
    await pick(page, "Unlikely", "Minor");
    await next(page);
  } else await next(page);
  await expect(heading(page, "One last look")).toBeVisible();
  await finish(page);
  await expect(
    heading(page, controlled ? "Good to go" : "Don’t start yet"),
  ).toBeVisible();
}

test("a worker finds saved Take 5s newest first and opens one as it was saved", async ({
  page,
}) => {
  await saveTake5(page, GOOD_JOB, true);
  const goodUrl = page.url();
  await saveTake5(page, STOPPED_JOB, false);
  await capture(page, "saved-result-link");

  // The first page of a new Take 5 links to the list.
  await page.goto("/");
  await expect(heading(page, "The job in front of you")).toBeVisible();
  await capture(page, "saved-job-link");
  await page.getByRole("link", { name: "Saved Take 5s", exact: true }).click();

  // Newest first, each with its verdict, job, worker and date.
  await expect(heading(page, "Saved Take 5s")).toBeVisible();
  const items = page.getByRole("listitem");
  // Newest first, so the first match is this run's, even on a retry.
  const good = items.filter({ hasText: GOOD_JOB }).first();
  const stopped = items.filter({ hasText: STOPPED_JOB }).first();
  await expect(good).toContainText("Good to go");
  await expect(good).toContainText("Alex Example");
  await expect(stopped).toContainText("Don’t start yet");
  await expect(stopped.locator("time")).toHaveText(
    /^\d{1,2}\s[A-Z][a-z]{2}\s\d{4},\s\d{1,2}:\d{2}\s[ap]m$/,
  );
  const jobs = await items.allTextContents();
  expect(jobs.findIndex((text) => text.includes(STOPPED_JOB))).toBeLessThan(
    jobs.findIndex((text) => text.includes(GOOD_JOB)),
  );
  await capture(page, "saved-list");

  // Opening one shows the result screen with the verdict it was saved with.
  await good.getByRole("link").click();
  await expect(heading(page, "Good to go")).toBeVisible();
  expect(page.url()).toBe(goodUrl);
  await expect(page.getByText(GOOD_JOB, { exact: true })).toBeVisible();

  // The result links back to the list.
  await page.getByRole("link", { name: "Saved Take 5s", exact: true }).click();
  await expect(heading(page, "Saved Take 5s")).toBeVisible();
});

test("the list says when nothing has been saved yet", async ({ page }) => {
  // The shared database already has Take 5s from other tests, so the reply is faked.
  await page.route("**/api/take5s", (route) => route.fulfill({ json: [] }));
  await page.goto("/take5s");
  await expect(
    page.getByText("No Take 5s have been saved yet.", { exact: true }),
  ).toBeVisible();
  await capture(page, "saved-list-empty");
});
