# ĐẶC TẢ DỰ ÁN SENSEGRAPH — BẢN TIẾNG VIỆT

**Tên:** SenseGraph — Explore STEM Beyond Sight  
**Tagline:** Making STEM Diagrams Accessible, Interactive and Understandable  
**Cuộc thi:** STEM2Connect AI Hackathon 2026  
**Track chính:** Education · Tác động xã hội: Community Impact  
**Hình thức:** Thi cá nhân · Web app · Chạy trên máy tính  
**Ngày đặc tả:** 15/11/2026

## 1. Mục tiêu và vấn đề

Học sinh/sinh viên khiếm thị có thể gặp khó khăn với các hình vẽ khoa học mà kiến thức nằm trong **đường nối, mũi tên, biểu tượng và quan hệ không gian**. Đọc một đoạn mô tả ngắn chưa đủ để họ tự khám phá và thử thay đổi các thành phần của sơ đồ.

SenseGraph không nhắm tới việc giải thích tất cả ảnh khoa học. Sản phẩm tập trung vào **một số nhóm sơ đồ có cấu trúc** và biến chúng thành dữ liệu dạng graph mà người học có thể **khám phá bằng bàn phím, nghe/đọc qua trình đọc màn hình, thực hiện tương tác và nhận kết quả có kiểm chứng**.

## 2. Ba tính chất tạo khác biệt

1. **From Image to Semantic Structure:** AI đề xuất các node (đối tượng) và edge (quan hệ), không chỉ trả một đoạn văn mô tả ảnh.
2. **Explore Relationships, Not Just Objects:** Người học chọn một đối tượng và tìm được các đối tượng liên quan, hướng quan hệ, mô tả và các bước khám phá tiếp theo.
3. **Experiment with Verified Logic:** Mỗi lĩnh vực có mô-đun tính toán riêng. AI không tự suy đoán trạng thái bóng đèn hoặc tác động sinh thái.

## 3. Người sử dụng

- **Chính:** Người học khiếm thị hoặc thị lực thấp, sử dụng máy tính và bàn phím, có thể dùng NVDA/VoiceOver.
- **Phụ:** Giáo viên/người chuẩn bị học liệu, kiểm tra và sửa kết quả AI nhận diện trước khi cho học sinh sử dụng.

Lưu ý: Đây là giả định thiết kế, **chưa phải kết quả khảo sát người dùng thực tế**.

## 4. Hai module bắt buộc + một module mở rộng

### Physics Explorer — Sơ đồ mạch điện đơn giản

- **Input:** Ảnh sơ đồ 1 pin + 1 công tắc + 1 hoặc 2 bóng đèn **nối tiếp trên một vòng mạch**.
- **AI Output:** Danh sách linh kiện, kết nối giữa linh kiện, trạng thái công tắc được nhận diện, phần chưa chắc chắn.
- **Explore:** Xem/tìm hiểu pin, công tắc, bóng đèn; di chuyển tới các linh kiện kết nối.
- **Interact:** Bật/tắt công tắc bằng nút có thể dùng qua bàn phím.
- **Deterministic Output:** Nếu vòng mạch đủ kết nối và công tắc đóng thì bóng đèn bật; công tắc mở thì tắt. Có thể Reset.
- **Giới hạn:** Không phân tích mạch song song, điện trở, công suất, dòng điện hoặc điện áp định lượng trong bản MVP.

### Biology Explorer — Chuỗi/lưới thức ăn

- **Input:** Ảnh chuỗi/lưới thức ăn khoảng 3–8 sinh vật, có mũi tên.
- **AI Output:** Danh sách sinh vật, mối quan hệ theo **hướng năng lượng từ thức ăn/con mồi sang sinh vật tiêu thụ**, cảnh báo nếu không rõ chiều mũi tên.
- **Explore:** Với mỗi sinh vật, xem nó nhận năng lượng từ đâu và truyền năng lượng tới sinh vật nào.
- **Interact:** Thử loại bỏ một sinh vật khỏi **sơ đồ mô phỏng**.
- **Deterministic Output:** Chỉ ra những quan hệ bị xóa hoặc còn lại, không khẳng định loài nào tuyệt chủng hoặc tăng/giảm số lượng.
- **Giới hạn:** Không mô phỏng động lực quần thể, bệnh tật hoặc chu kỳ sinh thái.

### Computer Science Explorer — Lưu đồ thuật toán (nếu còn thời gian)

- **Input:** Lưu đồ gồm Start, Process, Decision, End.
- **Explore:** Xem khối và các nhánh True/False.
- **Interact:** Nhập giá trị, chạy thuật toán từng bước.
- **Giới hạn:** Chỉ hỗ trợ biểu thức/điều kiện đơn giản qua bộ tính toán an toàn; không thực thi code bất kỳ do AI tạo.

**Đối với hạn thi:** Hoàn thành Physics + Biology thật ổn định trước, sau đó mới quyết định làm Computer Science.

## 5. Luồng xử lý tổng thể

```text
Người dùng chọn ví dụ có sẵn hoặc tải ảnh sơ đồ
         |
         v
    [Chọn lĩnh vực]
         |
         +-- Ví dụ có sẵn --> Graph JSON đã kiểm chứng
         |
         +-- Ảnh tải lên --> Đồng ý gửi cho AI provider
                                  |
                                  v
                            Gemini Vision
                                  |
                                  v
                           JSON đề xuất
                                  |
                                  v
                     Kiểm tra schema + khoa học
                                  |
                                  v
                     Người dùng sửa/xác nhận
                                  |
                                  v
                     Graph đã xác nhận
                                  |
                                  v
      Accessible Explorer: tổng quan, node, edge, quan hệ
                                  |
                                  v
       Mô phỏng theo lĩnh vực (Python deterministic)
                                  |
                                  v
                 Thông báo và giải thích bằng chữ
```

