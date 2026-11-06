"""Sinh data/products.json và trang /san-pham/<mã>/ từ brain đã chốt.
Chạy từ thư mục bất kỳ: python scripts/build-products.py
Nguồn: brain/knowledge/products/catalog_pricing.md (tên, giá, quà, đơn vị), size_guides.md (bảng size),
brain/content/products/<mã>.md (kiểu dáng, áp lực, chất liệu, mô tả). Link Shopee và danh mục là dữ liệu website (SITE bên dưới).
Không đưa ghi chú nội bộ, brain.db hay nguồn vào file sinh ra.
"""
from html import escape
from pathlib import Path
import hashlib
import json
import os
import re
import struct

from workspace_paths import SITE as ROOT, KNOWLEDGE, CONTENT
from og_tags import og_block

# Nội dung mô tả trang chi tiết lấy từ file mô tả sàn (cùng nội dung đăng Shopee/TikTok), đặt cạnh ảnh sản phẩm:
# <Ảnh sản phẩm>/<mã viết thường>/<MÃ>_Tieu_de_Mo_ta.txt. File sinh từ brain; sửa nội dung thì sửa brain rồi sinh lại file.
LISTINGS = Path(os.environ.get('PRODUCT_IMAGE_SOURCE', 'C:/Users/mrtua/OneDrive/Desktop/Database Comfycare/Ảnh sản phẩm'))

# Trang chi tiết: mẫu CS22 được duyệt 22/10/2026, áp dụng cho cả 19 mã (kế hoạch 09, bước 2).
PAGE_SKUS = ['CS21', 'CS22', 'CS23', 'CS24', 'CS26', 'CS27', 'CS33', 'CS34', 'CS35',
             'CS25', 'CS28', 'CS29', 'CS30', 'CS31', 'CS11', 'CS12', 'CS14', 'CS110', 'CS100', 'CS101']
# Ảnh sàn không đưa lên web vì trái brain. Trống từ 24/10/2026: CS12 ảnh 3, CS14 ảnh 5 đã sửa theo brain.
GALLERY_SKIP = {}
# Ảnh trong gallery có bảng size + vị trí đo, dùng làm hình minh họa ở khối chọn size (dòng y tế dùng measure-leg).
SIZE_FIGURE = {'CS25': 8, 'CS28': 9, 'CS29': 9, 'CS30': 8, 'CS31': 9, 'CS11': 3, 'CS12': 3, 'CS14': 5, 'CS110': 4}
# Số đo cần lấy theo F.3–F.7 cho mã ngoài dòng y tế. Ghi chú chọn size lấy từ file mô tả (mục HƯỚNG DẪN CHỌN SIZE).
MEASURE = {
    'CS25': ['Size giày đang đi'],
    'CS28': ['Chu vi đùi, đo cách gối 10 cm', 'Cân nặng, chỉ để tham khảo khi chưa đo được'],
    'CS29': ['Chu vi cổ tay, chỗ nhỏ nhất'],
    'CS30': ['Chu vi cổ tay, chỗ nhỏ nhất'],
    'CS31': ['Chu vi qua tâm khuỷu tay'],
    'CS11': ['Chu vi bắp chân, chỗ to nhất'],
    'CS12': ['Size giày đang đi'],
    'CS14': ['Chu vi đùi, đo ngay phía trên gối'],
    'CS110': ['Giới tính và cân nặng (bảng tham khảo)'],
}
CATEGORIES = {
    'D.1': ('c2-y-te', 'tat-y-te-cap-2', 'Tất y tế cấp 2'),
    'D.2': ('c2-the-thao', 'tat-dai-the-thao-cap-2', 'Tất/đai thể thao cấp 2'),
    'D.3': ('c1', 'tat-the-thao-cap-1', 'Tất thể thao cấp 1'),
    'D.4': ('phu-kien', 'phu-kien', 'Phụ kiện'),
}
# Link sản phẩm Shopee đang dùng trên thẻ danh mục (validate_sources.py đối chiếu với trang danh mục).
SHOPEE = {
    'CS21': '26651928715', 'CS22': '27851924204', 'CS23': '24881765401', 'CS24': '29151924794',
    'CS26': '28156777299', 'CS27': '27356777930', 'CS33': '45558066622', 'CS34': '44858057663',
    'CS35': '41729664819', 'CS25': '28956486512', 'CS28': '41050137462', 'CS29': '49758235651',
    'CS30': '43800142577', 'CS31': '45108300810', 'CS11': '26751930208', 'CS12': '26601929950',
    'CS14': '29406484639', 'CS110': '29484186147', 'CS100': '28706085493', 'CS101': '49169771048',
}
SHOP_ID = '1268125014'
ZALO = 'https://zalo.me/0848621092'
BYT_NUMBER = '250000052/PCBA-HP'
# F.1–F.7: các cỡ đang bán. CS11 (business 39), CS12 (business 36), CS14, CS110 có S/M và L/XL.
FULL_SIZES = ['S', 'M', 'L', 'XL', 'XXL']
SIZES = {'CS11': ['S/M', 'L/XL'], 'CS12': ['S/M', 'L/XL'], 'CS14': ['S/M', 'L/XL'], 'CS110': ['S/M', 'L/XL'], 'CS100': [], 'CS101': []}
# Tiêu đề trong size_guides.md -> mã dùng bảng đó; neo tương ứng trên /huong-dan-chon-size/.
SIZE_SECTIONS = [
    ('### F.1.', ['CS21', 'CS22', 'CS26', 'CS23', 'CS24', 'CS27', 'CS33', 'CS34', 'CS35'], 'medical-compression-size'),
    ('### F.3.', ['CS25'], 'cs25-size'),
    ('### F.4.', ['CS28'], 'cs28-size'),
    ('### F.5.', ['CS29', 'CS30'], 'cs29-cs30-size'),
    ('### F.6.', ['CS31'], 'cs31-size'),
    ('#### CS14 ', ['CS14'], 'sport-level-1-size'),
    ('#### CS110 ', ['CS110'], 'sport-level-1-size'),
    ('#### CS11 ', ['CS11'], 'sport-level-1-size'),
    ('#### CS12 ', ['CS12'], 'sport-level-1-size'),
]
# F.1 "Số đo cần thu thập": tất ống chân chỉ cần cB + cC.
LEG_ONLY = {'CS21', 'CS22', 'CS26'}
def read(path):
    return path.read_text(encoding='utf-8-sig')


