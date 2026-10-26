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
  stage = 'untrusted-launch';
  const untrusted = await launch(home('untrusted-browser', false));
  try {
    const page = await untrusted.newPage();
    stage = 'untrusted-denial';
    await assert.rejects(page.goto(config.origin), /ERR_CERT_AUTHORITY_INVALID/);
  } finally { await untrusted.close(); }
  stage = 'trusted-launch';
  const browser = await launch(home('trusted-browser', true));
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true, ignoreHTTPSErrors: false });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.name));
    const requested = new Set();
    page.on('request', request => requested.add(request.url()));
    stage = 'trusted-navigation';
    const response = await page.goto(config.origin);
    assert.equal(response.status(), 200);
    assert.equal(await page.evaluate(() => window.isSecureContext), true);
    assert.ok(response.headers()['content-security-policy'].includes("frame-ancestors 'none'"));
    stage = 'invalid-login';
    await page.locator('#login-code').fill('deliberately-wrong-code');
    await page.locator('#login-button').click();
    await page.getByText('Mã không hợp lệ, đã dùng hoặc đã hết hạn.', { exact: false }).waitFor();
    stage = 'owner-login';
    await page.locator('#login-code').fill(config.code);
    await page.locator('#login-button').click();
    await page.locator('#application').waitFor({ state: 'visible' });
    await page.getByText('Controller online', { exact: true }).waitFor();
    const cookies = await context.cookies();
    const session = cookies.find(value => value.name === '__Host-ASC-Demo');
    assert.ok(session && session.secure && session.httpOnly && session.sameSite === 'Strict');
    assert.equal(await page.evaluate(() => document.cookie.includes('__Host-ASC-Demo')), false);
    stage = 'node-details';
    await page.locator('[data-tab="nodes"]').click();
    assert.equal(await page.locator('.node-card').count(), 2);
    await page.locator('.node-card button').first().click();
    await page.locator('#details[open]').waitFor();
    await page.getByText('Node ID', { exact: true }).waitFor();
    await page.locator('#details-close').click();
    await page.locator('[data-tab="files"]').click();
    stage = 'upload';
    await page.locator('#file-input').setInputFiles(config.payload);
    await page.locator('#logical-path').fill(config.logical);
    await page.locator('#upload-button').click();
    await page.getByText('Đã xác nhận đủ hai bản sao trên hai miền lỗi độc lập.', { exact: true }).waitFor({ timeout: 90000 });
    stage = 'replica-details';
    // Retained native-qualification state can contain earlier real files. Keep
    // the original fresh-fixture behavior; target only this NEW upload on resume.
    const row = config.existing_file_count === undefined ? page.locator('.file-row').first()
      : page.locator('.file-row').filter({ has: page.locator('.file-name').filter({ hasText: config.logical }) });
    await row.getByText('Đủ hai bản sao', { exact: true }).waitFor();
    assert.equal(await row.locator('.file-name').innerText(), config.logical);
    assert.equal(await page.locator('img').count(), 0);
    assert.equal(await page.evaluate(() => globalThis.dashboardXss), undefined);
    const fileId = await row.getAttribute('data-file-id');
    await row.locator('[data-action="replicas"]').click();
    await page.locator('#details[open]').waitFor();
    const copies = await page.locator('[data-replica-node]').evaluateAll(nodes => nodes.map(node => node.dataset.replicaNode));
    assert.equal(copies.length, 2);
    assert.equal(new Set(copies).size, 2);
    await page.locator('#details-close').click();
    await page.screenshot({ path: path.join(config.output, 'dashboard-desktop.png'), fullPage: true });
    stage = 'mobile-layout';
    await page.setViewportSize({ width: 390, height: 844 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.screenshot({ path: path.join(config.output, 'dashboard-mobile.png'), fullPage: true });
    // Test-only parent fixture stops an ACTUAL synthetic node. No product control endpoint.
    stage = 'node-offline';
    const stopNode = config.required_native_node_id || copies[0];
    assert.ok(copies.includes(stopNode));
    fs.writeFileSync(path.join(config.output, 'stop-node.json'), JSON.stringify({ node_id: stopNode }));
    const deadline = Date.now() + 30000;
    while (!fs.existsSync(path.join(config.output, 'node-stopped')) && Date.now() < deadline) await delay(100);
    assert.ok(fs.existsSync(path.join(config.output, 'node-stopped')));
    await page.locator('#refresh').click();
    await row.getByText('Chưa đủ hai bản sao', { exact: true }).waitFor({ timeout: 20000 });
    stage = 'download-sha';
    const download = page.waitForEvent('download');
    await row.locator('[data-action="download"]').click();
    stage = 'wait-download-event';
    const saved = await download;
    stage = 'save-download';
    const output = path.join(config.output, 'downloaded-after-node-offline.bin');
    assert.equal(fs.existsSync(output), false);
    await saved.saveAs(output);
    stage = 'download-file-hash';
    const digest = crypto.createHash('sha256').update(fs.readFileSync(output)).digest('hex');
    assert.equal(digest, config.sha);
    stage = 'download-browser-confirmation';
    await page.locator('#download-status').filter({ hasText: 'SHA-256 khớp.' }).waitFor();
    stage = 'unsafe-upload-denied';
    await page.locator('#logical-path').fill('browser/new-after-node-offline.bin');
    await page.locator('#upload-button').click();
    await page.getByText('Không đủ dung lượng hoặc chưa có hai điện thoại độc lập đủ điều kiện.', { exact: false }).waitFor({ timeout: 20000 });
    assert.equal(await page.locator('.file-row').count(), (config.existing_file_count || 0) + 1);
    stage = 'controller-network-offline';
    await context.setOffline(true);
    await page.locator('#refresh').click();
    await page.getByText('Controller UNKNOWN', { exact: true }).waitFor();
    assert.ok(await page.locator('#upload-button').isDisabled());
    assert.ok(await row.locator('[data-action="download"]').isDisabled());
    await row.getByText('UNKNOWN · dữ liệu cũ', { exact: true }).waitFor();
    await context.setOffline(false);
    await page.locator('#refresh').click();
    await page.getByText('Controller online', { exact: true }).waitFor();
    stage = 'logout';
    await page.locator('#logout').click();
    await page.locator('#login-panel').waitFor({ state: 'visible' });
    assert.equal((await context.cookies()).some(value => value.name === '__Host-ASC-Demo'), false);
    assert.deepEqual(errors, []);
    assert.ok([...requested].every(url => url.startsWith(config.origin + '/') || url === config.origin));
    console.log(JSON.stringify({ passed: true, file_id: fileId, sha256: digest, replicas: copies.length,
      trusted_tls: true, untrusted_tls_denied: true, mobile_width: 390, offline_refused: true, page_errors: errors.length }));
    await context.close();
  } finally { await browser.close(); }
})().catch(error => {
  const known = ['ERR_CERT_AUTHORITY_INVALID', 'ERR_CERT_COMMON_NAME_INVALID', 'canceled', 'ERR_BLOCKED_BY_CSP', 'Target closed'].find(value => String(error).includes(value));
  const review = '/workspace/work/demo4-browser';
  fs.mkdirSync(review, { recursive: true });
  for (const name of ['dashboard-desktop.png', 'dashboard-mobile.png']) {
    const source = path.join(config.output, name);
    if (fs.existsSync(source)) fs.copyFileSync(source, path.join(review, name));
  }
  console.error('Synthetic browser integration failed at ' + stage + ': ' + (known || error.name) + '; credentials suppressed.');
  process.exitCode = 1;
});
