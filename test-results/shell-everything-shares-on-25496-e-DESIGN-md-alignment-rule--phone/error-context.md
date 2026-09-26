# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: shell.spec.js >> everything shares one left edge (DESIGN.md alignment rule)
- Location: tests/e2e/shell.spec.js:57:5

# Error details

```
Error: left edges differ by 12px: {"title":16,"nav":4,"heading":16,"footer":16}

expect(received).toBeLessThanOrEqual(expected)

Expected: <= 2
Received:    12
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Skip to content" [ref=e2] [cursor=pointer]:
    - /url: "#main"
  - banner [ref=e3]:
    - generic [ref=e4]:
      - heading "Karachi Heat Priority Map" [level=1] [ref=e5]
      - navigation "Main" [ref=e6]:
        - link "Map" [ref=e7] [cursor=pointer]:
          - /url: index.html
        - link "Plan supplies" [ref=e8] [cursor=pointer]:
          - /url: plan.html
        - link "Field briefs" [ref=e9] [cursor=pointer]:
          - /url: briefs.html
        - link "How it works" [ref=e10] [cursor=pointer]:
          - /url: how-it-works.html
        - link "Data and credits" [ref=e11] [cursor=pointer]:
          - /url: data-and-credits.html
        - link "About" [ref=e12] [cursor=pointer]:
          - /url: about.html
  - main [ref=e13]:
    - generic [ref=e14]:
      - heading "About" [level=2] [ref=e15]
      - paragraph [ref=e16]: This page is not built yet. It arrives in Phase 3 (P3-06).
  - contentinfo [ref=e17]:
    - generic [ref=e18]:
      - paragraph [ref=e19]: Priority is a ranking within Landhi Town, not a measurement of risk on any absolute scale, and not a prediction of deaths. This is not an official warning system — for warnings follow the Pakistan Meteorological Department and PDMA Sindh.
      - paragraph [ref=e20]: Built with Claude Code as a coding assistant. Research question, modelling decisions, weights and fieldwork by Samraj Lal Ukrani.
      - paragraph [ref=e21]: Code MIT · text CC BY 4.0 · data ODbL 1.0, containing data derived from OpenStreetMap, © OpenStreetMap contributors.
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const PAGES = [
  4  |   ['/index.html', 'Karachi Heat Priority Map'],
  5  |   ['/plan.html', 'Plan supplies'],
  6  |   ['/briefs.html', 'Field briefs'],
  7  |   ['/how-it-works.html', 'How it works'],
  8  |   ['/data-and-credits.html', 'Data and credits'],
  9  |   ['/about.html', 'About'],
  10 | ];
  11 | 
  12 | for (const [path, title] of PAGES) {
  13 |   test(`${path} loads with a clean console`, async ({ page }) => {
  14 |     const problems = [];
  15 |     page.on('console', m => { if (m.type() === 'error') problems.push(m.text()); });
  16 |     page.on('pageerror', e => problems.push(String(e)));
  17 |     const response = await page.goto(path);
  18 |     expect(response.status()).toBe(200);
  19 |     await expect(page).toHaveTitle(new RegExp(title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  20 |     expect(problems, `console errors on ${path}`).toEqual([]);
  21 |   });
  22 | 
  23 |   test(`${path} never scrolls horizontally`, async ({ page }) => {
  24 |     await page.goto(path);
  25 |     const overflow = await page.evaluate(() =>
  26 |       document.documentElement.scrollWidth - document.documentElement.clientWidth);
  27 |     expect(overflow, `${path} overflows by ${overflow}px`).toBeLessThanOrEqual(0);
  28 |   });
  29 | 
  30 |   test(`${path} is reachable by keyboard`, async ({ page }) => {
  31 |     await page.goto(path);
  32 |     await page.keyboard.press('Tab');
  33 |     const first = await page.evaluate(() => document.activeElement?.className || '');
  34 |     expect(first).toContain('skip');
  35 |   });
  36 | }
  37 | 
  38 | test('every navigation link resolves', async ({ page }) => {
  39 |   await page.goto('/index.html');
  40 |   const hrefs = await page.$$eval('header.site nav a', els => els.map(e => e.getAttribute('href')));
  41 |   expect(hrefs.length).toBe(PAGES.length);
  42 |   for (const href of hrefs) {
  43 |     const response = await page.request.get(href);
  44 |     expect(response.status(), `${href} is broken`).toBe(200);
  45 |   }
  46 | });
  47 | 
  48 | test('tap targets in the header are at least 44px', async ({ page }) => {
  49 |   await page.goto('/index.html');
  50 |   const links = await page.$$('header.site nav a');
  51 |   for (const link of links) {
  52 |     const box = await link.boundingBox();
  53 |     expect(box.height, 'nav link height').toBeGreaterThanOrEqual(44);
  54 |   }
  55 | });
  56 | 
  57 | test('everything shares one left edge (DESIGN.md alignment rule)', async ({ page }) => {
  58 |   await page.goto('/about.html');
  59 |   const edges = await page.evaluate(() => {
  60 |     const x = s => { const el = document.querySelector(s); return el ? Math.round(el.getBoundingClientRect().left) : null; };
  61 |     return {
  62 |       title: x('header.site h1'),
  63 |       nav: x('header.site nav a'),
  64 |       heading: x('main h2'),
  65 |       footer: x('footer.site p'),
  66 |     };
  67 |   });
  68 |   const values = Object.values(edges).filter(v => v !== null);
  69 |   expect(values.length).toBe(4);
  70 |   const spread = Math.max(...values) - Math.min(...values);
> 71 |   expect(spread, `left edges differ by ${spread}px: ${JSON.stringify(edges)}`).toBeLessThanOrEqual(2);
     |                                                                                ^ Error: left edges differ by 12px: {"title":16,"nav":4,"heading":16,"footer":16}
  72 | });
  73 | 
  74 | test('the page background and body text match the DESIGN.md tokens', async ({ page }) => {
  75 |   await page.goto('/about.html');
  76 |   const styles = await page.evaluate(() => {
  77 |     const cs = getComputedStyle(document.body);
  78 |     return { bg: cs.backgroundColor, fg: cs.color };
  79 |   });
  80 |   expect(styles.bg).toBe('rgb(250, 248, 245)');  // --paper
  81 |   expect(styles.fg).toBe('rgb(26, 28, 30)');     // --ink
  82 | });
  83 | 
```