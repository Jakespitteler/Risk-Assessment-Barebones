import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Keep what was printed before Vite started, such as start.py's installs and warnings.
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
    // While developing, Vite serves the screens and passes every /api call on to FastAPI.
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["src/test-setup.ts"],
  },
});
