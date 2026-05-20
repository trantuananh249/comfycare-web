(() => {
  const basePath = document.body.dataset.basePath || '/';
  const currentPath = document.body.dataset.currentPath || '';
  const route = (path = '') => `${basePath}${path}`;
  const homeRoute = () => route('');
  const pageRoute = (path = '') => (path ? route(`${path}/`) : homeRoute());
  const isCurrent = (path) => currentPath === path;
  const isContactPage = currentPath === 'lien-he';
  const link = (path, label) => `<a href="${pageRoute(path)}"${isCurrent(path) ? ' aria-current="page"' : ''}>${label}</a>`;

  const headerMount = document.querySelector('[data-site-header]');
  const footerMount = document.querySelector('[data-site-footer]');

  if (headerMount) {
    headerMount.outerHTML = `
      <div class="top-bar">
        <div class="container top-bar__inner">
          <span class="top-bar__item">
            <svg class="top-bar__icon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 7h12a4 4 0 0 1 4 4v1" />
              <path d="m16 3 4 4-4 4" />
              <path d="M20 17H8a4 4 0 0 1-4-4v-1" />
              <path d="m8 21-4-4 4-4" />
            </svg>
            <span class="top-bar__desktop-text">${isContactPage ? 'Danh bạ liên hệ chính thức Comfycare' : 'Đổi size miễn phí 15 ngày từ khi nhận hàng'}</span>
            <span class="top-bar__mobile-text">${isContactPage ? 'Danh bạ liên hệ' : 'Đổi size 15 ngày'}</span>
          </span>
          <a class="top-bar__item" href="tel:0848621092">
            <svg class="top-bar__icon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M6.6 4.2 9 3.2l3 5-1.8 1.6a12.1 12.1 0 0 0 4 4l1.6-1.8 5 3-1 2.4c-.4.9-1.3 1.5-2.3 1.4C9.8 18.2 5.8 14.2 5.2 6.5c-.1-1 .5-1.9 1.4-2.3Z" />
            </svg>
            <span>Hotline/Zalo: 0848 621 092</span>
          </a>
        </div>
      </div>

      <header class="site-header">
        <div class="container header__inner">
          <a class="brand" href="${homeRoute()}" aria-label="Comfycare trang chủ">
            <img src="${route('assets/logo/comfycare-logo.png')}" alt="Comfycare" />
            <span>COMFYCARE</span>
          </a>
          <button class="nav-toggle" type="button" aria-label="Mở menu" aria-expanded="false">
            <span></span>
            <span></span>
            <span></span>
          </button>
          <nav class="main-nav" aria-label="Menu chính">
            ${link('san-pham', 'Sản phẩm')}
            ${link('huong-dan-chon-size', 'Chọn size')}
            ${link('chung-nhan', 'Chứng nhận')}
            ${link('gioi-thieu', 'Giới thiệu')}
            ${link('lien-he', 'Liên hệ')}
            <details class="nav-more">
              <summary>Thêm</summary>
              <div class="nav-more__panel">
                <div>
                  <strong>Sản phẩm</strong>
                  ${link('tat-y-te-cap-2', 'Tất y tế cấp 2')}
                  ${link('tat-dai-the-thao-cap-2', 'Tất/đai thể thao cấp 2')}
                  ${link('tat-the-thao-cap-1', 'Tất thể thao cấp 1')}
                  ${link('phu-kien', 'Phụ kiện')}
                </div>
                <div>
                  <strong>Hướng dẫn</strong>
                  ${link('huong-dan-su-dung', 'Hướng dẫn sử dụng')}
                  ${link('cau-hoi-thuong-gap', 'Câu hỏi thường gặp')}
                </div>
                <div>
                  <strong>Chính sách</strong>
                  ${link('chinh-sach-doi-tra', 'Đổi trả')}
                  ${link('chinh-sach-van-chuyen', 'Vận chuyển')}
                  ${link('chinh-sach-thanh-toan', 'Thanh toán')}
                  ${link('chinh-sach-bao-mat', 'Bảo mật')}
                  ${link('dieu-khoan-su-dung', 'Điều khoản sử dụng')}
                </div>
              </div>
            </details>
          </nav>
          <div class="header-actions">
            <a class="btn btn--small btn--primary" href="${isContactPage ? 'tel:0848621092' : pageRoute('san-pham')}">${isContactPage ? 'Gọi ngay' : 'Mua ngay'}</a>
          </div>
        </div>
      </header>
    `;
  }

  if (footerMount) {
    footerMount.outerHTML = `
      <footer class="site-footer" id="contact">
        <section class="footer-newsletter" aria-labelledby="footer-newsletter-title">
          <div class="container footer-newsletter__inner">
            <div class="footer-newsletter__content">
              <div>
                <h2 id="footer-newsletter-title">${isContactPage ? 'LIÊN HỆ COMFYCARE QUA HOTLINE/ZALO CHÍNH THỨC' : 'TÔI MUỐN ĐƯỢC TƯ VẤN CHỌN TẤT/SIZE PHÙ HỢP'}</h2>
              </div>
            </div>
            <a class="btn btn--primary footer-newsletter__cta" href="https://zalo.me/0848621092">${isContactPage ? 'NHẮN ZALO' : 'TƯ VẤN QUA ZALO'}</a>
          </div>
        </section>

        <div class="footer-main">
          <div class="container footer-grid">
            <div class="footer-company">
              <a class="footer-brand" href="${homeRoute()}" aria-label="Comfycare trang chủ">
                <img class="footer-logo" src="${route('assets/logo/comfycare-logo.png')}" alt="Comfycare" />
                <span>COMFYCARE</span>
              </a>
              <p>
                Comfycare cung cấp tất áp lực y khoa cấp 2, tất/đai thể thao áp lực và phụ kiện hỗ trợ chăm sóc đôi chân đúng cách.
              </p>
              <div class="footer-social" aria-label="Mạng xã hội Comfycare">
                <a href="https://facebook.com/Comfycare249" aria-label="Facebook Comfycare">
                  <img src="${route('assets/icons/icon facebook.png')}" alt="" loading="lazy" />
                </a>
                <a href="https://zalo.me/0848621092" aria-label="Zalo Comfycare">
                  <img src="${route('assets/icons/icon zalo.png')}" alt="" loading="lazy" />
                </a>
                <a href="https://shopee.vn/comfycare_official_store" aria-label="Shopee Comfycare">
                  <img src="${route('assets/icons/icon shopee.png')}" alt="" loading="lazy" />
                </a>
                <a href="https://tiktok.com/@comfycare_store" aria-label="TikTok Comfycare">
                  <img src="${route('assets/icons/icon tiktok.png')}" alt="" loading="lazy" />
                </a>
              </div>
            </div>

            <nav class="footer-links" aria-label="Sản phẩm">
              <h3>SẢN PHẨM</h3>
              ${link('san-pham', 'Tất cả sản phẩm')}
              ${link('tat-y-te-cap-2', 'Tất y tế cấp 2')}
              ${link('tat-dai-the-thao-cap-2', 'Tất/đai thể thao cấp 2')}
              ${link('tat-the-thao-cap-1', 'Tất thể thao cấp 1')}
              ${link('phu-kien', 'Phụ kiện')}
            </nav>

            <nav class="footer-links" aria-label="Hướng dẫn và giới thiệu">
              <h3>HƯỚNG DẪN</h3>
              ${link('huong-dan-chon-size', 'Hướng dẫn chọn size')}
              ${link('huong-dan-su-dung', 'Hướng dẫn sử dụng')}
              ${link('cau-hoi-thuong-gap', 'Câu hỏi thường gặp')}
              ${link('gioi-thieu', 'Giới thiệu')}
              ${link('chung-nhan', 'Chứng nhận')}
              ${link('lien-he', 'Liên hệ')}
            </nav>

            <nav class="footer-links" aria-label="Chính sách">
              <h3>CHÍNH SÁCH</h3>
              ${link('chinh-sach-doi-tra', 'Chính sách đổi trả')}
              ${link('chinh-sach-van-chuyen', 'Chính sách vận chuyển')}
              ${link('chinh-sach-thanh-toan', 'Chính sách thanh toán')}
              ${link('chinh-sach-bao-mat', 'Chính sách bảo mật')}
              ${link('dieu-khoan-su-dung', 'Điều khoản sử dụng')}
            </nav>

            <div class="footer-support">
              <div class="footer-contact">
                <h3>HỖ TRỢ KHÁCH HÀNG</h3>
                <ul>
                  <li>
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4h4l2 5-2.5 1.5A12 12 0 0 0 15 15.5L16.5 13l5 2v4a2 2 0 0 1-2 2C10.4 21 3 13.6 3 4.5a2 2 0 0 1 2-2z"></path></svg>
                    <a href="tel:0848621092">Hotline/Zalo: 0848 621 092</a>
                  </li>
                  <li>
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16v12H4z"></path><path d="m4 7 8 6 8-6"></path></svg>
                    <a href="mailto:comfycare.store@gmail.com">Email: comfycare.store@gmail.com</a>
                  </li>
                  <li>
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 6v6l4 2"></path><path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z"></path></svg>
                    <span>CSKH chat: 8:00 - 22:00 hằng ngày</span>
                  </li>
                  <li>
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s7-5.1 7-11a7 7 0 1 0-14 0c0 5.9 7 11 7 11z"></path><path d="M12 10.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"></path></svg>
                    <span>48 Phương Lưu, Đông Hải, Hải Phòng</span>
                  </li>
                </ul>
              </div>
              <div class="footer-protection">
                <h3>CHỨNG NHẬN / BẢO VỆ</h3>
                <div class="footer-badge">
                  <span class="footer-badge__icon footer-badge__icon--bct" aria-hidden="true">
                    <img src="${route('assets/icons/icon bocongthuong.png')}" alt="" loading="lazy" />
                  </span>
                  <strong>ĐÃ THÔNG BÁO BỘ CÔNG THƯƠNG</strong>
                </div>
              </div>
            </div>
          </div>

          <div class="container footer-bottom">
            <p>© 2026 Comfycare. All rights reserved.</p>
            <div class="payment-icons" aria-label="Icon phương thức thanh toán">
              <span class="payment-icon"><img src="${route('assets/payment/payment-visa.png')}" alt="Visa" loading="lazy" /></span>
              <span class="payment-icon"><img src="${route('assets/payment/payment-mastercard.png')}" alt="Mastercard" loading="lazy" /></span>
              <span class="payment-icon"><img src="${route('assets/payment/payment-momo.png')}" alt="MoMo" loading="lazy" /></span>
              <span class="payment-icon"><img src="${route('assets/payment/payment-zalopay.png')}" alt="ZaloPay" loading="lazy" /></span>
              <span class="payment-icon"><img src="${route('assets/payment/payment-vnpay.png')}" alt="VNPay" loading="lazy" /></span>
            </div>
          </div>
        </div>
      </footer>

      <div class="mobile-sticky-cta" aria-label="Liên hệ nhanh">
        <a class="btn btn--secondary" href="https://zalo.me/0848621092">${isContactPage ? 'Nhắn Zalo' : 'Tư vấn size qua Zalo'}</a>
        <a class="btn btn--primary" href="tel:0848621092">Gọi hotline</a>
      </div>
    `;
  }
})();
