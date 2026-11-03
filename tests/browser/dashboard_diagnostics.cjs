'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');const {chromium}=require('playwright');
const cfg=JSON.parse(fs.readFileSync(0,'utf8'));let stage='trust';
(async()=>{
  const home=path.join(cfg.output,'browser-home'),db=path.join(home,'.pki','nssdb');fs.mkdirSync(db,{recursive:true,mode:0o700});
  execFileSync('certutil',['-N','-d','sql:'+db,'--empty-password'],{stdio:'pipe'});
  execFileSync('certutil',['-A','-d','sql:'+db,'-n','ASC synthetic CA','-t','C,,','-i',cfg.ca],{stdio:'pipe'});
  const browser=await chromium.launch({headless:true,executablePath:process.env.ASC_TEST_CHROMIUM||'/usr/bin/chromium',env:{...process.env,HOME:home},args:['--disable-background-networking','--disable-component-update','--disable-sync']});
  try{
    const context=await browser.newContext({viewport:{width:390,height:844},acceptDownloads:true,ignoreHTTPSErrors:false});
    const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.name));await page.goto(cfg.origin);
    stage='login';await page.locator('#login-code').fill(cfg.code);await page.locator('#login-button').click();await page.locator('#application').waitFor({state:'visible'});
    stage='preferences';await page.locator('#settings-tab').click();const label='<img src=x onerror=globalThis.dashboardXss=1> Nhà';
    await page.locator('#preferences-name').fill(label);await page.locator('#preferences-refresh').fill('5');await page.locator('#preferences-save').click();
    await page.waitForFunction(()=>document.querySelector('#preferences-status').textContent.includes('Controller đã xác nhận'));
    assert.equal(await page.locator('#cluster-name').innerText(),label);assert.equal(await page.evaluate(()=>globalThis.dashboardXss),undefined);
    stage='reload';await page.reload();await page.locator('#application').waitFor({state:'visible'});await page.locator('#settings-tab').click();
    await page.waitForFunction(()=>document.querySelector('#preferences-refresh').value==='5');assert.equal(await page.locator('#preferences-name').inputValue(),label);
    stage='measured-health';await page.waitForFunction(()=>document.querySelectorAll('[data-health-volume]').length===2);
    assert.ok((await page.locator('#storage-health').innerText()).includes('Có / Có / Có'));
    stage='redacted-json';const event=page.waitForEvent('download');await page.locator('#diagnostics-download').click();
    const download=await event;await download.saveAs(path.join(cfg.output,'asc-diagnostics.json'));
    const report=JSON.parse(fs.readFileSync(path.join(cfg.output,'asc-diagnostics.json'),'utf8'));assert.equal(report.diagnostic_api_version,1);
    assert.ok(Object.values(report.features).every(v=>v===false));assert.ok(!JSON.stringify(report).includes(label));
    assert.equal(errors.length,0);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:path.join(cfg.output,'diagnostics-mobile.png'),fullPage:true});await context.close();console.log(JSON.stringify({passed:true,settings_persisted:true,redacted_export:true}));
  }finally{await browser.close();}
})().catch(error=>{console.error('Diagnostic browser failed at '+stage+' ('+error.name+'): '+error.message);process.exit(1);});
