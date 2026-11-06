// Trang chi tiết sản phẩm /san-pham/<mã>/: gallery ảnh (thumbnail, nút trước/sau, vuốt trên điện thoại).
(() => {
  const gallery = document.querySelector('[data-gallery]');
  if (!gallery) return;
  const main = gallery.querySelector('[data-gallery-main]');
  const thumbs = [...gallery.querySelectorAll('.pd-thumb')];
  const count = gallery.querySelector('[data-gallery-count]');
  const name = gallery.dataset.name;
  if (!main || thumbs.length < 2) return;
  let current = 0;

  const show = (index) => {
    current = (index + thumbs.length) % thumbs.length;
    const thumb = thumbs[current];
    main.srcset = `${thumb.dataset.medium} 640w, ${thumb.dataset.src} ${thumb.dataset.width}w`;
    main.src = thumb.dataset.src;
    main.alt = `${name} – ảnh ${current + 1}/${thumbs.length}`;
    thumbs.forEach((item, i) => item.toggleAttribute('aria-current', i === current));
    thumb.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' });
    if (count) count.textContent = `${current + 1}/${thumbs.length}`;
  };

  thumbs.forEach((thumb, i) => thumb.addEventListener('click', () => show(i)));
  gallery.querySelector('[data-gallery-prev]')?.addEventListener('click', () => show(current - 1));
  gallery.querySelector('[data-gallery-next]')?.addEventListener('click', () => show(current + 1));
  gallery.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') show(current - 1);
    if (event.key === 'ArrowRight') show(current + 1);
  });

  let startX = null;
  main.addEventListener('touchstart', (event) => { startX = event.touches[0].clientX; }, { passive: true });
  main.addEventListener('touchend', (event) => {
    if (startX === null) return;
    const delta = event.changedTouches[0].clientX - startX;
    if (Math.abs(delta) > 40) show(current + (delta < 0 ? 1 : -1));
    startX = null;
  }, { passive: true });
})();

// Tab nội dung chi tiết (Thông tin, Bảng size, Cách dùng…): một tab hiện một lúc; link #pd-... mở đúng tab.
(() => {
  const root = document.querySelector('[data-tabs]');
  if (!root) return;
  const tabs = [...root.querySelectorAll('[role="tab"]')];
  const panels = tabs.map((tab) => document.getElementById(tab.getAttribute('aria-controls')));

  const select = (index, focus) => {
    tabs.forEach((tab, i) => {
      const on = i === index;
      tab.setAttribute('aria-selected', String(on));
      tab.tabIndex = on ? 0 : -1;
      panels[i].classList.toggle('is-active', on);
    });
    if (focus) tabs[index].focus();
    tabs[index].scrollIntoView({ block: 'nearest', inline: 'nearest' });
  };

  // Thanh tab trên điện thoại cuộn ngang: mờ dần mép phải làm gợi ý vuốt, hết khi đã cuộn tới cuối.
  const bar = tabs[0] && tabs[0].parentElement;
  const markEnd = () => bar.classList.toggle('is-end', bar.scrollLeft + bar.clientWidth >= bar.scrollWidth - 4);
  if (bar) {
    bar.addEventListener('scroll', markEnd, { passive: true });
    window.addEventListener('resize', markEnd);
    markEnd();
  }

  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => select(i));
    tab.addEventListener('keydown', (event) => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
      if (step) select((i + step + tabs.length) % tabs.length, true);
    });
  });

  const openHash = (hash) => {
    const target = hash && document.getElementById(hash.slice(1));
    const index = target ? panels.findIndex((panel) => panel.contains(target)) : -1;
    if (index < 0) return false;
    select(index);
    root.scrollIntoView({ block: 'start' });
    return true;
  };
  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[href^="#pd-"]');
    if (link && openHash(link.getAttribute('href'))) {
      event.preventDefault();
      history.replaceState(null, '', link.getAttribute('href'));
    }
  });
  openHash(location.hash);
})();

// Nút − / + cạnh ô số lượng (layout 04/11).
document.querySelectorAll('[data-qty]').forEach((button) => button.addEventListener('click', () => {
  const input = button.parentElement.querySelector('input');
  const next = (parseInt(input.value, 10) || 1) + Number(button.dataset.qty);
  input.value = String(Math.max(Number(input.min) || 1, Math.min(Number(input.max) || 20, next)));
}));
