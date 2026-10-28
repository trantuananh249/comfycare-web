"""Đường dẫn tới workspace Comfycare (repo comfycare-workspace): brain và tài liệu dự án nằm ngoài repo website."""
import os
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
# Đặt biến môi trường COMFYCARE_WORKSPACE nếu workspace ở chỗ khác (máy khác, đổi tên thư mục).
WORKSPACE = Path(os.environ.get('COMFYCARE_WORKSPACE', r'C:\Users\mrtua\workspace'))
BRAIN = WORKSPACE / 'brain'
BRAIN_DB = BRAIN / 'brain.db'
KNOWLEDGE = BRAIN / 'knowledge'
CONTENT = BRAIN / 'content'
MASTER_SPEC = BRAIN / 'source' / 'Comfycare_Master_Spec_v3.2_2026-10-10.md'
PROJECT_DOCS = WORKSPACE / 'projects' / 'website-comfycare'
QA_BASELINES = PROJECT_DOCS / 'qa-baselines'

if not BRAIN_DB.exists():
    raise SystemExit(f'Không thấy {BRAIN_DB}. Đặt COMFYCARE_WORKSPACE trỏ tới thư mục workspace Comfycare.')
