// Runtime source. Rebuild chatbot.js after editing this file or sales_script.md.
(() => {
  'use strict';
  if (document.getElementById('comfy-chat')) return;
  const content = /* SALES_SCRIPT_DATA */;
  const base = document.body.dataset.basePath || '/';
  const links = {
    zalo: ['Nhắn tư vấn viên qua Zalo', 'https://zalo.me/0848621092'],
    shop: ['Mở gian hàng Shopee', 'https://shopee.vn/comfycare_official_store'],
    size: ['Xem hướng dẫn chọn size', `${base}huong-dan-chon-size/`],
    products: ['Xem các mẫu sản phẩm', `${base}san-pham/`],
    facebook: ['Đặt qua Fanpage', 'https://facebook.com/Comfycare249']
  };
  const root = document.createElement('aside');
  root.id = 'comfy-chat';
  root.setAttribute('aria-label', 'Tư vấn Comfycare');
  root.innerHTML = `
    <section class="cc-panel" id="cc-panel" role="dialog" aria-labelledby="cc-title" hidden>
      <header class="cc-header">
        <span class="cc-avatar" aria-hidden="true">C</span>
        <div><h2 id="cc-title">Comfycare</h2><p>Trợ lý tư vấn tự động</p></div>
        <button type="button" class="cc-close" aria-label="Đóng cửa sổ chat">×</button>
      </header>
      <div class="cc-history" role="log" aria-label="Cuộc trò chuyện" aria-live="polite" aria-relevant="additions" tabindex="0"></div>
      <details class="cc-topics"><summary>Câu hỏi thường gặp · 10 chủ đề</summary><div class="cc-topic-list"></div></details>
      <form class="cc-form">
        <label class="cc-sr" for="cc-input">Câu hỏi của anh/chị</label>
        <input id="cc-input" name="message" type="text" maxlength="600" autocomplete="off" placeholder="Anh/chị muốn hỏi gì?" enterkeyhint="send" />
        <button type="submit" aria-label="Gửi tin nhắn">Gửi</button>
      </form>
      <p class="cc-note">Cần tư vấn riêng? <a href="https://zalo.me/0848621092" target="_blank" rel="noopener noreferrer">Nhắn Zalo</a> · 08:00–22:00</p>
    </section>
    <button type="button" class="cc-launcher" aria-controls="cc-panel" aria-expanded="false" aria-label="Mở chat tư vấn Comfycare">
      <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M20 11.5a8 8 0 0 1-8 8H5l-3 2v-10a9 9 0 0 1 18 0Z"/><path d="M7 11h.01M12 11h.01M17 11h.01" stroke-width="3" stroke-linecap="round"/></svg>
      <span>Tư vấn</span>
    </button>`;
  document.body.append(root);
  const panel = root.querySelector('.cc-panel');
  const launcher = root.querySelector('.cc-launcher');
  const history = root.querySelector('.cc-history');
  const input = root.querySelector('input');
  const topics = root.querySelector('.cc-topics');
  let started = false;
  let lastTopic = null;
  let sku = '';
  let channel = '';
  const normalize = text => text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/[^a-z0-9]+/g, ' ').trim();
  const has = (text, phrases) => phrases.some(phrase => (` ${text} `).includes(` ${phrase} `));
  const message = (text, author = 'bot', actions = []) => {
    const row = document.createElement('div');
    row.className = `cc-message cc-message--${author}`;
    const label = document.createElement('span');
    label.className = 'cc-message-label';
    label.textContent = author === 'bot' ? 'Comfycare' : 'Anh/chị';
    const body = document.createElement('p');
    body.textContent = text;
    row.append(label, body);
    if (actions.length) {
      const group = document.createElement('div');
      group.className = 'cc-actions';
      actions.forEach(key => {
        const a = document.createElement('a');
        [a.textContent, a.href] = links[key];
        if (/^https:/.test(links[key][1])) { a.target = '_blank'; a.rel = 'noopener noreferrer'; }
        group.append(a);
      });
      row.append(group);
    }
    history.append(row);
    // Keep the DOM bounded; messages stay only in memory for this page visit.
    while (history.children.length > 100) history.firstElementChild.remove();
    history.scrollTop = history.scrollHeight;
  };
  const fallback = () => message('Phần này em cần kiểm tra thêm cho đúng. Anh/chị nhắn tư vấn viên qua Zalo giúp em nhé, hoặc gọi 0848 621 092.', 'bot', ['zalo']);
  function answerFAQ(id, text = '') {
    lastTopic = id;
    const answers = content.faqs[id - 1].answers;
    if (id === 2) {
      if (sku && !/^CS(21|22|23|24|26|27|33|34|35)$/.test(sku)) {
        message(`Mẫu ${sku} cần đối chiếu bảng size riêng. Anh/chị xem hướng dẫn theo đúng mã, hoặc gửi số đo qua Zalo để bên em kiểm tra nhé.`, 'bot', ['size', 'zalo']);
      } else message(answers[0], 'bot', ['size', 'zalo']);
    } else if (id === 3) {
      if (sku === 'CS21') message(answers[channel === 'fanpage' ? 2 : 1], 'bot', ['shop']);
      else if (sku) message(`Với mẫu ${sku}, giá bán lẻ hiện ngay trên trang này; anh/chị bấm "Mua ngay" để đặt trên website (ship 25.000đ, miễn ship từ 300.000đ), hoặc xem trên gian hàng chính thức. Nếu muốn đặt qua Fanpage, bên em sẽ kiểm tra giá và phí ship theo số lượng trước khi anh/chị quyết định.`, 'bot', ['shop', 'facebook']);
      else message(answers[0]);
    } else if (id === 5) {
      message(answers[0], 'bot', ['zalo']);
      if (sku && !/^CS(21|22|23|24|26|27|33|34|35)$/.test(sku)) message(`Em chưa có cơ sở áp dụng công bố trên cho ${sku}. Anh/chị nhắn tư vấn viên để kiểm tra đúng mã và lô hàng nhé.`, 'bot', ['zalo']);
    } else if (id === 9) message(answers.join('\n\n'), 'bot', ['zalo']);
    else if (id === 10) {
      message(answers[0] + (channel ? '\n\n' + answers[channel === 'fanpage' ? 2 : 1] : ''));
    } else if (id === 7) {
      message(answers[has(text, ['may gio', 'bao nhieu gio', '12 gio', 'di ngu', 'ban dem']) ? 1 : 0], 'bot', ['zalo']);
    } else if (id === 1) {
      message(answers[has(text, ['ap luc', 'cap 1', 'cap 2', 'mmhg']) ? 1 : 0], 'bot', ['products']);
    } else message(answers[0], 'bot', id === 8 ? ['size', 'zalo'] : []);
  }
  function respond(raw) {
    const text = normalize(raw);
    const code = text.match(/\bcs\s*(\d{2,3})\b/);
    if (code) sku = `CS${code[1]}`;
    if (has(text, ['shopee', 'tiktok', 'san'])) channel = 'marketplace';
    else if (has(text, ['fanpage', 'facebook', 'fb'])) channel = 'fanpage';
    // Symptoms and medical circumstances take priority over commercial intents.
    if (has(text, ['te chan', 'te ngon', 'doi mau', 'tim tai', 'lanh chan', 'dau bat thuong'])) return answerFAQ(7, text);
    if (has(text, ['mang thai', 'bau', 'tieu duong', 'phau thuat', 'benh nen', 'vet thuong', 'sau sinh'])) return answerFAQ(8, text);
    if (has(text, ['chua mua', 'chua san sang', 'can nhac', 'suy nghi them', 'de sau', 'form', 'chua quyet'])) { lastTopic = null; return message(content.later, 'bot', ['zalo']); }
    if (has(text, ['doi tra', 'doi size', 'khong vua', 'rong', 'chat qua', 'hoan tien', 'bao hanh', 'khong hai long', 'bi rach'])) return answerFAQ(9, text);
    if (has(text, ['re hon', 'dat qua', 'gia cao', 'ben khac', 'mac qua'])) return answerFAQ(4, text);
    if (has(text, ['xuat xu', 'san xuat', 'giay to', 'chung nhan', 'fda', 'iso', 'byt', 'trung quoc'])) return answerFAQ(5, text);
    if (has(text, ['khoi', 'hieu qua', 'bao lau thi do', 'tac dung', 'chua benh'])) return answerFAQ(6, text);
    if (has(text, ['ship', 'giao hang', 'giao bao lau', 'van chuyen', 'kiem tra hang', 'dong kiem', 'cod', 'thanh toan', 'phi giao', 'may ngay nhan'])) return answerFAQ(10, text);
    if (has(text, ['gia', 'bao nhieu tien', 'bao nhieu', 'mot doi', '1 doi', 'combo', 'khuyen mai', 'voucher']) && !has(text, ['bao nhieu gio', 'bao nhieu ngay'])) return answerFAQ(3, text);
    if (has(text, ['size', 'kich co', 'so do', 'chu vi', 'mat ca', 'bap chan', 'cm', 'kg', 'can nang', 'chieu cao'])) return answerFAQ(2, text);
    if (has(text, ['kho mang', 'cach mang', 'bo qua', 'may gio', 'bao nhieu gio', 'di ngu', 'ban dem'])) return answerFAQ(7, text);
    if (has(text, ['chon loai', 'loai nao', 'ap luc', 'cap 1', 'cap 2', 'the thao', 'dung lau', 'ngoi lau'])) return answerFAQ(1, text);
    if (has(text, ['dat hang', 'dat mua', 'chot don', 'mua ngay', 'muon mua', 'lay mot', 'lay 1', 'lay hai', 'lay 2'])) {
      lastTopic = null;
      return message(channel === 'fanpage'
        ? 'Anh/chị nhắn Fanpage mẫu muốn mua, size và số lượng nhé. Bên em sẽ kiểm tra rồi báo tổng tiền trước khi anh/chị quyết định.'
        : 'Anh/chị có thể đặt trên gian hàng chính thức nhé. Chọn đúng mẫu, size, màu và số lượng, rồi kiểm tra tổng tiền sau voucher. Nếu chưa chắc size, em hướng dẫn đo trước; khi nhận mà chưa vừa ý hoặc cần hướng dẫn cách mang, cứ nhắn Comfycare.', 'bot', channel === 'fanpage' ? ['facebook', 'size'] : ['shop', 'size']);
    }
    if (has(text, ['tu van vien', 'nguoi that', 'hotline', 'zalo', 'lien he'])) { lastTopic = null; return fallback(); }
    if (/^(chao|xin chao|hello|hi|alo)( ban| shop)?$/.test(text)) return message(content.greeting);
    if (has(text, ['cam on', 'thank'])) { lastTopic = null; return message('Không có gì nhé. Khi cần kiểm tra size hoặc cách mang, anh/chị cứ nhắn Comfycare.'); }
    if (has(text, ['cho minh', 'nguoi than', 'cho me', 'cho bo', 'cho ba', 'cho ong'])) return message(content.discovery);
    if ((code || has(text, ['fanpage', 'facebook', 'fb', 'shopee', 'tiktok', 'san'])) && [3, 10].includes(lastTopic)) return answerFAQ(lastTopic, text);
    if (code) return message(`Anh/chị đang xem mẫu ${sku}. Anh/chị muốn hỏi về size, giá hay cách mang?`);
    fallback();
  }
  content.faqs.forEach(faq => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = faq.question;
    button.addEventListener('click', () => {
      message(faq.question, 'user');
      topics.open = false;
      answerFAQ(faq.id);
      input.focus({ preventScroll: true });
    });
    root.querySelector('.cc-topic-list').append(button);
  });
  function toggle(open) {
    panel.hidden = !open;
    launcher.setAttribute('aria-expanded', String(open));
    launcher.setAttribute('aria-label', open ? 'Thu gọn chat tư vấn Comfycare' : 'Mở chat tư vấn Comfycare');
    if (open) {
      if (!started) { message(content.greeting); started = true; topics.open = true; }
      // Focus the close button on touch screens to avoid opening the keyboard immediately.
      (window.matchMedia('(pointer: coarse)').matches ? root.querySelector('.cc-close') : input).focus({ preventScroll: true });
      history.scrollTop = history.scrollHeight;
    } else launcher.focus({ preventScroll: true });
  }
  launcher.addEventListener('click', () => toggle(panel.hidden));
  root.querySelector('.cc-close').addEventListener('click', () => toggle(false));
  root.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !panel.hidden) { event.preventDefault(); event.stopPropagation(); toggle(false); }
  });
  root.querySelector('form').addEventListener('submit', event => {
    event.preventDefault();
    const value = input.value.trim();
    if (!value) return;
    input.value = '';
    topics.open = false;
    message(value.slice(0, 600), 'user');
    respond(value.slice(0, 600));
  });
  // Keep the panel above the mobile keyboard and the existing sticky CTA.
  function updateViewport() {
    const viewport = window.visualViewport;
    const keyboard = viewport ? Math.max(0, window.innerHeight - viewport.height - viewport.offsetTop) : 0;
    const sticky = document.querySelector('.mobile-sticky-cta');
    const stickyHeight = sticky && getComputedStyle(sticky).display !== 'none' ? sticky.getBoundingClientRect().height : 0;
    const available = (viewport ? viewport.height : window.innerHeight) - (keyboard ? 0 : stickyHeight) - 90;
    root.classList.toggle('cc-compact', available < 450);
    root.style.setProperty('--cc-bottom', `${Math.max(keyboard, stickyHeight) + 12}px`);
    root.style.setProperty('--cc-height', `${Math.max(180, available)}px`);
  }
  window.addEventListener('resize', updateViewport);
  window.visualViewport?.addEventListener('resize', updateViewport);
  window.visualViewport?.addEventListener('scroll', updateViewport);
  updateViewport();
})();
