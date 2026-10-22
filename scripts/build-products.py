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
import re
import struct

from workspace_paths import SITE as ROOT, KNOWLEDGE, CONTENT

# Trang chi tiết: mẫu CS22 được duyệt 22/10/2026, áp dụng cho cả 19 mã (kế hoạch 09, bước 2).
PAGE_SKUS = ['CS21', 'CS22', 'CS23', 'CS24', 'CS26', 'CS27', 'CS33', 'CS34', 'CS35',
             'CS25', 'CS28', 'CS29', 'CS30', 'CS31', 'CS11', 'CS12', 'CS14', 'CS110', 'CS100']
# Ảnh sàn không đưa lên web vì trái brain: CS14 ảnh 5 chọn size theo cân nặng (F.7: CS14 chỉ theo chu vi đùi A).
GALLERY_SKIP = {'CS14': {5}}
# Ảnh trong gallery có bảng size + vị trí đo, dùng làm hình minh họa ở khối chọn size (dòng y tế dùng measure-leg).
SIZE_FIGURE = {'CS25': 8, 'CS28': 9, 'CS29': 9, 'CS30': 8, 'CS31': 9, 'CS11': 3, 'CS12': 3, 'CS110': 4}
# Số đo cần lấy theo F.3–F.7 cho mã ngoài dòng y tế: (các bước, ghi chú).
MEASURE = {
    'CS25': (['Size giày đang đi'], ''),
    'CS28': (['Chu vi đùi, đo cách gối 10 cm', 'Cân nặng, chỉ để tham khảo khi chưa đo được'], ''),
    'CS29': (['Chu vi cổ tay'], ''),
    'CS30': (['Chu vi cổ tay'], ''),
    'CS31': (['Chu vi khuỷu tay'], ''),
    'CS11': (['Chu vi bắp chân: cỡ S/M dưới 35 cm', 'Cân nặng tham khảo: dưới 55 kg'], 'CS11 chỉ có một cỡ S/M.'),
    'CS12': (['Size giày: cỡ S/M cho giày 36–40'], 'Đi giày trên size 40: xem <a class="pd-link" href="/san-pham/cs25/">Tất Bàn Chân Cấp 2 (CS25)</a>.'),
    'CS14': (['Chu vi đùi tại vị trí A, phần trên gối'], 'Không chọn CS14 theo cân nặng. Chu vi đùi tại A trên 52 cm hiện chưa có size phù hợp.'),
    'CS110': (['Giới tính và cân nặng (bảng tham khảo)'], 'Cân nặng ngoài khoảng trong bảng: nhắn Comfycare để kiểm tra số đo thực tế trước khi mua.'),
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
    'CS14': '29406484639', 'CS110': '29484186147', 'CS100': '28706085493',
}
SHOP_ID = '1268125014'
ZALO = 'https://zalo.me/0848621092'
BYT_NUMBER = '250000052/PCBA-HP'
# F.1–F.7: các cỡ đang bán. CS11, CS12 chỉ một cỡ S/M; CS14, CS110 có S/M và L/XL.
FULL_SIZES = ['S', 'M', 'L', 'XL', 'XXL']
SIZES = {'CS11': ['S/M'], 'CS12': ['S/M'], 'CS14': ['S/M', 'L/XL'], 'CS110': ['S/M', 'L/XL'], 'CS100': []}
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
# J.1, rút gọn. Không đưa các dòng claim nhạy cảm (DVT, sau phẫu thuật) lên trang bán hàng.
AUDIENCE = {
    'c2-y-te': ['Người phải đứng lâu, đi lại nhiều: giáo viên, bán hàng, tài xế, y tá, lễ tân',
                'Phụ nữ sau sinh có dấu hiệu suy giãn tĩnh mạch',
                'Người trung niên, cao tuổi hay đau mỏi, nặng chân vào cuối ngày',
                'Người đã được chẩn đoán suy giãn tĩnh mạch chân'],
    'c2-the-thao': ['Người chơi thể thao cần ổn định khớp, cơ',
                    'Người đau mỏi khớp gối, khuỷu tay, cổ tay nhẹ, chưa đến mức cần điều trị',
                    'Người tập gym, chạy bộ, leo núi, tennis, cầu lông'],
    'c1': ['Người muốn phòng ngừa từ sớm',
           'Người chơi thể thao cường độ vừa',
           'Người đứng, ngồi lâu nhưng chưa có triệu chứng'],
}
# J.2, J.3.
CAUTIONS = [
    'Không dùng khi vùng đeo có vết thương hở, viêm nhiễm da hoặc viêm mô tế bào.',
    'Không dùng nếu dị ứng Nylon, Polyester hoặc Spandex.',
    'Có bệnh tim mạch, tuần hoàn nặng, đang mang thai, tiểu đường, sau phẫu thuật hoặc dùng thuốc chống đông: hỏi bác sĩ trước khi dùng.',
    'Nếu đau, tê, lạnh, đổi màu da hoặc tổn thương da khi mang: ngừng mang và hỏi ý kiến bác sĩ.',
]


