// Print one local HTML file to an A4 PDF with Playwright's Chromium, failing if the
// content runs off the page. Usage: node scripts/render_pdf.mjs in.html out.pdf
import { chromium } from '@playwright/test';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [input, output] = process.argv.slice(2);
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 794, height: 1123 } });
  await page.goto(pathToFileURL(path.resolve(input)).href);
  const bottom = await page.evaluate(() =>
    document.querySelector('.page').lastElementChild.getBoundingClientRect().bottom);
  if (bottom > 1123 - 20) throw new Error(`${input}: runs off the A4 page (${bottom}px)`);
  await page.pdf({ path: output, format: 'A4', printBackground: true, preferCSSPageSize: true });
  console.log(`wrote ${output}`);
} finally {
  await browser.close();
}
