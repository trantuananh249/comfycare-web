"""Thẻ Open Graph/Twitter dùng chung: build-products.py (trang chi tiết) và build-og.py (các trang còn lại).

Ảnh xem trước nằm ở assets/og/ (JPG 1200×630, Zalo/Facebook/Messenger đọc được), sinh bằng build-og.py.
"""
from html import escape
import re

SITE_URL = 'https://comfycare.vn'
DEFAULT_IMAGE = '/assets/og/comfycare.jpg'
START, END = '<!-- og:start -->', '<!-- og:end -->'


def og_block(title, description, url, image=DEFAULT_IMAGE, kind='website', indent='    '):
    image_url = SITE_URL + image
    tags = [
        ('property', 'og:type', kind),
        ('property', 'og:site_name', 'Comfycare'),
        ('property', 'og:locale', 'vi_VN'),
        ('property', 'og:title', title),
        ('property', 'og:description', description),
        ('property', 'og:url', url),
        ('property', 'og:image', image_url),
        ('property', 'og:image:width', '1200'),
        ('property', 'og:image:height', '630'),
        ('property', 'og:image:alt', title),
        ('name', 'twitter:card', 'summary_large_image'),
    ]
    lines = [START] + [f'<meta {a}="{k}" content="{escape(v)}" />' for a, k, v in tags] + [END]
    return ('\n' + indent).join(lines)


def strip_block(html):
    return re.sub(r'\n?[ \t]*' + re.escape(START) + r'.*?' + re.escape(END), '', html, flags=re.S)
