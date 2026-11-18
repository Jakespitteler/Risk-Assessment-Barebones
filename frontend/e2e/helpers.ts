import { expect } from "@playwright/test";
import type { Page } from "@playwright/test";

export const HAZARD = "Wheel moving while being removed";
export const CONTROL = "Barricade the work area before removing the wheel";

export async function next(page: Page) {
  await page.getByRole("button", { name: "Continue", exact: true }).click();
}

export async function finish(page: Page) {
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
}

export async function back(page: Page) {
  await page.getByRole("button", { name: "Back", exact: true }).click();
}

export function heading(page: Page, name: string) {
  return page.getByRole("heading", { name, exact: true });
}

export async function fillJob(page: Page) {
  await page.getByLabel("Your name", { exact: true }).fill("Sam Example");
  await page.getByLabel("What is the job?").fill("Change front tyre on LV12");
  await page.getByLabel("Where will you do it?").fill("Example workshop");
  await next(page);
  await expect(heading(page, "Think it through")).toBeVisible();
}

export const THINK = "Think it through";
export const CHECK = "Did you miss any?";

/**
 * Once the page with this heading shows, answer each of its questions, by wording:
 * as `changed` says, or else `answer`.
 */
export async function answerAll(
  page: Page,
  pageHeading: string,
  answer: string,
  changed: Record<string, string> = {},
) {
  await expect(heading(page, pageHeading)).toBeVisible();
  for (const group of await page.getByRole("group").all()) {
    const question = (await group.locator("legend").textContent()) ?? "";
    await group.getByText(changed[question] ?? answer, { exact: true }).click();
  }
}

/** Answer the think-through questions, Yes unless `changed` says otherwise. */
export async function answerThinkThrough(
  page: Page,
  changed: Record<string, string> = {},
) {
  await answerAll(page, THINK, "Yes", changed);
  await next(page);
  await expect(heading(page, "What could hurt someone?")).toBeVisible();
}

/** List one hazard, then answer every hazard question No. */
export async function fillOneHazard(page: Page) {
  await page.getByLabel("Hazard 1", { exact: true }).fill(HAZARD);
  await next(page);
  await answerAll(page, CHECK, "No");
  await next(page);
  await expect(heading(page, "Before any controls")).toBeVisible();
}

export async function pick(
  page: Page,
  likelihood: string,
  consequence: string,
) {
  await page
    .getByRole("group", { name: "How likely is it?" })
    .getByText(likelihood, { exact: true })
    .click();
  await page
    .getByRole("group", { name: "How bad would it be?" })
    .getByText(consequence, { exact: true })
    .click();
}

/** Fill in control 1, which a hazard with no controls opens with, empty. */
export async function addControl(page: Page) {
  await page.getByLabel("What will you do?").fill(CONTROL);
  await page.getByLabel("Kind of control").selectOption("Barricade the hazard");
}

/** Fill in a whole Take 5 with one controlled hazard, and stop on the review. */
export async function controlledDraft(
  page: Page,
  before: [string, string] = ["Possible", "Minor"],
  after: [string, string] = ["Unlikely", "Minor"],
  thinkAnswers: Record<string, string> = {},
) {
  await page.goto("/");
  await fillJob(page);
  await answerThinkThrough(page, thinkAnswers);
  await fillOneHazard(page);
  await pick(page, ...before);
  await next(page);
  await addControl(page);
  await next(page);
  await pick(page, ...after);
  await next(page);
  await expect(heading(page, "One last look")).toBeVisible();
}

/**
 * Save a 360 px screenshot, and check the page fits a small phone: no sideways scroll,
 * every tap target at least 48 px high, and no text smaller than 14 px.
 */
export async function capture(page: Page, name: string) {
  await expect(page.locator("html")).toHaveJSProperty("scrollWidth", 360);
  await page.screenshot({
    path: `test-results/screenshots/${name}.png`,
    fullPage: true,
  });
  const targets = page.locator(
    "button, a, input:not([type=radio]), textarea, select, summary, label:has(input[type=radio])",
  );
  for (const target of await targets.all()) {
    if (!(await target.isVisible())) continue;
    const bounds = await target.boundingBox();
    expect(
      bounds?.height,
      "a tap target is at least 48 px high",
    ).toBeGreaterThanOrEqual(48);
  }
  const smallest = await page.evaluate(() => {
    const sizes = Array.from(document.body.querySelectorAll("*"))
      .filter((element) =>
        Array.from(element.childNodes).some(
          (node) =>
            node.nodeType === Node.TEXT_NODE && node.textContent?.trim(),
        ),
      )
      .map((element) => parseFloat(getComputedStyle(element).fontSize));
    return Math.min(...sizes);
  });
  expect(smallest, "no text is smaller than 14 px").toBeGreaterThanOrEqual(14);
}

/** The heading the focus moved to, so a screen reader starts at the new page. */
export function focusedHeading(page: Page) {
  return page.locator("h1:focus");
}
