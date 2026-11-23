import { expect, test } from "@playwright/test";
import { capture, controlledDraft, finish, heading } from "./helpers";

for (const { width, name } of [
  { width: 360, name: "take5-table" },
  { width: 1280, name: "desktop-take5-table" },
]) {
  test(`at ${String(width)} px, the saved list opens every Take 5 as a table, filtered and downloadable (F11)`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 800 });
    // Possible / Major is 18, Extreme, which needs a JHA.
    await controlledDraft(page, ["Possible", "Major"], ["Unlikely", "Minor"]);
    await finish(page);

    await page.goto("/take5s");
    await page.getByRole("link", { name: "All Take 5s", exact: true }).click();
    await expect(heading(page, "All Take 5s")).toBeVisible();
    await expect(page.getByText(/^\d+ Take 5s? match(es)?\.$/)).toBeVisible();

    await page.getByLabel("Risk band").selectOption("Extreme");
    await expect(page).toHaveURL(/band=Extreme/);
    const table = page.getByRole("region", {
      name: "Take 5s, the most important first",
    });
    await expect(table.getByText("Needs a JHA").first()).toBeVisible();
    await capture(page, name);

    const csv = await page.request.get(
      (await page
        .getByRole("link", { name: "Download CSV" })
        .getAttribute("href")) ?? "",
    );
    expect(csv.headers()["content-type"]).toContain("text/csv");
    expect(await csv.text()).toContain("Extreme");
  });
}
