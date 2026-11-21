import { expect, type Page, test } from "@playwright/test";
import { capture, heading } from "./helpers";

// The whole-app tests run with no AI, so the photo read is answered here with what an
// AI might have read off a booklet card. Saving and ranking use the real back end.
const READ = {
  draft: {
    worker_name: "Sam Example",
    job: "Change the front tyre on LV12",
    location: "Workshop bay 2",
    answers: { scope: "Yes", procedure: "Yes", steps: "No" },
    hazards: [
      {
        description: "The wheel falls off the hub onto a foot",
        before: { likelihood: "Possible", consequence: "Major" },
        controls: [],
        after: { likelihood: null, consequence: null },
        weak_controls_reason: "",
        covers: [],
      },
    ],
  },
  filled_in_at: "2026-04-03",
  unreadable: ["location"],
};

// A 1 × 1 PNG: the page shrinks and sends it, and the read above answers.
const PHOTO = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC",
  "base64",
);

async function scanTwoCards(page: Page) {
  await page.route("**/api/scans", (route) =>
    route.fulfill({ status: 200, json: READ }),
  );
  await page.goto("/take5s");
  await page.getByRole("link", { name: "Scan paper cards" }).click();
  await expect(heading(page, "Scan paper cards")).toBeVisible();
  await page.getByLabel("Choose photos").setInputFiles([
    { name: "card-1.png", mimeType: "image/png", buffer: PHOTO },
    { name: "card-2.png", mimeType: "image/png", buffer: PHOTO },
  ]);
  await expect(heading(page, "Check card 1 of 2")).toBeVisible();
}

for (const { width, name } of [
  { width: 360, name: "scan" },
  { width: 1280, name: "desktop-scan" },
]) {
  test(`at ${String(width)} px, photographed cards are checked, saved as written and ranked (F10)`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 800 });
    await scanTwoCards(page);
    await expect(page.getByLabel("Name")).toHaveValue("Sam Example");
    await expect(
      page.getByText("Couldn’t read this. Check the photo."),
    ).toBeVisible();
    await capture(page, `${name}-check`);

    await page.getByLabel("Where").fill("Workshop bay 2");
    await page.getByRole("button", { name: "Save as written" }).click();
    await expect(heading(page, "Check card 2 of 2")).toBeVisible();
    await page.getByRole("button", { name: "Skip this card" }).click();

    await expect(page.getByText("1 card saved, 1 skipped.")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "This batch, worst first" }),
    ).toBeVisible();
    const ranked = page.getByRole("listitem");
    await expect(ranked).toHaveCount(1);
    await expect(ranked).toContainText("Highest risk 18 Extreme.");
    // The date on the card, not the time it was scanned (D127).
    await expect(ranked).toContainText("Dated 3 Apr 2026");
    await capture(page, `${name}-ranked`);

    await ranked.getByRole("link").click();
    await expect(page.getByText("From paper")).toBeVisible();
    await expect(page.getByText("Not rated")).toBeVisible();
  });
}