def read(path):
    return path.read_text(encoding='utf-8-sig')


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
    assert len(products) == 19, 'Danh mục phải có 19 mã đang bán'
    assert set(products) == set(SHOPEE), 'SHOPEE thiếu/thừa mã so với catalog'
    tables = parse_sizes()
    for sku, p in products.items():
        p.update(parse_content(sku))
        p['has_byt'] = p['group'] == 'c2-y-te'
        # D.6: tất quần bán theo chiếc; CS100 theo chiếc; còn lại theo đôi.
        p['unit'] = 'chiếc' if sku in ('CS33', 'CS34', 'CS35', 'CS100') else 'đôi'
        p['colors'] = [] if sku == 'CS100' else ['Da', 'Đen']  # D.7; CS100 chưa có biến thể màu.
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
        'site': pick(r'<script src="/site\.min\.js\?v=\w+" defer></script>'),
        'pixel': pick(r'<!-- Meta Pixel Code -->.*?<!-- End Meta Pixel Code -->'),
        'chatbot': pick(r'<link rel="stylesheet" href="/chatbot\.css[^>]+>\s*<script defer src="/chatbot\.js[^>]+></script>'),
    }


def size_table_html(p):
    header, rows = p['size_table']['header'], p['size_table']['rows']
    th = ''.join(f'<th scope="col">{escape(h)}</th>' for h in header)
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


