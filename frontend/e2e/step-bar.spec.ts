import { expect, test } from "@playwright/test";
import { capture, controlledDraft, fillJob, heading } from "./helpers";

function step(page: import("@playwright/test").Page, name: string) {
  return page
    .getByRole("navigation", { name: "Take 5 steps" })
    .getByRole("button", { name, exact: true });
}

test("a new Take 5 can only tap the steps it has reached", async ({ page }) => {
  await page.goto("/");
  await expect(heading(page, "The job in front of you")).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Take 5 steps" }).getByRole("button"),
  ).toHaveCount(0);
  await capture(page, "step-bar-new");
  await fillJob(page);
  await expect(step(page, "Job")).toBeVisible();
  await expect(step(page, "Hazards")).toHaveCount(0);
  await capture(page, "step-bar-think");
});

test("the step bar goes back, and forward again only past a page with no gaps", async ({
  page,
}) => {
  await controlledDraft(page);
  await capture(page, "step-bar-review");

  await step(page, "Job").click();
  await expect(heading(page, "The job in front of you")).toBeVisible();
  await capture(page, "step-bar-back-to-job");

  // A gap on this page keeps the worker here, as Continue does.
  const location = page.getByLabel("Where will you do it?");
  await location.fill("");
  await step(page, "Review").click();
  await expect(heading(page, "The job in front of you")).toBeVisible();
  await expect(location).toBeFocused();
  await capture(page, "step-bar-gap");

  await location.fill("Example workshop");
  await step(page, "Review").click();
  await expect(heading(page, "One last look")).toBeVisible();

  // The back gesture undoes a tap, as it undoes Continue.
  await page.goBack();
  await expect(heading(page, "The job in front of you")).toBeVisible();

  await step(page, "Assess").click();
  await expect(heading(page, "Before any controls")).toBeVisible();
  await capture(page, "step-bar-assess");
});
