import { expect, test } from "@playwright/test";
import {
  CONTROL,
  HAZARD,
  addControl,
  back,
  capture,
  controlledDraft,
  fillJob,
  fillOneHazard,
  finish,
  focusedHeading,
  heading,
  next,
  pick,
} from "./helpers";

// Two retries, a second apart and doubling, after the first try.
const RETRIES_DONE = { timeout: 15_000 };

test("a worker fills in, saves, reopens and starts a new Take 5", async ({
  page,
}) => {
  const requests: string[] = [];
  page.on("request", (request) => {
    requests.push(`${request.method()} ${new URL(request.url()).pathname}`);
  });
  await page.goto("/");
  await expect(page.getByLabel("Your name", { exact: true })).toHaveValue("");
  await capture(page, "take5-job");
  await fillJob(page);
  await expect(focusedHeading(page)).toHaveText("What could hurt someone?");
  await page.getByLabel("Hazard 1", { exact: true }).fill(HAZARD);
  await capture(page, "take5-hazards");
  await next(page);
  await expect(page.getByRole("radio", { checked: true })).toHaveCount(0);
  await page.getByText("What do the ratings mean?").click();
  await expect(
    page.getByText("First aid treatment.", { exact: true }),
  ).toBeVisible();
  await page.getByText("What do the ratings mean?").click();
  await pick(page, "Possible", "Minor");
  await expect(page.getByRole("status", { name: "Risk score" })).toHaveText(
    "8Moderate",
  );
  await capture(page, "take5-before");
  await next(page);
  await addControl(page);
  await capture(page, "take5-controls");
  await next(page);
  await expect(page.getByRole("radio", { checked: true })).toHaveCount(0);
  await pick(page, "Unlikely", "Minor");
  await capture(page, "take5-after");
  await next(page);
  await expect(heading(page, "One last look")).toBeVisible();
  await expect(page.getByText(CONTROL, { exact: true })).toBeVisible();
  await capture(page, "take5-review");
  expect(requests).not.toContain("POST /api/take5s");

  await finish(page);
  await expect(heading(page, "Good to go")).toBeVisible();
  await capture(page, "take5-good-to-go");
  // The result came with the save, so the result screen didn't fetch it again.
  expect(
    requests.filter((request) => request.startsWith("GET /api/take5s/")),
  ).toEqual([]);
  expect(
    requests.filter((request) => request === "POST /api/take5s"),
  ).toHaveLength(1);

  await page.reload();
  await expect(heading(page, "Good to go")).toBeVisible();
  await expect(page.getByText(HAZARD, { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Start a new Take 5" }).first().click();
  await expect(page.getByLabel("Your name", { exact: true })).toHaveValue(
    "Sam Example",
  );
  await expect(page.getByLabel("What is the job?")).toHaveValue("");
});

test("a rating of 12 says Don't start yet with the JHA reason", async ({
  page,
}) => {
  await controlledDraft(page, ["Likely", "Minor"], ["Likely", "Minor"]);
  await finish(page);
  await expect(heading(page, "Don’t start yet")).toBeVisible();
  await expect(
    page.getByText(
      "The risk is High (12). At 11 or more you need a JHA before you start. Talk to your supervisor.",
      { exact: true },
    ),
  ).toBeVisible();
  await capture(page, "take5-dont-start");
});

test("a hazard with no controls skips the second rating and stops the job", async ({
  page,
}) => {
  await page.goto("/");
  await fillJob(page);
  await fillOneHazard(page);
  await pick(page, "Possible", "Minor");
  await next(page);
  await next(page);
  await expect(heading(page, "One last look")).toBeVisible();
  await finish(page);
  await expect(heading(page, "Don’t start yet")).toBeVisible();
  await expect(
    page.getByText(`Say how you will control: ${HAZARD}`, { exact: true }),
  ).toBeVisible();
  // The overall rating, the before rating and the after rating are all 8.
  await expect(page.getByText("8", { exact: true })).toHaveCount(3);
});

test("Continue shows that page's gaps there and puts the cursor in the first", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Your name", { exact: true }).fill("");
  await next(page);
  await expect(heading(page, "The job in front of you")).toBeVisible();
  const name = page.getByLabel("Your name", { exact: true });
  await expect(name).toHaveAttribute("aria-invalid", "true");
  await expect(name).toHaveAccessibleDescription("Fill in this field.");
  await expect(name).toBeFocused();
  await expect(
    page.getByLabel("Where will you do it?"),
  ).toHaveAccessibleDescription("Fill in this field.");
  await capture(page, "take5-field-errors");
  await name.fill("Sam Example");
  await expect(name).toHaveAttribute("aria-invalid", "false");
});

test("Enter in a one-line box continues; in a bigger box it starts a new line", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Your name", { exact: true }).fill("Sam Example");
  const job = page.getByLabel("What is the job?");
  await job.fill("Change front tyre");
  await job.press("Enter");
  await job.pressSequentially("on LV12");
  await expect(job).toHaveValue("Change front tyre\non LV12");
  await expect(heading(page, "The job in front of you")).toBeVisible();
  await page.getByLabel("Where will you do it?").fill("Example workshop");
  await page.getByLabel("Where will you do it?").press("Enter");
  await expect(heading(page, "What could hurt someone?")).toBeVisible();
  await page.getByLabel("Hazard 1", { exact: true }).fill(HAZARD);
  await page.getByLabel("Hazard 1", { exact: true }).press("Enter");
  await expect(heading(page, "What could hurt someone?")).toBeVisible();
  await next(page);
  await pick(page, "Possible", "Minor");
  await page.getByRole("radio", { name: "Minor" }).press("Enter");
  await expect(heading(page, "What will stop it?")).toBeVisible();
});

test("Enter while Continue is checking sends one check and moves on once", async ({
  page,
}) => {
  let checks = 0;
  let release: () => void = () => {
    throw new Error("The gate is not set up yet.");
  };
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/take5s/check", async (route) => {
    checks++;
    await gate;
    await route.continue();
  });
  await page.goto("/");
  await page.getByLabel("Your name", { exact: true }).fill("Sam Example");
  await page.getByLabel("What is the job?").fill("Change front tyre on LV12");
  const location = page.getByLabel("Where will you do it?");
  await location.fill("Example workshop");
  await location.press("Enter");
  await expect(
    page.getByRole("button", { name: "Checking…", exact: true }),
  ).toBeDisabled();
  await location.press("Enter");
  release();
  await expect(heading(page, "What could hurt someone?")).toBeVisible();
  expect(checks).toBe(1);
});

