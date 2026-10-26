"""Gắn shop.js (mọi trang có site.min.js) và shop.css (trang /cart/, /thanh-toan/, /don-hang/) kèm version theo hash.
Chạy sau khi sửa shop.js/shop.css: python scripts/build-shop.py
Trang chi tiết sản phẩm lấy dòng shop.js từ /san-pham/ khi chạy scripts/build-products.py.
"""
from pathlib import Path
import hashlib
import re

root = Path(__file__).resolve().parents[1]
version = lambda name: hashlib.sha256((root / name).read_bytes()).hexdigest()[:12]
js_tag = f'<script src="/shop.js?v={version("shop.js")}" defer></script>'
css_tag = f'<link rel="stylesheet" href="/shop.css?v={version("shop.css")}" />'
SHOP_PAGES = {'cart', 'thanh-toan', 'don-hang'}

changed = 0
for page in sorted(root.rglob('*.html')):
    if any(part in ('outputs', '.git', 'node_modules') for part in page.relative_to(root).parts):
        continue
    raw = page.read_bytes().decode('utf-8')
    if 'site.min.js' not in raw:
        continue
    nl = '\r\n' if '\r\n' in raw else '\n'
    html = raw.replace('\r\n', '\n')
    html = re.sub(r'\n\s*<script src="/shop\.js\?v=\w+" defer></script>', '', html)
    html = re.sub(r'\n\s*<link rel="stylesheet" href="/shop\.css\?v=\w+" />', '', html)
    html, n = re.subn(r'(\n(\s*)<script src="/site\.min\.js\?v=\w+" defer></script>)', lambda m: f'{m[1]}\n{m[2]}{js_tag}', html, count=1)
    assert n == 1, page
    if page.parent.name in SHOP_PAGES and page.parent.parent == root:
        html = re.sub(r'(\n(\s*)<link rel="stylesheet" href="/styles\.min\.css\?v=\w+" />)', lambda m: f'{m[1]}\n{m[2]}{css_tag}', html, count=1)
    out = html.replace('\n', nl)
    if out != raw:
        page.write_bytes(out.encode('utf-8'))
        changed += 1
print({'shop_js': js_tag, 'shop_css': css_tag, 'pages_changed': changed})
