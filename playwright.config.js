import { defineConfig, devices } from '@playwright/test';

// The site has no build step, so the "server" is just a static file server over site/.
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'line' : [['list']],
  use: {
    // Must end in '/': a relative path resolves against the last path
    // segment, and a Pages project URL is not the domain root.
    baseURL: (process.env.SITE_URL || 'http://127.0.0.1:8765').replace(/\/?$/, '/'),
    trace: 'off',
  },
  projects: [
    { name: 'phone',  use: { ...devices['Desktop Chrome'], viewport: { width: 375, height: 812 } } },
    { name: 'laptop', use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } } },
  ],
  webServer: process.env.SITE_URL ? undefined : {
    command: 'python3 -m http.server 8765 --directory site',
    url: 'http://127.0.0.1:8765/index.html',
    reuseExistingServer: !process.env.CI,
    timeout: 60000,
  },
});
