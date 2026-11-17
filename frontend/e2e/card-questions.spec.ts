import { expect, test } from "@playwright/test";
import {
  HAZARD,
  CHECK,
  addControl,
  answerAll,
  answerThinkThrough,
  capture,
  controlledDraft,
  fillJob,
  finish,
  heading,
  next,
  pick,
} from "./helpers";

const PERMITS = "Do you have the necessary permits?";
const HEIGHTS = "Will I be working at heights?";

test("a No to a think-through question says Don't start yet (example 19)", async ({
  page,
}) => {
  await controlledDraft(page, undefined, undefined, { [PERMITS]: "No" });
  await expect(
    page.getByText("You answered No: you'll be told not to start.", {
      exact: true,
    }),
  ).toBeVisible();
  await capture(page, "questions-review-no");
  await finish(page);
  await expect(heading(page, "Don’t start yet")).toBeVisible();
  await expect(
    page.getByText(`You answered No to: ${PERMITS} Sort this out first.`, {
      exact: true,
    }),
  ).toBeVisible();
  await capture(page, "questions-result-no");
});

test("N/A to a think-through question is Good to go (example 20)", async ({
  page,
}) => {
  await controlledDraft(page, undefined, undefined, { [PERMITS]: "N/A" });
  await finish(page);
  await expect(heading(page, "Good to go")).toBeVisible();
  await expect(page.getByText("Thinking it through")).toBeVisible();
  await capture(page, "questions-result-na");
});

test("a No's warning at the review opens the question, then comes back", async ({
  page,
}) => {
  await controlledDraft(page, undefined, undefined, { [PERMITS]: "No" });
  await page
    .getByRole("button", { name: "Change answer", exact: true })
    .click();
  await expect(heading(page, "Think it through")).toBeVisible();
  await page
    .getByRole("group", { name: PERMITS })
    .getByText("Yes", { exact: true })
    .click();
  await next(page);
  await expect(heading(page, "One last look")).toBeVisible();
  await finish(page);
  await expect(heading(page, "Good to go")).toBeVisible();
});

test("an unanswered question keeps the worker on the page, named beside it", async ({
  page,
}) => {
  await page.goto("/");
  await fillJob(page);
  await next(page);
  await expect(heading(page, "Think it through")).toBeVisible();
  const first = page.getByRole("group").first();
  await expect(first).toHaveAttribute("aria-invalid", "true");
  await expect(first).toHaveAccessibleDescription("Pick Yes, No or N/A.");
  await expect(first.getByRole("radio").first()).toBeFocused();
  await capture(page, "questions-think-gaps");
});

