import { expect, test } from "@playwright/test";

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
    path: "test-results/screenshots/rate-a-risk-empty.png",
    fullPage: true,
  });

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
    path: "test-results/screenshots/rate-a-risk-picked.png",
    fullPage: true,
  });
});
