# SenseGraph — BẮT ĐẦU TỪ ĐÂY (dành cho người dùng Codex)

**Mục tiêu:** Dùng Codex xây một ứng dụng web thật, có tính năng AI đọc sơ đồ và tương tác hỗ trợ người khiếm thị. Bộ này là **đặc tả + dữ liệu mẫu + hướng dẫn**, chưa phải mã nguồn ứng dụng hoàn chỉnh.

## 1. Việc cần làm trước khi code

1. Giải nén `SenseGraph_Codex_Starter.zip` vào một thư mục, ví dụ `D:\Projects\SenseGraph`.
2. Mở thư mục `SenseGraph` trong VS Code / Codex (mở **cả thư mục**, không chỉ một file).
3. Mở `AGENTS.md` và `docs/PRODUCT_SPEC.md` để Codex có ngữ cảnh. Trước hết dùng prompt ở `prompts/01_CODEX_BOOTSTRAP.md`.
4. Yêu cầu Codex làm **từng giai đoạn**, chạy test sau mỗi giai đoạn, liệt kê file đã tạo, lỗi còn lại và cách chạy trên Windows PowerShell.
5. Không nhập API key vào chat, GitHub hay mã nguồn. Khi cần dùng AI thật, tạo `.env` trên máy từ `.env.example` và điền `GEMINI_API_KEY` (không commit `.env`).

## 2. Ưu tiên công việc

- **P0 (bắt buộc):** Trang web chạy được + demo fixture Physics/Biology + keyboard/screen reader + logic tương tác có test.
- **P1 (bắt buộc nếu có API key):** Upload PNG/JPEG/WEBP -> gọi Gemini Vision -> JSON đúng schema -> review/correction -> tương tác.
- **P2 (nếu kịp):** Module Computer Science / giọng nói bổ sung / giao diện đẹp hơn.

**Đừng** bắt đầu bằng thiết kế animation, cơ chế đăng nhập, database phức tạp, hệ thống tài khoản hoặc hỗ trợ mọi loại hình khoa học.

## 3. Bộ file quan trọng

| File | Chức năng |
|---|---|
| `AGENTS.md` | Quy tắc Codex phải tuân theo |
| `docs/PRODUCT_SPEC.md` | Bài toán, persona, user flow, phạm vi, acceptance criteria |
| `docs/TECHNICAL_SPEC.md` | Kiến trúc, API, xử lý AI, mô phỏng, bảo mật |
| `docs/ACCESSIBILITY_AND_TESTS.md` | Quy tắc keyboard/screen reader và test plan |
| `docs/ROADMAP_AND_SUBMISSION.md` | Roadmap, checklist STEM2Connect, demo |
| `contracts/diagram.schema.json` | Hợp đồng JSON cho output đã được chuẩn hóa |
| `fixtures/*.json` | Dữ liệu sơ đồ đã kiểm chứng để demo và test |
| `fixtures/images/*.png` | Hình ảnh mẫu để thử tải lên |
| `prompts/*.md` | Các lời nhắc Codex copy/paste theo từng giai đoạn |

## 4. Câu lệnh chạy dự kiến (sau khi Codex tạo code)

```powershell
cd D:\Projects\SenseGraph
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload
```

Mở `http://127.0.0.1:8000`. Nếu máy dùng Python 3.13, Codex cần chọn các dependency hỗ trợ phiên bản đó và chỉnh hướng dẫn khi cần. Không tự cho rằng hệ thống đã chạy nếu chưa kiểm thử.

Chạy kiểm thử dự kiến:

```powershell
python -m pytest -q
```

## 5. Những lựa chọn đã chốt

- **Track:** Education; tác động phụ: Community Impact.
- **Tech:** FastAPI + Pydantic + vanilla HTML/CSS/JavaScript + pytest.
- **AI:** Gemini multimodal qua SDK `google-genai` khi có key; provider phải hoán đổi được.
- **Không có key:** dùng hai fixture có nhãn "Pre-annotated demo — no AI used", **không** giả lập gọi API AI.
- **Phạm vi vật lý:** mạch một vòng nối tiếp với 1 pin, 1 công tắc, 1–2 bóng đèn; chỉ mô phỏng on/off định tính.
- **Phạm vi sinh học:** lưới thức ăn đơn giản, mũi tên biểu thị dòng năng lượng từ thức ăn/con mồi tới sinh vật tiêu thụ; chỉ truy vấn/thay đổi liên kết, không dự đoán quần thể.
- **Computer Science:** stretch goal, không ảnh hưởng hai module chính.

## 6. Hạn cuộc thi

STEM2Connect: hạn trên trang chính thức là **21/11/2026 23:59 EST = 22/11/2026 11:59 tại Việt Nam (UTC+7)**. Cần nộp public GitHub, video demo tối đa 6 phút qua YouTube/Vimeo, Devpost description, primary track và Demo Day 24/11 theo giờ Mỹ. Hãy xem `docs/ROADMAP_AND_SUBMISSION.md` và kiểm tra lại Discord trước khi nộp.

## 7. Điểm cần nhớ

Đây là **bản thiết kế triển khai**, không phải cam kết về độ chính xác Vision, hiệu quả với người khiếm thị hoặc việc đạt chuẩn WCAG. Cần chạy test kỹ thuật và thử với người dùng thực tế khi có thể, đồng thời công bố các giới hạn rõ ràng.
