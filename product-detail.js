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