test("a gap found at the review is fixed in place, then back to the review", async ({
  page,
}) => {
  await controlledDraft(page);
  await page.goto("/?page=job");
  await page.getByLabel("Your name", { exact: true }).fill("");
  await page.goto("/?page=review");
  await expect(heading(page, "The job in front of you")).toBeVisible();
  await expect(page.getByLabel("Your name", { exact: true })).toBeFocused();
  await page.getByLabel("Your name", { exact: true }).fill("Sam Example");
  await next(page);
  await expect(heading(page, "One last look")).toBeVisible();
});

test("controls that raise the risk are stopped on the after page (example 15)", async ({
  page,
}) => {
  await page.goto("/");
  await fillJob(page);
  await fillOneHazard(page);
  await pick(page, "Unlikely", "Minor");
  await next(page);
  await addControl(page);
  await next(page);
  await pick(page, "Possible", "Minor");
  await next(page);
  await expect(heading(page, "After your controls")).toBeVisible();
  await expect(
    page.getByText("Controls cannot make the after risk higher than before.", {
      exact: true,
    }),
  ).toBeVisible();
});

test("a lost answer to Finish is retried by itself and saves one Take 5", async ({
  page,
}) => {
  const answers: string[] = [];
  await page.route("**/api/take5s", async (route) => {
    const response = await route.fetch();
    answers.push(await response.text());
    if (answers.length === 1) await route.abort();
    else await route.fulfill({ response });
  });
  await controlledDraft(page);
  await finish(page);
  await expect(heading(page, "Good to go")).toBeVisible(RETRIES_DONE);
  expect(answers).toHaveLength(2);
  expect(answers[1]).toBe(answers[0]);
});

