import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import {
  addControl,
  answerThinkThrough,
  capture,
  fillJob,
  fillOneHazard,
  heading,
  next,
  pick,
} from "./helpers";

const QUESTION =
  "Everything here relies on people getting it right. Could you remove, isolate or barricade it?";
const LABEL = "Why aren't stronger controls possible?";
const REASON = "Live testing, so the panel can't be isolated";

async function controls(page: Page) {
  await page.goto("/");
  await fillJob(page);
  await answerThinkThrough(page);
  await fillOneHazard(page);
  await pick(page, "Possible", "Major");
  await next(page);
  await addControl(page);
}

test("T1: direct links, reload and offline Continue cannot reveal questions before a hazard", async ({
  page,
}) => {
  await page.goto("/?page=check");
  await expect(heading(page, "What could hurt someone?")).toBeVisible();
  await expect(
    page.getByText("Will I be working at heights?", { exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Hazard 1", { exact: true }).fill("   ");
  await page.reload();
  await page.route("**/api/take5s/check", (route) => route.abort());
  await next(page);
  await expect(heading(page, "What could hurt someone?")).toBeVisible();
  await expect(
    page.getByText("Will I be working at heights?", { exact: true }),
  ).toHaveCount(0);
  await capture(page, "thinking-own-words");
  await page.getByLabel("Hazard 1", { exact: true }).fill("Moving wheel");
  await next(page);
  await expect(heading(page, "Did you miss any?")).toBeVisible();
  await page.goBack();
  await page.getByLabel("Hazard 1", { exact: true }).fill("");
  await page.goForward();
  await expect(heading(page, "What could hurt someone?")).toBeVisible();
});

test("T2: a vague control is rejected beside its field and concrete wording can continue", async ({
  page,
}) => {
  await controls(page);
  await page.getByLabel("What will you do?").fill("Be careful.");
  await next(page);
  await expect(page.getByText("Say what you'll actually do.")).toBeVisible();
  await expect(page.getByLabel("What will you do?")).toBeFocused();
  await capture(page, "thinking-vague-control");
  await page
    .getByLabel("What will you do?")
    .fill("Be careful of the pinch point when lowering the tray");
  await next(page);
  await expect(heading(page, "After your controls")).toBeVisible();
});

test("T3: a required answer survives reload, review, saving and reopening without changing the verdict", async ({
  page,
}) => {
  await controls(page);
  await page.getByLabel("What will you do?").fill("Wear insulating gloves");
  await page.getByLabel("Kind of control").selectOption("Wear PPE");
  await expect(page.getByText(QUESTION)).toBeVisible();
  await next(page);
  await expect(page.getByLabel(LABEL)).toBeFocused();
  await expect(page.getByLabel(LABEL)).toHaveAttribute("aria-invalid", "true");
  await capture(page, "thinking-weak-controls");
  await page.getByLabel(LABEL).pressSequentially(REASON);
  await expect(page.getByLabel(LABEL)).toBeFocused();
  await page.reload();
  await expect(page.getByLabel(LABEL)).toHaveValue(REASON);
  await next(page);
  await pick(page, "Rare", "Major");
  await next(page);
  await expect(heading(page, "One last look")).toBeVisible();
  await expect(page.getByText(REASON, { exact: true })).toBeVisible();
  await capture(page, "thinking-review");
  await page.getByRole("button", { name: "Finish Take 5" }).click();
  await expect(heading(page, "Good to go")).toBeVisible();
  await expect(page.getByText(REASON, { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText(REASON, { exact: true })).toBeVisible();
  await expect(heading(page, "Good to go")).toBeVisible();
  await capture(page, "thinking-result");
});

test("T3: adding a strong control removes the requirement and undo restores it", async ({
  page,
}) => {
  await controls(page);
  await page.getByLabel("What will you do?").fill("Wear insulating gloves");
  await page.getByLabel("Kind of control").selectOption("Wear PPE");
  await expect(page.getByLabel(LABEL)).toBeVisible();
  await page
    .getByRole("button", { name: "Add a control", exact: true })
    .click();
  await page.getByLabel("What will you do?").nth(1).fill("Isolate the supply");
  await page
    .getByLabel("Kind of control")
    .nth(1)
    .selectOption("Isolate the hazard");
  await expect(page.getByLabel(LABEL)).toHaveCount(0);
  await page.getByRole("button", { name: "Remove control 2" }).click();
  await expect(page.getByLabel(LABEL)).toBeVisible();
  await page.getByRole("button", { name: "Undo", exact: true }).click();
  await expect(page.getByLabel(LABEL)).toHaveCount(0);
  await next(page);
  await expect(heading(page, "After your controls")).toBeVisible();
});

test("T4: a three-word job is blocked beside the field, and four words can continue", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Your name", { exact: true }).fill("Sam Example");
  await page.getByLabel("What is the job?").fill("Change the tyre");
  await page.getByLabel("Where will you do it?").fill("Example workshop");
  await next(page);
  await expect(
    page.getByText("Describe the job in at least four words."),
  ).toBeVisible();
  await expect(page.getByLabel("What is the job?")).toBeFocused();
  await capture(page, "thinking-short-job");
  await page.getByLabel("What is the job?").fill("Change tyre on LV12");
  await next(page);
  await expect(heading(page, "Think it through")).toBeVisible();
});

test("T3: adding an unfinished control keeps an existing answer visible", async ({
  page,
}) => {
  await controls(page);
  await page.getByLabel("What will you do?").fill("Wear insulating gloves");
  await page.getByLabel("Kind of control").selectOption("Wear PPE");
  await page.getByLabel(LABEL).fill(REASON);
  await page
    .getByRole("button", { name: "Add a control", exact: true })
    .click();
  await expect(page.getByText(QUESTION)).toHaveCount(0);
  await expect(page.getByLabel(LABEL)).toHaveValue(REASON);
  await expect(
    page.getByText("Your earlier answer is kept. You can still edit it."),
  ).toBeVisible();
  await capture(page, "thinking-kept-answer");
});
