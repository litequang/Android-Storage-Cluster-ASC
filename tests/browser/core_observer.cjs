'use strict';
// Actual Chromium UI with an isolated NSS trust DB. No certificate-error bypass.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const { chromium } = require('playwright');
const config = JSON.parse(fs.readFileSync(0, 'utf8'));
let stage = 'setup';
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
function home(name, trust) {
  const root = path.join(config.output, name);
  const database = path.join(root, '.pki', 'nssdb');
  fs.mkdirSync(database, { recursive: true, mode: 0o700 });
  execFileSync('certutil', ['-N', '-d', 'sql:' + database, '--empty-password'], { stdio: 'pipe' });
  if (trust) execFileSync('certutil', ['-A', '-d', 'sql:' + database, '-n', 'ASC synthetic Dashboard CA', '-t', 'C,,', '-i', config.ca], { stdio: 'pipe' });
  return root;
}
async function launch(root) {
  return chromium.launch({ executablePath: process.env.ASC_TEST_CHROMIUM || '/usr/bin/chromium', headless: true,
    env: { ...process.env, HOME: root }, args: ['--disable-background-networking', '--disable-component-update', '--disable-sync'] });
}
(async () => {
  const browser = await launch(home('core-trusted', true));
  try {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, ignoreHTTPSErrors: false });
    const page = await context.newPage(), errors = [], posts = [];
    page.on('pageerror', error => errors.push(error.name));
    page.on('request', request => { if (request.method() !== 'GET') posts.push(new URL(request.url()).pathname); });
    stage = 'mode-before-login';
    await page.goto(config.origin);
    await page.locator('#login-method').filter({ hasText: 'serve --issue-login-code' }).waitFor();
    await page.locator('#login-code').fill(config.code); await page.locator('#login-button').click();
    stage = 'strong-core-overview';
    await page.locator('#core-status').filter({ hasText: 'Đã xác minh barrier' }).waitFor({ timeout: 40000 });
    assert.equal(await page.locator('[data-controller-id]').count(), 3);
    assert.ok(await page.locator('[data-tab="quick-join"]').isHidden());
    assert.ok(await page.locator('#snapshots-tab').isHidden());
    await page.locator('[data-tab="nodes"]').click(); assert.equal(await page.locator('.node-card[data-node-id]').count(), 3);
    await page.locator('[data-tab="files"]').click(); assert.ok(await page.locator('#upload-panel').isHidden());
    assert.equal(await page.locator('[data-action="download"]').count(), 0);
    assert.equal(await page.locator('.file-name').first().innerText(), config.logical);
    assert.equal(await page.locator('img').count(), 0); assert.equal(await page.evaluate(() => globalThis.coreXss), undefined);
    await page.locator('.file-row').getByText('Đạt policy 3 miền lỗi', { exact: true }).waitFor();
    await page.locator('[data-action="replicas"]').first().click(); await page.locator('#details[open]').waitFor();
    assert.equal(await page.locator('[data-replica-node]').count(), 3); await page.locator('#details-close').click();
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    const stored = await page.evaluate(() => JSON.stringify({ local: {...localStorage}, session: {...sessionStorage} }));
    assert.ok(!stored.includes(config.code));
    stage = 'actual-quorum-loss'; fs.writeFileSync(path.join(config.output, 'partition'), 'request actual transport fault');
    while (!fs.existsSync(path.join(config.output, 'partitioned'))) await delay(100);
    await page.locator('#refresh').waitFor({ state: 'visible' });
    await page.locator('#refresh:not([disabled])').click();
    await page.getByText('QUORUM UNAVAILABLE', { exact: true }).first().waitFor({ timeout: 40000 });
    await page.locator('.file-row').getByText('UNKNOWN · cần xác minh', { exact: true }).waitFor();
    stage = 'actual-reconnect'; fs.writeFileSync(path.join(config.output, 'heal'), 'request actual heal');
    while (!fs.existsSync(path.join(config.output, 'healed'))) await delay(100);
    stage = 'reconnect-refresh'; await page.locator('#refresh:not([disabled])').click();
    stage = 'reconnect-protection'; await page.locator('.file-row').getByText('Đạt policy 3 miền lỗi', { exact: true }).waitFor({ timeout: 40000 });
    stage = 'reconnect-overview'; await page.locator('[data-tab="overview"]').click();
    stage = 'core-screenshot'; await page.screenshot({ path: path.join(config.output, 'core-observer-mobile.png'), fullPage: true });
    stage = 'core-logout'; await page.locator('#logout').click(); await page.locator('#login-panel').waitFor();
    stage = 'core-no-writes'; assert.deepEqual(posts.filter(value => !['/api/login', '/api/logout'].includes(value)), []);
    stage = 'core-page-errors'; assert.deepEqual(errors, []);
    console.log(JSON.stringify({ passed: true, actual_quorum_loss_heal: true, read_only_posts: true, controllers: 3, mobile_width: 390 }));
    await context.close();
  } finally { await browser.close(); }
})().catch(error => {
  console.error('Synthetic Core observer browser failed at ' + stage + ': ' + error.name + '; credentials suppressed.');process.exitCode = 1;
});
