/* Lighthouse against the local site, with the PROMPT.md section 10 thresholds. */
import fs from 'node:fs';
import { launch } from 'chrome-launcher';
import lighthouse from 'lighthouse';

const THRESHOLDS = { performance: 85, accessibility: 95, 'best-practices': 90, seo: 90 };
const url = process.argv[2] || 'http://127.0.0.1:8765/index.html';

const chrome = await launch({ chromeFlags: ['--headless=new', '--no-sandbox'] });
try {
  const result = await lighthouse(url, {
    port: chrome.port,
    output: 'json',
    logLevel: 'error',
    formFactor: 'mobile',
    screenEmulation: { mobile: true, width: 375, height: 812, deviceScaleFactor: 2 },
  });
  fs.mkdirSync('artifacts', { recursive: true });
  fs.writeFileSync('artifacts/lighthouse.json', result.report);

  const failures = [];
  const lines = [];
  for (const [key, floor] of Object.entries(THRESHOLDS)) {
    const score = Math.round((result.lhr.categories[key].score ?? 0) * 100);
    lines.push(`${key}: ${score} (needs ${floor})`);
    if (score < floor) failures.push(`${key} ${score} < ${floor}`);
  }
  console.log(lines.join('; '));
  if (failures.length) {
    console.error('LIGHTHOUSE FAIL: ' + failures.join(', '));
    process.exit(1);
  }
} finally {
  await chrome.kill();
}
