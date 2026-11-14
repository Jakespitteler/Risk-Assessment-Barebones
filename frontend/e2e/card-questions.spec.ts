import { expect, test } from "@playwright/test";
import {
  HAZARD,
  CHECK,
  answerAll,
  answerThinkThrough,
  capture,
  controlledDraft,
  fillJob,
  finish,
  heading,
  next,
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

test("a Yes to a hazard question offers to add it to the list", async ({
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
    page.getByText("Make sure it’s on your list.", { exact: true }),
  ).toBeVisible();
  await capture(page, "questions-hazard-check-yes");

  await page.getByRole("button", { name: "Add a hazard", exact: true }).click();
  await expect(heading(page, "What could hurt someone?")).toBeVisible();
  const added = page.getByLabel("Hazard 2", { exact: true });
  await expect(added).toBeFocused();
  await added.fill("Fall from the trailer deck");
  await next(page);
  await expect(heading(page, "Did you miss any?")).toBeVisible();
  await expect(
    page.getByText("Fall from the trailer deck", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("group", { name: HEIGHTS }).getByRole("radio", {
      name: "Yes",
    }),
  ).toBeChecked();
  await expect(page.getByText("Added to your list")).toBeVisible();
  await expect(page.getByRole("button", { name: "Add a hazard" })).toHaveCount(
    0,
  );
  await capture(page, "questions-hazard-check-added");
});
