"""Giá trên thẻ sản phẩm ở trang tĩnh (trang chủ, danh mục, hướng dẫn chọn size) theo data/products.json.

Anh duyệt 13/11/2026: hiện giá niêm yết gạch ngang cạnh giá bán; bỏ nút "Mua trên Shopee" trên thẻ.
Chạy sau scripts/build-products.py mỗi khi giá trong brain thay đổi.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'san-pham/index.html', 'tat-y-te-cap-2/index.html', 'tat-dai-the-thao-cap-2/index.html',
         'tat-the-thao-cap-1/index.html', 'phu-kien/index.html', 'huong-dan-chon-size/index.html']


def vnd(amount):
    return f'{amount:,}'.replace(',', '.') + 'đ'


def main():
    products = {p['sku'].lower(): p for p in json.loads((ROOT / 'data/products.json').read_text(encoding='utf-8'))['products']}
    changed = 0
    for rel in PAGES:
        path = ROOT / rel
        page = path.read_text(encoding='utf-8')
        page = re.sub(r'\s*<a class="c26-shopee"[^>]*>.*?</a>', '', page, flags=re.S)

        def card(match):
            block = match.group(0)
            sku = re.search(r'/san-pham/(cs\d+)/', block)
            if not sku:
                return block
            p = products[sku[1]]
            old = f'<del>{vnd(p["list_price"])}</del> ' if p.get('list_price') else ''
            block = re.sub(r'<del>[^<]*</del> ', '', block)
            block = re.sub(r'(<p class="c26-price">)<strong>[^<]*</strong>',
                           lambda m: f'{m[1]}{old}<strong>{vnd(p["price"])}</strong>', block)
            block = re.sub(r'(<p class="t-pcard__price">)[0-9.]+đ',
                           lambda m: f'{m[1]}{old}{vnd(p["price"])}', block)
            return block

        new = re.sub(r'<article class="[^"]*\b(?:c26-card|t-pcard)\b[^"]*"[^>]*>.*?</article>', card, page, flags=re.S)
        if new != path.read_text(encoding='utf-8'):
            path.write_text(new, encoding='utf-8')
            changed += 1
    print({'pages_changed': changed})


if __name__ == '__main__':
    main()
