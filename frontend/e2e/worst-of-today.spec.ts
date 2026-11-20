import { expect, test } from "@playwright/test";
import { capture, controlledDraft, finish, heading } from "./helpers";

test("the saved list opens today's Take 5s worst first, each with why (W1, W7)", async ({
  page,
}) => {
  await controlledDraft(page);
  await finish(page);
  await expect(heading(page, "Good to go")).toBeVisible();

  await page.goto("/take5s");
  await page.getByRole("link", { name: "Worst of today", exact: true }).click();
  await expect(heading(page, "Worst of today")).toBeVisible();
  const first = page.getByRole("listitem").first();
  await expect(first.getByText("1.", { exact: true })).toBeVisible();
  await expect(first.getByText(/^Highest risk \d+ /)).toBeVisible();
  await capture(page, "worst-of-today");
});
