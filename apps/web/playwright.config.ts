import { defineConfig, devices } from "@playwright/test";

const isCI = Boolean(process.env.CI);

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  reporter: isCI ? [["github"], ["html", { open: "never" }]] : "list",
  use: { baseURL: "http://localhost:3000", trace: "on-first-retry" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "uv run uvicorn wordmeter_api.main:app --port 8000",
      cwd: "../api",
      url: "http://localhost:8000/health",
      reuseExistingServer: !isCI,
    },
    {
      command: isCI ? "pnpm start" : "pnpm dev",
      url: "http://localhost:3000",
      reuseExistingServer: !isCI,
    },
  ],
});