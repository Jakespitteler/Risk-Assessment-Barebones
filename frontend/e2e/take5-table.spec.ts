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

    // On a phone the filters start folded away.
    const filters = page.locator("details");
    if ((await filters.getAttribute("open")) === null)
      await page.getByText("Filters", { exact: true }).click();
    // Typing at speed keeps every letter, and the address follows once it pauses.
    await page.getByLabel("Find words").pressSequentially("tyre lv12");
    await expect(page.getByLabel("Find words")).toHaveValue("tyre lv12");
    await expect(page).toHaveURL(/search=tyre\+lv12/);
    const table = page.getByRole("region", {
      name: "Take 5s, the most important first",
    });
    // Each heading's filter opens a list of the column's values to tick (E6).
    await table.getByRole("button", { name: "Filter Highest risk" }).click();
    const list = page.getByRole("dialog", { name: "Filter highest risk" });
    await list.getByLabel("Extreme").check();
    await list.getByLabel("High", { exact: true }).check();
    await capture(page, `${name}-ticking`);
    await list.getByRole("button", { name: "Apply" }).click();
    await expect(page).toHaveURL(/band=Extreme&band=High/);
    await expect(
      table.getByRole("button", { name: "Filter Highest risk, 2 ticked" }),
    ).toBeFocused();
    await expect(table.getByText("Needs a JHA").first()).toBeVisible();
    await capture(page, name);

    const csv = await page.request.get(
      (await page
        .getByRole("link", { name: "Download CSV" })
        .getAttribute("href")) ?? "",
    );
    expect(csv.headers()["content-type"]).toContain("text/csv");
    expect(await csv.text()).toContain("Extreme");

    // One button turns every filter off, above and in the columns.
    await page.getByRole("button", { name: "Clear filters" }).click();
    await expect(page).toHaveURL(/\/take5-table$/);
    await expect(
      table.getByRole("button", { name: "Filter Highest risk" }),
    ).toBeVisible();
    await expect(page.getByLabel("Find words")).toHaveValue("");
    await expect(
      page.getByRole("button", { name: "Clear filters" }),
    ).toBeDisabled();
  });
}
