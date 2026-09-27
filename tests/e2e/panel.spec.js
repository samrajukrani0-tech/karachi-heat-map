import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const LAYERS = ['priority', 'hazard', 'exposure', 'vulnerability', 'stability'];

async function ready(page) {
  await page.goto('index.html');
  await page.waitForFunction(() => window.__mapReady, null, { timeout: 20000 });
}

async function fills(page) {
  return page.$$eval('#map path.leaflet-interactive', els => els.map(e => e.getAttribute('fill')));
}

test('all five layers are offered', async ({ page }) => {
  await ready(page);
  const values = await page.$$eval('#layer-select option', els => els.map(e => e.value));
  expect(values).toEqual(LAYERS);
});

test('switching layer changes the colours', async ({ page }) => {
  await ready(page);
  const before = (await fills(page)).join(',');
  const seen = new Set([before]);
  for (const layer of LAYERS.slice(1)) {
    await page.selectOption('#layer-select', layer);
    await page.waitForTimeout(150);
    const after = (await fills(page)).join(',');
    expect(after, `${layer} looks identical to priority`).not.toBe(before);
    seen.add(after);
  }
  expect(seen.size, 'every layer should look different').toBe(LAYERS.length);
});

test('uncertain cells are hatched, not merely tinted', async ({ page }) => {
  // DESIGN.md principle 1: a cell the model is unsure about must LOOK unsure.
  await ready(page);
  const hatched = await page.locator('#map path.cell-uncertain').count();
  expect(hatched, 'no uncertain cells are marked').toBeGreaterThan(0);
  const dash = await page.evaluate(() => {
    const el = document.querySelector('#map path.cell-uncertain');
    return getComputedStyle(el).strokeDasharray;
  });
  expect(dash).not.toBe('none');
});

test('@smoke the panel shows every required section', async ({ page }) => {
  await ready(page);
  await page.locator('#map path.leaflet-interactive').first().click();
  const panel = page.locator('#panel');
  await expect(panel.locator('.panel-rank')).toContainText(/Rank \d+ of \d+/);
  await expect(panel.locator('.panel-band')).toContainText(/priority|range/i);
  await expect(panel.locator('.reasons li').first()).toBeVisible();
  await expect(panel).toContainText('Confidence');
  await expect(panel).toContainText('Values');
  await expect(panel.locator('details.cannot summary'))
    .toContainText('What this cannot tell you');
});

test('the panel reports values with their units', async ({ page }) => {
  await ready(page);
  await page.locator('#map path.leaflet-interactive').first().click();
  const text = await page.locator('#panel table').innerText();
  expect(text).toMatch(/°C/);
  expect(text).toMatch(/\bm\b/);
  expect(text).toContain('not available');   // dist_centre, honestly reported
});

test('the panel carries the caveats that keep a screenshot honest', async ({ page }) => {
  await ready(page);
  await page.locator('#map path.leaflet-interactive').first().click();
  await page.locator('details.cannot summary').click();
  const text = await page.locator('details.cannot').innerText();
  expect(text).toContain('half');            // the population undercount
  expect(text).toContain('relief centre');   // the missing indicator
  expect(text).toContain('not the air');     // LST is not air temperature
  expect(text).toContain('Power cuts');      // D20
  expect(text.toLowerCase()).toContain('never a verdict');
});

