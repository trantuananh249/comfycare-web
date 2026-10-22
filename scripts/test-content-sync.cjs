// Local browser regression for approved content synchronization; no external requests.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const out=path.resolve(process.env.CONTENT_TEST_OUTPUT||path.join(root,'outputs/content-latest'));fs.mkdirSync(out,{recursive:true});
const base=process.env.CHATBOT_TEST_URL||'http://127.0.0.1:4183';
const routes=['','cart/','cau-hoi-thuong-gap/','chinh-sach-bao-mat/','chinh-sach-doi-tra/','chinh-sach-thanh-toan/','chinh-sach-van-chuyen/','chung-nhan/','dieu-khoan-su-dung/','gioi-thieu/','huong-dan-chon-size/','huong-dan-su-dung/','lien-he/','phu-kien/','san-pham/','tat-dai-the-thao-cap-2/','tat-the-thao-cap-1/','tat-y-te-cap-2/'];
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const ctx=await browser.newContext();
 await ctx.route('**/*',route=>new URL(route.request().url()).origin===new URL(base).origin?route.continue():route.fulfill({status:200,body:''}));
 const page=await ctx.newPage(),errors=[],failed=[],results=[],existingOverflow=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)failed.push(r.url())});
 try{
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:900});
  for(const route of routes){
   await page.goto(base+'/'+route);await page.locator('footer').waitFor();
   const footer=await page.locator('footer').innerText();
   assert.match(footer,/111 đường 3C/);assert.doesNotMatch(footer,/48 Phương Lưu/);
   assert.equal(await page.locator('#comfy-chat').count(),1);
   const sizes=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,width:innerWidth}));
   assert.ok(sizes.scroll<=sizes.width+1,`${route} ${width}px horizontal overflow: ${sizes.scroll}`);
   // Viewport changes can switch srcset after load; wait for the selected images.
   await page.locator('img').evaluateAll(imgs=>Promise.all(imgs.map(async img=>{img.loading='eager';try{await img.decode()}catch{}})));
   // External requests are stubbed above, so only same-origin images are checked.
   assert.deepEqual(await page.locator('img').evaluateAll(imgs=>imgs.filter(i=>i.currentSrc&&new URL(i.currentSrc).origin===location.origin&&i.naturalWidth===0).map(i=>i.currentSrc)),[],route+' images');
   results.push({route,width,passed:true});
  }
 }
 await page.goto(base+'/lien-he/');
 assert.match(decodeURIComponent(await page.getByRole('link',{name:'Chỉ đường',exact:true}).getAttribute('href')),/111 đường 3C/);
 assert.match(await page.locator('main').innerText(),/15C\/19\/128 An Đà/);
 for(const route of ['lien-he','chinh-sach-doi-tra','chung-nhan','tat-the-thao-cap-1']){
  await page.goto(base+'/'+route+'/');await page.setViewportSize({width:390,height:844});
  await page.evaluate(async()=>{for(let y=0;y<document.documentElement.scrollHeight;y+=600){scrollTo(0,y);await new Promise(r=>setTimeout(r,40));}scrollTo(0,0);});
  // Newer Chrome never settles decode() on a lazy image that has not started loading.
  await page.locator('img').evaluateAll(imgs=>Promise.all(imgs.map(img=>{img.loading='eager';return img.decode().catch(()=>{})})));
  await page.screenshot({path:path.join(out,route+'-mobile.png'),fullPage:true});
 }
 await page.setViewportSize({width:1440,height:1000});await page.goto(base+'/chinh-sach-doi-tra/');
 const copy=await page.locator('main').innerText();assert.match(copy,/trừ số tiền khách thực trả/);assert.match(copy,/bằng chuyển khoản/);assert.doesNotMatch(copy,/giảm đi 20%/);
 await page.evaluate(async()=>{for(let y=0;y<document.documentElement.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,40));}scrollTo(0,0);});
 await page.locator('img').evaluateAll(imgs=>Promise.all(imgs.map(img=>{img.loading='eager';return img.decode().catch(()=>{})})));
 await page.screenshot({path:path.join(out,'returns-desktop.png'),fullPage:true});
 // The one static bundle edit must match the editable layout source exactly.
 const bundledFooter=await page.locator('footer').innerHTML();
 await page.addScriptTag({content:fs.readFileSync(path.join(root,'layout.js'),'utf8')});
 assert.equal(await page.locator('footer').innerHTML(),bundledFooter,'Bundled footer differs from source');
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 fs.writeFileSync(path.join(out,'validation.json'),JSON.stringify({base,checks:results,errors,failed,existingOverflow,footerSourceMatchesBundle:true},null,2));
 console.log('PASS: 54 page/viewport regression checks, new address/map, exchange policy, images, JS and bundle/source consistency.');
 console.log(JSON.stringify({existingOverflow}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