test("a Yes to a hazard question offers to add it to the list, linked to it", async ({
  page,
}) => {
  await page.goto("/");
  await fillJob(page);
  await answerThinkThrough(page);
  await page.getByLabel("Hazard 1", { exact: true }).fill(HAZARD);
  await next(page);
  await expect(heading(page, "Did you miss any?")).toBeVisible();
  await answerAll(page, CHECK, "No", { [HEIGHTS]: "Yes" });
  await expect(
    page.getByText("Which hazard on your list is this?", { exact: true }),
  ).toBeVisible();
  await capture(page, "questions-hazard-check-yes");

  await page.getByRole("button", { name: "Add a hazard", exact: true }).click();
  await expect(heading(page, "What could hurt someone?")).toBeVisible();
  const added = page.getByLabel("Hazard 2", { exact: true });
  await expect(added).toBeFocused();
  await added.fill("Fall from the trailer deck while loading");
  await next(page);
  await expect(heading(page, "Did you miss any?")).toBeVisible();
  await expect(
    page.getByText("Fall from the trailer deck while loading", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("group", { name: HEIGHTS }).getByRole("radio", {
      name: "Yes",
    }),
  ).toBeChecked();
  await expect(
    page.getByText("On your list: Fall from the trailer deck while loading"),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Add a hazard" })).toHaveCount(
    0,
  );
  await capture(page, "questions-hazard-check-added");
});

test("a Yes needs a hazard picked from the list before Continue (T5)", async ({
  page,
}) => {
  await page.goto("/");
  await fillJob(page);
  await answerThinkThrough(page);
  await page.getByLabel("Hazard 1", { exact: true }).fill(HAZARD);
  await next(page);
  await answerAll(page, CHECK, "No", { [HEIGHTS]: "Yes" });
  await next(page);
  const heights = page.getByRole("group", { name: HEIGHTS });
  await expect(heights).toHaveAccessibleDescription(
    "Pick the hazard on your list that this is, or add it.",
  );
  await capture(page, "link-yes-gap");

  await page
    .getByRole("button", { name: "It’s on my list", exact: true })
    .click();
  await expect(
    page.getByRole("group", { name: "Which one on your list is it?" }),
  ).toBeVisible();
  await capture(page, "link-picker");
  await page.getByText(HAZARD, { exact: true }).last().click();
  await expect(page.getByText(`On your list: ${HAZARD}`)).toBeVisible();
  await capture(page, "link-picked");
  await next(page);
  await expect(heading(page, "Before any controls")).toBeVisible();
  await pick(page, "Possible", "Minor");
  await next(page);
  await addControl(page);
  await next(page);
  await pick(page, "Unlikely", "Minor");
  await next(page);
  await expect(heading(page, "One last look")).toBeVisible();
  await expect(page.getByText(`On your list: ${HAZARD}`)).toBeVisible();
  await finish(page);
  await expect(heading(page, "Good to go")).toBeVisible();
  await expect(page.getByText(`On your list: ${HAZARD}`)).toBeVisible();
  await capture(page, "link-result");
});

const VEHICLES =
  "Am I or others at risk from the operation of vehicles or mobile equipment?";

test("a short hazard picked for a Yes is nudged to be specific (T6)", async ({
  page,
}) => {
  await page.goto("/");
  await fillJob(page);
  await answerThinkThrough(page);
  await page.getByLabel("Hazard 1", { exact: true }).fill(HAZARD);
  await page
    .getByRole("button", { name: "Add another hazard", exact: true })
    .click();
  await page.getByLabel("Hazard 2", { exact: true }).fill("Get hit by a car");
  await next(page);
  await answerAll(page, CHECK, "No", { [VEHICLES]: "Yes" });
  await page
    .getByRole("button", { name: "It’s on my list", exact: true })
    .click();
  await page.getByRole("button", { name: "Get hit by a car" }).click();
  const nudge = page.getByText(
    'Make it specific: say what could hurt you, and where. For example: "Hit by a haul truck at the crib hut crossing"',
  );
  await expect(nudge).toBeVisible();
  await capture(page, "nudge-shown");

  await page
    .getByLabel("Your hazard")
    .fill("Hit by a haul truck at the workshop crossing");
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await expect(nudge).toBeHidden();
  await expect(
    page.getByText(
      "On your list: Hit by a haul truck at the workshop crossing",
    ),
  ).toBeVisible();
  await capture(page, "nudge-reworded");
});

test("keeping a short hazard as it is stops the nudge and never blocks (T6)", async ({
  page,
}) => {
  await page.goto("/");
  await fillJob(page);
  await answerThinkThrough(page);
  await page.getByLabel("Hazard 1", { exact: true }).fill("Crusher dust");
  await next(page);
  await answerAll(page, CHECK, "No", { [HEIGHTS]: "Yes" });
  await page
    .getByRole("button", { name: "It’s on my list", exact: true })
    .click();
  await page.getByRole("button", { name: "Crusher dust" }).click();
  await expect(page.getByLabel("Your hazard")).toBeVisible();
  await page
    .getByRole("button", { name: "Keep it as it is", exact: true })
    .click();
  await expect(page.getByLabel("Your hazard")).toBeHidden();
  await next(page);
  await expect(heading(page, "Before any controls")).toBeVisible();
});
