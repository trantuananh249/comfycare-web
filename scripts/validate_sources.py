"""Read-only checks: approved database -> shared knowledge -> data -> website."""
from pathlib import Path
import re
import sqlite3
from urllib.parse import unquote

from workspace_paths import SITE as PROJECT, BRAIN, BRAIN_DB, KNOWLEDGE, CONTENT, MASTER_SPEC
# Nguồn duy nhất: Tuấn Anh Workspace/brain/brain.db
issues = []
def check(condition, message):
    if not condition:
        issues.append(message)
def read(path):
    return path.read_text(encoding='utf-8-sig')
check(not (PROJECT / 'brain.db').exists(), 'Duplicate brain.db in website repo')
db = sqlite3.connect(BRAIN_DB.as_uri() + '?mode=ro', uri=True)
records = dict(db.execute('SELECT id,content FROM business'))
check(db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Database integrity')
db.close()
prices = {}
for rid in (10, 11):
    prices.update({sku: retail for sku, retail in re.findall(r'(CS\d+) ([\d.]+) → [\d.]+', records[rid])})
for sku in ('CS11', 'CS12'):
    prices[sku] = re.search(sku + r' ([\d.]+) →', records[12])[1]
prices['CS14'] = prices['CS110'] = re.search(r'CS14 và CS110 ([\d.]+) →', records[12])[1]
prices['CS100'] = re.search(r'CS100: ([\d.]+)', records[12])[1]
catalog = read(KNOWLEDGE/'products/catalog_pricing.md')
master = read(MASTER_SPEC)
# Compare complete price rows, not just a retail number occurring somewhere.
master_catalog = re.search(r'^## D\.[\s\S]*?(?=^## E\.)', master, re.M)[0]
master_rows = re.findall(r'^\| \*\*CS\d+(?: Combo 2)?\*\*[^\n]+', master_catalog, re.M)
for row in master_rows:
    if row.startswith('| **CS100**'):
        continue  # Construction remains an explicitly documented source conflict.
    check(row in catalog, 'Master list/retail/CTV or multi-buy row differs: '+row.split('|')[1])
check(len(master_rows) == 23, 'Master price coverage: 19 products and 4 combos')
size_page = read(PROJECT/'huong-dan-chon-size/index.html')
for sku, expected in [('CS14', ['≤44 cm', '>44–52 cm', 'không chọn CS14 theo cân nặng']),
                      ('CS25', ['| S | ≤35 |', '| XXL | ≥44 |'])]:
    product = read(CONTENT/'products'/f'{sku}.md')
    for value in expected:
        check(value in product, 'Updated size data '+sku+': '+value)
check('Size giày">≤35' in size_page and 'Size giày">≥44' in size_page, 'CS25 web inclusive boundaries')
cs14_rows = re.findall(r'<tr>[^\n]*Áp dụng">CS14</td>[^\n]*</tr>', size_page)
check(len(cs14_rows) == 2 and all('kg' not in row for row in cs14_rows), 'CS14 web must use circumference only')
check('≤44 cm' in size_page and '&gt;44–52 cm' in size_page and 'trên 52 cm' in size_page, 'CS14 web boundaries and unsupported size')
for sku in ('CS11','CS12','CS14','CS110'):
    check('55% Nylon + 35% Polyester + 10% Spandex' in read(CONTENT/'products'/f'{sku}.md'), 'C1 composition: '+sku)
for sku in ('CS33','CS34','CS35'):
    check('Có silicon theo v3.2 J.4' in read(CONTENT/'products'/f'{sku}.md'), 'Silicone: '+sku)
for rel in ('index.html','cau-hoi-thuong-gap/index.html','huong-dan-su-dung/index.html','chatbot.js'):
    page = read(PROJECT/rel)
    check(not any(old in page for old in ('12 giờ', '1–2 giờ/ngày', '1-2 giờ/ngày')), 'Obsolete wear schedule: '+rel)
check('Không gập hoặc cuộn viền' in read(PROJECT/'cau-hoi-thuong-gap/index.html'), 'Cuff folding advice')
check(not (BRAIN/'source'/'Comfycare_Master_Spec_v1.2.md').exists(), 'User-authorized obsolete source removal')
web_prices = {}
for route in ('tat-y-te-cap-2','tat-dai-the-thao-cap-2','tat-the-thao-cap-1','phu-kien'):
    page = read(PROJECT/route/'index.html')
    for sku, amount in re.findall(r'<span class="sku">(CS\d+)</span>[\s\S]*?<strong>([\d.]+)đ</strong>', page):
        check(sku not in web_prices, 'Duplicate product card: '+sku)
        web_prices[sku] = amount
check(set(prices) == set(web_prices), 'Website SKU coverage differs from approved catalog')
for sku, amount in prices.items():
    row = re.search(r'^\| \*\*'+sku+r'\*\*[^\n]+',catalog,re.M)
    check(row is not None and '**'+amount+'đ**' in row[0], 'Shared price: '+sku)
    check('- Giá bán lẻ/TMĐT: **'+amount+'đ**' in read(CONTENT/'products'/f'{sku}.md'), 'Data price: '+sku)
    check(web_prices.get(sku) == amount, 'Website price: '+sku)
returns = read(PROJECT/'chinh-sach-doi-tra/index.html')
check('giảm đi 20%' not in returns, 'Old exchange formula remains')
check('trừ số tiền khách thực trả' in returns and 'bằng chuyển khoản' in returns, 'Exchange/refund wording')
check('ngoài điều kiện chuẩn' in returns and 'lỗi do sử dụng' in returns, 'Flexible exchange wording')
check('giá sản phẩm mới' in returns, 'Exchange price reference')
check('Đai thể thao áp lực hỗ trợ đầu gối' in read(PROJECT/'tat-the-thao-cap-1/index.html'), 'CS14 name')
check('CS32 chưa được xác nhận bán' in read(PROJECT/'chung-nhan/index.html'), 'Separate declaration and sale catalog')
check('chưa có hồ sơ FY2026' in read(PROJECT/'chung-nhan/index.html'), 'FDA date qualification')
check('không gồm dùng thử' in read(PROJECT/'chinh-sach-van-chuyen/index.html'), 'Delivery inspection qualification')
check('111 đường 3C' in read(PROJECT/'layout.js'), 'Footer source address')
registry = read(BRAIN/'source_registry.md')
check('created_at không phải ngày hiệu lực' in registry, 'Approval vs creation date')
check('business 1 |' in registry and 'business 2 |' in registry and registry.count('Mẫu giả lập — đã gỡ khỏi brain.db') == 2, 'Sample record exclusions')
check(1 not in records and 2 not in records, 'Sample records must not be in brain.db')
check('Đề xuất thử nghiệm — chưa áp giá 199.000đ' in registry, 'Experimental price status')
links = 0
for directory in (KNOWLEDGE, CONTENT):
    for file in directory.rglob('*.md'):
        text = read(file)
        check('\ufffd' not in text, 'Invalid Unicode: '+str(file))
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            if re.match(r'[a-z]+:', target):
                continue
            links += 1
            check((file.parent/unquote(target.split('#')[0])).resolve().exists(), 'Broken link: '+str(file)+' -> '+target)
print({'products_checked_across_layers':len(prices),'local_links_checked':links,'issues':issues})
raise SystemExit(bool(issues))
