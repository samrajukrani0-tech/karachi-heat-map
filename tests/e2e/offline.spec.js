import { test, expect } from '@playwright/test';

// P5-02. Load once online so the service worker installs, then cut the network.
async function installWorker(page, path) {
  await page.goto(path);
  await page.evaluate(async () => { await navigator.serviceWorker.ready; });
  await page.reload();
  await page.waitForFunction(() => navigator.serviceWorker.controller !== null);
}

test('the map works offline, with roads instead of basemap tiles', async ({ page, context }) => {
  await installWorker(page, 'index.html');
  await context.setOffline(true);
  await page.reload();
  await page.waitForFunction(() => window.__mapReady, null, { timeout: 15000 });
  expect(await page.locator('#map path.leaflet-interactive').count()).toBe(265);
  await page.waitForFunction(() => window.__offlineRoads > 0, null, { timeout: 10000 });
  expect(await page.locator('#map path.offline-road').count()).toBeGreaterThan(50);
  await expect(page.locator('#offline-note')).toBeVisible();
  await expect(page.locator('#offline-note')).toContainText('main roads');
  const edges = await page.evaluate(() => [document.querySelector('#offline-note'),
    document.querySelector('main h2')].map(e => Math.round(e.getBoundingClientRect().left)));
  expect(Math.abs(edges[0] - edges[1]), 'the offline note shares the page edge').toBeLessThanOrEqual(2);
  const tiles = await page.evaluate(() => [...document.querySelectorAll('img.leaflet-tile')]
    .filter(i => i.complete && i.naturalWidth > 0).length);
  expect(tiles, 'the tile layer is replaced, not overlaid').toBe(0);
  const cachedTiles = await page.evaluate(async () => {
    let n = 0;
    for (const key of await caches.keys()) {
      for (const req of await (await caches.open(key)).keys()) {
        if (!req.url.startsWith(location.origin)) n++;
      }
    }
    return n;
  });
  expect(cachedTiles, 'our cache stores no third-party tiles').toBe(0);
  // the panel still works: the "why" is in the cached data
  await page.locator('#map path.leaflet-interactive').first().click();
  await expect(page.locator('#panel')).toContainText('Why here');
});

test('every page opens offline once the site has been visited', async ({ page, context }) => {
  await installWorker(page, 'index.html');
  await context.setOffline(true);
  for (const [path, heading] of [['plan.html', 'Plan supplies'], ['how-it-works.html', 'How it works'],
                                 ['about.html', 'About'], ['briefs.html', 'Field briefs']]) {
    const response = await page.goto(path);
    expect(response.status(), path).toBe(200);
    await expect(page.locator('main h2').first()).toContainText(heading);
  }
});

test('the planner quick estimate runs offline', async ({ page, context }) => {
  await installWorker(page, 'plan.html');
  await context.setOffline(true);
  await page.reload();
  await page.waitForFunction(() => window.__planReady, null, { timeout: 15000 });
  await page.click('#add-point');
  await page.click('#run');
  await page.waitForFunction(() => window.__planResult && window.__planResult.kind === 'greedy');
  const r = await page.evaluate(() => window.__planResult);
  expect(r.total).toBeGreaterThan(0);
  expect(r.total).toBeLessThanOrEqual(1000);
});

test('online, the road outline stays hidden and tiles are used', async ({ page }) => {
  await page.goto('index.html');
  await page.waitForFunction(() => window.__mapReady);
  await expect(page.locator('#offline-note')).toBeHidden();
  expect(await page.locator('#map path.offline-road').count()).toBe(0);
});
