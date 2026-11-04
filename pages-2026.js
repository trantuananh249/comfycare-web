// Giao diện 2026: lọc sản phẩm theo kiểu tất (trang danh mục), tìm câu hỏi (trang Câu hỏi thường gặp).
(() => {
  const filter = document.querySelector('[data-catalog-filter]');
  if (filter) {
    const cards = [...document.querySelectorAll('.category-product-card[data-length]')];
    const buttons = [...filter.querySelectorAll('[data-filter]')];
    const apply = () => {
      const on = {};
      buttons.filter((b) => b.getAttribute('aria-pressed') === 'true').forEach((b) => { on[b.dataset.filter] = b.dataset.value; });
      cards.forEach((card) => { card.hidden = Object.entries(on).some(([key, value]) => card.dataset[key] !== value); });
    };
    buttons.forEach((button) => button.addEventListener('click', () => {
      const pressed = button.getAttribute('aria-pressed') === 'true';
      buttons.filter((b) => b.dataset.filter === button.dataset.filter).forEach((b) => b.setAttribute('aria-pressed', 'false'));
      button.setAttribute('aria-pressed', String(!pressed));
      apply();
    }));
  }

  const search = document.querySelector('[data-faq-search]');
  if (search) {
    const items = [...document.querySelectorAll('.faq-list details')];
    const sections = [...document.querySelectorAll('.faq-section')];
    const empty = document.querySelector('[data-faq-empty]');
    const norm = (text) => text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
    search.addEventListener('input', () => {
      const q = norm(search.value.trim());
      items.forEach((item) => { item.hidden = Boolean(q) && !norm(item.textContent).includes(q); });
      sections.forEach((section) => { section.hidden = !section.querySelector('details:not([hidden])'); });
      if (empty) empty.hidden = items.some((item) => !item.hidden);
    });
  }
})();

// Link có #neo trỏ vào mục nằm trong khối thu gọn (vd. #cs25-size): mở các khối cha rồi cuộn tới.
(() => {
  const open = () => {
    const target = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!target) return;
    for (let el = target; el; el = el.parentElement) if (el.tagName === 'DETAILS') el.open = true;
    target.scrollIntoView({ block: 'start' });
  };
  window.addEventListener('hashchange', open);
  open();
})();

// Dải "Ống chân · Đùi · Quần" trên trang danh mục: bấm hình thì lọc theo kiểu dài tương ứng.
document.querySelectorAll('[data-length-pick]').forEach((pick) => pick.addEventListener('click', () => {
  const button = document.querySelector(`[data-filter="length"][data-value="${pick.dataset.lengthPick}"]`);
  if (!button) return;
  if (button.getAttribute('aria-pressed') !== 'true') button.click();
  document.querySelector('[data-catalog-filter]')?.scrollIntoView({ block: 'center' });
}));
