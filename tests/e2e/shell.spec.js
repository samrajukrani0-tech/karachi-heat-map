import { test, expect } from '@playwright/test';

const PAGES = [
  ['/index.html', 'Karachi Heat Priority Map'],
  ['/plan.html', 'Plan supplies'],
  ['/briefs.html', 'Field briefs'],
  ['/how-it-works.html', 'How it works'],
  ['/data-and-credits.html', 'Data and credits'],
  ['/about.html', 'About'],
];

for (const [path, title] of PAGES) {
  test(`${path} loads with a clean console`, async ({ page }) => {
    const problems = [];
    page.on('console', m => { if (m.type() === 'error') problems.push(m.text()); });
    page.on('pageerror', e => problems.push(String(e)));
    const response = await page.goto(path);
    expect(response.status()).toBe(200);
    await expect(page).toHaveTitle(new RegExp(title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
    expect(problems, `console errors on ${path}`).toEqual([]);
  });

  test(`${path} never scrolls horizontally`, async ({ page }) => {
    await page.goto(path);
    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, `${path} overflows by ${overflow}px`).toBeLessThanOrEqual(0);
  });

  test(`${path} is reachable by keyboard`, async ({ page }) => {
    await page.goto(path);
    await page.keyboard.press('Tab');
    const first = await page.evaluate(() => document.activeElement?.className || '');
    expect(first).toContain('skip');
  });
}

test('every navigation link resolves', async ({ page }) => {
  await page.goto('/index.html');
  const hrefs = await page.$$eval('header.site nav a', els => els.map(e => e.getAttribute('href')));
  expect(hrefs.length).toBe(PAGES.length);
  for (const href of hrefs) {
    const response = await page.request.get(href);
    expect(response.status(), `${href} is broken`).toBe(200);
  }
});

test('tap targets in the header are at least 44px', async ({ page }) => {
  await page.goto('/index.html');
  const links = await page.$$('header.site nav a');
  for (const link of links) {
    const box = await link.boundingBox();
    expect(box.height, 'nav link height').toBeGreaterThanOrEqual(44);
  }
});

test('everything shares one left edge (DESIGN.md alignment rule)', async ({ page }) => {
  await page.goto('/about.html');
  const edges = await page.evaluate(() => {
    const x = s => { const el = document.querySelector(s); return el ? Math.round(el.getBoundingClientRect().left) : null; };
    return {
      title: x('header.site h1'),
      nav: x('header.site nav a'),
      heading: x('main h2'),
      footer: x('footer.site p'),
    };
  });
  const values = Object.values(edges).filter(v => v !== null);
  expect(values.length).toBe(4);
  const spread = Math.max(...values) - Math.min(...values);
  expect(spread, `left edges differ by ${spread}px: ${JSON.stringify(edges)}`).toBeLessThanOrEqual(2);
});

test('the page background and body text match the DESIGN.md tokens', async ({ page }) => {
  await page.goto('/about.html');
  const styles = await page.evaluate(() => {
    const cs = getComputedStyle(document.body);
    return { bg: cs.backgroundColor, fg: cs.color };
  });
  expect(styles.bg).toBe('rgb(250, 248, 245)');  // --paper
  expect(styles.fg).toBe('rgb(26, 28, 30)');     // --ink
});
