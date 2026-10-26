"""Sinh data/dvhc-2025.json: 34 tỉnh/thành và 3.321 phường/xã/đặc khu sau sắp xếp đơn vị hành chính (hiệu lực 01/07/2025,
bảng danh mục kèm Quyết định 19/2025/QĐ-TTg). Dùng cho ô chọn tỉnh → phường/xã ở trang thanh toán và để API kiểm tra địa chỉ.

Chạy: python scripts/build-dvhc.py <file JSON nguồn>
Nguồn đã dùng (26/10/2026): https://provinces.open-api.vn/api/v2/?depth=2 (tải về, không gọi lúc chạy web).
Script dừng nếu số lượng khác 34 tỉnh / 3.321 xã (687 phường, 2.621 xã, 13 đặc khu) hoặc trùng tên trong một tỉnh.
Sau khi chạy: đồng bộ sang API bằng `node scripts/sync-products.mjs` trong repo comfycare-api.
"""
import collections
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))

provinces = []
for p in source:
    wards = [w['name'] for w in p['wards']]
    assert len(wards) == len(set(wards)), f"Trùng tên phường/xã trong {p['name']}"
    short = p['name'].removeprefix('Thành phố ').removeprefix('Tỉnh ')
    provinces.append({'code': f"{int(p['code']):02d}", 'name': p['name'], 'short': short, 'wards': wards})

types = collections.Counter(w['division_type'] for p in source for w in p['wards'])
assert len(provinces) == 34, len(provinces)
assert sum(len(p['wards']) for p in provinces) == 3321
assert types == {'xã': 2621, 'phường': 687, 'đặc khu': 13}, types

out = {
    'note': 'Sinh bởi scripts/build-dvhc.py; không sửa tay. 34 tỉnh/thành, 3.321 đơn vị cấp xã, hiệu lực 01/07/2025 (Quyết định 19/2025/QĐ-TTg).',
    'source': 'provinces.open-api.vn API v2, tải 26/10/2026',
    'provinces': provinces,
}
(root / 'data' / 'dvhc-2025.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
print({'provinces': len(provinces), 'wards': sum(len(p['wards']) for p in provinces), 'types': dict(types)})