LISTING = {}


def parse_listing(sku):
    """File mô tả sàn -> {tiêu đề mục: [dòng]}; dòng gạch đầu dòng bỏ '- '."""
    text = read(LISTINGS / sku.lower() / f'{sku}_Tieu_de_Mo_ta.txt')
    sections = {}
    for block in re.split(r'\n=+\n', text):
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if lines:
            sections[lines[0]] = lines[1:]
    for need in ('GIỚI THIỆU SẢN PHẨM', 'CÔNG DỤNG', 'QUÀ TẶNG', 'ĐỔI TRẢ 15 NGÀY'):
        assert need in sections, f'{sku}: file mô tả thiếu mục {need}'
    return sections


def bullets(lines):
    return [l[2:] for l in lines if l.startswith('- ')]


def money(text):
    return int(text.replace('.', '').replace('đ', '').replace('*', '').strip())


def vnd(amount):
    return f'{amount:,}'.replace(',', '.') + 'đ'


def table_after(lines, start):
    """Bảng Markdown đầu tiên sau dòng start: (tiêu đề cột, các hàng)."""
    rows = []
    for line in lines[start + 1:]:
        if line.startswith('#'):
            break
        if line.startswith('|'):
            cells = [c.strip().replace('**', '') for c in line.strip().strip('|').split('|')]
            if not all(set(c) <= set('-: ') for c in cells):
                rows.append(cells)
        elif rows:
            break
    assert rows, f'Không thấy bảng sau dòng {start + 1}'
    return rows[0], rows[1:]


def parse_catalog():
    products, section = {}, None
    for line in read(KNOWLEDGE / 'products/catalog_pricing.md').splitlines():
        heading = re.match(r'### (D\.\d)\.', line)
        if heading:
            section = heading[1]
            continue
        row = re.match(r'\| \*\*(CS\d+)\*\* \|', line)
        if not row or section not in CATEGORIES:
            continue  # Bỏ dòng "Combo 2": web không bán combo (Q4, Q5).
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        group, route, label = CATEGORIES[section]
        # D.1–D.3: cột 4 là giá bán lẻ/TMĐT; D.4 (CS100) chỉ có một mức giá ở cột 4.
        products[row[1]] = {'sku': row[1], 'name': cells[1].replace('**', ''), 'group': group,
                            'category_route': route, 'category_label': label,
                            'price': money(cells[3])}
    gifts = re.search(r'Tặng kèm cho:\*\* ([^(]+)', read(KNOWLEDGE / 'products/catalog_pricing.md'))[1]
    gift_skus = set(re.findall(r'CS\d+', gifts))
    assert gift_skus == {'CS21', 'CS22', 'CS23', 'CS24', 'CS33', 'CS34'}, 'D.5 thay đổi: rà lại quà CS100'
    for sku, product in products.items():
        product['gift_cs100'] = sku in gift_skus
    return products


def parse_content(sku):
    text = read(CONTENT / 'products' / f'{sku}.md')
    field = lambda name: re.search(rf'^- {name}: (.+)$', text, re.M)[1].strip()
    pressure = re.search(r'(\d+–\d+ mmHg)', field('Áp lực theo nguồn'))
    material = field('Chất liệu')
    if material.startswith('Nguồn chưa công bố'):
        material = None
    else:
        material = re.split(r';| — ', material)[0]
        material = re.sub(r'\s*(\(v3\.2 [^)]+\)|theo v3\.2 \S+)', '', material).rstrip('. ')
    intro = re.search(r'## Mô tả mẫu dùng cho nội dung\n\n(.+)', text)[1]
    # Giữ câu mô tả sản phẩm; bỏ câu mời nhắn tin (giọng chat "anh/chị ... em").
    sentences = [s for s in re.split(r'(?<=\.) ', intro) if not re.search(r'\bem\b|Anh/chị', s)]
    return {'style': field('Kiểu dáng/vị trí').rstrip('.'), 'pressure': pressure[1] if pressure else None,
            'material': material, 'description': ' '.join(sentences)}


def parse_sizes():
    lines = read(KNOWLEDGE / 'products/size_guides.md').splitlines()
    tables = {}
    for prefix, skus, anchor in SIZE_SECTIONS:
        start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
        header, rows = table_after(lines, start)
        for sku in skus:
            if sku in LEG_ONLY:
                keep = [i for i, h in enumerate(header) if not h.startswith('cG')]
                tables[sku] = ([header[i] for i in keep], [[r[i] for i in keep] for r in rows], anchor)
            else:
                tables[sku] = (header, rows, anchor)
    return tables


