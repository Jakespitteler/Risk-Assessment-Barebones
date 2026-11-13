import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

async function next(page: Page) {
  await page.getByRole("button", { name: "Continue", exact: true }).click();
}

async function jobAndHazard(page: Page) {
  await page.goto("/");
  await page.getByLabel("Your name", { exact: true }).fill("Sam Example");
  await page.getByLabel("What is the job?").fill("Change front tyre on LV12");
  await page.getByLabel("Where will you do it?").fill("Example workshop");
  await next(page);
  await page
    .getByLabel("Hazard 1", { exact: true })
    .fill("Wheel moving while being removed");
  await next(page);
}

async function pick(page: Page, likelihood: string, consequence: string) {
  await page
    .getByRole("group", { name: "How likely is it?" })
    .getByText(likelihood, { exact: true })
    .click();
  await page
    .getByRole("group", { name: "How bad would it be?" })
    .getByText(consequence, { exact: true })
    .click();
}

async function controlledDraft(page: Page, high = false) {
  await jobAndHazard(page);
  await pick(page, high ? "Likely" : "Possible", "Minor");
  await next(page);
  await page
    .getByRole("button", { name: "Add a control", exact: true })
    .click();
  await page
    .getByLabel("What will you do?")
    .fill("Barricade the work area before removing the wheel");
  await page.getByLabel("Kind of control").selectOption("Barricade the hazard");
  await next(page);
  await pick(page, high ? "Likely" : "Unlikely", "Minor");
  await next(page);
}

async function capture(page: Page, name: string) {
  await expect(page.locator("html")).toHaveJSProperty("scrollWidth", 360);
  await page.screenshot({
    path: `test-results/screenshots/${name}.png`,
    fullPage: true,
  });
  for (const target of await page
    .locator(
      "button, input:not([type=radio]), textarea, select, summary, label:has(input[type=radio])",
    )
    .all()) {
    if (await target.isVisible()) {
      const bounds = await target.boundingBox();
      expect(
        bounds?.height,
        "Visible control must have a 48 px tap target",
      ).toBeGreaterThanOrEqual(48);
    }
  }
}

test("a worker completes, reopens and starts a new Take 5 on a phone", async ({
  page,
}) => {
  const posts: string[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST") posts.push(request.url());
  });
  await page.goto("/");
  await expect(page.getByLabel("Your name", { exact: true })).toHaveValue("");
  await capture(page, "take5-job");
  await page.getByLabel("Your name", { exact: true }).fill("Sam Example");
  await page.getByLabel("What is the job?").fill("Change front tyre on LV12");
  await page.getByLabel("Where will you do it?").fill("Example workshop");
  await next(page);
  await page
    .getByLabel("Hazard 1", { exact: true })
    .fill("Wheel moving while being removed");
  await capture(page, "take5-hazards");
  await next(page);
  await expect(page.getByRole("radio", { checked: true })).toHaveCount(0);
  const guide = page.locator("details");
  await expect(guide).not.toHaveAttribute("open");
  await guide.getByText("What do the ratings mean?").click();
  await expect(
    page.getByText("First aid treatment.", { exact: true }),
  ).toBeVisible();
  await guide.getByText("What do the ratings mean?").click();
  await pick(page, "Possible", "Minor");
  await capture(page, "take5-before");
  await next(page);
  await page
    .getByRole("button", { name: "Add a control", exact: true })
    .click();
  await expect(page.getByLabel("Kind of control")).toHaveValue("");
  await page
    .getByLabel("What will you do?")
    .fill("Barricade the work area before removing the wheel");
  await page.getByLabel("Kind of control").selectOption("Barricade the hazard");
  await capture(page, "take5-controls");
  await next(page);
  await expect(page.getByRole("radio", { checked: true })).toHaveCount(0);
  await pick(page, "Unlikely", "Minor");
  await capture(page, "take5-after");
  await next(page);
  await capture(page, "take5-review");
  expect(posts).toHaveLength(0);
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Good to go", exact: true }),
  ).toBeVisible();
  await capture(page, "take5-good-to-go");
  const resultUrl = page.url();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Good to go", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Wheel moving while being removed", { exact: true }),
  ).toBeVisible();
  expect(page.url()).toBe(resultUrl);
  expect(posts.filter((url) => url.endsWith("/api/take5s"))).toHaveLength(1);
  await page.getByRole("link", { name: "Start a new Take 5" }).click();
  await expect(page.getByLabel("Your name", { exact: true })).toHaveValue(
    "Sam Example",
  );
  await expect(page.getByLabel("What is the job?")).toHaveValue("");
});

test("a JHA result shows the reason and the saved after rating", async ({
  page,
}) => {
  await controlledDraft(page, true);
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Don’t start yet", exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/At 11 or more you need a JHA/)).toBeVisible();
  await capture(page, "take5-dont-start");
});

