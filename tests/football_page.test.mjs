// Football was removed from the TV experience. Keep this browser check so an
// old hash, saved setting, or future edit cannot bring its pages or requests back.
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let failed = 0;
const check = (name, ok, detail = '') => {
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (ok ? '' : '  -> ' + detail));
  if (!ok) failed++;
};

const browser = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
for (const file of ['tv.html', 'tv-en.html']) {
  for (const hash of [
    'widget=1&football=1&teams=136013&leagues=Saudi-Arabian%20Pro%20League',
    'matchpage=1&tour=1&teams=136013&leagues=Saudi-Arabian%20Pro%20League',
  ]) {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const sportsRequests = [];
    const errors = [];
    await ctx.route(/^https?:/, route => {
      const url = route.request().url();
      if (/thesportsdb|data-leagues|eventsnext|eventslast|tournaments\.json/i.test(url)) sportsRequests.push(url);
      return route.abort();
    });
    const page = await ctx.newPage();
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('file://' + path.join(ROOT, 'dist', file) + '#' + hash);
    await page.waitForTimeout(1000);

    const state = await page.evaluate(() => ({
      footballNodes: document.querySelectorAll('#fb,#fb-row,#mp,#mp-list,.fbw,.fcd,.mpg').length,
      footballClasses: document.documentElement.classList.contains('fb') || document.documentElement.classList.contains('matchpage'),
    }));
    const label = `${file} ${hash.startsWith('matchpage') ? 'old matches hash' : 'old football widget hash'}`;
    check(`${label}: no script error`, errors.length === 0, errors.join(' | '));
    check(`${label}: no football screen or card`, state.footballNodes === 0 && !state.footballClasses, JSON.stringify(state));
    check(`${label}: no football data request`, sportsRequests.length === 0, sportsRequests.join(' | '));
    await ctx.close();
  }
}
await browser.close();
if (failed) process.exit(1);
console.log('\nall removed-football browser tests passed');
