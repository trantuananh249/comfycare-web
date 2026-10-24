// Run with Node and PLAYWRIGHT_MODULE pointing to the installed playwright package.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const output = process.env.CHATBOT_TEST_OUTPUT || path.join(root, 'outputs/chatbot-latest');
fs.mkdirSync(output, { recursive: true });
const base = process.env.CHATBOT_TEST_URL || 'http://127.0.0.1:4173';
const pages = ['', 'cart/', 'cau-hoi-thuong-gap/', 'chinh-sach-bao-mat/', 'chinh-sach-doi-tra/', 'chinh-sach-thanh-toan/', 'chinh-sach-van-chuyen/', 'chung-nhan/', 'dieu-khoan-su-dung/', 'gioi-thieu/', 'huong-dan-chon-size/', 'huong-dan-su-dung/', 'lien-he/', 'phu-kien/', 'san-pham/', 'tat-dai-the-thao-cap-2/', 'tat-the-thao-cap-1/', 'tat-y-te-cap-2/',
  // Trang chi tiết sản phẩm (scripts/build-products.py)
  ...['cs21', 'cs22', 'cs23', 'cs24', 'cs26', 'cs27', 'cs33', 'cs34', 'cs35', 'cs25', 'cs28', 'cs29', 'cs30', 'cs31', 'cs11', 'cs12', 'cs14', 'cs110', 'cs100', 'cs101'].map(sku => `san-pham/${sku}/`)];
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  const context = await browser.newContext({ viewport: { width: 1366, height: 900 } });
  // Do not send analytics events during local QA.
  await context.route(/facebook\.com|facebook\.net/, route => route.fulfill({ status: 200, body: '' }));
  const page = await context.newPage();
  const errors = [], failures = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => { if (response.url().includes('chatbot.') && response.status() >= 400) failures.push(response.url()); });
  try {
    for (const route of pages) {
      await page.goto(`${base}/${route}`);
      assert.equal(await page.locator('#comfy-chat').count(), 1, route);
      assert.equal(await page.locator('.cc-panel').isVisible(), false, route);
      await page.locator('.cc-launcher').click();
      assert.match(await page.locator('.cc-history').innerText(), /Chào anh\/chị, em là trợ lý tư vấn/);
      assert.equal(await page.locator('.cc-topic-list button').count(), 10);
    }
    await page.goto(base);
    await page.locator('.cc-launcher').click();
    const greetingCount = await page.locator('.cc-message').count();
    await page.locator('#cc-input').press('Escape');
    assert.equal(await page.locator('.cc-panel').isVisible(), false);
    assert.equal(await page.locator('.cc-launcher').evaluate(el => el === document.activeElement), true);
    await page.locator('.cc-launcher').click();
    assert.equal(await page.locator('.cc-message').count(), greetingCount, 'No duplicate greeting');
    await page.locator('#cc-input').fill('   ');
    await page.locator('.cc-form button').click();
    assert.equal(await page.locator('.cc-message').count(), greetingCount, 'Blank ignored');
    const expected = [/Comfycare có/, /số đo chân/, /mẫu nào/, /bên đó/, /Jinhua/, /không hứa khỏi/, /đau bất thường/, /bác sĩ điều trị/, /15 ngày/, /2–3 ngày/];
    for (let i = 0; i < 10; i++) {
      await page.locator('.cc-topics').evaluate(el => { el.open = true; });
      await page.locator('.cc-topic-list button').nth(i).click();
      assert.match(await page.locator('.cc-message--bot').last().innerText(), expected[i], `FAQ ${i+1}`);
    }
    async function send(text, pattern) {
      await page.locator('#cc-input').fill(text);
      await page.locator('.cc-form button').click();
      const reply = await page.locator('.cc-message--bot').last().innerText();
      assert.match(reply, pattern, text);
      assert.doesNotMatch(reply, /\{\{|Nội bộ|đã lên đơn|đã nhận được nhu cầu/);
    }
    await send('Chon size the nao?', /số đo chân/);
    await send('Giá bao nhiêu?', /mẫu nào/);
    await send('CS21', /178\.500/);
    await send('Fanpage', /300\.000/);
    await send('Shopee', /178\.500/);
    await send('CS21 gia bao nhieu?', /178\.500/);
    await send('phi ship fanpage', /25\.000/);
    await send('shopee', /bước đặt hàng trên sàn/);
    await send('Tôi mang thai muốn mua CS21', /bác sĩ điều trị/);
    await send('Tôi bị tê chân khi mang', /tháo tất và hỏi bác sĩ/);
    await send('Toi can nhac them', /cân nhắc thêm/);
    await send('Tôi muốn mua ngay', /gian hàng chính thức/);
    await send('CS25 chọn size nào', /bảng size riêng/);
    await send('<img src=x onerror=alert(1)>', /kiểm tra thêm/);
    assert.equal(await page.locator('.cc-history img').count(), 0, 'Input rendered as text');
    await send('Xin chào', /Chào anh\/chị/);
    await page.screenshot({ path: path.join(output, 'desktop.png') });
    const mobile = await context.newPage();
    await mobile.setViewportSize({ width: 390, height: 844 });
    await mobile.goto(`${base}/san-pham/`);
    await mobile.locator('.cc-launcher').click();
    await mobile.screenshot({ path: path.join(output, 'mobile.png') });
    for (const [width, height] of [[390,844], [320,568], [844,390]]) {
      await mobile.setViewportSize({ width, height });
      await mobile.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const panel = await mobile.locator('.cc-panel').boundingBox();
      const launcher = await mobile.locator('.cc-launcher').boundingBox();
      const sticky = await mobile.locator('.mobile-sticky-cta').boundingBox();
      assert(panel.x >= 0 && panel.y >= 0 && panel.x + panel.width <= width + 1, `Panel fits ${width}`);
      assert(launcher.y + launcher.height <= (sticky ? sticky.y : height), `CTA does not overlap ${width}`);
      assert(await mobile.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `No horizontal overflow ${width}`);
      const input = await mobile.locator('#cc-input').boundingBox();
      assert(input.y + input.height <= panel.y + panel.height, `Input visible ${width}`);
    }
    assert.deepEqual(errors, []);
    assert.deepEqual(failures, []);
    fs.writeFileSync(path.join(output, 'validation.json'), JSON.stringify({ pages: pages.length, faq: 10, scenarios: 15, viewports: ['1366x900','390x844','320x568','844x390'], errors, assetFailures: failures, result: 'passed' }, null, 2));
    console.log(`PASS: ${pages.length} pages, 10 FAQs, conversation routing, safe rendering, keyboard controls, responsive layout.`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
