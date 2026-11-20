# SenseGraph — Checklist Nộp Bài STEM2Connect (Tiếng Việt)

**Hạn chót chính thức:** **21/11/2026 23:59 EST = 22/11/2026 11:59 sáng giờ Việt Nam (Asia/Ho_Chi_Minh)**  
**Khuyến nghị:** Hoàn tất và nộp trong ngày **21/11 theo giờ Việt Nam** để có khoảng đệm an toàn.

---

## Bước 1: Kiểm tra mã nguồn, CI & bảo mật cục bộ (5 phút)
- [ ] Chạy đầy đủ kiểm thử và lint:
  ```powershell
  cd D:\AI-tools\Project\SenseGraph
  python -m ruff check app tests evaluation
  python -m pytest -v
  python -m evaluation.benchmark --mode dry-run
  ```
  (Kỳ vọng: **All checks passed**, **82 passed**, và dry-run trả về 6 case hợp lệ.)
- [ ] Đảm bảo `.env` **không** được commit lên Git (`git status` không hiện `.env`, không có API key trong code).

## Bước 2: Kiểm tra trực tiếp trên trình duyệt (10–15 phút)
- [ ] Chạy server cục bộ:
  ```powershell
  python -m uvicorn app.main:app --reload
  ```
- [ ] Mở `http://127.0.0.1:8000` trên Chrome/Edge và tự kiểm tra bằng **bàn phím thuần** (`Tab`, `Shift+Tab`, `Enter`, `Space`):
  - [ ] Nhấn `Tab` thấy link **Skip to main content** hiện rõ; các panel ẩn không nằm trong thứ tự Tab.
  - [ ] **Physics:** Mở Physics Circuit -> thử Guided Tour -> Guided Learning Lab -> dự đoán Bulb ON -> chạy thí nghiệm -> Reset.
  - [ ] **Biology:** Mở Biology Food Web -> chọn Rabbit -> Remove Rabbit (đúng 2 liên kết bị xóa + lưu ý không dự đoán tuyệt chủng) -> Reset.
  - [ ] **Evidence-Grounded Tutor:** Hỏi 1 câu trong phạm vi (*"Is there a path from Grass to Fox?"*) và 1 câu ngoài phạm vi (*"Will Fox go extinct?"* -> phải trả về *"Not established by this diagram."*).
  - [ ] **CS / Math / Chemistry:** Chạy Trace ở CS Flowchart, thử điều hướng điểm + Import CSV ở Math Plot, thử SMILES hợp lệ (`O=C=O`) và không hợp lệ (`c1ccccc1`) ở Chemistry.
  - [ ] Kiểm tra zoom trình duyệt **200%** không bị vỡ bố cục và mở DevTools Console xác nhận **0 lỗi console / 0 lỗi 404**.
  - [ ] *(Tùy chọn nếu có NVDA trên Windows)*: mở NVDA nghe thử `role="status"` và ghi nhận thực tế vào `docs/USER_STUDY_PROTOCOL.md`.

## Bước 3: Thử Gemini Vision thật (tùy chọn nếu có `GEMINI_API_KEY`)
- [ ] Tạo `.env` từ `.env.example`, điền `AI_PROVIDER=gemini` và `GEMINI_API_KEY=...`, khởi động lại `uvicorn`.
- [ ] Tải lên `fixtures/images/physics_series.png` và `fixtures/images/biology_food_web.png`, tick đồng ý consent, xem màn hình **Review AI-Generated Diagram**, sửa nếu cần -> **Validate** -> **Confirm** -> chạy thí nghiệm.
- [ ] Chạy `python -m evaluation.benchmark --mode live` và ghi nhận kết quả thực tế vào `docs/EXTRACTION_EVALUATION.md`. Nếu chưa có key, giữ nguyên trạng thái `not tested` (tuyệt đối không bịa kết quả).

## Bước 4: Push mã nguồn & xác nhận GitHub Actions CI xanh
- [ ] Khi bạn đã kiểm tra và cho phép push:
  ```powershell
  git push origin main
  git push origin v1.0.0-rc2
  ```
- [ ] Mở tab **Actions** trên https://github.com/lamngoc0312/SenseGraph xác nhận workflow **SenseGraph CI** xanh trên cả **Python 3.11** và **Python 3.13**.
- [ ] Kiểm tra repo đang ở chế độ **Public** và `README.md` không có link `file:///` bị hỏng.

## Bước 5: Quay & đăng video demo (<= 6 phút)
- [ ] Quay màn hình theo `submission/DEMO_SHOT_LIST.md` và thuyết minh theo `submission/DEMO_SCRIPT_EN.md` (~5:15, **tuyệt đối dưới 6 phút**).
- [ ] Đăng lên **YouTube** hoặc **Vimeo** ở chế độ **Public** hoặc **Unlisted**.
- [ ] Chụp 3–5 ảnh màn hình (Homepage, Physics + Learning Lab, Biology Food Web, Grounded Tutor, CS Flowchart) để đính kèm Devpost.

## Bước 6: Nộp bài trên Devpost & Demo Day
- [ ] Kiểm tra lại thể lệ tại `https://stem2connect-online-hackathon.devpost.com/rules`.
- [ ] Chọn Primary Track: **Education**.
- [ ] Dán nội dung từ `submission/DEVPOST_DESCRIPTION.md` (cập nhật phần Live Gemini nếu bạn đã test thật ở Bước 3).
- [ ] Điền link GitHub công khai, link video demo, ảnh màn hình và xác nhận nộp bài trước **22/11/2026 11:59 sáng (giờ VN)**.
- [ ] Kiểm tra thông báo **Demo Day (24/11 giờ Mỹ)** trên Discord của ban tổ chức.
