import { expect, test } from "@playwright/test";
import {
  addControl,
  answerAll,
  answerThinkThrough,
  capture,
  CHECK,
  expectHoverAndFocus,
  fillJob,
  finish,
  HAZARD,
  heading,
  next,
  pick,
} from "./helpers";

// A desktop screen (spec D65 and F2): every screen of a Take 5 and the saved list still fit,
// with nothing scrolling sideways, and everything on them a person can click changes under
// the mouse and shows the focus outline. Screenshots start with `desktop-`.
test.use({ viewport: { width: 1280, height: 800 } });

test("on a desktop, a whole Take 5 and the saved list fit the screen and react to a mouse and keyboard", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByLabel("Your name", { exact: true })).toBeVisible();
  await capture(page, "desktop-job");
  await expectHoverAndFocus(page);
  await fillJob(page);
  await capture(page, "desktop-think");
  await expectHoverAndFocus(page);
  await answerThinkThrough(page);
  await page.getByLabel("Hazard 1", { exact: true }).fill(HAZARD);
  await capture(page, "desktop-hazards");
  await expectHoverAndFocus(page);
  // The undo bar only shows after a removal.
  await page.getByRole("button", { name: "Remove hazard 1" }).click();
  await expect(page.getByRole("status")).toContainText("Hazard 1 removed.");
  await expectHoverAndFocus(page);
  await page.getByRole("button", { name: "Undo", exact: true }).click();
  await expect(page.getByLabel("Hazard 1", { exact: true })).toHaveValue(
    HAZARD,
  );
  await next(page);
  await answerAll(page, CHECK, "No");
  await capture(page, "desktop-check");
  await expectHoverAndFocus(page);
  await next(page);
  await pick(page, "Possible", "Minor");
  await capture(page, "desktop-before");
  await expectHoverAndFocus(page);
  await next(page);
  await addControl(page);
  await capture(page, "desktop-controls");
  await expectHoverAndFocus(page);
  await next(page);
  await pick(page, "Unlikely", "Minor");
  await capture(page, "desktop-after");
  await expectHoverAndFocus(page);
  await next(page);
  await expect(heading(page, "One last look")).toBeVisible();
  await capture(page, "desktop-review");
  await expectHoverAndFocus(page);
  await finish(page);
  await expect(heading(page, "Good to go")).toBeVisible();
  await capture(page, "desktop-good-to-go");
  await expectHoverAndFocus(page);

  await page.getByRole("link", { name: "Saved Take 5s", exact: true }).click();
  await expect(heading(page, "Saved Take 5s")).toBeVisible();
  await capture(page, "desktop-saved-list");
  await expectHoverAndFocus(page);
});

test("the 5 at the top goes back to the start page", async ({ page }) => {
  await page.goto("/take5s");
  await expect(heading(page, "Saved Take 5s")).toBeVisible();
  await page.getByRole("link", { name: "Take 5 home", exact: true }).click();
  await expect(page).toHaveURL("/");
  await expect(page.getByLabel("Your name", { exact: true })).toBeVisible();
});