def image_size(path):
    """(rộng, cao) của PNG hoặc WebP (VP8, VP8L, VP8X), đọc từ header."""
    with open(path, 'rb') as f:
        head = f.read(32)
    if head[:8] == b'\x89PNG\r\n\x1a\n':
        return struct.unpack('>II', head[16:24])
    assert head[:4] == b'RIFF' and head[8:12] == b'WEBP', path
    chunk = head[12:16]
    if chunk == b'VP8 ':
        w, h = struct.unpack('<HH', head[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if chunk == b'VP8L':
        bits = int.from_bytes(head[21:25], 'little')
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    assert chunk == b'VP8X', path
    return int.from_bytes(head[24:27], 'little') + 1, int.from_bytes(head[27:30], 'little') + 1


def gallery(sku):
    """Ảnh gallery do scripts/import-product-images.cjs tạo; chưa có thì dùng ảnh danh mục 1.*."""
    folder = ROOT / 'assets/products' / sku / 'gallery'
    numbers = sorted(int(f.stem) for f in folder.glob('*.webp')
                     if f.stem.isdigit() and int(f.stem) not in GALLERY_SKIP.get(sku, ())) if folder.exists() else []
    if not numbers:
        w, h = image_size(ROOT / 'assets/products' / sku / '1.png')
        base = f'/assets/products/{sku}/1'
        return [{'src': f'{base}.webp', 'medium': f'{base}-640.webp', 'thumb': f'{base}-320.webp', 'width': w, 'height': h}]
    images = []
    for n in numbers:
        base = f'/assets/products/{sku}/gallery/{n}'
        for suffix in ('-640', '-160'):
            assert (ROOT / f'{base.lstrip("/")}{suffix}.webp').exists(), f'Thiếu {base}{suffix}.webp'
        w, h = image_size(ROOT / f'{base.lstrip("/")}.webp')
        images.append({'n': n, 'src': f'{base}.webp', 'medium': f'{base}-640.webp', 'thumb': f'{base}-160.webp', 'width': w, 'height': h})
    return images


def build_products():
    products = parse_catalog()
    assert len(products) == 20, 'Danh mục phải có 20 mã đang bán'
    assert set(products) == set(SHOPEE), 'SHOPEE thiếu/thừa mã so với catalog'
    tables = parse_sizes()
    for sku, p in products.items():
        p.update(parse_content(sku))
        LISTING[sku] = parse_listing(sku)
        # Câu mở đầu trang lấy từ file mô tả sàn để web và sàn nói cùng một nội dung.
        p['description'] = next(l for l in LISTING[sku]['GIỚI THIỆU SẢN PHẨM'] if not l.startswith('- '))
        p['has_byt'] = p['group'] == 'c2-y-te'
        # D.6: tất quần bán theo chiếc; phụ kiện CS100, CS101 theo chiếc; còn lại theo đôi.
        p['unit'] = 'chiếc' if sku in ('CS33', 'CS34', 'CS35', 'CS100', 'CS101') else 'đôi'
        p['colors'] = [] if p['group'] == 'phu-kien' else ['Da', 'Đen']  # D.7; phụ kiện không có biến thể màu.
        p['sizes'] = SIZES.get(sku, FULL_SIZES)
        if sku in tables:
            header, rows, anchor = tables[sku]
            p['size_table'] = {'header': header, 'rows': rows}
            p['size_guide_url'] = f'/huong-dan-chon-size/#{anchor}'
        else:
            p['size_table'] = None
            p['size_guide_url'] = None
        p['shopee_url'] = f'https://shopee.vn/product/{SHOP_ID}/{SHOPEE[sku]}'
        p['image'] = f'/assets/products/{sku}/1.png'
        p['gallery'] = gallery(sku)
        p['url'] = f'/san-pham/{sku.lower()}/'
    return products


def head_parts():
    """Lấy CSS/JS version và Meta Pixel từ trang /san-pham/ để trang chi tiết đồng bộ với site."""
    html = read(ROOT / 'san-pham/index.html')
    pick = lambda pattern: re.search(pattern, html, re.S)[0]
    return {
        'styles': pick(r'<link rel="stylesheet" href="/styles\.min\.css\?v=\w+" />'),
        'site': pick(r'<script src="/site\.min\.js\?v=\w+" defer></script>\s*<script src="/shop\.js\?v=\w+" defer></script>'),
        'pixel': pick(r'<!-- Meta Pixel Code -->.*?<!-- End Meta Pixel Code -->'),
        'chatbot': pick(r'<link rel="stylesheet" href="/chatbot\.css[^>]+>\s*<script defer src="/chatbot\.js[^>]+></script>'),
    }


def size_table_html(p):
    header, rows = p['size_table']['header'], p['size_table']['rows']
    long_names = {'cB (cm)': 'Vòng cổ chân cB (cm)', 'cC (cm)': 'Vòng bắp chân cC (cm)', 'cG (cm)': 'Vòng đùi cG (cm)'}
    th = ''.join(f'<th scope="col">{escape(long_names.get(h, h).replace(" (vị trí A)", " (ngay trên gối)"))}</th>' for h in header)
    body = '\n'.join(
        '                  <tr>' + ''.join(f'<td>{escape(c)}</td>' for c in row) + '</tr>' for row in rows)
    # Không dùng catalog-size-table: CSS chung đổi bảng đó thành thẻ dọc trên điện thoại.
    return f'''<div class="pd-table-shell">
                <table class="pd-size-table">
                  <caption class="sr-only">Bảng size {escape(p['name'])}</caption>
                  <thead><tr>{th}</tr></thead>
                  <tbody>
{body}
                  </tbody>
                </table>
              </div>'''


def render_page(p, head, css_version, js_version, theme_version):
    sku, name, unit = p['sku'], escape(p['name']), p['unit']
    badge = (f'<span class="catalog-badge">BYT {BYT_NUMBER}</span>' if p['has_byt']
             else f'<span class="catalog-badge catalog-badge--warm">{escape(p["category_label"])}</span>')
    title = f'{p["name"]} {sku} | Comfycare'
    description = f'{p["name"]} ({sku}) Comfycare, {p["category_label"].lower()}'
    description += f', áp lực {p["pressure"]}' if p['pressure'] else ''
    description += f'. Giá bán lẻ {vnd(p["price"])}/{unit}, đã gồm VAT. Bảng size, cách chọn size, đặt mua trên website hoặc Shopee.'
    # Layout duyệt 04/11: 3 ô đặc điểm có dấu tích dưới giá (áp lực + kiểu dáng tách theo dấu phẩy).
    CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" /><path d="m7.5 12.5 3 3 6-6.5" /></svg>'
    feats = []
    if p['pressure']:
        level = ' (cấp 2)' if p['group'].startswith('c2') else ' (cấp 1)' if p['group'] == 'c1' else ''
        feats.append(f'Áp lực {p["pressure"]}{level}')
    if p['group'] == 'c2-y-te':
        n = p['name']
        feats.append('Hở 5 đầu ngón' if 'Hở Ngón' in n else 'Hở cả bàn chân' if 'Không Bàn' in n else 'Kín bàn chân')
        feats.append('Dài đến dưới gối' if 'Ống Chân' in n else 'Dài đến đùi' if 'Đùi' in n else 'Dài đến eo')
    elif p['group'] != 'phu-kien':
        feats.append(p['style'][:1].upper() + p['style'][1:])
    pressure = (f'<ul class="pd-feats">{"".join(f"<li>{CHECK}<span>{escape(f)}</span></li>" for f in feats)}</ul>'
                if feats else '')
    gift = ('''<p class="pd-gift"><strong>Tặng kèm</strong> dụng cụ hỗ trợ xỏ tất CS100 (dạng miếng vải polyester).</p>'''
            if p['gift_cs100'] else '')
    scope = ''  # business 41: chỉ tất y tế nhắc chứng nhận; đồ thể thao không nhắc.
    if sku == 'CS100':
        # D.5: dụng cụ không xỏ vừa tất kín bàn.
        scope = '<p class="pd-scope">Dùng cho các mẫu tất không bàn và hở ngón; không dùng được với tất kín bàn (CS26, CS27, CS35).</p>'
    elif sku == 'CS101':
        scope = '<p class="pd-scope">Kích thước 30×40 cm. Dùng để bảo vệ tất áp lực khi giặt máy; giặt theo hướng dẫn: chế độ nhẹ, tối đa 30°C, không sấy.</p>'
    # business 38: tặng túi giặt CS101 cho đơn từ 300.000đ sau voucher, mọi kênh.
    promo = ('<p class="pd-muted">Đơn từ 300.000đ tiền hàng (sau giảm giá/voucher, không tính ship) được tặng 01 túi giặt tất áp lực CS101.</p>'
             if sku != 'CS101' else
             '<p class="pd-muted">Đơn từ 300.000đ tiền hàng (sau giảm giá/voucher, không tính ship) được tặng 01 túi giặt này.</p>')

    def options(field, values):
        return ''.join(
            f'<label class="pd-chip"><input type="radio" name="{field}" value="{escape(v)}" /><span>{escape(v)}</span></label>'
            for v in values)
    size_field = ''
    if p['sizes']:
        guide = ('<a class="pd-link" href="#pd-size">Cách đo chân để chọn size</a>' if p['size_table'] else '')
        size_field = f'''<fieldset class="pd-field">
                  <legend>Chọn size</legend>
                  <div class="pd-chips">{options("size", p["sizes"])}</div>
                  {guide}
                </fieldset>'''
    SWATCH = {'Da': '#f2cfae', 'Đen': '#1f1f1f'}
    swatches = ''.join(
        f'<label class="pd-chip pd-chip--color"><input type="radio" name="color" value="{escape(v)}" /><span><i style="background:{SWATCH.get(v, "#ccc")}"></i>{escape(v)}</span></label>'
        for v in p['colors'])
    color_field = (f'''<fieldset class="pd-field">
                  <legend>Màu sắc</legend>
                  <div class="pd-chips">{swatches}</div>
                </fieldset>''' if p['colors'] else '')

    listing = LISTING[sku]
    # Thông tin sản phẩm: các dòng "Tên: giá trị" trong mục GIỚI THIỆU của file mô tả; dòng không có nhãn gom vào "Đặc điểm".
    facts = []
    for line in bullets(listing['GIỚI THIỆU SẢN PHẨM']):
        key, sep, value = line.partition(': ')
        if not sep:
            key, value = 'Đặc điểm', line
        if key in ('Tên sản phẩm', 'Thương hiệu'):
            continue
        facts.append((key, value[:1].upper() + value[1:]))
    fact_rows = '\n'.join(f'                <div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>' for k, v in facts)
    if p['has_byt']:
        fact_rows += (f'\n                <div><dt>Công bố</dt><dd>Công bố tiêu chuẩn áp dụng {BYT_NUMBER} tại Sở Y tế Hải Phòng, '
                      f'size S–XXL. <a href="/chung-nhan/">Xem hồ sơ</a></dd></div>')

    # Lời khuyên chọn size (dòng không gạch đầu dòng, không kết thúc bằng ":" trong mục HƯỚNG DẪN CHỌN SIZE).
    notes = [l for l in listing.get('HƯỚNG DẪN CHỌN SIZE', []) if not l.startswith('- ') and not l.endswith(':')]
    size_notes = '\n              '.join(f'<p class="pd-muted">{escape(n)}</p>' for n in notes)
    size_section = ''
    if p['size_table']:
        figure, measures = '', ''
        if p['group'] == 'c2-y-te':
            # F.1: cB mắt cá, cC bắp chân (vùng to nhất), cG đùi (vùng to nhất, sát bẹn). Hình chân có nhãn như layout.
            points = [('cC', 'Vòng bắp chân', 'c'), ('cB', 'Vòng cổ chân', 'b')]
            if sku not in LEG_ONLY:
                points.insert(0, ('cG', 'Vòng đùi', 'g'))
            labels = ''.join(f'<span class="leg-tag leg-tag--{c}"><b>{k}</b>({v})</span>' for k, v, c in points)
            leg = 'chan-do-duoi' if sku in LEG_ONLY else 'chan-do'
            # Ảnh cắt từ layout (sp-chan) bị vỡ: dùng hình chân vẽ nét cao + nhãn HTML (04/11).
            figure = f'''<figure class="leg-figure{' leg-figure--short' if sku in LEG_ONLY else ''}">
                <img src="/assets/trang-2026/{leg}-600.webp" srcset="/assets/trang-2026/{leg}-600.webp 600w, /assets/trang-2026/{leg}.webp 900w" sizes="(max-width: 900px) 90vw, 480px" alt="Vị trí đo {', '.join(f'{k} ({v.lower()})' for k, v, _ in points)}" width="900" height="{1100 if leg == 'chan-do' else 770}" loading="lazy" decoding="async" />
                {labels}
              </figure>'''
        elif sku in MEASURE:
            items = ''.join(f'<li><span class="pd-measure-key">{i}</span>{escape(s)}</li>' for i, s in enumerate(MEASURE[sku], 1))
            measures = f'''<p class="pd-size__need">{sku} chọn size theo:</p>
                <ol class="pd-measure">{items}</ol>'''
            g = next((g for g in p['gallery'] if g.get('n') == SIZE_FIGURE.get(sku)), None)
            if g:
                figure = f'''<figure class="pd-size__figure pd-size__figure--square">
                <img src="{g["medium"]}" srcset="{g["medium"]} 640w, {g["src"]} {g["width"]}w" sizes="(max-width: 900px) calc(100vw - 32px), 560px" alt="Hướng dẫn chọn size {name}" width="{g["width"]}" height="{g["height"]}" loading="lazy" decoding="async" />
              </figure>'''
        # Layout: bảng bên trái + ghi chú dạng thanh; hình đo bên phải.
        size_section = f'''
          <h2 class="pd-h2" id="pd-size-title">Bảng size</h2>
          <div class="pd-size__grid{'' if figure else ' pd-size__grid--single'}">
            <div class="pd-size__chart">
              {size_table_html(p)}
              <p class="pd-note"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" /><path d="M12 11v5M12 8h.01" /></svg><span>Số đo nằm giữa 2 size hoặc mới dùng lần đầu: <a href="{ZALO}" target="_blank" rel="noopener noreferrer">nhắn Zalo để em tư vấn</a>.</span></p>
              {measures}
              {size_notes}
              <a class="pd-link" href="{p["size_guide_url"]}">Hướng dẫn chọn size đầy đủ</a>
            </div>
            {figure}
          </div>'''

    images = p['gallery']
    first = images[0]
    many = len(images) > 1
    thumbs = ''
    if many:
        thumbs = '\n'.join(
            f'''                <button class="pd-thumb" type="button" data-index="{i}" data-src="{g["src"]}" data-medium="{g["medium"]}" data-width="{g["width"]}" aria-label="Xem ảnh {i + 1}"{' aria-current="true"' if i == 0 else ''}><img src="{g["thumb"]}" alt="" width="160" height="{round(g["height"] * 160 / g["width"])}" loading="lazy" decoding="async" /></button>'''
            for i, g in enumerate(images))
        thumbs = f'\n              <div class="pd-gallery__thumbs">\n{thumbs}\n              </div>'
    nav = (f'''
                <button class="pd-gallery__nav pd-gallery__nav--prev" type="button" aria-label="Ảnh trước" data-gallery-prev><span aria-hidden="true">‹</span></button>
                <button class="pd-gallery__nav pd-gallery__nav--next" type="button" aria-label="Ảnh sau" data-gallery-next><span aria-hidden="true">›</span></button>
                <span class="pd-gallery__count" data-gallery-count aria-live="polite">1/{len(images)}</span>''' if many else '')
    gallery_html = f'''<div class="pd-gallery" data-gallery data-name="{name}">
              <div class="pd-gallery__main">
                <img data-gallery-main src="{first["src"]}" srcset="{first["medium"]} 640w, {first["src"]} {first["width"]}w" sizes="(max-width: 900px) calc(100vw - 32px), 540px" alt="{name}{f' – ảnh 1/{len(images)}' if many else ''}" width="{first["width"]}" height="{first["height"]}" fetchpriority="high" decoding="async" />{nav}
              </div>{thumbs}
            </div>'''

    # Các thẻ nội dung lấy nguyên từ file mô tả sàn: (mục trong file, tiêu đề trên web, id, kiểu thẻ, link kèm).
    cards_spec = [
        ('CÔNG DỤNG', 'Công dụng', 'benefit', '', ''),
        ('PHÙ HỢP VỚI', 'Phù hợp với ai', 'audience', '', ''),
        ('HƯỚNG DẪN SỬ DỤNG', 'Cách sử dụng', 'usage', '', '<a class="pd-link" href="/huong-dan-su-dung/">Hướng dẫn mang tất chi tiết</a>'),
        ('CÁCH DÙNG', 'Cách dùng', 'usage', '', ''),
        ('GIẶT VÀ BẢO QUẢN', 'Giặt và bảo quản', 'care', '', ''),
        ('LƯU Ý KHI DÙNG', 'Lưu ý khi dùng', 'caution', ' pd-card--warn', ''),
        ('HỒ SƠ CHẤT LƯỢNG', 'Hồ sơ chất lượng', 'quality', '', '<a class="pd-link" href="/chung-nhan/">Xem hồ sơ chứng nhận</a>'),
        ('QUÀ TẶNG', 'Quà tặng', 'gift', '', ''),
        ('ĐỔI TRẢ 15 NGÀY', 'Đổi trả 15 ngày', 'exchange', '', '<a class="pd-link" href="/chinh-sach-doi-tra/">Xem chính sách đổi trả</a>'),
    ]
    cards = {}
    for key, heading, cid, extra, link in cards_spec:
        items = bullets(listing.get(key, []))
        if not items:
            continue
        lis = ''.join(f'<li>{escape(i)}</li>' for i in items)
        tail = f'\n            <p>{link}</p>' if link else ''
        cards[cid] = f'''
          <section class="pd-card{extra}" aria-labelledby="pd-{cid}-title">
            <h2 id="pd-{cid}-title">{heading}</h2>
            <ul class="pd-list">{lis}</ul>{tail}
          </section>'''
    cta = (f'Gửi mã {sku} và số đo qua Zalo, Comfycare chọn size cùng anh/chị.' if p['sizes']
           else 'Cần mua thêm túi giặt hoặc hỏi về quà tặng? Nhắn Comfycare qua Zalo.' if sku == 'CS101'
           else 'Gửi mã tất đang dùng qua Zalo, Comfycare kiểm tra dụng cụ có phù hợp không.')

    schema = {
        '@context': 'https://schema.org', '@type': 'Product', 'name': p['name'], 'sku': sku,
        'image': [f'https://comfycare.vn{g["src"]}' for g in p['gallery']], 'description': p['description'],
        'brand': {'@type': 'Brand', 'name': 'Comfycare'},
        'offers': {'@type': 'Offer', 'price': p['price'], 'priceCurrency': 'VND',
                   'url': f'https://comfycare.vn{p["url"]}'},
    }

    # J.3: dòng tất y tế nhắc hỏi bác sĩ với thai kỳ, bệnh nền, sau phẫu thuật.
    notice = ('''
          <div class="t-notice pd-notice">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg>
            <p>Đang mang thai, có bệnh nền hoặc sau phẫu thuật: anh/chị hỏi ý kiến bác sĩ trước khi dùng.</p>
          </div>''' if p['has_byt'] else '')
    # Nội dung chi tiết chia tab (anh yêu cầu 04/11), bố cục từng tab theo layout duyệt: Mô tả, Bảng size, Cách mang, Giặt và bảo quản, Đổi trả.
    ICONS = {
        'leg': '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M18 4v22c0 4-2 7-6 9l-4 2c-2 1-2 5 1 5h18c3 0 5-2 5-5V4" /><path d="M18 14h14" /></svg>',
        'cycle': '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M38 18A15 15 0 0 0 11 13l-3 3" /><path d="M8 8v8h8" /><path d="M10 30a15 15 0 0 0 27 5l3-3" /><path d="M40 40v-8h-8" /></svg>',
        'toe': '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M14 6h16v18l10 8c3 2 2 8-3 8H20c-4 0-6-3-6-6Z" /><path d="M14 16h16" /><path d="M32 40c1-3 0-6-2-8" /></svg>',
        'gauge': '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M8 34a16 16 0 1 1 32 0" /><path d="m24 34 8-10" /><circle cx="24" cy="34" r="2.5" /></svg>',
    }
    highlights = [('leg', 'Hỗ trợ giảm đau mỏi chân'), ('cycle', 'Hỗ trợ tuần hoàn')]
    if p['group'] == 'c2-y-te' and 'Hở Ngón' in p['name']:
        highlights.append(('toe', 'Hở ngón dễ kiểm tra đầu ngón'))
    elif p['pressure']:
        highlights.append(('gauge', f'Áp lực {p["pressure"]}'))
    if p['group'] == 'phu-kien':
        highlights = []
    hl = ''.join(f'<li>{ICONS[i]}<span>{escape(t)}</span></li>' for i, t in highlights)
    spec_keys = ('Chất liệu', 'Quy cách', 'Màu sắc', 'Kích cỡ')
    specs = [(k, v) for k, v in facts if k in spec_keys] or facts[:4]
    spec_html = ''.join(f'<li><b>{escape(k)}:</b> {escape(v)}</li>' for k, v in specs)
    more_facts = ''.join(f'<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>' for k, v in facts if (k, v) not in specs)
    if p['has_byt']:
        more_facts += (f'<div><dt>Công bố</dt><dd>Công bố tiêu chuẩn áp dụng {BYT_NUMBER} tại Sở Y tế Hải Phòng, '
                       f'size S–XXL. <a href="/chung-nhan/">Xem hồ sơ</a></dd></div>')
    desc_panel = f'''
          <h2 class="pd-h2" id="pd-info-title">Mô tả</h2>
          <p class="pd-desc">{escape(p["description"])}</p>
          {f'<ul class="pd-highlights">{hl}</ul>' if hl else ''}
          <ul class="pd-specs">{spec_html}</ul>
          <details class="pd-xem-them">
            <summary>Xem thêm thông tin sản phẩm</summary>
            <div class="pd-more">
              {f'<section class="pd-card"><h3>Thông tin thêm</h3><dl class="pd-facts">{more_facts}</dl></section>' if more_facts else ''}{''.join(cards.get(c, '') for c in ('benefit', 'audience', 'quality'))}
            </div>
          </details>'''
    # Cách mang: 4 bước dùng dụng cụ xỏ tất CS100 (ảnh thật của CS100) cho các mẫu không bàn, hở ngón.
    wear_steps = ''
    if p['gift_cs100'] or sku == 'CS100':
        step_list = [('Mang dụng cụ', 'Đặt dụng cụ CS100 vào bàn chân'), ('Xỏ tất', 'Luồn tất qua dụng cụ lên cổ chân'),
                     ('Kéo tất lên', 'Kéo tất lên bắp chân nhẹ nhàng'), ('Rút qua đầu hở', 'Rút dụng cụ ra qua đầu hở')]
        wear_steps = '<ol class="pd-wear">' + ''.join(
            f'<li><figure><img src="/assets/trang-2026/cs100-buoc-{i}.webp" alt="{escape(d)}" width="442" height="322" loading="lazy" decoding="async" /><span>{i}</span></figure><b>{t}</b></li>'
            for i, (t, d) in enumerate(step_list, 1)) + '</ol>'
    wear_panel = f'''
          <h2 class="pd-h2" id="pd-wear-title">Cách mang</h2>
          {wear_steps}
          {notice}
          <details class="pd-xem-them">
            <summary>Cách sử dụng và lưu ý khi dùng</summary>
            <div class="pd-more">{''.join(cards.get(c, '') for c in ('usage', 'caution'))}
            </div>
          </details>'''
    care_panel = f'''
          <h2 class="pd-h2">Giặt và bảo quản</h2>
          <div class="pd-more">{cards.get('care', '')}
          </div>'''
    exchange_panel = f'''
          <h2 class="pd-h2">Đổi trả</h2>
          <div class="pd-more">{cards.get('exchange', '')}{cards.get('gift', '')}
          </div>'''
    panel_spec = [
        ('pd-mo-ta', 'Mô tả', desc_panel),
        ('pd-size', 'Bảng size', size_section),
        ('pd-cach-mang', 'Cách mang', wear_panel if (wear_steps or 'usage' in cards or 'caution' in cards) else ''),
        ('pd-giat', 'Giặt và bảo quản', care_panel if 'care' in cards else ''),
        ('pd-doi-tra', 'Đổi trả', exchange_panel if ('exchange' in cards or 'gift' in cards) else ''),
    ]
    panel_spec = [x for x in panel_spec if x[2].strip()]
    tabs = ''.join(
        f'<button class="pd-tab" type="button" role="tab" id="{pid}-tab" aria-controls="{pid}" aria-selected="{"true" if i == 0 else "false"}"{"" if i == 0 else " tabindex=\"-1\""}>{label}</button>'
        for i, (pid, label, _) in enumerate(panel_spec))
    panels = ''.join(
        f'''
          <div class="pd-panel{' is-active' if i == 0 else ''}" id="{pid}" role="tabpanel" aria-labelledby="{pid}-tab" tabindex="0">{body}
          </div>'''
        for i, (pid, _, body) in enumerate(panel_spec))
    SVC = {
        'swap': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 7v5h-5" /><path d="M4 17v-5h5" /><path d="M18.6 9A7 7 0 0 0 6.4 6.1L4 8.5" /><path d="M5.4 15A7 7 0 0 0 17.6 17.9L20 15.5" /></svg>',
        'truck': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h11v10H3z" /><path d="M14 9h4l3 4v3h-7z" /><circle cx="7" cy="18" r="2" /><circle cx="17" cy="18" r="2" /></svg>',
        'gift': '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="8" width="18" height="5" rx="1" /><path d="M5 13v8h14v-8M12 8v13" /><path d="M12 8c-2-4-6-4-6-1s6 1 6 1Zm0 0c2-4 6-4 6-1s-6 1-6 1Z" /></svg>',
        'chat': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12Z" /></svg>',
    }
    services = [('swap', 'Đổi trả 15 ngày'), ('truck', 'Giao hàng toàn quốc')]
    services.append(('gift', 'Tặng kèm dụng cụ xỏ tất CS100') if p['gift_cs100'] else ('chat', 'Tư vấn size qua Zalo'))
    service_row = ''.join(f'<li{" class=\"pd-gift\"" if i == "gift" else ""}>{SVC[i]}<span>{t}</span></li>' for i, t in services)
    related = ''.join(
        f'''
            <article class="pd-rcard">
              <a class="pd-rcard__media" href="{r["url"]}" tabindex="-1" aria-hidden="true"><img src="{r["gallery"][0]["medium"].replace("-640", "-320")}" alt="" width="320" height="320" loading="lazy" decoding="async" /></a>
              <div>
                <h3><a href="{r["url"]}">{escape(r["name"])}</a></h3>
                <span class="pd-rcard__sku">{r["sku"]}</span>
                <p class="pd-rcard__price">{vnd(r["price"])}</p>
                <a class="t-btn t-btn--outline t-btn--small" href="{r["url"]}">Xem chi tiết</a>
              </div>
            </article>''' for r in p['related'])
    reviews = ''.join(
        f'''
            <figure class="pd-review">
              <figcaption><span aria-hidden="true">“</span>Khách hàng trên Shopee</figcaption>
              <a href="/assets/reviews/review-shopee-0{i}.png" target="_blank" rel="noopener" aria-label="Xem ảnh đánh giá {i} cỡ lớn"><img src="/assets/reviews/review-shopee-0{i}-800.webp" srcset="/assets/reviews/review-shopee-0{i}-480.webp 480w, /assets/reviews/review-shopee-0{i}-800.webp 800w" sizes="(max-width: 860px) calc(100vw - 72px), 760px" alt="Đánh giá của khách hàng trên Shopee Comfycare" width="480" height="{h}" loading="lazy" decoding="async" /></a>
            </figure>''' for i, h in ((1, 147), (2, 160), (3, 151)))

    return f'''<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{escape(title)}</title>
    <meta name="description" content="{escape(description)}" />
    <link rel="canonical" href="https://comfycare.vn{p["url"]}" />
    {og_block(title, description, "https://comfycare.vn" + p["url"], f"/assets/og/{sku.lower()}.jpg", "product")}
    <link rel="icon" type="image/webp" href="/assets/logo/comfycare-logo-64.webp" />
    <script>document.documentElement.classList.add('js')</script>
    <link rel="preload" href="/assets/fonts/be-vietnam-pro-400-latin.woff2" as="font" type="font/woff2" crossorigin />
    <link rel="preload" href="/assets/fonts/be-vietnam-pro-400-vietnamese.woff2" as="font" type="font/woff2" crossorigin />
    <link rel="preload" href="/assets/fonts/be-vietnam-pro-700-latin.woff2" as="font" type="font/woff2" crossorigin />
    <link rel="preload" href="/assets/fonts/be-vietnam-pro-700-vietnamese.woff2" as="font" type="font/woff2" crossorigin />
    {head["styles"]}
    <link rel="stylesheet" href="/theme-2026.css?v={theme_version}" />
    <link rel="stylesheet" href="/product-detail.css?v={css_version}" />
    {head["site"]}
    <script src="/product-detail.js?v={js_version}" defer></script>
    <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
    {head["pixel"]}
    {head["chatbot"]}
  </head>
  <body class="t26 info-page product-detail-page" data-base-path="/" data-current-path="{p["category_route"]}" data-sku="{sku}">
    <div data-site-header></div>

    <main class="content-page" id="top">
      <section class="pd-hero">
        <div class="container">
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <a href="/">Trang chủ</a>
            <span aria-hidden="true">/</span>
            <a href="/{p["category_route"]}/">{escape(p["category_label"])}</a>
            <span aria-hidden="true">/</span>
            <span aria-current="page">{name}</span>
          </nav>
          <div class="pd-hero__grid">
            {gallery_html}
            <div class="pd-summary">
              <span class="pd-cat">{escape(p["category_label"])}</span>
              <h1>{name}</h1>
              <p class="pd-sku">{sku}</p>
              <p class="pd-price"><strong>{vnd(p["price"])}</strong><small>Giá cho 1 {unit}{' (2 chiếc)' if unit == 'đôi' else ''}, đã gồm VAT</small></p>
              {pressure}
              {scope}
              <form class="pd-options" aria-label="Chọn phân loại" onsubmit="return false">
                {color_field}
                {size_field}
                <div class="pd-field pd-field--qty">
                  <label for="pd-qty">Số lượng</label>
                  <div class="pd-stepper">
                    <button type="button" data-qty="-1" aria-label="Giảm số lượng">−</button>
                    <input id="pd-qty" class="pd-qty" type="number" name="qty" min="1" max="20" value="1" inputmode="numeric" />
                    <button type="button" data-qty="1" aria-label="Tăng số lượng">+</button>
                  </div>
                </div>
              </form>
              <div class="pd-actions">
                <button class="btn pd-web-buy" type="button" disabled aria-describedby="pd-web-note">Mua ngay</button>
                <button class="btn pd-web-add" type="button" disabled>Thêm vào giỏ</button>
              </div>
              <p class="pd-muted" id="pd-web-note" hidden></p>
              <a class="pd-zalo" href="{ZALO}" target="_blank" rel="noopener noreferrer"><img src="/assets/icons/mxh-zalo.svg" alt="" width="36" height="36" />{'Gửi số đo, nhờ tư vấn size qua Zalo' if p['sizes'] else 'Cần tư vấn? Nhắn Zalo'}</a>
              <ul class="pd-services">{service_row}</ul>
              {'<p class="pd-cert">Thuộc công bố tiêu chuẩn: 9 mẫu tất y tế cấp 2, cỡ S–XXL</p>' if p['has_byt'] else ''}
              <p class="pd-shopee">{promo.replace('<p class="pd-muted">', '').replace('.</p>', '')}, áp dụng khi đặt trên website và tại <a href="{p["shopee_url"]}" target="_blank" rel="noopener noreferrer">gian hàng Shopee chính hãng</a>.</p>
            </div>
          </div>
        </div>
      </section>

      <section class="pd-details" aria-label="Chi tiết sản phẩm" data-tabs>
        <div class="pd-tabs">
          <div class="container" role="tablist" aria-label="Chi tiết sản phẩm">{tabs}</div>
        </div>
        <div class="container">{panels}
        </div>
      </section>

      <section class="pd-related" aria-labelledby="pd-related-title">
        <div class="container">
          <h2 class="pd-h2" id="pd-related-title">Sản phẩm liên quan</h2>
          <div class="pd-related__grid">{related}
          </div>
          <div class="pd-reviews">
            <h2>Lắng nghe để đồng hành tốt hơn</h2>
            <div class="pd-reviews__grid">{reviews}
            </div>
          </div>
        </div>
      </section>

      <section class="t-cta" aria-label="Tư vấn qua Zalo">
        <div class="container t-cta__inner">
          <img class="t-cta__avatar" src="/assets/home-2026/tu-van-240.webp" alt="" width="240" height="240" loading="lazy" decoding="async" />
          <div>
            <h2>Cùng tìm đôi tất vừa ý</h2>
            <p>{cta}</p>
          </div>
          <a class="t-btn t-btn--cta" href="{ZALO}" target="_blank" rel="noopener noreferrer">{SVC['chat']}Nhắn Zalo 0848 621 092</a>
        </div>
      </section>
    </main>

    <div data-site-footer></div>

</body>
</html>
'''


def update_sitemap(skus):
    path = ROOT / 'sitemap.xml'
    xml = read(path)
    xml = re.sub(r'\s*<url>\s*<loc>https://comfycare\.vn/san-pham/cs\d+/</loc>\s*</url>', '', xml)
    entries = ''.join(f'\n  <url>\n    <loc>https://comfycare.vn/san-pham/{s.lower()}/</loc>\n  </url>' for s in skus)
    xml = xml.replace('\n</urlset>', entries + '\n</urlset>')
    path.write_text(xml, encoding='utf-8')


products = build_products()
out = ROOT / 'data' / 'products.json'
out.parent.mkdir(exist_ok=True)
payload = {'note': 'Sinh tự động bởi scripts/build-products.py từ brain; sửa nguồn rồi chạy lại.',
           'shipping': {'fee': 25000, 'free_from': 300000},
           'products': list(products.values())}
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

version = lambda name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()[:12]
css_version, js_version = version('product-detail.css'), version('product-detail.js')
theme_version = version('theme-2026.css')
head = head_parts()
for sku in PAGE_SKUS:
    p = products[sku]
    # Sản phẩm liên quan: 3 mã cùng nhóm theo thứ tự PAGE_SKUS; phụ kiện gợi ý dòng tất y tế.
    group = 'c2-y-te' if p['group'] == 'phu-kien' else p['group']
    pool = [s for s in PAGE_SKUS if s != sku and products[s]['group'] == group]
    p['related'] = [products[s] for s in (pool + [s for s in PAGE_SKUS if s != sku and s not in pool])[:3]]
    page = ROOT / 'san-pham' / sku.lower() / 'index.html'
    page.parent.mkdir(exist_ok=True)
    page.write_text(render_page(p, head, css_version, js_version, theme_version), encoding='utf-8')
    del p['related']
update_sitemap(PAGE_SKUS)
print({'products': len(products), 'pages': PAGE_SKUS, 'gallery': {s: len(products[s]['gallery']) for s in PAGE_SKUS},
       'css_version': css_version, 'js_version': js_version})
