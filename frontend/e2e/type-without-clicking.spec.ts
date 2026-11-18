import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import {
  CHECK,
  HAZARD,
  answerAll,
  answerThinkThrough,
  capture,
  fillJob,
  focusedHeading,
  heading,
  next,
  pick,
} from "./helpers";

const CONTROL =
  "Isolate and lock out the conveyor before going near the pulley";

/** From the hazard list, with hazard 1 written, to the first hazard's controls page. */
async function onToControls(page: Page) {
  await next(page);
  await answerAll(page, CHECK, "No");
  await next(page);
  await expect(heading(page, "Before any controls")).toBeVisible();
  await pick(page, "Possible", "Major");
  await next(page);
  await expect(heading(page, "What will stop it?")).toBeVisible();
}

/** From the job page to the first hazard's controls page, typing without clicking boxes. */
async function typeToControls(page: Page) {
  await page.goto("/");
  await fillJob(page);
  await answerThinkThrough(page);
  await page.keyboard.type(HAZARD);
  await onToControls(page);
}

test.describe("on a computer", () => {
  test("typing goes straight into the first empty box on each page", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByLabel("Your name", { exact: true })).toBeFocused();
    await page.keyboard.type("Sam Example");
    await expect(page.getByLabel("Your name", { exact: true })).toHaveValue(
      "Sam Example",
    );
    await capture(page, "type-job-focused");
    await typeToControls(page);
    await expect(page.getByLabel("Hazard 1")).toHaveCount(0);
    // Control 1 opens empty, with the cursor in it, and no Remove or Add yet.
    await expect(page.getByLabel("What will you do?")).toBeFocused();
    await expect(
      page.getByRole("button", { name: "Add a control", exact: true }),
    ).toHaveCount(0);
    await capture(page, "type-control-1-open");
    await page.keyboard.type(CONTROL);
    await page.getByLabel("Kind of control").selectOption("Isolate the hazard");
    await page
      .getByRole("button", { name: "Add a control", exact: true })
      .click();
    await expect(page.getByLabel("What will you do?").nth(1)).toBeFocused();
    await capture(page, "type-control-2-added");
  });

  test("a hazard left with no controls still goes on with none", async ({
    page,
  }) => {
    await typeToControls(page);
    await next(page);
    await expect(heading(page, "One last look")).toBeVisible();
    await expect(page.getByText("No controls listed.")).toBeVisible();
  });
});

test.describe("on a phone", () => {
  test.use({ hasTouch: true, isMobile: true });

  test("pages open on the heading, so the keyboard stays down", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(focusedHeading(page)).toHaveText("The job in front of you");
    await fillJob(page);
    await answerThinkThrough(page);
    await expect(focusedHeading(page)).toHaveText("What could hurt someone?");
    await page.getByLabel("Hazard 1", { exact: true }).fill(HAZARD);
    await onToControls(page);
    await expect(focusedHeading(page)).toHaveText("What will stop it?");
    await expect(page.getByLabel("What will you do?")).toBeVisible();
    await capture(page, "type-phone-control-1-open");
  });
});
