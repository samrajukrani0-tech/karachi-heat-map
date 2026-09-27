import { test, expect } from '@playwright/test';

test('@smoke every field brief link on the page resolves', async ({ page }) => {
  await page.goto('briefs.html');
  const hrefs = await page.$$eval('table.briefs a', as => as.map(a => a.getAttribute('href')));
  expect(hrefs.length).toBe(36);           // 12 places x view, PDF, image
  for (const href of hrefs) {
    const r = await page.request.get(href);
    expect(r.status(), href).toBe(200);
    const type = r.headers()['content-type'] || '';
    if (href.endsWith('.pdf')) expect(type).toContain('pdf');
    if (href.endsWith('.png')) expect(type).toContain('png');
  }
});

test('a brief page opens and states its caveats', async ({ page }) => {
  await page.goto('briefs.html');
  await page.locator('table.briefs a', { hasText: 'View' }).first().click();
  await expect(page.locator('h1')).toBeVisible();
  await expect(page.locator('body')).toContainText('What this cannot tell you');
  await expect(page.locator('body')).toContainText('not an official warning system', { ignoreCase: true });
});

test('brief download links are full-size tap targets', async ({ page }) => {
  await page.goto('briefs.html');
  const heights = await page.$$eval('table.briefs .links a',
    as => as.map(a => a.getBoundingClientRect().height));
  expect(Math.min(...heights)).toBeGreaterThanOrEqual(44);
});
