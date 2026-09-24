import { defineConfig } from "@playwright/test";
const port = process.env.QA_BROWSER_PORT || "8765";
export default defineConfig({
  testDir: "./tests",
  workers: 1,
  timeout: 30000,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    viewport: { width: 1536, height: 1024 },
    launchOptions: { executablePath: process.env.QA_CHROMIUM_PATH },
    permissions: ["clipboard-read", "clipboard-write"],
  },
  webServer: {
    command:
      (process.env.QA_TEST_PYTHON
        ? `"${process.env.QA_TEST_PYTHON}"`
        : "uv run python") +
      ` -m uvicorn backend.main:app --host 127.0.0.1 --port ${port}`,
    cwd: "..",
    url: `http://127.0.0.1:${port}/api/v1/health`,
    reuseExistingServer: false,
    timeout: 60000,
    env: {
      RUN_MODE: "demo",
      OPENAI_API_KEY: "",
      TYPESAFE_API_KEY: "",
      QA_JEV_ENABLED: "false",
      CORE_REVIEW_MODELS: "gpt-6-astra,controlled-second-model",
      ACCESS_MODE: "local",
      QA_DATA_DIR:
        process.env.QA_BROWSER_DATA_DIR || ".qa-browser-test-data-v0.5",
      QA_POLICY_PATH: "",
    },
  },
  reporter: "list",
});
