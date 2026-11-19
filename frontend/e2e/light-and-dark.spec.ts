import { expect, test } from "@playwright/test";
import { capture } from "./helpers";

// Light or dark (spec F7). Each test sets the phone itself, so the dark run leaves this file out.

const THEME_ATTRIBUTE = "data-theme";

test("the app follows a phone set to dark", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute(THEME_ATTRIBUTE, "dark");
  await expect(
    page.getByRole("button", { name: "Switch to light" }),
  ).toBeVisible();
});

test("the switch changes the mode at once, and the choice survives a reload", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute(THEME_ATTRIBUTE, "light");
  await page.getByRole("button", { name: "Switch to dark" }).click();
  await expect(page.locator("html")).toHaveAttribute(THEME_ATTRIBUTE, "dark");
  await capture(page, "theme-switched-to-dark");

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute(THEME_ATTRIBUTE, "dark");
  await expect(
    page.getByRole("button", { name: "Switch to light" }),
  ).toBeVisible();
});

test("a choice lasts until the phone's own setting next changes", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Switch to dark" }).click();
  // The phone goes dark at sunset, then light again at sunrise.
  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("html")).toHaveAttribute(THEME_ATTRIBUTE, "dark");
  // The choice is forgotten as the phone changes (dark either way, so wait to see it go).
  await expect
    .poll(() =>
      page.evaluate(() => localStorage.getItem("take5-colour-scheme")),
    )
    .toBeNull();
  await page.emulateMedia({ colorScheme: "light" });
  await expect(page.locator("html")).toHaveAttribute(THEME_ATTRIBUTE, "light");

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute(THEME_ATTRIBUTE, "light");
});

test("a dark phone never sees a white page, even before the app draws", async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: "dark" });
  // Hold back the app itself, so only the page's own first lines have run.
  await page.route("**/src/main.tsx", () => undefined);
  await page.goto("/", { waitUntil: "commit" });
  await expect(page.locator("html")).toHaveAttribute(THEME_ATTRIBUTE, "dark");
  // The app's colours haven't loaded yet: it is this that makes the browser's own page dark.
  const browserScheme = await page.evaluate(
    () => document.documentElement.style.colorScheme,
  );
  expect(browserScheme).toBe("dark");
  await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute(
    "content",
    "#0f172b",
  );
});

test("the switch sits in the top bar of every screen, beside the saved list link", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByLabel("Your name", { exact: true })).toBeVisible();
  const header = page.locator("header");
  await expect(
    header.getByRole("button", { name: "Switch to dark" }),
  ).toBeVisible();
  await expect(
    header.getByRole("link", { name: "Saved Take 5s" }),
  ).toBeVisible();
});
