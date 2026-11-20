import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

export const HAZARD = "Wheel moving while being removed";
export const CONTROL = "Barricade the work area before removing the wheel";

export async function next(page: Page) {
  await page.getByRole("button", { name: "Continue", exact: true }).click();
}

export const QUESTION_HEADING = "One question before you start";
export const ANSWER = "Wheels chocked both sides";

/** Press Submit on the review, which saves the Take 5 and asks its question. */
export async function submit(page: Page) {
  await page
    .getByRole("button", { name: "Submit Take 5", exact: true })
    .click();
}

/** Answer the question asked before the result, and press Finish (spec C4). */
export async function answerQuestion(page: Page, answer = ANSWER) {
  await expect(heading(page, QUESTION_HEADING)).toBeVisible();
  await page.getByRole("textbox").fill(answer);
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
}

/** Submit the Take 5 and answer its question, to reach the result. */
export async function finish(page: Page) {
  await submit(page);
  await answerQuestion(page);
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

/** The screenshot's file name: `name`, ending in `-dark` in the run on a dark phone. */
export function screenshotPath(name: string): string {
  const suffix = test.info().project.name === "dark" ? "-dark" : "";
  return `test-results/screenshots/${name}${suffix}.png`;
}

/**
 * Check the page with Deque's axe: every text colour against what it sits on, to 7 to 1
 * (4.5 to 1 for large text) as well as the usual 4.5 to 1 (spec D76), and the rest of axe's
 * WCAG 2.2 AA rules.
 */
export async function expectReadable(page: Page) {
  // withRules() would replace the tags, so the 7 to 1 rule is turned on as an option.
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .options({ rules: { "color-contrast-enhanced": { enabled: true } } })
    .analyze();
  expect(results.violations).toEqual([]);
}

/**
 * Save a screenshot, and check the page fits the screen (360 px, a small phone, unless the
 * test says otherwise): no sideways scroll, every tap target at least 48 px high, no text
 * smaller than 14 px, and readable to axe.
 */
export async function capture(page: Page, name: string) {
  const screenWidth = page.viewportSize()?.width ?? 360;
  await expect(page.locator("html")).toHaveJSProperty(
    "scrollWidth",
    screenWidth,
  );
  await page.screenshot({ path: screenshotPath(name), fullPage: true });
  await expectReadable(page);
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

const CLICKABLE =
  "button:not(:disabled), a, summary, label:has(input[type=radio]:not(:checked))";

// What the keyboard can reach. A radio group is one stop, so radios are counted by group.
const TAB_STOPS =
  "a[href], button:not(:disabled), summary, input:not(:disabled), textarea, select";

/**
 * Check that everything a person can click on the page changes when the mouse is over it,
 * and shows the app's own focus outline when the keyboard reaches it (spec F2).
 */
export async function expectHoverAndFocus(page: Page) {
  // What shows under the element, so a fill the same colour as the page doesn't count.
  const look = (element: Element) => {
    const style = getComputedStyle(element);
    let fill = style.backgroundColor;
    for (
      let behind = element.parentElement;
      behind && fill === "rgba(0, 0, 0, 0)";
      behind = behind.parentElement
    ) {
      fill = getComputedStyle(behind).backgroundColor;
    }
    return `${fill} ${style.textDecorationThickness} ${style.borderColor}`;
  };
  let hovered = 0;
  for (const target of await page.locator(CLICKABLE).all()) {
    if (!(await target.isVisible())) continue;
    await page.mouse.move(0, 0);
    const before = await target.evaluate(look);
    await target.hover();
    const name = await target.evaluate((element) => element.outerHTML);
    expect(await target.evaluate(look), `${name} changes on hover`).not.toBe(
      before,
    );
    hovered += 1;
  }
  expect(hovered, "something on the page can be clicked").toBeGreaterThan(0);
  await page.mouse.move(0, 0);

  // Tab round the whole page, from wherever the focus is, until it comes back round.
  const seen = await page.evaluateHandle(() => new Set<Element>());
  let cameRound = false;
  for (let step = 0; step < 100 && !cameRound; step += 1) {
    await page.keyboard.press("Tab");
    const outline = await page.evaluate((reached) => {
      const focused = document.activeElement;
      if (!focused || focused === document.body) return null;
      if (reached.has(focused)) return "came round";
      reached.add(focused);
      const shown = focused.matches("input[type=radio]")
        ? (focused.closest("label") ?? focused)
        : focused;
      const style = getComputedStyle(shown);
      const probe = document.createElement("div");
      // On the dark undo bar the outline is the bar's text colour (D97).
      const onDarkBar =
        shown.parentElement?.closest("[role=status].bg-action") != null;
      probe.style.color = onDarkBar
        ? "var(--color-on-action)"
        : "var(--color-focus)";
      document.body.append(probe);
      const focusColour = getComputedStyle(probe).color;
      probe.remove();
      return {
        name: shown.outerHTML,
        look: `${style.outlineStyle} ${style.outlineWidth} ${style.outlineColor}`,
        expected: `solid 4px ${focusColour}`,
      };
    }, seen);
    if (outline === "came round") cameRound = true;
    else if (outline) {
      expect(outline.look, `${outline.name} shows the focus outline`).toBe(
        outline.expected,
      );
    }
  }
  expect(cameRound, "the Tab key came back round the page").toBe(true);
  const missed = await page.evaluate(
    ([reached, selector]) => {
      const groupsReached = new Set(
        [...reached]
          .filter((element) => element.matches("input[type=radio]"))
          .map((element) => element.getAttribute("name")),
      );
      return [...document.querySelectorAll(selector)]
        .filter((element) => element.checkVisibility())
        .filter((element) => !reached.has(element))
        .filter(
          (element) =>
            !(
              element.matches("input[type=radio]") &&
              groupsReached.has(element.getAttribute("name"))
            ),
        )
        .map((element) => element.outerHTML);
    },
    [seen, TAB_STOPS] as const,
  );
  expect(missed, "the Tab key reaches everything clickable").toEqual([]);
  await seen.dispose();
}
