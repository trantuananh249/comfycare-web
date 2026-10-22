# Công cụ bảo trì

Chạy từ thư mục repo (`C:\Users\mrtua\dev\comfycare-vn-website`). Các script đọc dữ liệu ở workspace OneDrive qua `scripts/workspace_paths.py`; đặt biến `COMFYCARE_WORKSPACE` nếu workspace nằm chỗ khác.

- Kiểm tra asset/link: `python scripts/validate_site.py`.
- Kiểm tra kho nội dung theo brain.db: `python scripts/validate_data.py`. Đọc `brain/brain.db` và `brain/content/` trong workspace; so file với baseline lịch sử `projects/website-comfycare/qa-baselines/data-brain-20261012` (không xóa). Hash brain.db so với `qa-baselines/brain-baseline-20261022d.json` (44 bản ghi, mới nhất business 34). Khi brain.db được duyệt thay đổi, tạo baseline mới bên cạnh và trỏ DB_BASELINE sang, không ghi đè bản cũ.
- Đối chiếu giá/nguồn giữa database, `brain/knowledge`, `brain/content` và HTML: `python scripts/validate_sources.py`.
- Regression nội dung local: `node scripts/test-content-sync.cjs` (Playwright; CHATBOT_TEST_URL mặc định http://127.0.0.1:4183; kết quả mặc định ở outputs/content-latest).
- Tạo ảnh responsive: `python scripts/generate_responsive_images.py` (cần Pillow). Chỉ chạy khi thay ảnh nguồn.
- Chatbot: `python scripts/build-chatbot.py`; nguồn `brain/content/sales_script.md` trong workspace; sau đó `node scripts/test-chatbot.cjs` với Playwright có sẵn.
- Kiểm thử chatbot hỗ trợ CHATBOT_TEST_URL, CHATBOT_TEST_OUTPUT, PLAYWRIGHT_MODULE, CHROME_PATH; mặc định ghi outputs/chatbot-latest.

`outputs/` là kết quả tạm của các lần kiểm tra, không commit, có thể xóa sau mỗi lần publish. Hồ sơ trình duyệt QA dùng thư mục tạm bên ngoài repo. Các công cụ trên không commit/push/deploy.

Đối chiếu v3.2: validate_sources.py kiểm tra thêm 23 dòng giá gồm combo, ranh giới size CS14/CS25, vật liệu C1, silicon và lịch đeo. Checklist người duyệt: `projects/website-comfycare/docs/source_data/master-v32-reconciliation.md` trong workspace.
