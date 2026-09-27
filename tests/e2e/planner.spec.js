import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';

// SYNTHETIC fixtures written by tests/fixtures/make_planner_fixtures.py. They reach the
// page only through route interception inside these tests, never from site/.
const FIX = path.resolve('tests/fixtures');
const PARITY = JSON.parse(fs.readFileSync(path.join(FIX, 'greedy_parity_SYNTHETIC.json')));
const SCENARIOS_FIXTURE = fs.readFileSync(path.join(FIX, 'scenarios_SYNTHETIC.json'), 'utf8');

async function ready(page) {
  await page.goto('plan.html');
  await page.waitForFunction(() => window.__planReady, null, { timeout: 15000 });
}

async function placeAndRun(page, stocks, distance) {
  for (let i = 0; i < stocks.length; i++) {
    await page.click('#add-point');
    await page.fill(`#stock-${i}`, String(stocks[i]));
  }
  if (distance) await page.selectOption('#distance', String(distance));
  await page.click('#run');
  await page.waitForFunction(() => window.__planResult && window.__planResult.kind === 'greedy');
  return page.evaluate(() => window.__planResult);
}

test('@smoke the planner loads and says honestly that no exact plan exists yet', async ({ page }) => {
  const problems = [];
  page.on('console', m => { if (m.type() === 'error') problems.push(m.text()); });
  page.on('pageerror', e => problems.push(String(e)));
  await ready(page);
  await expect(page.locator('#scenario-empty')).toContainText('verified');
  await expect(page.locator('#scenario-empty')).toContainText('Q2');
  expect(problems).toEqual([]);
});

test('the quick estimate is clearly labelled approximate', async ({ page }) => {
  await ready(page);
  await expect(page.locator('h3', { hasText: 'Quick estimate' })).toContainText('approximate');
  await expect(page.locator('#approx-note')).toContainText('exact planner can do better');
  await expect(page.locator('#approx-note')).toContainText('not verified relief centres');
  const result = await placeAndRun(page, [800]);
  await expect(page.locator('#result-summary')).toContainText('Quick estimate (approximate)');
  expect(result.kind).toBe('greedy');
});

test('totals never exceed stock, for any mix of stock points', async ({ page }) => {
  await ready(page);
  const result = await placeAndRun(page, [0, 1, 250, 1000000, 37], 3000);
  expect(result.total).toBeLessThanOrEqual(result.stock.reduce((a, b) => a + b, 0));
  result.dispatched.forEach((d, j) => expect(d).toBeLessThanOrEqual(result.stock[j]));
  expect(result.dispatched[0]).toBe(0);
  expect(result.tableUnits).toBe(result.total);
  for (const d of result.delivered) expect(Number.isInteger(d)).toBe(true);
});

test('zero stock sends nothing', async ({ page }) => {
  await ready(page);
  const result = await placeAndRun(page, [0]);
  expect(result.total).toBe(0);
  expect(result.rows).toBe(0);
  await expect(page.locator('#result-summary')).toContainText('nothing is sent');
});

test('the table and the map agree with the plan', async ({ page }) => {
  await ready(page);
  const result = await placeAndRun(page, [2000]);
  const rows = await page.locator('#result-table tbody tr').count();
  expect(rows).toBe(result.rows);
  const shares = await page.$$eval('#result-table tbody tr td:nth-child(3)',
    tds => tds.map(td => parseFloat(td.textContent)));
  expect(shares.reduce((a, b) => a + b, 0)).toBeLessThanOrEqual(100 + rows * 0.5);
  const coloured = await page.$$eval('#map path', ps =>
    ps.filter(p => (p.getAttribute('fill') || '').toUpperCase() !== '#FFFFFF').length);
  expect(coloured).toBe(result.rows);
});

test('the browser greedy matches the Python solver on 63 SYNTHETIC problems, ties included', async ({ page }) => {
  await ready(page);
  const mismatches = await page.evaluate((cases) => cases.map((c, k) => {
    const got = PlannerCore.greedy(c.priority, c.need, c.stock, c.dist, c.max_distance_m).x;
    return JSON.stringify(got) === JSON.stringify(c.expected_x) ? null : k;
  }).filter(k => k !== null), PARITY.greedy);
  expect(PARITY.greedy.length).toBe(63);
  expect(mismatches).toEqual([]);
});

test('browser distances agree with the pipeline to 0.05%', async ({ page }) => {
  await ready(page);
  const errors = await page.evaluate((cases) => cases.map(c => {
    const d = PlannerCore.distanceM(c.cell[0], c.cell[1], c.point[0], c.point[1], c.circuity);
    return Math.abs(d - c.expected_m) / c.expected_m;
  }), PARITY.distance);
  for (const e of errors) expect(e).toBeLessThan(0.0005);
});

test('exact scenarios render with their summary once a centre exists (SYNTHETIC)', async ({ page }) => {
  await page.route('**/data/scenarios.json', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: SCENARIOS_FIXTURE }));
  await ready(page);
  const options = await page.locator('#scenario-select option').count();
  expect(options).toBe(18);
  await expect(page.locator('#scenario-summary')).toContainText('estimated need');
  await page.selectOption('#scenario-select', '8');
  const result = await page.evaluate(() => window.__planResult);
  expect(result.kind).toBe('exact');
  expect(result.shareTotal).toBeLessThanOrEqual(1.001);
  await expect(page.locator('#result-kind')).toContainText('exact plan');
});

test('a stock point can be added by keyboard and removed', async ({ page }) => {
  await ready(page);
  await page.focus('#add-point');
  await page.keyboard.press('Enter');
  await expect(page.locator('#point-list li')).toHaveCount(1);
  await page.click('#remove-0');
  await expect(page.locator('#point-list li')).toHaveCount(0);
  await expect(page.locator('#run')).toBeDisabled();
});

test('axe finds no serious violations on the planner', async ({ page }) => {
  await ready(page);
  await placeAndRun(page, [500]);
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  const serious = results.violations.filter(
    v => v.impact === 'serious' || v.impact === 'critical');
  expect(serious.map(v => `${v.id}: ${v.description}`)).toEqual([]);
});
