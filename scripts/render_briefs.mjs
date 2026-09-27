// P5-01: print each site/briefs/*.html to an A4 PDF and a PNG with Playwright's
// Chromium. Called by scripts/field_briefs.py; the same browser the tests use, so the
// output is the same on every machine.
import { chromium } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const dir = path.resolve('site/briefs');
const pages = fs.readdirSync(dir).filter(f => f.endsWith('.html')).sort();
const browser = await chromium.launch();
try {
  // A4 at 96 CSS px per inch is 794 x 1123; 1.5x gives a PNG sharp enough to read on a
  // phone without going near the 1 MB limit.
  const page = await browser.newPage({ viewport: { width: 794, height: 1123 },
                                       deviceScaleFactor: 1.5 });
  for (const file of pages) {
    const base = path.join(dir, file.replace(/\.html$/, ''));
    await page.goto(pathToFileURL(path.join(dir, file)).href);
    // One A4 page means everything fits: .page hides overflow, so check the last
    // element's bottom edge rather than trusting the page count.
    const bottom = await page.evaluate(() =>
      document.querySelector('footer').getBoundingClientRect().bottom);
    if (bottom > 1123 - 20) {
      throw new Error(`${file}: content runs off the A4 page (footer ends at ${bottom}px)`);
    }
    await page.pdf({ path: `${base}.pdf`, format: 'A4', printBackground: true,
                     preferCSSPageSize: true });
    await page.screenshot({ path: `${base}.png`, fullPage: false });
  }
  console.log(`rendered ${pages.length} briefs to PDF and PNG`);
} finally {
  await browser.close();
}
