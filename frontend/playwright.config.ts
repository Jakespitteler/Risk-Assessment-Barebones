import { defineConfig } from "@playwright/test";
import { tmpdir } from "node:os";
import { join } from "node:path";

const isCi = Boolean(process.env.CI);

// The whole app in a real browser, at the width of a small phone (spec F2).
export default defineConfig({
  testDir: "e2e",
  forbidOnly: isCi,
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