**Nguyên tắc trung thực:** Khi chọn dữ liệu mẫu, ứng dụng ghi rõ **Pre-annotated demo — no AI used**. Chỉ được ghi **Live AI** khi Gemini đã được gọi thật và có kết quả. Nếu chưa có API key, ứng dụng vẫn chạy ví dụ mẫu nhưng không được giả lập đã phân tích ảnh bằng AI.

## 6. Dữ liệu chung dùng cho cả hai môn

Mỗi sơ đồ có:

- `domain`: tên lĩnh vực
- `title`, `summary`: tiêu đề và mô tả tổng quan dễ hiểu
- `nodes`: từng đối tượng (`id`, `kind`, `label`, `description`, `attributes`)
- `edges`: từng quan hệ (`source`, `target`, `relation`, `description`)
- `domain_model`: dữ liệu riêng cho mô phỏng vật lý hoặc sinh học
- `source`: nguồn từ fixture hay AI thật
- `review_status`: đã xác nhận hay chưa
- `warnings`: kết nối/đối tượng chưa chắc chắn

Cấu trúc đầy đủ nằm trong `contracts/diagram.schema.json`. Codex phải dùng đúng hợp đồng này; file `fixtures/*.json` là ví dụ chạy thử.

## 7. Các màn hình MVP

**Trang bắt đầu:** giới thiệu vấn đề, chọn hai sơ đồ mẫu, mục tải ảnh và thông báo về xử lý ảnh bởi AI.

**Trang phân tích:** mô tả sơ đồ, tên lĩnh vực, nhãn nguồn dữ liệu, các cảnh báo, danh sách đối tượng/quan hệ; người dùng có thể sửa tên và kết nối sai.

**Trang khám phá:** một danh sách đối tượng chọn được bằng bàn phím, phần chi tiết, các đối tượng liên quan, nút mô phỏng và nút Reset; thông báo kết quả bằng text, không chỉ đổi màu trên hình.

## 8. Khám phá bằng bàn phím là gì?

Ví dụ: Người dùng mở Physics fixture, nhấn **Tab** để tới `Switch S1`, nhấn **Enter** để nghe thông tin. Sau đó Tab tới nút `Close switch`, nhấn **Space**, trình đọc màn hình thông báo `Switch S1 closed. Bulb L1 is on.` Người dùng có thể chọn bulb, nghe trạng thái mới, rồi Reset. Không cần dùng chuột hoặc nhìn hình.

Trong web thực tế, trình đọc màn hình (NVDA/VoiceOver) và phím điều hướng có nhiều chế độ; chúng ta ưu tiên dùng `<button>`, `<label>`, danh sách HTML thật và `role=status` thay vì tự làm hệ thống phím tắt phức tạp.

## 9. Công nghệ

- Python + FastAPI: API và logic mô phỏng.
- Pydantic: kiểm tra cấu trúc dữ liệu.
- Gemini qua SDK `google-genai`: AI đọc ảnh nếu người dùng cung cấp API key. Model cấu hình qua biến môi trường, không hardcode bí mật.
- HTML + CSS + JavaScript: web app đơn giản, hỗ trợ accessibility.
- `pytest`: kiểm thử logic và endpoints.
- Dữ liệu mẫu có sẵn: hai sơ đồ PNG và hai file JSON đã được tạo trong bộ handoff.

## 10. Những kiểm thử tối thiểu

- Tải 2 ví dụ không cần mạng/API key.
- Chọn đối tượng bằng Tab/Enter, không bắt buộc chuột.
- Công tắc mở -> đèn tắt; đóng -> đèn bật; Reset quay về ban đầu.
- Loại bỏ Rabbit -> xóa đúng quan hệ Grass→Rabbit và Rabbit→Fox, không xóa quan hệ không liên quan.
- Node ID trùng, edge trỏ tới node không tồn tại, sơ đồ sai cấu trúc -> bị chặn với thông báo dễ hiểu.
- Chưa xác nhận AI output -> không cho mô phỏng.
- Khi thiếu key -> thông báo cấu hình AI không có, không hiện fake result.
- Không tự ý tuyên bố đã đạt chuẩn WCAG hay đã test với người khiếm thị nếu chưa thực hiện.

## 11. Tiến độ

- 15–16/11: cấu trúc và dữ liệu; dựng API.
- 17–18/11: mô phỏng và giao diện dùng bàn phím.
- 19–20/11: Gemini AI, sửa graph, kiểm thử.
- 21/11: README, quay demo tối đa 6 phút, nộp Devpost sớm.

**Hạn chính thức:** 22/11/2026, 11:59 sáng giờ Việt Nam (21/11 23:59 EST). **Demo Day:** 24/11/2026 (giờ Mỹ), cần kiểm tra thông báo Discord.

## 12. Đầu ra dự án cần có

1. Web app chạy trên máy thật, không chỉ hình thiết kế.
2. Hai module có logic tương tác, dữ liệu và kiểm thử.
3. Tính năng live AI image-to-graph nếu cung cấp API key, có cảnh báo và bước xác nhận.
4. Repository GitHub public với README, cách chạy, AI disclosure và credits.
5. Video demo <=6 phút trên YouTube/Vimeo; Devpost form; tham gia Demo Day.

**Dành cho Codex:** Đọc tiếp `AGENTS.md`, `docs/PRODUCT_SPEC.md`, `docs/TECHNICAL_SPEC.md`, `docs/ACCESSIBILITY_AND_TESTS.md` và dùng prompt `prompts/01_CODEX_BOOTSTRAP.md` để triển khai. Các tài liệu tiếng Anh là hợp đồng kỹ thuật chi tiết hơn bản tổng quan tiếng Việt này.
