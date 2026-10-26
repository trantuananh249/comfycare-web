// Bán hàng trên web (kế hoạch 09 bước 4): giỏ hàng, trang thanh toán, trang đơn hàng, nút "Mua ngay".
// Đang BẬT (mở bán 26/10/2026). Đặt SHOP.enabled = false để tạm ngừng: website trở lại "Sắp ra mắt" và các trang
// /cart/, /thanh-toan/, /don-hang/ chỉ hiện thông báo (nhớ chạy scripts/build-shop.py để cập nhật version).
(() => {
  const SHOP = {
    enabled: true,        // mở bán 26/10/2026 (bước 6)
    apiBase: 'https://comfycare-api.mr-tuananh-hp92.workers.dev',
    turnstileSiteKey: '0x4AAAAAAFl-R4cZq2lK3Fqs', // khóa site Cloudflare Turnstile (công khai), chỉ chạy trên comfycare.vn
    zalo: 'https://zalo.me/0848621092',
  };

  // Xem thử trên máy: mở http://127.0.0.1:4183/...?shop-preview=http://127.0.0.1:8787 (chỉ có tác dụng trên localhost).
  const store = (kind) => { try { return window[kind]; } catch { return null; } };
  if (['127.0.0.1', 'localhost'].includes(location.hostname)) {
    try {
      const preview = new URLSearchParams(location.search).get('shop-preview');
      if (preview) store('sessionStorage').setItem('cc-shop-preview', preview);
      const saved = store('sessionStorage')?.getItem('cc-shop-preview');
      // Khóa Turnstile thật không chạy trên localhost; API thử trên máy không kiểm Turnstile khi thiếu TURNSTILE_SECRET.
      if (saved) Object.assign(SHOP, { enabled: true, apiBase: saved, turnstileSiteKey: '' });
    } catch { /* bỏ qua */ }
  }
  // Đặt thử nội bộ (bước 5): mở https://comfycare.vn/?shop-test=<mã> → chỉ tab đó thấy bán hàng; mã gửi kèm mỗi lần gọi API
  // (API ở chế độ ORDERS_ENABLED = "internal" chỉ nhận đơn có đúng mã). ?shop-test=off để tắt.
  let testKey = '';
  try {
    const param = new URLSearchParams(location.search).get('shop-test');
    if (param === 'off') store('sessionStorage')?.removeItem('cc-shop-test');
    else if (param) store('sessionStorage')?.setItem('cc-shop-test', param);
    testKey = store('sessionStorage')?.getItem('cc-shop-test') || '';
  } catch { /* bỏ qua */ }
  if (testKey) SHOP.enabled = true;
  if (!SHOP.enabled || !SHOP.apiBase) return;
  document.documentElement.classList.add('shop-on');

  // ----- Tiện ích -----
  const CART_KEY = 'cc-cart';
  const LAST_ORDER_KEY = 'cc-last-order';
  const MAX_QTY = 20;
  const vnd = (n) => `${Number(n).toLocaleString('vi-VN').replace(/,/g, '.')}đ`;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  function h(tag, attrs = {}, ...children) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === false || v === null || v === undefined) continue;
      if (k === 'class') el.className = v;
      else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? '' : v);
    }
    for (const child of children.flat()) if (child !== null && child !== undefined && child !== false) el.append(child.nodeType ? child : String(child));
    return el;
  }
  // Meta Pixel + sự kiện 'cc:track' trên document (dùng cho kiểm thử, gắn GA4 sau này).
  const track = (event, data) => {
    // Đơn đặt thử nội bộ không gửi sự kiện lên Meta để không làm sai số liệu quảng cáo.
    try { if (window.fbq && !testKey) window.fbq('track', event, data); } catch { /* bỏ qua */ }
    document.dispatchEvent(new CustomEvent('cc:track', { detail: { event, data } }));
  };

  function readCart() {
    try { const cart = JSON.parse(store('localStorage')?.getItem(CART_KEY) || '[]'); return Array.isArray(cart) ? cart : []; } catch { return []; }
  }
  function writeCart(cart) {
    try { store('localStorage')?.setItem(CART_KEY, JSON.stringify(cart)); } catch { /* bỏ qua: giỏ chỉ sống trong trang */ }
    updateCartBadge(cart);
  }
  function addToCart(item) {
    const cart = readCart();
    const same = cart.find((l) => l.sku === item.sku && l.size === item.size && l.color === item.color);
    if (same) same.quantity = Math.min(MAX_QTY, same.quantity + item.quantity);
    else cart.push(item);
    writeCart(cart);
  }
  function updateCartBadge(cart = readCart()) {
    const count = cart.reduce((s, l) => s + l.quantity, 0);
    $$('[data-cart-link], [data-shop-link]').forEach((link) => { link.hidden = false; });
    $$('[data-cart-count]').forEach((badge) => { badge.textContent = String(count); badge.hidden = count === 0; });
  }

  async function api(path, options = {}) {
    const response = await fetch(`${SHOP.apiBase}${path}`, { ...options, headers: { 'content-type': 'application/json', ...(testKey ? { 'x-shop-test': testKey } : {}), ...(options.headers || {}) } });
    const data = await response.json().catch(() => ({ ok: false, error: 'Không đọc được phản hồi' }));
    return { status: response.status, data };
  }

  let catalogPromise;
  const catalog = () => (catalogPromise ||= fetch('/data/products.json').then((r) => r.json()).then((d) => new Map(d.products.map((p) => [p.sku, p]))));

  // Header nằm trong layout.js (chạy defer); đợi DOM xong rồi mới cập nhật.
  const ready = (fn) => (document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', fn) : fn());

  // ----- Nút "Mua ngay" trên thẻ sản phẩm (trang chủ, danh mục): dẫn vào trang chi tiết để chọn size/màu -----
  function enableCardButtons() {
    $$('.btn-web-soon').forEach((button) => {
      const card = button.closest('article');
      const href = card && $('h3 a', card)?.getAttribute('href');
      if (!href) return;
      const link = h('a', { class: button.className.replace('btn-web-soon', 'btn--teal btn-web-buy'), href }, 'Mua ngay');
      button.replaceWith(link);
    });
  }

  // Làm mờ lựa chọn hết hàng (cờ còn hàng trong trang quản trị): đang chọn size M thì màu hết hàng của M mờ đi,
  // đang chọn màu Da thì size hết hàng của Da mờ đi; size/màu hết ở mọi lựa chọn kia thì mờ ngay từ đầu.
  async function applyStock(sku, form, button) {
    let out = [];
    try { out = (await api(`/api/stock/${encodeURIComponent(sku)}`)).data.out || []; } catch { return; }
    if (!out.length) return;
    const isOut = (size, color) => out.some((o) => o.size === size && o.color === color);
    const sizes = [...form.querySelectorAll('input[name="size"]')];
    const colors = [...form.querySelectorAll('input[name="color"]')];
    const values = (inputs) => (inputs.length ? inputs.map((i) => i.value) : ['']);
    const mark = (input, dead) => {
      input.disabled = dead;
      if (dead) input.checked = false;
      input.closest('.pd-chip')?.setAttribute('title', dead ? 'Tạm hết hàng' : '');
    };
    const refresh = () => {
      const size = sizes.find((i) => i.checked)?.value;
      const color = colors.find((i) => i.checked)?.value;
      sizes.forEach((i) => mark(i, (color !== undefined ? [color] : values(colors)).every((c) => isOut(i.value, c))));
      colors.forEach((i) => mark(i, (size !== undefined ? [size] : values(sizes)).every((s) => isOut(s, i.value))));
      if (!sizes.length && !colors.length && isOut('', '')) { button.disabled = true; button.textContent = 'Tạm hết hàng'; }
    };
    form.addEventListener('change', refresh);
    refresh();
  }

  // ----- Trang chi tiết sản phẩm -----
  function enableDetailPage() {
    const button = $('.pd-web-buy');
    if (!button) return;
    const sku = document.body.dataset.sku;
    const form = $('.pd-options');
    button.disabled = false;
    button.classList.add('btn--teal');
    button.textContent = 'Mua ngay';
    const note = $('#pd-web-note');
    if (note) note.textContent = 'Đặt trên web: thanh toán khi nhận hàng (COD) hoặc chuyển khoản qua mã QR. Phí ship 25.000đ, miễn ship cho đơn từ 300.000đ.';
    const error = h('p', { class: 'pd-error', role: 'alert', hidden: true });
    button.closest('.pd-actions').after(error);
    applyStock(sku, form, button);
    button.addEventListener('click', async () => {
      const size = form.querySelector('input[name="size"]:checked')?.value ?? '';
      const color = form.querySelector('input[name="color"]:checked')?.value ?? '';
      const quantity = Math.max(1, Math.min(MAX_QTY, parseInt(form.querySelector('input[name="qty"]').value, 10) || 1));
      const missing = [];
      if (form.querySelector('input[name="size"]') && !size) missing.push('size');
      if (form.querySelector('input[name="color"]') && !color) missing.push('màu');
      if (missing.length) {
        error.textContent = `Vui lòng chọn ${missing.join(' và ')} trước khi mua.`;
        error.hidden = false;
        form.querySelector(`input[name="${missing[0] === 'size' ? 'size' : 'color'}"]`)?.focus();
        return;
      }
      error.hidden = true;
      addToCart({ sku, size, color, quantity });
      const product = (await catalog()).get(sku);
      track('AddToCart', { content_ids: [sku], content_type: 'product', value: (product?.price || 0) * quantity, currency: 'VND' });
      location.href = '/cart/';
    });
  }

  // ----- Hiện phần bán hàng, ẩn thông báo "chưa mở" trên /cart/, /thanh-toan/, /don-hang/ -----
  function switchShopSections() {
    $$('[data-shop-off]').forEach((el) => { el.hidden = true; });
    $$('[data-shop-on]').forEach((el) => { el.hidden = false; });
    if ($('[data-shop-cart]')) document.title = 'Giỏ hàng | Comfycare';
  }

  function lineView(line, product, controls) {
    const image = product?.gallery?.[0]?.thumb || product?.image;
    return h('li', { class: `cart-line${line.is_gift ? ' cart-line--gift' : ''}` },
      h('a', { class: 'cart-line__media', href: product?.url || '#', tabindex: '-1', 'aria-hidden': 'true' },
        image ? h('img', { src: image, alt: '', width: '160', height: '160', loading: 'lazy' }) : null),
      h('div', { class: 'cart-line__body' },
        h('a', { class: 'cart-line__name', href: product?.url || '#' }, line.name),
        h('p', { class: 'cart-line__meta' }, [line.sku, line.size && `Size ${line.size}`, line.color && `Màu ${line.color}`].filter(Boolean).join(' · ')),
        line.is_gift ? h('p', { class: 'cart-line__gift' }, 'Quà tặng kèm đơn') : h('p', { class: 'cart-line__price' }, `${vnd(line.unit_price)} / ${line.unit}`),
        controls || null),
      h('strong', { class: 'cart-line__total' }, line.is_gift ? '0đ' : vnd(line.line_total)));
  }

  function summaryView(quote, { placed = false } = {}) {
    const rows = [
      ['Tạm tính', vnd(quote.subtotal)],
      ['Phí vận chuyển', quote.shipping ? vnd(quote.shipping) : 'Miễn phí'],
    ];
    const missing = 300000 - quote.subtotal;
    return h('div', { class: 'shop-summary' },
      h('dl', {}, rows.map(([k, v]) => h('div', {}, h('dt', {}, k), h('dd', {}, v)))),
      h('div', { class: 'shop-summary__total' }, h('span', {}, 'Tổng thanh toán'), h('strong', {}, vnd(quote.total))),
      missing > 0 && !placed ? h('p', { class: 'shop-muted' }, `Mua thêm ${vnd(missing)} để được miễn phí vận chuyển.`) : null,
      h('p', { class: 'shop-muted' }, 'Giá bán lẻ, đã gồm VAT.'));
  }

  // ----- /cart/ -----
  async function renderCart(root) {
    const cart = readCart();
    root.replaceChildren();
    if (!cart.length) {
      root.append(h('div', { class: 'shop-empty' },
        h('h2', {}, 'Giỏ hàng đang trống'),
        h('p', {}, 'Chọn sản phẩm, size và màu ở trang sản phẩm rồi bấm "Mua ngay".'),
        h('a', { class: 'btn btn--primary', href: '/san-pham/' }, 'Xem sản phẩm')));
      return;
    }
    root.append(h('p', { class: 'shop-loading' }, 'Đang tính tiền…'));
    const [{ status, data }, products] = await Promise.all([api('/api/quote', { method: 'POST', body: JSON.stringify({ items: cart }) }), catalog()]);
    root.replaceChildren();
    if (status !== 200) {
      // Dòng lỗi (hết hàng, size không còn bán…) → cho khách xóa dòng đó.
      const bad = Number.isInteger(data.line) ? cart[data.line] : null;
      root.append(h('div', { class: 'shop-alert', role: 'alert' },
        h('p', {}, data.error || 'Không tính được giỏ hàng.'),
        bad ? h('button', { class: 'btn btn--small btn--secondary', type: 'button', onclick: () => { cart.splice(data.line, 1); writeCart(cart); renderCart(root); } }, `Bỏ ${bad.sku} ${bad.size} ${bad.color} khỏi giỏ`)
          : h('button', { class: 'btn btn--small btn--secondary', type: 'button', onclick: () => { writeCart([]); renderCart(root); } }, 'Xóa giỏ hàng')));
      return;
    }
    const list = h('ul', { class: 'cart-lines' });
    data.lines.forEach((line) => {
      let controls = null;
      if (!line.is_gift) {
        const index = cart.findIndex((l) => l.sku === line.sku && (l.size || '') === line.size && (l.color || '') === line.color);
        const setQty = (q) => {
          if (q < 1) cart.splice(index, 1); else cart[index].quantity = Math.min(MAX_QTY, q);
          writeCart(cart); renderCart(root);
        };
        controls = h('div', { class: 'cart-line__controls' },
          h('div', { class: 'qty-stepper' },
            h('button', { type: 'button', 'aria-label': `Giảm số lượng ${line.sku}`, onclick: () => setQty(line.quantity - 1) }, '−'),
            h('span', { 'aria-live': 'polite' }, String(line.quantity)),
            h('button', { type: 'button', 'aria-label': `Tăng số lượng ${line.sku}`, disabled: line.quantity >= MAX_QTY, onclick: () => setQty(line.quantity + 1) }, '+')),
          h('button', { class: 'cart-line__remove', type: 'button', onclick: () => setQty(0) }, 'Xóa'));
      }
      list.append(lineView(line, products.get(line.sku), controls));
    });
    root.append(h('div', { class: 'shop-layout' },
      h('section', { class: 'shop-panel', 'aria-label': 'Sản phẩm trong giỏ' }, list),
      h('aside', { class: 'shop-panel shop-panel--summary' },
        h('h2', {}, 'Tóm tắt đơn'), summaryView(data),
        h('a', { class: 'btn btn--primary shop-cta', href: '/thanh-toan/' }, 'Đặt hàng'),
        h('a', { class: 'shop-link', href: '/san-pham/' }, 'Tiếp tục xem sản phẩm'))));
  }

  // 34 tỉnh, thành sau sắp xếp đơn vị hành chính 2025 (Nghị quyết 202/2025/QH15).
  const PROVINCES = ['An Giang', 'Bắc Ninh', 'Cà Mau', 'Cao Bằng', 'Cần Thơ', 'Đà Nẵng', 'Đắk Lắk', 'Điện Biên', 'Đồng Nai', 'Đồng Tháp', 'Gia Lai', 'Hà Nội', 'Hà Tĩnh', 'Hải Phòng', 'Hồ Chí Minh', 'Huế', 'Hưng Yên', 'Khánh Hòa', 'Lai Châu', 'Lạng Sơn', 'Lào Cai', 'Lâm Đồng', 'Nghệ An', 'Ninh Bình', 'Phú Thọ', 'Quảng Ngãi', 'Quảng Ninh', 'Quảng Trị', 'Sơn La', 'Tây Ninh', 'Thái Nguyên', 'Thanh Hóa', 'Tuyên Quang', 'Vĩnh Long'];

  function field(name, label, input, hint) {
    input.id = `co-${name}`;
    input.name = name;
    return h('div', { class: 'shop-field', 'data-field': name },
      h('label', { for: input.id }, label),
      input,
      hint ? h('p', { class: 'shop-muted' }, hint) : null,
      h('p', { class: 'shop-field__error', id: `co-${name}-error`, hidden: true }));
  }

  // ----- /thanh-toan/ -----
  async function renderCheckout(root) {
    const cart = readCart();
    if (!cart.length) { location.replace('/cart/'); return; }
    const { status, data: quote } = await api('/api/quote', { method: 'POST', body: JSON.stringify({ items: cart }) });
    if (status !== 200) { location.replace('/cart/'); return; }
    track('InitiateCheckout', { value: quote.total, currency: 'VND', num_items: cart.reduce((s, l) => s + l.quantity, 0) });
    const products = await catalog();

    const province = h('select', { required: true, autocomplete: 'address-level1' }, h('option', { value: '' }, 'Chọn tỉnh/thành'), PROVINCES.map((p) => h('option', { value: p }, p)));
    const methodBox = h('fieldset', { class: 'shop-methods', 'data-field': 'method' },
      h('legend', {}, 'Cách thanh toán'),
      h('label', { class: 'shop-method' }, h('input', { type: 'radio', name: 'method', value: 'cod', checked: true }),
        h('span', {}, h('strong', {}, 'Thanh toán khi nhận hàng (COD)'), h('small', {}, 'Nhân viên gọi hoặc nhắn Zalo xác nhận đơn trước khi giao. Được kiểm tra hàng khi nhận (không gồm dùng thử).'))),
      h('label', { class: 'shop-method' }, h('input', { type: 'radio', name: 'method', value: 'bank' }),
        h('span', {}, h('strong', {}, 'Chuyển khoản qua mã QR'), h('small', {}, 'Quét mã QR có sẵn số tiền và nội dung ở bước sau. Tài khoản nhận tiền giai đoạn đầu là tài khoản cá nhân; tên chủ tài khoản hiển thị đầy đủ ở bước sau. Comfycare không bao giờ hỏi mã OTP.'))),
      h('p', { class: 'shop-field__error', id: 'co-method-error', hidden: true }));
    const consent = h('div', { class: 'shop-field shop-consent', 'data-field': 'accept_terms' },
      h('label', {}, h('input', { type: 'checkbox', name: 'accept_terms', required: true }),
        h('span', {}, 'Tôi đã đọc và đồng ý với ', h('a', { href: '/dieu-khoan-su-dung/', target: '_blank' }, 'điều khoản sử dụng'), ' và ', h('a', { href: '/chinh-sach-bao-mat/', target: '_blank' }, 'chính sách bảo mật'), '; đồng ý để Comfycare dùng thông tin này để xử lý và giao đơn hàng.')),
      h('p', { class: 'shop-field__error', id: 'co-accept_terms-error', hidden: true }));
    const turnstile = SHOP.turnstileSiteKey ? h('div', { class: 'cf-turnstile', 'data-sitekey': SHOP.turnstileSiteKey }) : null;
    const submit = h('button', { class: 'btn btn--primary shop-cta', type: 'submit' }, `Xác nhận đặt hàng · ${vnd(quote.total)}`);
    const formError = h('p', { class: 'shop-alert', role: 'alert', hidden: true });

    const form = h('form', { class: 'shop-panel shop-form', novalidate: true },
      h('h2', {}, 'Thông tin giao hàng'),
      field('name', 'Họ và tên', h('input', { type: 'text', required: true, autocomplete: 'name', maxlength: '80' })),
      field('phone', 'Số điện thoại', h('input', { type: 'tel', required: true, autocomplete: 'tel', inputmode: 'tel', maxlength: '15' }), 'Nhân viên dùng số này để xác nhận đơn và giao hàng.'),
      field('province', 'Tỉnh/thành phố', province),
      field('ward', 'Phường/xã', h('input', { type: 'text', required: true, maxlength: '80', placeholder: 'Theo địa giới hành chính mới (2025)' })),
      field('address', 'Số nhà, tên đường', h('input', { type: 'text', required: true, autocomplete: 'street-address', maxlength: '200' })),
      field('note', 'Ghi chú (không bắt buộc)', h('textarea', { rows: '3', maxlength: '500', placeholder: 'Ví dụ: giờ nhận hàng, cần tư vấn thêm size…' })),
      methodBox, consent, turnstile, formError, submit);

    const summary = h('aside', { class: 'shop-panel shop-panel--summary' },
      h('h2', {}, 'Đơn hàng của anh/chị'),
      h('ul', { class: 'cart-lines cart-lines--compact' }, quote.lines.map((l) => lineView(l, products.get(l.sku)))),
      summaryView(quote),
      h('a', { class: 'shop-link', href: '/cart/' }, 'Sửa giỏ hàng'));
    root.replaceChildren(h('div', { class: 'shop-layout' }, form, summary));

    if (turnstile) document.head.append(h('script', { src: 'https://challenges.cloudflare.com/turnstile/v0/api.js', async: true, defer: true }));

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      $$('.shop-field__error', form).forEach((e) => { e.hidden = true; });
      $$('[aria-invalid]', form).forEach((e) => e.removeAttribute('aria-invalid'));
      formError.hidden = true;
      const values = Object.fromEntries(new FormData(form));
      const body = {
        name: values.name, phone: values.phone, province: values.province, ward: values.ward, address: values.address,
        note: values.note || '', method: values.method, accept_terms: form.elements.accept_terms.checked,
        items: cart, turnstile_token: values['cf-turnstile-response'] || '',
        source: (() => { try { return new URLSearchParams(store('sessionStorage')?.getItem('cc-utm') || '').toString(); } catch { return ''; } })(),
      };
      submit.disabled = true;
      submit.textContent = 'Đang gửi đơn…';
      const { status: code, data } = await api('/api/orders', { method: 'POST', body: JSON.stringify(body) }).catch(() => ({ status: 0, data: {} }));
      if (code === 201) {
        try { store('sessionStorage')?.setItem(LAST_ORDER_KEY, JSON.stringify({ code: data.order.code, phone: body.phone })); } catch { /* bỏ qua */ }
        writeCart([]);
        location.href = `/don-hang/?ma=${encodeURIComponent(data.order.code)}`;
        return;
      }
      submit.disabled = false;
      submit.textContent = `Xác nhận đặt hàng · ${vnd(quote.total)}`;
      const fields = data.fields || {};
      Object.entries(fields).forEach(([name, message]) => {
        const err = $(`#co-${name}-error`, form);
        if (err) { err.textContent = message; err.hidden = false; }
        form.elements[name]?.setAttribute?.('aria-invalid', 'true');
      });
      formError.textContent = code === 0 ? 'Không kết nối được máy chủ. Vui lòng thử lại hoặc nhắn Zalo để đặt hàng.' : (data.error || 'Không gửi được đơn, vui lòng thử lại.');
      formError.hidden = false;
      (form.querySelector('[aria-invalid]') || formError).scrollIntoView({ block: 'center', behavior: 'smooth' });
      if (window.turnstile) window.turnstile.reset();
    });
  }

  // ----- /don-hang/ -----
  const STATUS = {
    cho_thanh_toan: ['Chờ chuyển khoản', 'Quét mã QR bên dưới để thanh toán. Trang tự cập nhật khi nhận được tiền.'],
    cho_xac_nhan: ['Đã nhận đơn – chờ xác nhận', 'Cảm ơn anh/chị đã đặt hàng. Nhân viên Comfycare sẽ gọi hoặc nhắn Zalo để xác nhận đơn trong giờ làm việc.'],
    da_thanh_toan: ['Đã nhận thanh toán', 'Cảm ơn anh/chị. Comfycare đã nhận tiền và sẽ kiểm tra hàng, xác nhận rồi giao trong ngày hoặc hôm sau.'],
    da_xac_nhan: ['Đã xác nhận', 'Đơn đã được xác nhận và đang chuẩn bị giao.'],
    dang_giao: ['Đang giao', 'Đơn đang trên đường giao tới anh/chị.'],
    da_giao: ['Đã giao', 'Đơn đã giao thành công. Cảm ơn anh/chị đã tin dùng Comfycare.'],
    het_han: ['Hết hạn thanh toán', 'Mã QR đã hết hạn 30 phút. Nếu anh/chị đã chuyển khoản, vui lòng nhắn Zalo kèm mã đơn để được xử lý.'],
    can_xu_ly: ['Đang được kiểm tra', 'Comfycare đang kiểm tra đơn/thanh toán và sẽ liên hệ anh/chị trong ngày.'],
    da_huy: ['Đã hủy', 'Đơn đã hủy. Nếu cần hỗ trợ, vui lòng nhắn Zalo kèm mã đơn.'],
    hoan_tien: ['Hoàn tiền', 'Đơn đang/đã được hoàn tiền bằng chuyển khoản.'],
  };
  const copyButton = (value, label) => h('button', { class: 'copy-btn', type: 'button', onclick: async (e) => {
    try { await navigator.clipboard.writeText(value); e.currentTarget.textContent = 'Đã chép'; } catch { e.currentTarget.textContent = 'Chép thủ công'; }
  }, 'aria-label': `Sao chép ${label}` }, 'Sao chép');

  function lookupForm(root, message) {
    const form = h('form', { class: 'shop-panel shop-form shop-lookup' },
      h('h2', {}, 'Tra cứu đơn hàng'),
      message ? h('p', { class: 'shop-alert', role: 'alert' }, message) : null,
      field('code', 'Mã đơn hàng', h('input', { type: 'text', required: true, maxlength: '20', autocapitalize: 'characters', placeholder: 'CC…' })),
      field('phone', 'Số điện thoại đặt hàng', h('input', { type: 'tel', required: true, inputmode: 'tel', maxlength: '15' })),
      h('button', { class: 'btn btn--primary', type: 'submit' }, 'Tra cứu'));
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const code = form.elements.code.value.trim().toUpperCase();
      try { store('sessionStorage')?.setItem(LAST_ORDER_KEY, JSON.stringify({ code, phone: form.elements.phone.value })); } catch { /* bỏ qua */ }
      history.replaceState(null, '', `/don-hang/?ma=${encodeURIComponent(code)}`);
      renderOrder(root);
    });
    return form;
  }

  let pollTimer;
  let countdownTimer;
  async function renderOrder(root) {
    clearTimeout(pollTimer);
    clearInterval(countdownTimer);
    const code = (new URLSearchParams(location.search).get('ma') || '').toUpperCase();
    let saved = null;
    try { saved = JSON.parse(store('sessionStorage')?.getItem(LAST_ORDER_KEY) || 'null'); } catch { /* bỏ qua */ }
    if (!code || !saved || saved.code !== code) { root.replaceChildren(lookupForm(root)); return; }
    const { status, data } = await api(`/api/orders/${encodeURIComponent(code)}?phone=${encodeURIComponent(saved.phone)}`, { method: 'GET' });
    if (status !== 200) { root.replaceChildren(lookupForm(root, data.error || 'Không tìm thấy đơn hàng.')); return; }
    const order = data.order;
    const products = await catalog();
    const [title, text] = STATUS[order.status] || [order.status, ''];

    // Purchase: đơn COD vừa tạo, hoặc đơn chuyển khoản đã nhận tiền (kế hoạch 09 mục 8). Mỗi đơn 1 lần.
    const purchased = order.method === 'cod' ? order.status === 'cho_xac_nhan' : ['da_thanh_toan', 'da_xac_nhan', 'dang_giao', 'da_giao'].includes(order.status);
    try {
      if (purchased && !store('localStorage')?.getItem(`cc-purchase-${order.code}`)) {
        track('Purchase', { value: order.total, currency: 'VND', content_ids: order.items.filter((i) => !i.is_gift).map((i) => i.sku), content_type: 'product' });
        store('localStorage')?.setItem(`cc-purchase-${order.code}`, '1');
      }
    } catch { /* bỏ qua */ }

    const head = h('section', { class: `shop-panel order-status order-status--${order.status}` },
      h('p', { class: 'eyebrow' }, 'Mã đơn hàng'),
      h('p', { class: 'order-code' }, h('strong', {}, order.code), copyButton(order.code, 'mã đơn')),
      h('h2', {}, title),
      h('p', {}, text),
      order.tracking_code ? h('p', {}, 'Mã vận đơn: ', h('strong', {}, order.tracking_code)) : null);

    let pay = null;
    if (order.payment) {
      const p = order.payment;
      const left = h('strong', { class: 'order-countdown' });
      const tick = () => {
        const ms = new Date(p.expires_at) - Date.now();
        if (ms <= 0) { left.textContent = '00:00'; clearInterval(countdownTimer); return; }
        left.textContent = `${String(Math.floor(ms / 60000)).padStart(2, '0')}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}`;
      };
      tick();
      countdownTimer = setInterval(tick, 1000);
      const row = (label, value, copy) => h('div', {}, h('dt', {}, label), h('dd', {}, h('span', {}, value), copy ? copyButton(copy, label) : null));
      pay = h('section', { class: 'shop-panel order-pay' },
        h('h2', {}, 'Chuyển khoản'),
        p.qr_url ? h('img', { class: 'order-qr', src: p.qr_url, alt: `Mã QR chuyển ${vnd(p.amount)} cho đơn ${order.code}`, width: '360', height: '360' }) : null,
        h('p', { class: 'order-timer' }, 'Mã QR còn hiệu lực: ', left),
        h('dl', { class: 'order-bank' },
          row('Ngân hàng', p.bank),
          row('Số tài khoản', p.account, p.account),
          row('Chủ tài khoản', p.holder),
          row('Số tiền', vnd(p.amount), String(p.amount)),
          row('Nội dung', p.content, p.content)),
        h('p', { class: 'shop-alert' }, 'Chỉ chuyển vào đúng tài khoản hiển thị tại đây, giữ nguyên nội dung là mã đơn. Comfycare không bao giờ hỏi mã OTP. Tài khoản nhận tiền giai đoạn đầu là tài khoản cá nhân.'));
      // Hỏi trạng thái mỗi 4 giây; chỉ vẽ lại khi trạng thái đổi (giữ nguyên đồng hồ, nút sao chép).
      const poll = async () => {
        const fresh = await api(`/api/orders/${encodeURIComponent(code)}?phone=${encodeURIComponent(saved.phone)}`, { method: 'GET' }).catch(() => null);
        if (fresh?.status === 200 && fresh.data.order.status !== order.status) renderOrder(root);
        else pollTimer = setTimeout(poll, 4000);
      };
      pollTimer = setTimeout(poll, 4000);
    }

    const items = h('section', { class: 'shop-panel shop-panel--summary' },
      h('h2', {}, 'Sản phẩm'),
      h('ul', { class: 'cart-lines cart-lines--compact' }, order.items.map((l) => lineView(l, products.get(l.sku)))),
      summaryView(order, { placed: true }),
      h('p', { class: 'shop-muted' }, order.method === 'cod' ? 'Thanh toán khi nhận hàng (COD).' : 'Thanh toán chuyển khoản.'),
      h('a', { class: 'btn btn--secondary', href: SHOP.zalo, target: '_blank', rel: 'noopener noreferrer' }, 'Cần hỗ trợ? Nhắn Zalo'));

    root.replaceChildren(h('div', { class: 'shop-layout' }, h('div', { class: 'shop-stack' }, head, pay), items));
  }

  // Lưu UTM của lượt truy cập đầu (nguồn đơn).
  try {
    const params = new URLSearchParams(location.search);
    const utm = [...params].filter(([k]) => k.startsWith('utm_'));
    if (utm.length && !store('sessionStorage')?.getItem('cc-utm')) store('sessionStorage')?.setItem('cc-utm', new URLSearchParams(utm).toString());
  } catch { /* bỏ qua */ }

  ready(() => {
    updateCartBadge();
    enableCardButtons();
    enableDetailPage();
    const views = [['[data-shop-cart]', renderCart], ['[data-shop-checkout]', renderCheckout], ['[data-shop-order]', renderOrder]];
    for (const [selector, render] of views) {
      const root = $(selector);
      if (root) { switchShopSections(); render(root); }
    }
  });
  // layout.js dựng header sau DOMContentLoaded của script defer trước → cập nhật lại huy hiệu giỏ khi tải xong.
  window.addEventListener('load', () => updateCartBadge());
})();
