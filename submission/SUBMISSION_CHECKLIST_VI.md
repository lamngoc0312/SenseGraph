# SenseGraph — Checklist Nộp Bài STEM2Connect (Tiếng Việt)

**Hạn chót chính thức:** **21/11/2026 23:59 EST = 22/11/2026 11:59 sáng giờ Việt Nam (Asia/Ho_Chi_Minh)**  
**Khuyến nghị:** Hoàn tất và nộp trong ngày **21/11 theo giờ Việt Nam** để tránh sự cố mạng hoặc upload video.

---

## Bước 1: Kiểm tra mã nguồn & bảo mật cục bộ (5 phút)
- [ ] Chạy test đầy đủ:
  ```powershell
  cd D:\AI-tools\Project\SenseGraph
  python -m pytest -v
  python -m ruff check app tests
  ```
  (Kỳ vọng: **54 passed**, **All checks passed**.)
- [ ] Đảm bảo `.env` **không** được commit lên Git (`git status` không hiện `.env`, không có API key trong code).

## Bước 2: Kiểm tra trực tiếp trên trình duyệt (10 phút)
- [ ] Chạy server cục bộ:
  ```powershell
  python -m uvicorn app.main:app --reload
  ```
- [ ] Mở `http://127.0.0.1:8000` trên Chrome/Edge và tự kiểm tra bằng **bàn phím thuần** (`Tab`, `Shift+Tab`, `Enter`, `Space`):
  - [ ] Nhấn `Tab` thấy link **Skip to main content** hiện rõ.
  - [ ] Mở **Physics Explorer**, thử **Guided Tour**, chuyển sang **Guided Learning Lab**, dự đoán Bulb ON -> chạy thí nghiệm -> Reset.
  - [ ] Chuyển sang **Biology Explorer**, chọn **Rabbit**, kiểm tra quan hệ vào/ra -> **Remove Rabbit** -> xác nhận đúng 2 liên kết bị xóa + dòng lưu ý không dự đoán tuyệt chủng -> Reset.
  - [ ] Kiểm tra zoom trình duyệt **200%** không bị vỡ bố cục và không bị kẹt bàn phím.
  - [ ] *(Tùy chọn nếu có NVDA trên Windows)*: mở NVDA nghe thử `role="status"` và ghi nhận thực tế vào `docs/EXTRACTION_EVALUATION.md`.

## Bước 3: Thử Gemini Vision thật (tùy chọn nếu có `GEMINI_API_KEY`)
- [ ] Tạo `.env` từ `.env.example`, điền `AI_PROVIDER=gemini` và `GEMINI_API_KEY=...`, khởi động lại `uvicorn`.
- [ ] Tải lên `fixtures/images/physics_series.png` và `fixtures/images/biology_food_web.png`, tick đồng ý consent, xem màn hình **Review AI-Generated Diagram**, sửa nếu cần -> **Validate** -> **Confirm** -> chạy thí nghiệm.
- [ ] Ghi kết quả thực tế (đúng/sai/cần sửa gì) vào `docs/EXTRACTION_EVALUATION.md`. Nếu chưa có API key, giữ nguyên trạng thái `not tested` (tuyệt đối không bịa số liệu).

## Bước 4: Push mã nguồn lên GitHub công khai
- [ ] Kiểm tra commit và tag release cục bộ (`git log -n 6 --oneline`, `git tag`).
- [ ] Khi đã sẵn sàng, chạy:
  ```powershell
  git push origin main
  git push origin v0.7.0-rc1
  ```
- [ ] Mở https://github.com/lamngoc0312/SenseGraph kiểm tra repo đang ở chế độ **Public** và `README.md` hiển thị đẹp.

## Bước 5: Quay & đăng video demo (<= 6 phút)
- [ ] Quay màn hình theo `submission/DEMO_SHOT_LIST.md` và đọc lời thuyết minh theo `submission/DEMO_SCRIPT_EN.md` (mục tiêu ~5 phút, **tuyệt đối dưới 6 phút**).
- [ ] Đăng lên **YouTube** hoặc **Vimeo** ở chế độ **Public** hoặc **Unlisted** (không để Private).
- [ ] Chụp 3–4 ảnh màn hình (Homepage, Physics Explorer + Learning Lab, Biology Food Web, Review AI Diagram) để đính kèm Devpost.

## Bước 6: Nộp bài trên Devpost & Demo Day
- [ ] Mở trang nộp bài STEM2Connect trên Devpost, kiểm tra lại luật tại `https://stem2connect-online-hackathon.devpost.com/rules`.
- [ ] Chọn Primary Track: **Education**.
- [ ] Dán nội dung từ `submission/DEVPOST_DESCRIPTION.md` (cập nhật lại phần Live AI nếu bạn đã chạy smoke test thật ở Bước 3).
- [ ] Điền link GitHub công khai, link video demo, và upload ảnh màn hình.
- [ ] Kiểm tra lại thông báo **Demo Day (24/11 giờ Mỹ)** trên Discord của ban tổ chức.
