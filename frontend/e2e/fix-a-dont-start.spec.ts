import { expect, test } from "@playwright/test";
import {
  CONTROL,
  HAZARD,
  addControl,
  capture,
  fillJob,
  fillOneHazard,
  finish,
  heading,
  next,
  pick,
} from "./helpers";

const NO_CONTROLS = "No controls: you'll be told not to start.";
const V2_REASON = `Say how you will control: ${HAZARD}`;

test("a Don't start yet is fixed in a new Take 5, and the first stays as it was", async ({
  page,
}) => {
  // A hazard with no controls: the review warns, and Finish still saves it.
  await page.goto("/");
  await fillJob(page);
  await fillOneHazard(page);
  await pick(page, "Possible", "Minor");
  await next(page);
  await next(page);
  await expect(heading(page, "One last look")).toBeVisible();
  await expect(page.getByText(NO_CONTROLS, { exact: true })).toBeVisible();
  await capture(page, "fix-review-warning");
  await finish(page);
  await expect(heading(page, "Don’t start yet")).toBeVisible();
  await expect(page.getByText(V2_REASON, { exact: true })).toBeVisible();
  const firstUrl = page.url();
  const firstSaved: unknown = await (
    await page.request.get(`/api${new URL(firstUrl).pathname}`)
  ).json();
  await capture(page, "fix-dont-start");

  // The copy opens on the review with every answer, and the warning points the way.
  await page
    .getByRole("button", { name: "Fix this in a new Take 5", exact: true })
    .click();
  await expect(heading(page, "One last look")).toBeVisible();
  await expect(page.getByText(/This is a copy of a Take 5/)).toBeVisible();
  await expect(page.getByText(HAZARD, { exact: true })).toBeVisible();
  await expect(page.getByText("Change front tyre on LV12")).toBeVisible();
  await capture(page, "fix-copy-review");
  await page
    .getByRole("button", { name: "Add a control", exact: true })
    .click();
  await expect(heading(page, "What will stop it?")).toBeVisible();
  await addControl(page);
  await next(page);
  await expect(heading(page, "After your controls")).toBeVisible();
  await pick(page, "Unlikely", "Minor");
  await next(page);
  await expect(heading(page, "One last look")).toBeVisible();
  await expect(page.getByText(CONTROL, { exact: true })).toBeVisible();
  await expect(page.getByText(NO_CONTROLS, { exact: true })).toHaveCount(0);
  await finish(page);

  // The fix is Good to go and links back to the first.
  await expect(heading(page, "Good to go")).toBeVisible();
  expect(page.url()).not.toBe(firstUrl);
  await capture(page, "fix-good-to-go");
  await page
    .getByRole("link", { name: "Open the Take 5 it fixes", exact: true })
    .click();

  // The first is unchanged, and links to its fix instead of offering another.
  await expect(heading(page, "Don’t start yet")).toBeVisible();
  expect(page.url()).toBe(firstUrl);
  await expect(page.getByText(V2_REASON, { exact: true })).toBeVisible();
  await expect(page.getByText("No controls listed.")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Fix this in a new Take 5" }),
  ).toHaveCount(0);
  const reopened = (await (
    await page.request.get(`/api${new URL(firstUrl).pathname}`)
  ).json()) as { take5: unknown; fixed_by: string | null };
  expect(reopened.take5).toEqual((firstSaved as { take5: unknown }).take5);
  expect(reopened.fixed_by).not.toBeNull();
  await capture(page, "fix-first-linked");
  await page
    .getByRole("link", { name: "Open the Take 5 that fixes it", exact: true })
    .click();
  await expect(heading(page, "Good to go")).toBeVisible();
});
