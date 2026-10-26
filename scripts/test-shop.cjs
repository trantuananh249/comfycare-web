// Kiểm thử luồng mua trên web (kế hoạch 09 bước 4) với API chạy thử trên máy.
// Cần: website ở SHOP_TEST_URL (mặc định http://127.0.0.1:4183) và API thử ở SHOP_TEST_API
// (mặc định http://127.0.0.1:8787, chạy `node scripts/dev-server.mjs` trong repo comfycare-api).
// Biến: PLAYWRIGHT_MODULE, CHROME_PATH, SHOP_TEST_OUTPUT, SHOP_TEST_SEPAY_KEY (mặc định dev-sepay-key).
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const base = process.env.SHOP_TEST_URL || 'http://127.0.0.1:4183';
const apiBase = process.env.SHOP_TEST_API || 'http://127.0.0.1:8787';
const sepayKey = process.env.SHOP_TEST_SEPAY_KEY || 'dev-sepay-key';
const out = path.resolve(process.env.SHOP_TEST_OUTPUT || path.join(root, 'outputs/shop-latest'));
fs.mkdirSync(out, { recursive: true });

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  const results = [];
  const errors = [];
  const watch = (page) => {
    page.on('pageerror', (e) => errors.push(`${page.url()} ${e.message}`));
    page.on('response', (r) => { const u = new URL(r.url()); if (r.status() >= 500 || (r.status() >= 400 && u.origin === base)) errors.push(`${r.status()} ${r.url()}`); });
  };
  const block = (ctx) => ctx.route(/facebook\.(com|net)|vietqr\.app|challenges\.cloudflare\.com/, (route) => route.fulfill({ status: 200, body: '' }));
  const fbEvents = (page) => page.evaluate(() => (window.fbq?.queue || []).filter((a) => a[0] === 'track').map((a) => a[1]));
  const noOverflow = async (page, label) => {
    for (const width of [1440, 390, 320]) {
      await page.setViewportSize({ width, height: 900 });
      await page.waitForTimeout(150);
      const over = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(over <= 0, `${label} tràn ngang ${over}px ở ${width}px`);
      await page.screenshot({ path: path.join(out, `${label}-${width}.png`), fullPage: true });
    }
    await page.setViewportSize({ width: 1440, height: 900 });
  };

  try {
    // 1. Chưa mở bán: giữ nguyên "Sắp ra mắt" / thông báo.
    {
      const ctx = await browser.newContext(); await block(ctx);
      const page = await ctx.newPage(); watch(page);
      await page.goto(`${base}/san-pham/cs22/`);
      assert.equal(await page.locator('.pd-web-buy').isDisabled(), true);
      assert.equal(await page.locator('[data-cart-link]').isHidden(), true);
      for (const route of ['cart/', 'thanh-toan/', 'don-hang/']) {
        await page.goto(`${base}/${route}`);
        assert.equal(await page.locator('[data-shop-off]').first().isVisible(), true, route);
        assert.equal(await page.locator('[data-shop-on]').first().isHidden(), true, route);
      }
      await page.goto(`${base}/`);
      assert.equal(await page.locator('.product-card .btn-web-soon').count(), 8);
      results.push('Chưa mở bán: nút disabled, giỏ ẩn, 3 trang chỉ hiện thông báo');
      await ctx.close();
    }

    // 2. Xem thử (bật): thêm vào giỏ, giỏ, thanh toán COD.
    const ctx = await browser.newContext(); await block(ctx);
    await ctx.addInitScript(() => document.addEventListener('cc:track', (e) => {
      const list = JSON.parse(sessionStorage.getItem('__tracked') || '[]');
      list.push(e.detail.event);
      sessionStorage.setItem('__tracked', JSON.stringify(list));
    }));
    const page = await ctx.newPage(); watch(page);
    await page.goto(`${base}/?shop-preview=${encodeURIComponent(apiBase)}`);
    assert.equal(await page.locator('.product-card .btn-web-buy').count(), 8, 'thẻ trang chủ thành link Mua ngay');
    assert.equal(await page.locator('.product-card .btn-web-buy').first().getAttribute('href'), '/san-pham/cs21/');

    await page.goto(`${base}/san-pham/cs22/`);
    await page.locator('.pd-web-buy').click();
    assert.match(await page.locator('.pd-error').innerText(), /chọn size và màu/);
    await page.locator('label.pd-chip:has(input[name="size"][value="M"])').click();
    await page.locator('label.pd-chip:has(input[name="color"][value="Đen"])').click();
    await page.locator('#pd-qty').fill('2');
    await Promise.all([page.waitForURL('**/cart/'), page.locator('.pd-web-buy').click()]);
    await page.locator('.cart-line').first().waitFor();
    assert.equal(await page.locator('[data-cart-count]').innerText(), '2');
    assert.equal(await page.locator('.shop-summary__total strong').innerText(), '606.900đ');
    assert.equal(await page.locator('.cart-line--gift').count(), 1);
    assert.equal(await page.title(), 'Giỏ hàng | Comfycare');

    // Thêm CS29 → vẫn 1 quà; giảm CS22 còn 1 → 303.450 + 110.500 = 413.950đ, miễn ship.
    await page.evaluate(() => { const c = JSON.parse(localStorage.getItem('cc-cart')); c.push({ sku: 'CS29', size: 'S', color: 'Da', quantity: 1 }); localStorage.setItem('cc-cart', JSON.stringify(c)); });
    await page.reload();
    await page.locator('.cart-line').first().waitFor();
    await page.getByRole('button', { name: 'Giảm số lượng CS22' }).click();
    await page.waitForFunction(() => document.querySelector('.shop-summary__total strong')?.textContent === '413.950đ');
    assert.equal(await page.locator('.cart-line--gift').count(), 1);
    // Xóa CS22 → còn CS29 110.500 + ship 25.000, hết quà.
    await page.locator('.cart-line', { hasText: 'CS22' }).getByRole('button', { name: 'Xóa' }).click();
    await page.waitForFunction(() => document.querySelector('.shop-summary__total strong')?.textContent === '135.500đ');
    assert.equal(await page.locator('.cart-line--gift').count(), 0);
    assert.match(await page.locator('.shop-summary').innerText(), /Mua thêm 189\.500đ/);
    await noOverflow(page, 'cart');

    await Promise.all([page.waitForURL('**/thanh-toan/'), page.getByRole('link', { name: 'Đặt hàng' }).click()]);
    await page.locator('.shop-form').waitFor();
    await page.locator('.shop-form button[type="submit"]').click();
    await page.locator('#co-phone-error:not([hidden])').waitFor();
    assert.equal(await page.locator('.shop-field__error:not([hidden])').count(), 6);
    await noOverflow(page, 'checkout');
    await page.fill('#co-name', 'Khách Thử Tự Động');
    await page.fill('#co-phone', '0900000003');
    await page.selectOption('#co-province', 'Hải Phòng');
    await page.fill('#co-ward', 'Phường Thử');
    await page.fill('#co-address', '3 Đường Thử');
    await page.fill('#co-note', '<script>alert(1)</script>');
    await page.locator('input[name="accept_terms"]').check();
    await Promise.all([page.waitForURL('**/don-hang/?ma=*'), page.locator('.shop-form button[type="submit"]').click()]);
    await page.locator('.order-status h2').waitFor();
    assert.equal(await page.locator('.order-status h2').innerText(), 'Đã nhận đơn – chờ xác nhận');
    const codCode = new URL(page.url()).searchParams.get('ma');
    assert.match(codCode, /^CC\d{9}[2-9A-HJKMNP-Z]{3}$/);
    assert.equal(await page.locator('[data-cart-count]').isHidden(), true, 'giỏ đã xóa sau khi đặt');
    assert.doesNotMatch(await page.locator('.shop-summary').innerText(), /Mua thêm/);
    results.push(`COD: ${codCode}, tổng 135.500đ, giỏ xóa sau khi đặt`);

    // 3. Chuyển khoản: QR, webhook giả lập → trang tự đổi "Đã nhận thanh toán".
    await page.evaluate(() => localStorage.setItem('cc-cart', JSON.stringify([{ sku: 'CS22', size: 'L', color: 'Da', quantity: 1 }])));
    await page.goto(`${base}/thanh-toan/`);
    await page.locator('.shop-form').waitFor();
    await page.fill('#co-name', 'Khách Thử Chuyển Khoản');
    await page.fill('#co-phone', '0900000004');
    await page.selectOption('#co-province', 'Hà Nội');
    await page.fill('#co-ward', 'Phường Thử');
    await page.fill('#co-address', '4 Đường Thử');
    await page.locator('label.shop-method:has(input[value="bank"])').click();
    await page.locator('input[name="accept_terms"]').check();
    await Promise.all([page.waitForURL('**/don-hang/?ma=*'), page.locator('.shop-form button[type="submit"]').click()]);
    await page.locator('.order-pay').waitFor();
    const bankCode = new URL(page.url()).searchParams.get('ma');
    const qr = new URL(await page.locator('.order-qr').getAttribute('src'));
    assert.equal(qr.searchParams.get('amount'), '303450');
    assert.equal(qr.searchParams.get('des'), bankCode);
    assert.match(await page.locator('.order-countdown').innerText(), /^(29|30):\d\d$/);
    await noOverflow(page, 'order-bank');
    const hook = await fetch(`${apiBase}/api/webhooks/sepay`, {
      method: 'POST', headers: { 'content-type': 'application/json', authorization: `Apikey ${sepayKey}` },
      body: JSON.stringify({ id: `test-${Date.now()}`, gateway: 'MBBank', transactionDate: '', accountNumber: '', code: null, content: `NAP ${bankCode} CHUYEN`, transferType: 'in', description: '', transferAmount: 303450, accumulated: 0, referenceCode: 'TEST' }),
    });
    assert.deepEqual(await hook.json(), { success: true });
    await page.waitForFunction(() => document.querySelector('.order-status h2')?.textContent === 'Đã nhận thanh toán', null, { timeout: 15000 });
    assert.equal(await page.locator('.order-pay').count(), 0);
    results.push(`Chuyển khoản: ${bankCode}, QR 303.450đ, webhook → Đã nhận thanh toán`);

    // Meta Pixel: AddToCart, InitiateCheckout, Purchase (COD khi tạo đơn, chuyển khoản khi đã trả) — ghi qua sự kiện cc:track.
    const tracked = await page.evaluate(() => JSON.parse(sessionStorage.getItem('__tracked') || '[]'));
    assert.deepEqual(tracked, ['AddToCart', 'InitiateCheckout', 'Purchase', 'InitiateCheckout', 'Purchase']);
    assert.ok((await fbEvents(page)).includes('Purchase'), 'lệnh fbq Purchase có trong hàng đợi Pixel');
    results.push(`Pixel: ${tracked.join(' → ')}`);

    // 4. Tra cứu: sai SĐT báo lỗi, đúng thì hiện đơn.
    const lookup = await ctx.newPage(); watch(lookup);
    await lookup.goto(`${base}/don-hang/?shop-preview=${encodeURIComponent(apiBase)}`);
    await lookup.evaluate(() => sessionStorage.removeItem('cc-last-order'));
    await lookup.reload();
    await lookup.locator('.shop-lookup').waitFor();
    await lookup.fill('#co-code', bankCode.toLowerCase());
    await lookup.fill('#co-phone', '0911111111');
    await lookup.locator('.shop-lookup button[type="submit"]').click();
    await lookup.locator('.shop-lookup .shop-alert').waitFor();
    await lookup.fill('#co-code', bankCode);
    await lookup.fill('#co-phone', '0900000004');
    await lookup.locator('.shop-lookup button[type="submit"]').click();
    await lookup.waitForFunction(() => document.querySelector('.order-status h2')?.textContent === 'Đã nhận thanh toán');
    await noOverflow(lookup, 'order-lookup');
    results.push('Tra cứu: sai SĐT báo lỗi, đúng mã + SĐT hiện đơn');

    // CS100 bán lẻ: không có size/màu, thêm thẳng vào giỏ.
    const accessory = await ctx.newPage(); watch(accessory);
    await accessory.goto(`${base}/san-pham/cs100/?shop-preview=${encodeURIComponent(apiBase)}`);
    await Promise.all([accessory.waitForURL('**/cart/'), accessory.locator('.pd-web-buy').click()]);
    await accessory.locator('.cart-line').first().waitFor();
    assert.equal(await accessory.locator('.shop-summary__total strong').innerText(), '45.000đ');
    results.push('CS100 bán lẻ: thêm vào giỏ không cần size/màu, 20.000đ + ship 25.000đ');

    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(out, 'validation.json'), JSON.stringify({ base, apiBase, results, errors }, null, 2));
    console.log(`PASS: ${results.length} nhóm kiểm tra luồng mua trên web`);
    results.forEach((r) => console.log(` - ${r}`));
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