test("no controls skips the second rating and stops the job", async ({
  page,
}) => {
  await jobAndHazard(page);
  await pick(page, "Possible", "Minor");
  await next(page);
  await next(page);
  await expect(
    page.getByRole("heading", { name: "One last look" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Don’t start yet", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "Say how you will control: Wheel moving while being removed",
    ),
  ).toBeVisible();
  await expect(page.getByText("8", { exact: true })).toHaveCount(3);
});

test("backend field errors are shown beside missing answers", async ({
  page,
}) => {
  await page.goto("/");
  await next(page);
  await next(page);
  await next(page);
  await next(page);
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "The job in front of you" }),
  ).toBeVisible();
  await expect(page.getByLabel("Your name", { exact: true })).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  await expect(
    page.getByLabel("Your name", { exact: true }),
  ).toHaveAccessibleDescription("Fill in this field.");
  await capture(page, "take5-field-errors");
});

test("higher after risk returns to the hazard with the server message", async ({
  page,
}) => {
  await controlledDraft(page);
  await page.getByRole("button", { name: "Back", exact: true }).click();
  await pick(page, "Almost Certain", "Critical");
  await next(page);
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "After your controls" }),
  ).toBeVisible();
  await expect(
    page.getByText("Controls cannot make the after risk higher than before."),
  ).toBeVisible();
});

test("a lost response can be retried without saving a duplicate", async ({
  page,
}) => {
  let attempts = 0;
  let firstDocument = "";
  await page.route("**/api/take5s", async (route) => {
    const response = await route.fetch();
    attempts++;
    if (attempts === 1) {
      firstDocument = await response.text();
      await route.abort();
    } else {
      expect(await response.text()).toBe(firstDocument);
      await route.fulfill({ response });
    }
  });
  await controlledDraft(page);
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
  await expect(page.getByText(/Your answers are still here/)).toBeVisible();
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Good to go", exact: true }),
  ).toBeVisible();
  expect(attempts).toBe(2);
});

test("back navigation keeps answers and each hazard is assessed separately", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("What is the job?").fill("Example maintenance task");
  await next(page);
  await page
    .getByLabel("Hazard 1", { exact: true })
    .fill("First example hazard");
  await page.getByRole("button", { name: "Add another hazard" }).click();
  await page
    .getByLabel("Hazard 2", { exact: true })
    .fill("Second example hazard");
  await next(page);
  await expect(page.locator(".hazard-context")).toHaveText(
    "First example hazard",
  );
  await pick(page, "Rare", "Low");
  await next(page);
  await next(page);
  await expect(page.locator(".hazard-context")).toHaveText(
    "Second example hazard",
  );
  await page.getByRole("button", { name: "Back", exact: true }).click();
  await expect(page.locator(".hazard-context")).toHaveText(
    "First example hazard",
  );
  await page.getByRole("button", { name: "Back", exact: true }).click();
  await expect(
    page.getByRole("radio", { name: "Rare", exact: true }),
  ).toBeChecked();
});

test("the finish action stays disabled while saving and sends one submission", async ({
  page,
}) => {
  let submissions = 0;
  let release: () => void = () => {
    throw new Error("Gate not initialised");
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
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
  const saving = page.getByRole("button", { name: "Saving…", exact: true });
  try {
    await expect(saving).toBeDisabled();
    await expect.poll(() => submissions).toBe(1);
    await saving.dispatchEvent("click");
    expect(submissions).toBe(1);
  } finally {
    release();
  }
  await expect(
    page.getByRole("heading", { name: "Good to go", exact: true }),
  ).toBeVisible();
  expect(submissions).toBe(1);
});

test("changing answers after a lost response cannot overwrite the saved assessment", async ({
  page,
}) => {
  let attempts = 0;
  await page.route("**/api/take5s", async (route) => {
    const response = await route.fetch();
    attempts++;
    if (attempts === 1) await route.abort();
    else await route.fulfill({ response });
  });
  await controlledDraft(page);
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
  await expect(page.getByText(/Your answers are still here/)).toBeVisible();
  await page.getByRole("button", { name: "Back", exact: true }).click();
  await page.getByRole("button", { name: "Back", exact: true }).click();
  await page
    .getByLabel("What will you do?")
    .fill("Add a second barricade around the job");
  await next(page);
  await next(page);
  await page
    .getByRole("button", { name: "Finish Take 5", exact: true })
    .click();
  await expect(
    page.getByText(/already saved with different answers/),
  ).toBeVisible();
  await page.getByRole("link", { name: "Open the saved Take 5" }).click();
  await expect(
    page.getByRole("heading", { name: "Good to go", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Barricade the work area before removing the wheel", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText("Add a second barricade around the job", { exact: true }),
  ).toHaveCount(0);
});
