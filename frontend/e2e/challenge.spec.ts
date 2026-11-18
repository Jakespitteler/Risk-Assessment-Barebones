import { expect, test } from "@playwright/test";
import {
  ANSWER,
  HAZARD,
  QUESTION_HEADING,
  answerQuestion,
  capture,
  controlledDraft,
  heading,
  submit,
} from "./helpers";

// With no AI set up, the back end asks the fixed question about the riskiest hazard.
const FALLBACK = `What is the one thing that has to go right so that '${HAZARD}' doesn't hurt anyone, and how will you check it before you start?`;

test("Submit asks one question, a short answer is refused, and the answer shows on the result", async ({
  page,
}) => {
  await controlledDraft(page);
  await capture(page, "challenge-review-submit");
  await submit(page);

  await expect(heading(page, QUESTION_HEADING)).toBeVisible();
  await expect(page.getByText(FALLBACK, { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Back" })).toHaveCount(0);
  await capture(page, "challenge-question");

  // Example 51: three words are refused beside the box, and nothing is finished.
  await page.getByRole("textbox").fill("Chocked both sides");
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
  await expect(
    page.getByText(
      "Answer in at least four words: say what you'll check or do.",
    ),
  ).toBeVisible();
  await capture(page, "challenge-short-answer");

  await answerQuestion(page);
  await expect(heading(page, "Good to go")).toBeVisible();
  await expect(heading(page, "The question before you started")).toBeVisible();
  await expect(page.getByText(ANSWER, { exact: true })).toBeVisible();
  await capture(page, "challenge-result");

  // A finished Take 5 opens as its result, never as the question again.
  await page.reload();
  await expect(heading(page, "Good to go")).toBeVisible();
});

test("an unanswered Take 5 is kept: the list says so, and opening the app goes back to the question", async ({
  page,
  context,
  browser,
}) => {
  await controlledDraft(page);
  await submit(page);
  await expect(heading(page, QUESTION_HEADING)).toBeVisible();
  const questionUrl = page.url();

  // Leave the question for the list, where it shows as not finished.
  await page.getByRole("link", { name: "Saved Take 5s", exact: true }).click();
  await expect(heading(page, "Saved Take 5s")).toBeVisible();
  await expect(page.getByText("Not finished").first()).toBeVisible();
  await capture(page, "challenge-not-finished-in-list");

  // Another phone sees the question, but can't answer it (decision D47).
  const otherPhone = await browser.newPage({
    viewport: { width: 360, height: 780 },
    deviceScaleFactor: 2,
  });
  await otherPhone.goto(questionUrl);
  await expect(heading(otherPhone, "Not finished yet")).toBeVisible();
  await expect(otherPhone.getByRole("textbox")).toHaveCount(0);
  await capture(otherPhone, "challenge-other-phone");
  await otherPhone.close();

  // Opening the app again, in a new tab on the same phone, goes back to the question.
  await page.close();
  const reopened = await context.newPage();
  await reopened.goto("/");
  await expect(heading(reopened, QUESTION_HEADING)).toBeVisible();
  await expect(reopened.getByText(FALLBACK, { exact: true })).toBeVisible();
  await answerQuestion(reopened);
  await expect(heading(reopened, "Good to go")).toBeVisible();

  // Once it is answered, opening the app starts a new Take 5 again.
  const later = await context.newPage();
  await later.goto("/");
  await expect(heading(later, "The job in front of you")).toBeVisible();
});