test("with no signal the answers stay, and Finish works once it is back", async ({
  page,
}) => {
  await page.route("**/api/take5s", (route) => route.abort());
  await controlledDraft(page);
  await finish(page);
  await expect(page.getByText(/Your answers are still here/)).toBeVisible(
    RETRIES_DONE,
  );
  await expect(page.getByText(CONTROL, { exact: true })).toBeVisible();
  await page.unroute("**/api/take5s");
  await finish(page);
  await expect(heading(page, "Good to go")).toBeVisible();
});

test("the back gesture and a reload keep every answer", async ({ page }) => {
  await page.goto("/");
  await fillJob(page);
  await page
    .getByLabel("Hazard 1", { exact: true })
    .fill("First example hazard");
  await page.getByRole("button", { name: "Add another hazard" }).click();
  await page
    .getByLabel("Hazard 2", { exact: true })
    .fill("Second example hazard");
  await next(page);
  await expect(
    page.getByText("First example hazard", { exact: true }),
  ).toBeVisible();
  await pick(page, "Rare", "Low");
  await next(page);
  await next(page);
  await expect(
    page.getByText("Second example hazard", { exact: true }),
  ).toBeVisible();

  await page.goBack();
  await expect(heading(page, "What will stop it?")).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("radio", { name: "Rare", exact: true }),
  ).toBeChecked();
  await expect(focusedHeading(page)).toHaveText("Before any controls");
  await page.reload();
  await expect(
    page.getByRole("radio", { name: "Rare", exact: true }),
  ).toBeChecked();
  await back(page);
  await expect(page.getByLabel("Hazard 2", { exact: true })).toHaveValue(
    "Second example hazard",
  );
});

test("a removed hazard can be put back", async ({ page }) => {
  await page.goto("/");
  await fillJob(page);
  await page.getByLabel("Hazard 1", { exact: true }).fill(HAZARD);
  await page.getByRole("button", { name: "Remove hazard 1" }).click();
  await expect(page.getByLabel("Hazard 1", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("status")).toContainText("Hazard 1 removed.");
  await capture(page, "take5-undo");
  await page.getByRole("button", { name: "Undo", exact: true }).click();
  await expect(page.getByLabel("Hazard 1", { exact: true })).toHaveValue(
    HAZARD,
  );
});

test("Finish can't be pressed twice while saving, so one Take 5 is sent", async ({
  page,
}) => {
  let submissions = 0;
  let release: () => void = () => {
    throw new Error("The gate is not set up yet.");
  };
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/take5s", async (route) => {
    submissions++;
    await gate;
    await route.continue();
  });
  await controlledDraft(page);
  await finish(page);
  const saving = page.getByRole("button", { name: "Saving…", exact: true });
  await expect(saving).toBeDisabled();
  await saving.dispatchEvent("click");
  release();
  await expect(heading(page, "Good to go")).toBeVisible();
  expect(submissions).toBe(1);
});

test("changed answers after a lost save can't replace the saved Take 5", async ({
  page,
}) => {
  let saved = false;
  await page.route("**/api/take5s", async (route) => {
    // The first try is saved but its answer is lost; the retries get no signal.
    if (!saved) {
      saved = true;
      await route.fetch();
    }
    await route.abort();
  });
  await controlledDraft(page);
  await finish(page);
  await expect(page.getByText(/Your answers are still here/)).toBeVisible(
    RETRIES_DONE,
  );
  await page.unroute("**/api/take5s");
  await back(page);
  await back(page);
  await page
    .getByLabel("What will you do?")
    .fill("Add a second barricade around the job");
  await next(page);
  await next(page);
  await finish(page);
  await expect(
    page.getByText(/already saved with different answers/),
  ).toBeVisible();
  await page.getByRole("link", { name: "Open the saved Take 5" }).click();
  await expect(heading(page, "Good to go")).toBeVisible();
  await expect(page.getByText(CONTROL, { exact: true })).toBeVisible();
  await expect(
    page.getByText("Add a second barricade around the job", { exact: true }),
  ).toHaveCount(0);
});

test("a link to a Take 5 that doesn't exist says so", async ({ page }) => {
  await page.goto("/take5s/00000000-0000-4000-8000-000000000000");
  await expect(heading(page, "This Take 5 couldn’t be found")).toBeVisible();
});
