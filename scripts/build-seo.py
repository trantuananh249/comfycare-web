"""Dữ liệu có cấu trúc (JSON-LD) cho trang tĩnh và lastmod cho sitemap.

Rà soát 13/11/2026: trang chủ có Organization + WebSite + FAQPage, trang hỏi đáp có FAQPage
(lấy đúng câu hỏi/trả lời đang hiện trên trang), trang danh mục và trang tĩnh có BreadcrumbList.
Trang sản phẩm lấy JSON-LD từ build-products.py. Chạy lại sau khi sửa câu hỏi thường gặp.
"""
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://comfycare.vn'
START, END = '<!-- seo:start -->', '<!-- seo:end -->'

ORG = {
    '@context': 'https://schema.org', '@type': 'Organization', 'name': 'Comfycare',
    'legalName': 'Công ty TNHH Comfycare', 'url': f'{SITE}/',
    'logo': f'{SITE}/assets/logo/comfycare-logo-128.webp',
    'telephone': '+84848621092', 'email': 'comfycare.store@gmail.com',
    'address': {'@type': 'PostalAddress', 'streetAddress': '15C/19/128 An Đà, Phường Gia Viên',
                'addressLocality': 'Hải Phòng', 'addressCountry': 'VN'},
    'sameAs': ['https://facebook.com/Comfycare249', 'https://shopee.vn/comfycare_official_store',
               'https://www.tiktok.com/@comfycare_store'],
}
WEBSITE = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': 'Comfycare', 'url': f'{SITE}/',
           'inLanguage': 'vi'}

# Trang -> tên hiển thị trong breadcrumb (trang con của Trang chủ).
CRUMBS = {
    'san-pham': 'Sản phẩm', 'tat-y-te-cap-2': 'Tất y tế cấp 2', 'tat-dai-the-thao-cap-2': 'Tất/đai thể thao cấp 2',
    'tat-the-thao-cap-1': 'Tất thể thao cấp 1', 'phu-kien': 'Phụ kiện', 'huong-dan-chon-size': 'Hướng dẫn chọn size',
    'huong-dan-su-dung': 'Hướng dẫn sử dụng', 'cau-hoi-thuong-gap': 'Câu hỏi thường gặp', 'chung-nhan': 'Chứng nhận',
    'gioi-thieu': 'Giới thiệu', 'lien-he': 'Liên hệ', 'chinh-sach-doi-tra': 'Chính sách đổi trả',
    'chinh-sach-van-chuyen': 'Vận chuyển', 'chinh-sach-thanh-toan': 'Thanh toán',
    'chinh-sach-bao-mat': 'Bảo mật thông tin', 'dieu-khoan-su-dung': 'Điều khoản website',
}


def text(fragment):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def faq(page_html):
    pairs = re.findall(r'<details[^>]*>\s*<summary>(.*?)</summary>(.*?)</details>', page_html, re.S)
    items = [{'@type': 'Question', 'name': text(q),
              'acceptedAnswer': {'@type': 'Answer', 'text': text(a)}} for q, a in pairs if text(a)]
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': items} if items else None


def crumb(slug):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Trang chủ', 'item': f'{SITE}/'},
        {'@type': 'ListItem', 'position': 2, 'name': CRUMBS[slug], 'item': f'{SITE}/{slug}/'}]}


def inject(path, blocks):
    page = path.read_text(encoding='utf-8')
    page = re.sub(rf'\n?\s*{re.escape(START)}.*?{re.escape(END)}', '', page, flags=re.S)
    scripts = ''.join(f'\n    <script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>'
                      for b in blocks if b)
    block = f'\n    {START}{scripts}\n    {END}'
    page = page.replace('\n  </head>', block + '\n  </head>', 1)
    assert START in page, f'{path}: không tìm thấy </head>'
    path.write_text(page, encoding='utf-8')


def lastmod(rel):
    out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', rel], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip()


def sitemap():
    path = ROOT / 'sitemap.xml'
    xml = path.read_text(encoding='utf-8')
    xml = re.sub(r'\s*<lastmod>[^<]*</lastmod>', '', xml)

    def add(m):
        url = m.group(1)
        rel = url.replace(SITE + '/', '') + 'index.html'
        date = lastmod(rel or 'index.html')
        return f'<loc>{url}</loc>' + (f'<lastmod>{date}</lastmod>' if date else '')
    xml = re.sub(r'<loc>([^<]+)</loc>', add, xml)
    path.write_text(xml, encoding='utf-8')


def main():
    home = ROOT / 'index.html'
    inject(home, [ORG, WEBSITE, faq(home.read_text(encoding='utf-8'))])
    for slug in CRUMBS:
        path = ROOT / slug / 'index.html'
        blocks = [crumb(slug)]
        if slug == 'cau-hoi-thuong-gap':
            blocks.append(faq(path.read_text(encoding='utf-8')))
        inject(path, blocks)
    sitemap()
    print({'pages': 1 + len(CRUMBS)})


if __name__ == '__main__':
    main()
