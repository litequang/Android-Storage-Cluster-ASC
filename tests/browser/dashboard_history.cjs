'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');const {chromium}=require('playwright');
const cfg=JSON.parse(fs.readFileSync(0,'utf8'));let stage='trust';
const waitFile=async name=>{const end=Date.now()+25000;while(!fs.existsSync(path.join(cfg.output,name))){if(Date.now()>end)throw Error('owned process signal timeout');await new Promise(r=>setTimeout(r,100));}};
(async()=>{
  const home=path.join(cfg.output,'browser-home'),db=path.join(home,'.pki','nssdb');fs.mkdirSync(db,{recursive:true,mode:0o700});
  execFileSync('certutil',['-N','-d','sql:'+db,'--empty-password'],{stdio:'pipe'});
  execFileSync('certutil',['-A','-d','sql:'+db,'-n','ASC synthetic CA','-t','C,,','-i',cfg.ca],{stdio:'pipe'});
  const browser=await chromium.launch({headless:true,executablePath:process.env.ASC_TEST_CHROMIUM||'/usr/bin/chromium',env:{...process.env,HOME:home},args:['--disable-background-networking','--disable-component-update','--disable-sync']});
  try {
    const context=await browser.newContext({viewport:{width:390,height:844},acceptDownloads:true,ignoreHTTPSErrors:false});
    // Browser storage denial is a capability fault, not a mocked backend result.
    await context.addInitScript(()=>{Storage.prototype.getItem=()=>{throw new DOMException('Storage blocked','SecurityError');};Storage.prototype.setItem=()=>{throw new DOMException('Storage blocked','SecurityError');};});
    const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.name));
    await page.goto(cfg.origin);stage='login';await page.locator('#login-code').fill(cfg.code);await page.locator('#login-button').click();
    await page.locator('#application').waitFor({state:'visible'});await page.locator('#snapshots-tab').click();
    stage='capture-pause';await page.locator('#snapshot-label').fill('<img src=x onerror=globalThis.dashboardXss=1>');await page.locator('#snapshot-prefix').fill('history-browser');
    await page.locator('#snapshot-create').click();await page.locator('#history-pause').waitFor({state:'visible'});await page.locator('#history-pause').click();
    await page.waitForFunction(()=>document.querySelectorAll('[data-snapshot-id]').length===1);assert.equal(await page.evaluate(()=>globalThis.dashboardXss),undefined);
    const sid=await page.locator('[data-snapshot-id]').getAttribute('data-snapshot-id');
    stage='reload-progress';await page.reload();await page.locator('#application').waitFor({state:'visible'});await page.locator('#snapshots-tab').click();
    const snapshot=()=>page.locator('[data-snapshot-id="'+sid+'"]');await snapshot().waitFor();
    assert.equal(await page.locator('#history-pause').isHidden(),true);
    stage='node-offline';fs.writeFileSync(path.join(cfg.output,'stop-node'),'stop owned synthetic Node');await waitFile('node-stopped');
    await snapshot().locator('[data-history-step]').click();
    await page.waitForFunction(()=>document.querySelector('#history-status').textContent.includes('Chưa đọc đúng bytes'));
    assert.equal(await snapshot().locator('.badge').innerText(),'VERIFYING');assert.equal(await page.locator('[data-restore-id]').count(),0);
    stage='node-restart-resume';fs.writeFileSync(path.join(cfg.output,'restart-node'),'restart owned retained Node');await waitFile('node-restarted');
    await snapshot().locator('[data-history-step]').click();await page.waitForFunction(()=>document.querySelector('[data-snapshot-id] .badge').textContent==='VERIFIED');
    await page.waitForFunction(()=>document.querySelector('#history-pause').hidden);
    stage='confirmed-restore';await snapshot().getByRole('button',{name:'Xem phiên bản',exact:true}).click();
    await page.locator('[data-snapshot-file-id="'+cfg.first.file_id+'"] [data-action="restore-snapshot-file"]').click();
    await page.locator('#restore-dialog').waitFor({state:'visible'});await page.locator('#restore-confirm-path').fill('wrong/path');await page.locator('#restore-confirm').check();
    await page.locator('#restore-create').click();await page.waitForFunction(()=>document.querySelector('#restore-result').textContent.includes('Cần đúng đường dẫn'));
    assert.equal(await page.locator('[data-restore-id]').count(),0);
    await page.locator('#restore-confirm-path').fill(cfg.first.logical_path);await page.locator('#restore-create').click();
    await page.waitForFunction(()=>document.querySelector('[data-restore-id] .badge')?.textContent==='COMPLETED');
    assert.ok((await page.locator('[data-restore-id]').innerText()).includes('v1 → v4'));
    stage='restored-sha';const event=page.waitForEvent('download');await page.locator('[data-restore-id]').getByRole('button',{name:'Tải bản khôi phục',exact:true}).click();
    const download=await event,output=path.join(cfg.output,'restored.bin');await download.saveAs(output);
    assert.equal(crypto.createHash('sha256').update(fs.readFileSync(output)).digest('hex'),cfg.sha256);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.equal(errors.length,0);
    await page.screenshot({path:path.join(cfg.output,'history-mobile.png'),fullPage:true});
    await context.close();console.log(JSON.stringify({passed:true,paused_resume:true,real_node_restart:true,restored_version:4,sha256:cfg.sha256}));
  } finally {await browser.close();}
})().catch(error=>{console.error('History browser failed at '+stage+' ('+error.name+'): '+error.message);process.exit(1);});
