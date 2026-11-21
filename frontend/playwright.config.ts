import { defineConfig } from "@playwright/test";
import { tmpdir } from "node:os";
import { join } from "node:path";

const isCi = Boolean(process.env.CI);

// The whole app in a real browser, at the width of a small phone (spec F2), once on a phone
// set to light and once on a phone set to dark (spec F7). The dark run's screenshots end in
// `-dark`.
export default defineConfig({
  testDir: "e2e",
  forbidOnly: isCi,
  projects: [
    { name: "light", use: { colorScheme: "light" } },
    {
      name: "dark",
      use: { colorScheme: "dark" },
      testIgnore: "light-and-dark.spec.ts",
    },
  ],
  use: {
    baseURL: "http://localhost:5173",
    viewport: { width: 360, height: 780 },
    deviceScaleFactor: 2,
    locale: "en-AU",
    timezoneId: "Australia/Perth",
  },
  webServer: [
    {
      command:
        "uv run --directory ../backend uvicorn risk_assessment.api.app:create_app --factory --port 8000",
      url: "http://127.0.0.1:8000/api/take5/template",
      reuseExistingServer: false,
      env: {
        // No AI in the whole-app tests, even with a key in backend/.env: the
        // fixed question is asked every time, so the tests know what to expect.
        TAKE5_AI_KEY: "",
        // Risk by area counts every saved Take 5, as the tests expect, even
        // with the 30 days turned on in backend/.env (D119).
        TAKE5_AREA_LAST_30_DAYS_ONLY: "false",
        TAKE5_DATABASE_PATH: join(
          tmpdir(),
          `take5-e2e-${String(process.pid)}.sqlite3`,
        ),
      },
    },
    {
      command: "npm run dev",
      url: "http://localhost:5173",
      reuseExistingServer: !isCi,
    },
  ],
});
