import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  workers: 1,
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:8765",
    viewport: { width: 1536, height: 1024 },
    launchOptions: { executablePath: process.env.QA_CHROMIUM_PATH },
    permissions: ["clipboard-read", "clipboard-write"],
  },
  webServer: {
    command:
      (process.env.QA_TEST_PYTHON
        ? `"${process.env.QA_TEST_PYTHON}"`
        : "uv run python") +
      " -m uvicorn backend.main:app --host 127.0.0.1 --port 8765",
    cwd: "..",
    url: "http://127.0.0.1:8765/api/v1/health",
    reuseExistingServer: false,
    timeout: 60000,
    env: {
      QA_MODE: "demo",
      QA_AUTH_MODE: "local",
      QA_DATA_DIR:
        process.env.QA_BROWSER_DATA_DIR || ".qa-browser-test-data-v0.3",
      QA_POLICY_PATH: "",
    },
  },
  reporter: "list",
});
