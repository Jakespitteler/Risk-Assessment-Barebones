import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import {
  THINK,
  answerAll,
  capture,
  controlledDraft,
  fillJob,
  finish,
  heading,
  next,
} from "./helpers";

const JOB = "Change front tyre on LV12";

async function leave(page: Page) {
  await page.getByRole("button", { name: "Leave", exact: true }).click();
  await expect(heading(page, "Leave this Take 5?")).toBeVisible();
}

function button(page: Page, name: string) {
  return page.getByRole("button", { name, exact: true });
}

test("a Take 5 is kept to finish later, thrown away, and put back with Undo", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Saved Take 5s" })).toBeVisible();
  await expect(button(page, "Leave")).toHaveCount(0);
  await fillJob(page);
  await answerAll(page, THINK, "Yes", {
    "Do you have the necessary permits?": "No",
  });

  // Leave asks first, and Keep going changes nothing.
  await capture(page, "drafts-leave-button");
  await leave(page);
  await capture(page, "drafts-leave");
  await button(page, "Keep going").click();
  await expect(heading(page, THINK)).toBeVisible();

  // Kept for later: the list shows it at the top instead of Start a new Take 5.
  await leave(page);
  await button(page, "Keep it for later").click();
  await expect(heading(page, "Saved Take 5s")).toBeVisible();
  await expect(heading(page, "Your unfinished Take 5")).toBeVisible();
  await expect(page.getByText(JOB, { exact: true })).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Start a new Take 5" }),
  ).toHaveCount(0);
  await capture(page, "drafts-kept-in-list");

  // Closing the app and opening it again carries on from the same page and answers.
  await page.goto("/");
  await expect(heading(page, THINK)).toBeVisible();
  await expect(page).toHaveURL(/\?page=think$/);
  await expect(
    page
      .getByRole("group", { name: "Do you have the necessary permits?" })
      .getByRole("radio", { name: "No" }),
  ).toBeChecked();

  // Thrown away: the list offers Undo, which opens it again where it was left.
  await leave(page);
  await button(page, "Throw it away").click();
  await expect(page.getByText("Take 5 thrown away.")).toBeVisible();
  await expect(heading(page, "Your unfinished Take 5")).toHaveCount(0);
  await capture(page, "drafts-thrown-away");
  await button(page, "Undo").click();
  await expect(heading(page, THINK)).toBeVisible();
  await expect(
    page
      .getByRole("group", { name: "Do you have the necessary permits?" })
      .getByRole("radio", { name: "No" }),
  ).toBeChecked();

  // Thrown away for good: a new Take 5 starts empty, with the name remembered only
  // once a Take 5 is saved.
  await leave(page);
  await button(page, "Throw it away").click();
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.getByRole("link", { name: "Start a new Take 5" }).click();
  await expect(heading(page, "The job in front of you")).toBeVisible();
  await expect(page.getByLabel("What is the job?")).toHaveValue("");
});

test("a kept Take 5 more than 2 hours old is thrown away, with the reason", async ({
  page,
}) => {
  await page.goto("/");
  await fillJob(page);
  // Move the draft's start back three hours, as if it was left since breakfast.
  await page.evaluate(() => {
    const stored = JSON.parse(localStorage.getItem("take5-draft") ?? "{}") as {
      draft: { started_at: string };
    };
    stored.draft.started_at = new Date(
      Date.now() - 3 * 60 * 60 * 1000,
    ).toISOString();
    localStorage.setItem("take5-draft", JSON.stringify(stored));
  });

  await page.goto("/take5s");
  await expect(
    heading(page, "Your unfinished Take 5 has run out"),
  ).toBeVisible();
  await expect(
    page.getByText(
      "This Take 5 was started more than 2 hours ago. Start a new one at the job.",
    ),
  ).toBeVisible();
  await capture(page, "drafts-run-out-in-list");
  expect(await page.evaluate(() => localStorage.getItem("take5-draft"))).toBe(
    null,
  );
});

test("opening a Take 5 that has run out shows why, and starts a new one", async ({
  page,
}) => {
  await page.goto("/");
  await fillJob(page);
  await page.evaluate(() => {
    const stored = JSON.parse(localStorage.getItem("take5-draft") ?? "{}") as {
      draft: { started_at: string };
    };
    stored.draft.started_at = new Date(
      Date.now() - 3 * 60 * 60 * 1000,
    ).toISOString();
    localStorage.setItem("take5-draft", JSON.stringify(stored));
  });

  await page.goto("/");
  await expect(heading(page, "This Take 5 has run out")).toBeVisible();
  await expect(page.getByText(/^Started \d{1,2} \w{3} \d{4}/)).toBeVisible();
  await capture(page, "drafts-run-out");
  await button(page, "Start a new Take 5").click();
  await expect(heading(page, "The job in front of you")).toBeVisible();
  await expect(page.getByLabel("What is the job?")).toHaveValue("");
  await expect(page).toHaveURL(/\?page=job$/);
});

test("fixing a Don't start yet asks before it replaces an unfinished Take 5", async ({
  page,
}) => {
  await controlledDraft(page, ["Possible", "Minor"], ["Unlikely", "Minor"], {
    "Do you have the necessary permits?": "No",
  });
  await finish(page);
  await expect(heading(page, "Don’t start yet")).toBeVisible();
  const resultUrl = page.url();

  // An unfinished Take 5 for another job.
  await page.getByRole("link", { name: "Start a new Take 5" }).last().click();
  await page.getByLabel("What is the job?").fill("Replace the conveyor idler");
  await page.getByLabel("Where will you do it?").fill("Example plant");
  await next(page);
  await expect(heading(page, THINK)).toBeVisible();

  await page.goto(resultUrl);
  await button(page, "Fix this in a new Take 5").click();
  await expect(
    page.getByText(
      "You have an unfinished Take 5 for “Replace the conveyor idler”. Fixing this one throws it away.",
    ),
  ).toBeVisible();
  await capture(page, "drafts-fix-asks-first");
  await button(page, "Throw it away and fix this").click();
  await expect(heading(page, "One last look")).toBeVisible();
  await expect(page.getByText(JOB, { exact: true })).toBeVisible();
});
