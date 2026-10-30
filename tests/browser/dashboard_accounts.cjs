'use strict';
// Actual trusted HTTPS browser login/account roles; no default credentials or TLS bypass.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');const {chromium}=require('playwright');
const cfg=JSON.parse(fs.readFileSync(0,'utf8'));let stage='trust';
(async()=>{
  const home=path.join(cfg.output,'browser-home'),db=path.join(home,'.pki','nssdb');
  fs.mkdirSync(db,{recursive:true,mode:0o700});
  execFileSync('certutil',['-N','-d','sql:'+db,'--empty-password'],{stdio:'pipe'});
  execFileSync('certutil',['-A','-d','sql:'+db,'-n','ASC synthetic CA','-t','C,,','-i',cfg.ca],{stdio:'pipe'});
  const browser=await chromium.launch({headless:true,executablePath:process.env.ASC_TEST_CHROMIUM||'/usr/bin/chromium',env:{...process.env,HOME:home},
    args:['--disable-background-networking','--disable-component-update','--disable-sync']});
  try {
    const context=await browser.newContext({viewport:{width:390,height:844},acceptDownloads:true,ignoreHTTPSErrors:false});
    const page=await context.newPage(),errors=[],urls=[];page.on('pageerror',e=>errors.push(e.name));page.on('request',r=>urls.push(r.url()));
    await page.goto(cfg.origin);stage='bootstrap-code';await page.locator('#login-code').fill(cfg.code);await page.locator('#login-button').click();
    await page.locator('#application').waitFor({state:'visible'});await page.locator('#accounts-tab').click();
    async function create(name,password,role){
      await page.locator('#account-new-username').fill(name);await page.locator('#account-new-password').fill(password);await page.locator('#account-new-role').selectOption(role);
      await page.locator('#account-create').click();
      await page.waitForFunction(()=>document.querySelector('#account-result').textContent.includes('đã xác nhận tạo tài khoản'));
      assert.equal(await page.locator('#account-new-password').inputValue(),'');
    }
    stage='create-owner';await create('primary',cfg.owner_password,'owner');
    stage='create-viewer';await create('reader',cfg.viewer_password,'viewer');
    await page.waitForFunction(()=>document.querySelectorAll('#account-list [data-account-id]').length===2);
    const primary=()=>page.locator('#account-list .node-card').filter({has:page.getByRole('heading',{name:'primary',exact:true})});
    stage='last-owner-refusal';await primary().getByRole('button').click();await page.locator('#account-delete').check();
    await page.locator('#account-confirm-name').fill('primary');await page.locator('#account-save').click();
    await page.waitForFunction(()=>document.querySelector('#account-change-result').textContent.includes('Phải giữ ít nhất một Owner'));
    await page.locator('#account-close').click();
    async function logout(){await page.locator('#logout').click();await page.locator('#login-panel').waitFor({state:'visible'});
      await page.waitForFunction(()=>document.querySelector('#login-kind').value==='password');}
    async function login(name,password){
      await page.locator('#login-username').fill(name);await page.locator('#login-password').fill(password);await page.locator('#login-button').click();
      await page.locator('#application').waitFor({state:'visible'});assert.equal(await page.locator('#login-password').inputValue(),'');
    }
    stage='password-login';await logout();await login('primary',cfg.owner_password);
    assert.ok((await page.locator('#actor-label').innerText()).includes('primary'));
    await page.locator('#accounts-tab').click();await primary().getByRole('button').click();
    stage='self-password-rotation';await page.locator('#account-password').fill(cfg.rotated_password);
    await page.locator('#account-confirm-name').fill('primary');await page.locator('#account-save').click();
    await page.locator('#login-panel').waitFor({state:'visible'});
    await page.locator('#login-username').fill('primary');await page.locator('#login-password').fill(cfg.owner_password);await page.locator('#login-button').click();
    await page.waitForFunction(()=>document.querySelector('#login-error').textContent.length>0);
    assert.equal(await page.locator('#application').isHidden(),true);
    await login('primary',cfg.rotated_password);
    stage='viewer-login';await logout();await login('reader',cfg.viewer_password);
    assert.equal(await page.locator('#account-target').textContent(),'');
    assert.equal(await page.locator('#account-new-username').inputValue(),'');
    assert.equal(await page.locator('#accounts-tab').isHidden(),true);assert.equal(await page.locator('#upload-panel').isHidden(),true);
    assert.equal(await page.locator('[data-tab="quick-join"]').isHidden(),true);
    await page.locator('[data-tab="nodes"]').click();assert.equal(await page.locator('[data-action="manage"]').count(),0);
    const denied=await page.evaluate(async()=>{
      const session=await(await fetch('/api/session')).json();const r=await fetch('/api/refresh',{method:'POST',headers:{'Content-Type':'application/json','X-ASC-CSRF':session.csrf},body:'{}'});
      return {status:r.status,body:await r.json()};
    });assert.equal(denied.status,403);assert.equal(denied.body.error,'role_denied');
    stage='viewer-real-download';await page.locator('[data-tab="files"]').click();
    const event=page.waitForEvent('download');await page.locator('[data-file-id="'+cfg.file_id+'"] [data-action="download"]').click();
    const download=await event,output=path.join(cfg.output,'viewer.bin');await download.saveAs(output);
    assert.equal(crypto.createHash('sha256').update(fs.readFileSync(output)).digest('hex'),cfg.sha256);
    const storage=await page.evaluate(()=>JSON.stringify({local:{...localStorage},session:{...sessionStorage}}));
    for(const secret of [cfg.code,cfg.owner_password,cfg.viewer_password,cfg.rotated_password]) {
      assert.ok(!storage.includes(secret));assert.ok(urls.every(url=>!url.includes(secret)));
    }
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.equal(errors.length,0);
    await page.screenshot({path:path.join(cfg.output,'accounts-viewer-mobile.png'),fullPage:true});
    await logout();console.log(JSON.stringify({passed:true,roles:['owner','viewer'],password_rotation:true,sha256:cfg.sha256}));
    await context.close();
  } finally {await browser.close();}
})().catch(error=>{console.error('Account browser failed at '+stage+' ('+error.name+')');process.exit(1);});
