import { test, expect } from '@playwright/test';

test('first load stays under 1.5 MB, excluding basemap tiles', async ({ page }) => {
  // PROMPT.md section 9: the budget excludes basemap tiles, which are fetched on demand
  // as the user pans and are not part of the first load.
  const bytes = new Map();
  page.on('response', async (res) => {
    const url = res.url();
    if (url.includes('arcgisonline.com')) return;   // basemap tiles, excluded by the brief
    try {
      const body = await res.body();
      bytes.set(url, body.length);
    } catch { /* redirects and aborted requests have no body */ }
  });
  await page.goto('/index.html');
  await page.waitForFunction(() => window.__mapReady, null, { timeout: 20000 });

  const total = [...bytes.values()].reduce((a, b) => a + b, 0);
  const breakdown = [...bytes.entries()]
    .sort((a, b) => b[1] - a[1]).slice(0, 5)
    .map(([u, n]) => `${u.split('/').pop()} ${(n / 1024).toFixed(0)}kB`).join(', ');
  expect(total, `first load is ${(total / 1024).toFixed(0)} kB — ${breakdown}`)
    .toBeLessThan(1.5 * 1024 * 1024);
});

test('the site has no third-party runtime dependency beyond the basemap', async ({ page }) => {
  const hosts = new Set();
  page.on('request', r => {
    const host = new URL(r.url()).host;
    if (host && !host.startsWith('127.0.0.1') && !host.startsWith('localhost')) hosts.add(host);
  });
  await page.goto('/index.html');
  await page.waitForFunction(() => window.__mapReady, null, { timeout: 20000 });
  const unexpected = [...hosts].filter(h => !h.includes('arcgisonline.com'));
  expect(unexpected, 'Leaflet is vendored; nothing else should be remote').toEqual([]);
});

test('the provisional banner does not depend on JavaScript', async ({ browser }) => {
  // The honest state must not require a script to run.
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto('/index.html');
  await expect(page.locator('#provisional-note')).toBeVisible();
  await expect(page.locator('#provisional-note')).toContainText('Provisional');
  await context.close();
});
