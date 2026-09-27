import { test, expect } from '@playwright/test';

test('How it works explains the model without jargon', async ({ page }) => {
  await page.goto('/how-it-works.html');
  const text = await page.locator('main').innerText();
  for (const phrase of ['Heat', 'People', 'Vulnerability', 'Why multiply rather than add',
                        'How sure is it', 'What it cannot tell you']) {
    expect(text).toContain(phrase);
  }
  // The maths appendix is present but is not the first thing a coordinator meets.
  expect(text.indexOf('The maths')).toBeGreaterThan(text.indexOf('Why multiply'));
});

test('How it works states the numbers that matter', async ({ page }) => {
  await page.goto('/how-it-works.html');
  const text = await page.locator('main').innerText();
  expect(text).toMatch(/265 areas/);
  expect(text).toMatch(/28\s*\n?\s*stayed there|28 stayed there/);
  expect(text).toContain('half');            // the population undercount
  expect(text).toContain('Power cuts are not included');
  expect(text).toContain('not the air');
});

test('How it works explains the provisional banner it is linked from', async ({ page }) => {
  await page.goto('/how-it-works.html#provisional');
  const section = await page.locator('#provisional').innerText();
  expect(section.toLowerCase()).toContain('provisional');
  const text = await page.locator('main').innerText();
  expect(text).toContain('weights');
  expect(text).toContain('relief centre');
});

test('Data and credits lists every source with its licence', async ({ page }) => {
  await page.goto('/data-and-credits.html');
  const text = await page.locator('main').innerText();
  for (const source of ['OpenStreetMap', 'Landsat', 'Meta High Resolution', 'WorldPop',
                        'ESA WorldCover', 'Pakistan Bureau of Statistics', 'Esri', 'Leaflet']) {
    expect(text, `${source} is not credited`).toContain(source);
  }
  for (const licence of ['ODbL 1.0', 'CC BY 4.0', 'MIT', 'BSD-2-Clause', 'public domain']) {
    expect(text, `${licence} is not stated`).toContain(licence);
  }
});

test('Data and credits states the three project licences correctly', async ({ page }) => {
  await page.goto('/data-and-credits.html');
  const text = await page.locator('main').innerText();
  expect(text).toMatch(/Code:\s*MIT/);
  expect(text).toMatch(/documentation:\s*CC BY 4\.0/);
  expect(text).toMatch(/processed data:\s*ODbL 1\.0/);
  expect(text).toContain('share-alike');
});

test('About carries the disclaimer and the AI disclosure', async ({ page }) => {
  await page.goto('/about.html');
  const text = await page.locator('main').innerText();
  expect(text).toContain('Not an official warning system');
  expect(text).toContain('Pakistan Meteorological Department');
  expect(text).toContain('Not a model of deaths');
  expect(text).toContain('Not a verdict on any neighbourhood');
  expect(text).toContain('Built with Claude Code as a coding assistant');
  expect(text).toContain('Samraj Lal Ukrani');
});

test('About shows no contact channel, per D11c', async ({ page }) => {
  await page.goto('/about.html');
  const html = await page.locator('main').innerHTML();
  expect(html).not.toMatch(/mailto:/);
  expect(html).not.toMatch(/@[a-z0-9.-]+\.[a-z]{2,}/i);
  const text = await page.locator('main').innerText();
  expect(text).toContain('in person');
});

test('no content page names the school', async ({ page }) => {
  for (const path of ['/about.html', '/how-it-works.html', '/data-and-credits.html']) {
    await page.goto(path);
    const text = (await page.locator('body').innerText()).toLowerCase();
    expect(text, `${path} names the school`).not.toContain('nixor');
  }
});

test('no content page calls an area dangerous or unsafe', async ({ page }) => {
  for (const path of ['/index.html', '/about.html', '/how-it-works.html',
                      '/data-and-credits.html']) {
    await page.goto(path);
    const text = (await page.locator('body').innerText()).toLowerCase();
    for (const banned of ['unsafe', 'dangerous area', 'bad area', 'slum']) {
      expect(text, `${path} uses "${banned}"`).not.toContain(banned);
    }
  }
});