def render_page(p, head, css_version, js_version):
    sku, name, unit = p['sku'], escape(p['name']), p['unit']
    badge = (f'<span class="catalog-badge">BYT {BYT_NUMBER}</span>' if p['has_byt']
             else f'<span class="catalog-badge catalog-badge--warm">{escape(p["category_label"])}</span>')
    title = f'{p["name"]} {sku} | Comfycare'
    description = f'{p["name"]} ({sku}) Comfycare, {p["category_label"].lower()}'
    description += f', áp lực {p["pressure"]}' if p['pressure'] else ''
    description += f'. Giá bán lẻ {vnd(p["price"])}/{unit}, đã gồm VAT. Bảng size, cách chọn size và mua trên Shopee.'
    pressure = f'<p class="pd-pressure">Áp lực {p["pressure"]}</p>' if p['pressure'] else ''
    gift = ('''<p class="pd-gift"><strong>Tặng kèm</strong> dụng cụ hỗ trợ xỏ tất CS100 (dạng miếng vải polyester).</p>'''
            if p['gift_cs100'] else '')
    scope = ('<p class="pd-scope">Sản phẩm thể thao, không thuộc danh mục công bố thiết bị y tế.</p>'
             if p['group'] in ('c2-the-thao', 'c1') else '')
    if p['group'] == 'phu-kien':
        # D.5: dụng cụ không xỏ vừa tất kín bàn.
        scope = '<p class="pd-scope">Dùng cho các mẫu tất không bàn và hở ngón; không dùng được với tất kín bàn (CS26, CS27, CS35).</p>'

    def options(field, values):
        return ''.join(
            f'<label class="pd-chip"><input type="radio" name="{field}" value="{escape(v)}" /><span>{escape(v)}</span></label>'
            for v in values)
    size_field = ''
    if p['sizes']:
        guide = ('<a class="pd-link" href="#pd-size">Cách đo và bảng size</a>' if p['size_table'] else '')
        size_field = f'''<fieldset class="pd-field">
                  <legend>Size {guide}</legend>
                  <div class="pd-chips">{options("size", p["sizes"])}</div>
                </fieldset>'''
    color_field = (f'''<fieldset class="pd-field">
                  <legend>Màu</legend>
                  <div class="pd-chips">{options("color", p["colors"])}</div>
                </fieldset>''' if p['colors'] else '')

    facts = [('Mã', sku), ('Dòng', p['category_label']), ('Kiểu dáng', p['style'])]
    if p['pressure']:
        facts.append(('Áp lực', p['pressure']))
    if p['material']:
        facts.append(('Chất liệu', p['material']))
    facts.append(('Đơn vị bán', f'1 {unit}' + (' (2 chiếc)' if unit == 'đôi' else '')))
    if p['colors']:
        facts.append(('Màu', ', '.join(p['colors'])))
    if p['sizes']:
        facts.append(('Size', ', '.join(p['sizes'])))
    fact_rows = '\n'.join(f'                <div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>' for k, v in facts)
    if p['has_byt']:
        fact_rows += (f'\n                <div><dt>Công bố</dt><dd>Công bố tiêu chuẩn áp dụng {BYT_NUMBER} tại Sở Y tế Hải Phòng, '
                      f'size S–XXL. <a href="/chung-nhan/">Xem hồ sơ</a></dd></div>')

    size_section = ''
    if p['size_table']:
        figure, measures = '', ''
        if p['group'] == 'c2-y-te':
            # F.1: cB mắt cá, cC bắp chân (vùng to nhất), cG đùi (vùng to nhất, sát bẹn).
            steps = [('cB', 'Chu vi mắt cá chân'), ('cC', 'Chu vi bắp chân, chỗ to nhất')]
            if sku not in LEG_ONLY:
                steps.append(('cG', 'Chu vi đùi, chỗ to nhất sát bẹn'))
            items = ''.join(f'<li><span class="pd-measure-key">{k}</span>{v}</li>' for k, v in steps)
            note = ('<p class="pd-muted">Tất ống chân chỉ cần cB và cC, không cần đo đùi (cG).</p>'
                    if sku in LEG_ONLY else '')
            measures = f'''<p class="pd-size__need">{sku} cần <strong>{len(steps)} số đo</strong>:</p>
                <ol class="pd-measure">{items}</ol>
                {note}'''
            figure = '''<figure class="pd-size__figure pd-size__figure--wide">
                <img src="/assets/size-guide/measure-leg-800.webp" srcset="/assets/size-guide/measure-leg-480.webp 480w, /assets/size-guide/measure-leg-800.webp 800w, /assets/size-guide/measure-leg.webp 1448w" sizes="(max-width: 900px) calc(100vw - 32px), 560px" alt="Minh họa vị trí đo cB (mắt cá), cC (bắp chân), cG (đùi)" width="1448" height="1086" loading="lazy" decoding="async" />
              </figure>'''
        elif sku in MEASURE:
            steps, note = MEASURE[sku]
            items = ''.join(f'<li><span class="pd-measure-key">{i}</span>{escape(s)}</li>' for i, s in enumerate(steps, 1))
            measures = f'''<p class="pd-size__need">{sku} chọn size theo:</p>
                <ol class="pd-measure">{items}</ol>''' + (f'\n                <p class="pd-muted">{note}</p>' if note else '')
            g = next((g for g in p['gallery'] if g.get('n') == SIZE_FIGURE.get(sku)), None)
            if g:
                figure = f'''<figure class="pd-size__figure pd-size__figure--square">
                <img src="{g["medium"]}" srcset="{g["medium"]} 640w, {g["src"]} {g["width"]}w" sizes="(max-width: 900px) calc(100vw - 32px), 560px" alt="Hướng dẫn chọn size {name}" width="{g["width"]}" height="{g["height"]}" loading="lazy" decoding="async" />
              </figure>'''
        size_section = f'''
      <section class="pd-size" id="pd-size" aria-labelledby="pd-size-title">
        <div class="container">
          <h2 id="pd-size-title">Cách đo và chọn size</h2>
          <div class="pd-size__grid{'' if figure or measures else ' pd-size__grid--single'}">
            <div class="pd-size__how">
              {figure}
              {measures}
            </div>
            <div class="pd-size__chart">
              <p class="pd-size__label">Đối chiếu số đo với bảng (cm)</p>
              {size_table_html(p)}
              <p class="pd-muted">Số đo nằm giữa hai size hoặc chạm ranh giới: nhắn Comfycare để được kiểm tra, không tự chọn nhỏ hơn để tăng áp lực.</p>
              <div class="pd-size__links">
                <a class="btn btn--secondary btn--small" href="{ZALO}" target="_blank" rel="noopener noreferrer">Gửi số đo qua Zalo</a>
                <a class="pd-link" href="{p["size_guide_url"]}">Hướng dẫn chọn size đầy đủ</a>
              </div>
            </div>
          </div>
        </div>
      </section>'''

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

    audience = AUDIENCE.get(p['group'])
    audience_html = ''
    if audience:
        items = ''.join(f'<li>{escape(a)}</li>' for a in audience)
        audience_html = f'''
          <section class="pd-card" aria-labelledby="pd-audience-title">
            <h2 id="pd-audience-title">Phù hợp với ai</h2>
            <ul class="pd-list">{items}</ul>
          </section>'''
    cautions = ''
    if p['group'] != 'phu-kien':
        items = ''.join(f'<li>{escape(c)}</li>' for c in CAUTIONS)
        cautions = f'''
          <section class="pd-card pd-card--warn" aria-labelledby="pd-caution-title">
            <h2 id="pd-caution-title">Lưu ý khi dùng</h2>
            <ul class="pd-list">{items}</ul>
            <p class="pd-muted">Sản phẩm hỗ trợ, không thay thế chỉ định của bác sĩ. <a class="pd-link" href="/huong-dan-su-dung/">Cách mang và bảo quản</a></p>
          </section>'''
    cta = (f'Gửi mã {sku} và số đo qua Zalo, Comfycare chọn size cùng anh/chị.' if p['sizes']
           else 'Gửi mã tất đang dùng qua Zalo, Comfycare kiểm tra dụng cụ có phù hợp không.')

    schema = {
        '@context': 'https://schema.org', '@type': 'Product', 'name': p['name'], 'sku': sku,
        'image': [f'https://comfycare.vn{g["src"]}' for g in p['gallery']], 'description': p['description'],
        'brand': {'@type': 'Brand', 'name': 'Comfycare'},
        'offers': {'@type': 'Offer', 'price': p['price'], 'priceCurrency': 'VND',
                   'url': f'https://comfycare.vn{p["url"]}'},
    }

    return f'''<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{escape(title)}</title>
    <meta name="description" content="{escape(description)}" />
    <link rel="canonical" href="https://comfycare.vn{p["url"]}" />
    <link rel="icon" type="image/webp" href="/assets/logo/comfycare-logo-64.webp" />
    {head["styles"]}
    <link rel="stylesheet" href="/product-detail.css?v={css_version}" />
    {head["site"]}
    <script src="/product-detail.js?v={js_version}" defer></script>
    <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
    {head["pixel"]}
    {head["chatbot"]}
  </head>
  <body class="info-page product-detail-page" data-base-path="/" data-current-path="{p["category_route"]}" data-sku="{sku}">
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
              <div class="pd-badges">{badge}<span class="sku">{sku}</span></div>
              <h1>{name}</h1>
              {pressure}
              <p class="pd-lead">{escape(p["description"])}</p>
              {scope}
              <div class="pd-price">
                <strong>{vnd(p["price"])}</strong><span>/ {unit}</span>
                <small>Giá bán lẻ, đã gồm VAT. Giá trên Shopee có thể khác tùy phân loại và voucher.</small>
              </div>
              {gift}
              <form class="pd-options" aria-label="Chọn phân loại" onsubmit="return false">
                {size_field}
                {color_field}
                <div class="pd-field">
                  <label for="pd-qty">Số lượng</label>
                  <input id="pd-qty" class="pd-qty" type="number" name="qty" min="1" max="20" value="1" inputmode="numeric" />
                </div>
              </form>
              <div class="pd-actions">
                <a class="btn btn--primary" href="{p["shopee_url"]}" target="_blank" rel="noopener noreferrer">Mua trên Shopee</a>
                <button class="btn pd-web-buy" type="button" disabled aria-describedby="pd-web-note">Mua ngay <span class="pd-soon">Sắp ra mắt</span></button>
              </div>
              <p class="pd-muted" id="pd-web-note">Đặt mua trực tiếp trên website đang được chuẩn bị. Trong lúc chờ, anh/chị mua trên Shopee hoặc nhắn Zalo để được tư vấn.</p>
              <a class="pd-zalo" href="{ZALO}" target="_blank" rel="noopener noreferrer">{'Cần tư vấn size? Nhắn Zalo' if p['sizes'] else 'Cần tư vấn? Nhắn Zalo'}</a>
            </div>
          </div>
        </div>
      </section>
{size_section}

      <section class="pd-details">
        <div class="container pd-details__grid">
          <section class="pd-card" aria-labelledby="pd-info-title">
            <h2 id="pd-info-title">Thông tin sản phẩm</h2>
            <dl class="pd-facts">
{fact_rows}
            </dl>
          </section>
{audience_html}{cautions}
          <section class="pd-card" aria-labelledby="pd-exchange-title">
            <h2 id="pd-exchange-title">Mang chưa vừa?</h2>
            <p>Comfycare tư vấn size trước khi mua, hướng dẫn cách mang và hỗ trợ đổi nếu nhận về chưa vừa.</p>
            <p><a class="pd-link" href="/chinh-sach-doi-tra/">Xem chính sách đổi trả</a></p>
          </section>
        </div>
      </section>

      <section class="page-cta">
        <div class="container page-cta__inner">
          <div>
            <p class="eyebrow">Cần tư vấn thêm?</p>
            <h2>{cta}</h2>
          </div>
          <a class="btn btn--primary" href="{ZALO}" target="_blank" rel="noopener noreferrer">Tư vấn qua Zalo</a>
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
head = head_parts()
for sku in PAGE_SKUS:
    page = ROOT / 'san-pham' / sku.lower() / 'index.html'
    page.parent.mkdir(exist_ok=True)
    page.write_text(render_page(products[sku], head, css_version, js_version), encoding='utf-8')
update_sitemap(PAGE_SKUS)
print({'products': len(products), 'pages': PAGE_SKUS, 'gallery': {s: len(products[s]['gallery']) for s in PAGE_SKUS},
       'css_version': css_version, 'js_version': js_version})
