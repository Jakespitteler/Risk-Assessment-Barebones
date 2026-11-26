import { expect, test } from "@playwright/test";
import { capture, controlledDraft, finish, heading } from "./helpers";

test("the saved list opens patterns over time, with the counts beneath (S1 to S5)", async ({
  page,
}) => {
  await controlledDraft(page, ["Possible", "Major"], ["Unlikely", "Minor"]);
  await finish(page);

  await page.goto("/take5s");
  await page.getByRole("link", { name: "Patterns over time" }).click();
  await expect(heading(page, "Patterns over time")).toBeVisible();
  await expect(page.getByText(/Small numbers can be chance/)).toBeVisible();
  const byWeekday = page.getByRole("region", { name: "By weekday" });
  await expect(byWeekday.getByRole("row")).toHaveCount(8);
  await expect(
    page.getByRole("region", { name: "By time of day" }).getByRole("row"),
  ).toHaveCount(5);
  await capture(page, "patterns-over-time");
});
