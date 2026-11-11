import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/browser',
  outputDir: './test-results',
  fullyParallel: true,
  workers: 2,
  retries: 0,
  timeout: 60000,
  expect: { timeout: 10000 },
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:3420',
    browserName: 'chromium',
    headless: true,
    viewport: { width: 1440, height: 1000 },
    timezoneId: 'Asia/Shanghai',
    locale: 'zh-CN',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    launchOptions: { args: ['--no-sandbox'] },
  },
  webServer: {
    command: 'node node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port 3420 --strictPort',
    url: 'http://127.0.0.1:3420',
    reuseExistingServer: false,
    timeout: 30000,
  },
})
