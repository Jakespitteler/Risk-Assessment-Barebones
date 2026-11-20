import { expect, test } from "@playwright/test";
import { capture, controlledDraft, finish, heading } from "./helpers";

test("the saved list opens risk by area, hottest first, with what each shows (A1 to A5)", async ({
  page,
}) => {
  // Possible / Major is 18, which needs a JHA, so the area has a high-risk Take 5.
  await controlledDraft(page, ["Possible", "Major"], ["Unlikely", "Minor"]);
  await finish(page);

  await page.goto("/take5s");
  await page.getByRole("link", { name: "Risk by area", exact: true }).click();
  await expect(heading(page, "Risk by area")).toBeVisible();
  const workshop = page
    .getByRole("listitem")
    .filter({ has: page.getByRole("heading", { name: "Example workshop" }) });
  await expect(
    workshop.getByText(/^[1-9]\d* of \d+ Take 5s? high risk$/),
  ).toBeVisible();
  await expect(
    workshop.getByText(/^Highest risk before controls \d+ \w+/),
  ).toBeVisible();
  await capture(page, "risk-by-area");
});
