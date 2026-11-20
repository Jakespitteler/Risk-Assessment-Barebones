import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";
import { startLogger } from "./src/dev/startLogger.ts";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Keep what was printed before Vite started, such as start.py's installs and warnings.
  clearScreen: false,
  // One short line when the back end isn't answering, in place of a stack per request.
  customLogger: startLogger(),
  server: {
    port: 5173,
    strictPort: true,
    // Browser crashes, console.error and console.warn print in the terminal too (task 0028).
    forwardConsole: true,
    // While developing, Vite serves the screens and passes every /api call on to FastAPI.
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["src/test-setup.ts"],
  },
});
