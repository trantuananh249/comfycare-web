"""Ảnh xem trước khi chia sẻ link (Zalo, Facebook, Messenger) và thẻ Open Graph cho mọi trang.

- Sinh assets/og/comfycare.jpg (ảnh chung) và assets/og/<mã>.jpg (mỗi trang sản phẩm), 1200×630.
- Chèn thẻ og:/twitter: vào các trang tĩnh (trừ trang chuyển hướng và /san-pham/<mã>/ do build-products.py sinh).
Chạy lại khi đổi ảnh hero, ảnh gallery ảnh 1, tên sản phẩm, tiêu đề hoặc mô tả trang. Cần Pillow.
"""
from html import unescape
from pathlib import Path
import json
import re

from PIL import Image, ImageDraw, ImageFont

from og_tags import og_block, strip_block

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'og'
W, H = 1200, 630
TEAL, DEEP, INK, MUTED, CREAM = '#0aa9b2', '#0a757d', '#12343a', '#5b6e72', '#fffef7'
FONT = Path(r'C:\Windows\Fonts')


def font(bold, size):
    return ImageFont.truetype(str(FONT / ('segoeuib.ttf' if bold else 'segoeui.ttf')), size)


def logo(height):
    im = Image.open(ROOT / 'assets/logo/comfycare-logo.png').convert('RGBA')
    return im.resize((round(im.width * height / im.height), height), Image.LANCZOS)


def wrap(draw, text, fnt, width):
    lines, line = [], ''
    for word in text.split():
        test = f'{line} {word}'.strip()
        if draw.textlength(test, font=fnt) <= width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    return lines + [line]


def brand_header(img, draw, x, y):
    mark = logo(64)
    img.paste(mark, (x, y), mark)
    draw.text((x + mark.width + 14, y + 32), 'Comfycare', font=font(True, 36), fill=DEEP, anchor='lm')


def default_image():
    hero = Image.open(ROOT / 'assets/hero/hero-main.png').convert('RGB')
    scale = W / hero.width
    hero = hero.resize((W, round(hero.height * scale)), Image.LANCZOS)
    top = (hero.height - H) // 2
    img = hero.crop((0, top, W, top + H)).convert('RGBA')
    # Làm sáng nửa trái để chữ đọc rõ, chuyển mềm sang ảnh.
    fade = Image.new('L', (W, H))
    fd = ImageDraw.Draw(fade)
    for xpos in range(W):
        fd.line([(xpos, 0), (xpos, H)], fill=int(235 * max(0.0, min(1.0, (720 - xpos) / 260))))
    img = Image.composite(Image.new('RGBA', (W, H), (255, 254, 247, 255)), img, fade)
    draw = ImageDraw.Draw(img)
    brand_header(img, draw, 64, 64)
    y = 190
    for line in wrap(draw, 'Tất áp lực y tế cấp 2, tất và đai thể thao áp lực', font(True, 46), 600):
        draw.text((64, y), line, font=font(True, 46), fill=INK)
        y += 60
    y += 18
    for line in ('Tư vấn chọn size theo số đo chân', 'Đổi size miễn phí 15 ngày'):
        draw.ellipse((66, y + 13, 78, y + 25), fill=TEAL)
        draw.text((92, y), line, font=font(False, 28), fill=MUTED)
        y += 44
    draw.text((64, H - 64), 'comfycare.vn', font=font(True, 28), fill=DEEP, anchor='ls')
    return img.convert('RGB')


def product_image(p):
    img = Image.new('RGBA', (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    src = ROOT / p['gallery'][0]['src'].lstrip('/') if p.get('gallery') else ROOT / p['image'].lstrip('/')
    photo = Image.open(src).convert('RGB')
    side = min(photo.size)
    photo = photo.crop(((photo.width - side) // 2, (photo.height - side) // 2,
                        (photo.width + side) // 2, (photo.height + side) // 2)).resize((H, H), Image.LANCZOS)
    img.paste(photo, (W - H, 0))
    draw.rectangle((0, 0, 10, H), fill=TEAL)
    brand_header(img, draw, 56, 56)
    draw.text((56, 170), p['category_label'].upper(), font=font(True, 22), fill=TEAL)
    y = 210
    name_font = font(True, 44)
    for line in wrap(draw, p['name'], name_font, W - H - 100)[:4]:
        draw.text((56, y), line, font=name_font, fill=INK)
        y += 58
    draw.text((56, y + 14), p['sku'], font=font(False, 28), fill=MUTED)
    draw.text((56, H - 56), 'comfycare.vn', font=font(True, 28), fill=DEEP, anchor='ls')
    return img.convert('RGB')


def meta(html, pattern):
    m = re.search(pattern, html, re.S)
    return unescape(' '.join(m[1].split())) if m else ''


def inject(path):
    html = strip_block(path.read_text(encoding='utf-8'))
    title = meta(html, r'<title>(.*?)</title>')
    description = meta(html, r'name="description"\s+content="([^"]*)"')
    canonical = re.search(r'<link rel="canonical" href="([^"]+)" />', html)
    if not (title and description and canonical):
        return False
    block = og_block(title, description, canonical[1])
    html = html.replace(canonical[0], canonical[0] + '\n    ' + block, 1)
    path.write_text(html, encoding='utf-8')
    return True


OUT.mkdir(parents=True, exist_ok=True)
default_image().save(OUT / 'comfycare.jpg', quality=84, optimize=True, progressive=True)
products = json.loads((ROOT / 'data/products.json').read_text(encoding='utf-8'))['products']
for p in products:
    if (ROOT / p['url'].strip('/') / 'index.html').exists():
        product_image(p).save(OUT / f"{p['sku'].lower()}.jpg", quality=84, optimize=True, progressive=True)

done = []
for path in sorted(ROOT.rglob('*.html')):
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith(('outputs/', 'san-pham/cs')) or 'http-equiv="refresh"' in path.read_text(encoding='utf-8'):
        continue
    if inject(path):
        done.append(rel)
print({'images': len(list(OUT.glob('*.jpg'))), 'pages': done})