test('the panel matches the underlying data', async ({ page }) => {
  await ready(page);
  const expected = await page.evaluate(async () => {
    const doc = await (await fetch('data/cells.geojson')).json();
    const f = doc.features.find(f => f.properties.rank === 1);
    return { rank: f.properties.rank, lst: f.properties.lst, people: f.properties.people,
             max: doc.metadata.distinguishable_ranks };
  });
  await page.evaluate(() => {
    const el = [...document.querySelectorAll('#map path.leaflet-interactive')]
      .find(e => (e.getAttribute('aria-label') || '').startsWith('Cell ranked 1 of'));
    el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
  const panel = await page.locator('#panel').innerText();
  expect(panel).toContain(`Rank ${expected.rank} of ${expected.max}`);
  expect(panel).toContain(String(expected.lst));
  expect(panel).toContain(expected.people.toLocaleString('en-GB'));
});

test('a cell can be selected with the keyboard alone', async ({ page }) => {
  await ready(page);
  const cell = page.locator('#map path.leaflet-interactive').first();
  await cell.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#panel .panel-rank')).toBeVisible();
});

test('the layer picker is focusable, labelled, and drives the map', async ({ page }) => {
  // ArrowDown on a native select opens the popup in headless Chromium rather than
  // changing the value, so this checks the properties that actually make it usable:
  // it takes focus, it has an associated label, and selecting an option redraws.
  await ready(page);
  const select = page.locator('#layer-select');
  await select.focus();
  await expect(select).toBeFocused();
  const labelled = await page.evaluate(() => {
    const el = document.getElementById('layer-select');
    const label = document.querySelector('label[for="layer-select"]');
    return Boolean(label && label.textContent.trim()) && el.tagName === 'SELECT';
  });
  expect(labelled, 'the picker must have a real <label for>').toBe(true);
  const before = await page.$$eval('#map path.leaflet-interactive',
    els => els.map(e => e.getAttribute('fill')).join(','));
  await select.selectOption('stability');
  await page.waitForTimeout(150);
  const after = await page.$$eval('#map path.leaflet-interactive',
    els => els.map(e => e.getAttribute('fill')).join(','));
  expect(after).not.toBe(before);
});

test('@smoke axe finds no serious or critical accessibility violations', async ({ page }) => {
  await ready(page);
  await page.locator('#map path.leaflet-interactive').first().click();
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  const serious = results.violations.filter(
    v => v.impact === 'serious' || v.impact === 'critical');
  expect(serious.map(v => `${v.id}: ${v.description}`)).toEqual([]);
});

test('axe finds no violations on the content pages', async ({ page }) => {
  for (const path of ['about.html', 'how-it-works.html', 'data-and-credits.html']) {
    await page.goto(path);
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    const serious = results.violations.filter(
      v => v.impact === 'serious' || v.impact === 'critical');
    expect(serious.map(v => `${path} ${v.id}`)).toEqual([]);
  }
});

test('the Confidence layer uses the directional three-way call (D25)', async ({ page }) => {
  await ready(page);
  await page.selectOption('#layer-select', 'stability');
  await page.waitForTimeout(200);
  const ends = await page.locator('.legend-ends').innerText();
  expect(ends).toContain('Confidently a priority');
  expect(ends).toContain('Confidently not a priority');
  // The literal reading would print "low confidence" on cells the model is sure about.
  expect(ends.toLowerCase()).not.toContain('low confidence');
});

test('the Confidence layer explains which band matters', async ({ page }) => {
  await ready(page);
  await page.selectOption('#layer-select', 'stability');
  await page.waitForTimeout(200);
  const note = page.locator('#layer-note');
  await expect(note).toBeVisible();
  await expect(note).toContainText('middle band');
  await page.selectOption('#layer-select', 'priority');
  await page.waitForTimeout(200);
  await expect(note).toBeHidden();
});

test('the panel confidence wording never contradicts the data', async ({ page }) => {
  await ready(page);
  const cells = await page.evaluate(async () => {
    const doc = await (await fetch('data/cells.geojson')).json();
    const pick = s => doc.features.find(f => f.properties.stability === s);
    return { in: pick('confidently in')?.properties, out: pick('confidently out')?.properties };
  });
  expect(cells.in).toBeTruthy();
  expect(cells.out).toBeTruthy();
  for (const [kind, props] of Object.entries(cells)) {
    await page.evaluate((rank) => {
      const el = [...document.querySelectorAll('#map path.leaflet-interactive')]
        .find(e => (e.getAttribute('aria-label') || '').startsWith(`Cell ranked ${rank} of`));
      el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    }, props.rank);
    const text = await page.locator('#panel').innerText();
    expect(text).toContain(props.stability);
    expect(text).toContain(`between ${props.rank_low} and ${props.rank_high}`);
    if (kind === 'in') expect(text).toContain('confident this area is among the highest');
  }
});
