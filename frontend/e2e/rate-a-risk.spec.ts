import { expect, test } from "@playwright/test";
import { expectReadable, screenshotPath } from "./helpers";

test("a worker rates a risk on the matrix the back end sends", async ({
  page,
}) => {
  await page.goto("/rate-risk");
  await expect(
    page.getByRole("heading", { name: "Rate a risk" }),
  ).toBeVisible();
  await expect(page.getByRole("status")).toHaveText(
    "Pick both to see the score.",
  );
  await page.screenshot({
    path: screenshotPath("rate-a-risk-empty"),
    fullPage: true,
  });
  await expectReadable(page);

  await page
    .getByRole("group", { name: "How likely is it?" })
    .getByText("Rare")
    .click();
  await page
    .getByRole("group", { name: "How bad would it be?" })
    .getByText("Low")
    .click();

  // Spec worked example 1: Rare / Low is 1 Low.
  await expect(page.getByRole("status")).toHaveText("1Low");
  await page.screenshot({
    path: screenshotPath("rate-a-risk-picked"),
    fullPage: true,
  });
  await expectReadable(page);
});
