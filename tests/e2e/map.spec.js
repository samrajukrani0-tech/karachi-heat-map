import { test, expect } from '@playwright/test';

async function mapReady(page) {
  await page.goto('index.html');
  await page.waitForFunction(() => window.__mapReady, null, { timeout: 15000 });
  return page.evaluate(() => window.__mapReady);
}

test('@smoke every cell in the data renders on the map', async ({ page }) => {
  const ready = await mapReady(page);
  expect(ready.cells).toBe(265);
  const drawn = await page.locator('#map path.leaflet-interactive').count();
  expect(drawn, 'one SVG path per cell').toBe(ready.cells);
});

test('cells are coloured by quintile from the design ramp', async ({ page }) => {
  await mapReady(page);
  const fills = await page.$$eval('#map path.leaflet-interactive',
    els => [...new Set(els.map(e => e.getAttribute('fill')))]);
  const ramp = ['#F6E3D0', '#D4B5A4', '#B18678', '#8E584B', '#6C2A1F'];
  expect(fills.length, 'a quintile legend needs five bands').toBe(5);
  for (const fill of fills) expect(ramp).toContain(fill.toUpperCase());
});

test('the highest-priority cell is the darkest band', async ({ page }) => {
  await mapReady(page);
  const fill = await page.evaluate(() => {
    const el = [...document.querySelectorAll('#map path.leaflet-interactive')]
      .find(e => (e.getAttribute('aria-label') || '').startsWith('Cell ranked 1 of'));
    return el ? el.getAttribute('fill') : null;
  });
  expect(fill.toUpperCase()).toBe('#6C2A1F');
});

test('the legend is present and reads in plain words', async ({ page }) => {
  await mapReady(page);
  await expect(page.locator('.legend-swatch')).toHaveCount(5);
  const text = await page.locator('.legend-ends').innerText();
  expect(text).toContain('Highest priority');
  expect(text).toContain('Lower priority');
  expect(text.toLowerCase()).not.toContain('safe');
  expect(text.toLowerCase()).not.toContain('danger');
});

test('basemap attribution is visible', async ({ page }) => {
  await mapReady(page);
  const attribution = page.locator('.leaflet-control-attribution');
  await expect(attribution).toBeVisible();
  const text = await attribution.innerText();
  expect(text).toContain('OpenStreetMap');
  expect(text).toContain('Esri');
});

test('basemap tiles actually load', async ({ page }) => {
  await mapReady(page);
  await page.waitForFunction(
    () => [...document.querySelectorAll('img.leaflet-tile')]
            .filter(i => i.complete && i.naturalWidth > 0).length > 0,
    null, { timeout: 15000 });
  const loaded = await page.evaluate(() =>
    [...document.querySelectorAll('img.leaflet-tile')]
      .filter(i => i.complete && i.naturalWidth > 0).length);
  expect(loaded).toBeGreaterThan(0);
});

test('the provisional warning is shown while the model is provisional', async ({ page }) => {
  await mapReady(page);
  const note = page.locator('#provisional-note');
  await expect(note).toBeVisible();
  await expect(note).toContainText('Provisional');
});

test('the map starts above the fold on a phone', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'phone', 'phone viewport only');
  await mapReady(page);
  const top = await page.evaluate(() =>
    Math.round(document.getElementById('map').getBoundingClientRect().top));
  expect(top, `map starts at ${top}px on an 812px screen`).toBeLessThan(400);
});

test('cells are keyboard focusable and announce themselves', async ({ page }) => {
  await mapReady(page);
  const first = page.locator('#map path.leaflet-interactive').first();
  await expect(first).toHaveAttribute('tabindex', '0');
  const label = await first.getAttribute('aria-label');
  expect(label).toMatch(/Cell ranked \d+ of \d+/);
});
