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
  const browser = await launch(home('trusted-quick-browser', true));
  try {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, ignoreHTTPSErrors: false });
    const page = await context.newPage();
    const errors = [], requested = [];
    page.on('pageerror', error => errors.push(error.name));
    page.on('request', request => requested.push(request.url()));
    stage = 'login';
    await page.goto(config.origin);
    await page.locator('#login-code').fill(config.code);
    await page.locator('#login-button').click();
    await page.getByText('Controller online', { exact: true }).waitFor();
    await page.locator('[data-tab="quick-join"]').click();
    stage = 'create-owner-code';
    await page.locator('#pair-create').click();
    await page.locator('#pair-details').waitFor();
    const grant = {
      code: await page.locator('#pair-code').innerText(),
      controller: await page.locator('#pair-origin').innerText(),
      pin: await page.locator('#pair-pin').innerText(),
      cluster_id: await page.locator('#pair-cluster').innerText(),
    };
    assert.ok(grant.code.length >= 8);
    assert.equal(grant.controller, config.controller);
    assert.equal(grant.pin, config.pin);
    assert.equal(grant.cluster_id, config.cluster_id);
    assert.notEqual(grant.code, config.code);
    const storage = await page.evaluate(() => JSON.stringify({ local: {...localStorage}, session: {...sessionStorage} }));
    assert.ok(!storage.includes(grant.code) && !storage.includes(config.code));
    // Private synthetic parent invokes the actual installed/guided node CLI.
    fs.writeFileSync(path.join(config.output, 'pairing.json'), JSON.stringify(grant), { mode: 0o600 });
    stage = 'wait-real-node-registration';
    await page.locator('#pair-status[data-state="registered"]').waitFor({ timeout: 40000 });
    assert.ok((await page.locator('#pair-registration').innerText()).includes('CHƯA phê duyệt'));
    assert.equal(await page.locator('#pair-code').innerText(), '');
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.screenshot({ path: path.join(config.output, 'quick-join-mobile.png'), fullPage: true });
    stage = 'offline-clears-secret';
    await page.locator('#pair-create').click();
    await page.locator('#pair-details').waitFor();
    assert.ok((await page.locator('#pair-code').innerText()).length >= 8);
    await context.setOffline(true);
    await page.locator('#refresh').click();
    await page.getByText('Controller UNKNOWN', { exact: true }).waitFor();
    assert.equal(await page.locator('#pair-code').innerText(), '');
    assert.ok(await page.locator('#pair-details').isHidden());
    assert.ok(await page.locator('#pair-create').isDisabled());
    await context.setOffline(false);
    await page.locator('#refresh').click();
    await page.getByText('Controller online', { exact: true }).waitFor();
    stage = 'delayed-post-cannot-repaint-after-logout';
    // Delay only delivery to application JS AFTER Chromium validates actual TLS.
    // Playwright route.fetch uses a separate trust store, so do not bypass it.
    await page.evaluate(() => {
      const actualFetch = window.fetch;
      window.fetch = async (...args) => {
        const response = await actualFetch(...args);
        if (args[0] === '/api/v1/quick-join/pairings') {
          globalThis.quickResponseArrived = true;
          await new Promise(resolve => { globalThis.releaseQuickResponse = resolve; });
        }
        return response;
      };
    });
    await page.locator('#pair-create').click();
    await page.waitForFunction(() => globalThis.quickResponseArrived === true);
    await page.locator('#logout').click();
    await page.locator('#login-panel').waitFor();
    await page.evaluate(() => globalThis.releaseQuickResponse()); await delay(400);
    assert.equal(await page.locator('#pair-code').innerText(), '');
    assert.ok(await page.locator('#pair-details').isHidden());
    assert.equal((await context.cookies()).some(value => value.name === '__Host-ASC-Demo'), false);
    assert.deepEqual(errors, []);
    assert.ok(requested.every(url => url.startsWith(config.origin + '/') || url === config.origin));
    assert.ok(!requested.some(url => url.includes(grant.code) || url.includes(config.code)));
    console.log(JSON.stringify({ passed: true, mobile_width: 390, registered_not_approved: true,
      no_persistent_grants: true, offline_cleared: true, stale_reply_discarded: true, trusted_tls: true }));
    await context.close();
  } finally { await browser.close(); }
})().catch(error => {
  console.error('Synthetic Quick Join browser failed at ' + stage + ': ' + error.name + '; credentials suppressed.');
  process.exitCode = 1;
});
