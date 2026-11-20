# SENSEGRAPH — FULL PROJECT HANDOFF (VI + EN)

This consolidated file is readable by humans and Codex. The ZIP additionally contains the machine-readable JSON schema, original example images, graph fixtures and staged prompts.


---

# SOURCE: TONG_QUAN_DU_AN_VI.md

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


---

# SOURCE: README.md

# SenseGraph — Codex Project Handoff Kit

**SenseGraph: Making STEM Diagrams Accessible, Interactive and Understandable.**

An accessible learning prototype for blind and visually impaired students. A diagram is converted into a **reviewable semantic graph** so students can navigate its components and relationships using a keyboard and screen reader, then experiment with domain-specific deterministic interactions.

**Primary hackathon track:** Education. **Related social impact:** Community Impact.

This folder is an **implementation handoff kit, not the finished app**. Codex should generate the application following the specs and tests in this folder.

## Product narrative

`Input diagram -> Vision AI -> Structural validation -> Human review -> Accessible graph exploration -> Domain simulator -> Learning feedback`

P0: physics simple series circuits; biology food webs. P2: computer-science flowcharts. The **shared semantic graph** (nodes and directed edges) represents exploration; domain-specific payloads determine the behavior of a scientific simulator.

## Quick start

- Vietnamese step-by-step setup: [START_HERE_VI.md](START_HERE_VI.md)
- Codex rules: [AGENTS.md](AGENTS.md)
- Product requirements: [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md)
- Engineering contracts: [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md)
- Accessibility and acceptance: [docs/ACCESSIBILITY_AND_TESTS.md](docs/ACCESSIBILITY_AND_TESTS.md)
- Handoff prompts: [prompts/01_CODEX_BOOTSTRAP.md](prompts/01_CODEX_BOOTSTRAP.md)

## Important limitations

- The application must not claim to correctly interpret arbitrary scientific diagrams.
- Vision extraction can fail: the user reviews and corrects the structured result before simulation.
- Demo fixtures are curated, not evidence that AI extracted an uploaded image.
- Physics simulation covers only a single-loop series circuit; biology exploration shows graph changes, not ecological forecasts.
- Keyboard and screen reader accessibility require manual review with assistive technologies; no claims of user validation are made yet.

## Official references

- Hackathon rules: https://stem2connect-online-hackathon.devpost.com/rules
- W3C complex images: https://www.w3.org/WAI/tutorials/images/complex/
- W3C keyboard accessibility: https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- Gemini SDK: https://googleapis.github.io/python-genai/

## License and attribution

Choose an appropriate open-source license before publishing. Document third-party SDKs, models, external datasets, AI coding assistants, and which work was completed during the hackathon period. Use original or freely licensed sample diagrams; do not reuse private group project code without authorization.


---

# SOURCE: START_HERE_VI.md

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


---

# SOURCE: AGENTS.md

# AGENTS.md — Engineering instructions for Codex

You are building **SenseGraph**, an accessible interactive STEM diagram learning prototype for blind and visually impaired students. Read `START_HERE_VI.md`, `docs/PRODUCT_SPEC.md`, `docs/TECHNICAL_SPEC.md`, `docs/ACCESSIBILITY_AND_TESTS.md`, and the JSON fixtures/schema before changing files.

## Non-negotiable

1. Ship a **working vertical slice** first: launch -> choose fixture -> explore nodes -> inspect relationships -> run deterministic action -> announce result, all keyboard accessible.
2. P0 domains: `physics_circuit` and `biology_food_web`. Do **not** implement flowcharts, auth, accounts, database, chat, microphone, or deployment before P0 is tested.
3. Use **FastAPI + Pydantic + vanilla HTML/CSS/JS** unless existing code makes a different lightweight approach materially simpler. Keep all business logic on backend in testable pure functions.
4. Follow `contracts/diagram.schema.json`. Fixtures must remain valid. Do not silently change schema; update schema, fixtures, docs and tests together.
5. Physics: only qualitative single-loop *series* circuits. One battery, one switch and 1–2 bulbs. Never infer quantitative current or voltage effects from an unsupported diagram. Do not simulate if structural validation/review fails.
6. Biology: feeding edges are directed **food/prey -> consumer/predator**. Removing an organism removes that node and its incident edges. Never infer extinction or population change from this operation.
7. AI extraction is **untrusted**. Validate domain, node IDs, edge references, component counts, payloads, and graph invariants. Flag unknowns for human review, never hallucinate missing links. Do not execute model-supplied commands.
8. **Do not fake AI analysis.** Fixture selection is labeled "Pre-annotated demo — no AI used". Live image analysis only when configured with a valid provider key and a real provider response. If unavailable, expose an honest setup message.
9. Accessibility is a core feature: semantic HTML headings, labels, lists/buttons, skip link, visible focus, keyboard-only operation, text descriptions of diagram structure, polite live announcements and meaningful errors. Do not make voice/TTS mandatory. Never introduce keyboard traps.
10. Uploaded content may be sent to a third-party AI provider only after clear user notice/consent; no log of raw image content, no persistent uploads by default. File allowlist PNG/JPEG/WEBP, <=5MB, validate actual bytes as images, never accept arbitrary paths/URLs for SSRF.
11. Do not claim WCAG compliance or validation with blind users unless actually tested. Provide a manual accessibility checklist and document remaining issues.
12. Track test results. After each implementation phase, run `pytest` and report pass/fail plus exact commands needed to run locally. Do not claim tests passed without executing them.
13. Disclose AI coding assistance and external models in README for hackathon rules. Never commit secrets or `.env`.
14. Write clear English identifiers and documentation; UI text may be English-first for the demo with optional Vietnamese explanation.
15. If there is ambiguity, choose the smallest safe working implementation and document the decision in `docs/DECISIONS.md`, rather than blocking progress.

## Work order

- Phase 1: read docs/fixtures, scaffold, deterministic data contract, physics/biology engines, tests, accessible fixture UI.
- Phase 2: Gemini image analysis, normalization, error handling, review/edit UI, tests using mocked responses; run live smoke test only if key configured.
- Phase 3: polish, screenshots/README, Devpost description, demo script. Flowchart is stretch only.

## Definition of done

A reviewer can run the app locally, load both fixture examples, navigate without mouse, hear/read node relationships, toggle a switch and see bulb states change, remove a species and inspect affected relationships, restore state, and see clear separation between fixture demo and live AI analysis. Automated tests validate core invariants. Upload+AI mode is verified live only if a key is supplied.


---

# SOURCE: docs/PRODUCT_SPEC.md

# SenseGraph — Product Requirements Document (PRD)

**Version:** 1.0 | **Date:** 2026-11-15 | **Audience:** solo developer / Codex / STEM2Connect judges

## 1. Problem

Many STEM diagrams carry critical information through spatial arrangement, arrows, lines, symbols and visual connections. A static image or a generic one-sentence caption may not allow a blind or visually impaired learner to **independently explore relationships and manipulate the represented system**.

The prototype addresses one narrow, testable problem: helping learners independently explore **two graph-like categories of STEM diagrams** with a keyboard and screen reader, without relying exclusively on image descriptions or a general chatbot.

**Do not claim** that all blind learners have identical needs, that a product is clinically/educationally validated, or that all diagrams can be accurately extracted.

## 2. One-line solution

> Upload or select a STEM diagram; SenseGraph converts it to an editable semantic graph, describes its entities and connections in an accessible interface, and enables safe, deterministic domain-specific experiments.

## 3. Target audience and use cases

**Primary persona:** A blind or visually impaired university / secondary student using a Windows laptop with keyboard + NVDA, or macOS with VoiceOver, learning foundational STEM concepts.

**Secondary persona:** A sighted teacher who wants to review or correct extraction before sharing accessible study materials.

Primary use cases:

1. Listen to an overview of a textbook diagram and visit each labeled object in a logical order.
2. Explore what connects to a selected object, what a relation means, and navigate directly to its neighbor.
3. Verify or correct an ambiguous AI-identified object/connection.
4. Apply a domain action and hear an explanation grounded in deterministic model state.
5. Reset and repeat without changing the original source image.

## 4. Domain scope and priority

### P0 — Physics / Circuit Explorer

- Input: schematic of **one closed series loop** with exactly one battery, one switch, and one or two light bulbs, clear labels and wires.
- Output: device nodes, wire relations, component order, switch state, summary, warnings.
- Explore: device label, type, role, adjacent elements, current switch/bulb state.
- Interact: toggle switch; compute `ON` for bulbs iff `loop_wired = true` and all switches are closed; otherwise `OFF`. For P0, there is exactly one switch. No current, brightness, resistance, polarity, or electrical-safety predictions.
- Unsupported: parallel circuits, multi-switch control, resistors with values, LED orientation, wiring shorts, dynamic electrical analysis.
- If AI cannot establish one valid series loop, disable simulation, request correction and display safe message.

### P0 — Biology / Food-Web Explorer

- Input: simple food chain/web with ~3–8 named organisms and directed arrows.
- Convention: **arrow from food/prey to its consumer/predator** (energy flow). Explain this convention before exploration; if arrow convention is ambiguous, do not silently assume it.
- Output: organism nodes, directed `energy_to` edges, summary, warnings.
- Explore: incoming/outgoing feeding relations, direct neighbors, energy paths.
- Interact: temporarily remove one organism; remove its incident relations; report exactly which relationships disappeared and which still remain; undo/reset.
- Unsupported: predicting extinction, population sizes, multi-year environmental change, quantitative energy transfer.

### P2 — Computer Science / Flowchart Explorer (stretch)

- Represent `start`, `process`, `decision`, `end`, directed flow edges and optional branch labels.
- Navigate conditions and paths. Only execute a strict whitelist of simple arithmetic/comparison operations with bounded steps; never execute source code returned by an LLM.
- This module MUST NOT delay P0 completion.

## 5. Main user flow

**Mode A: deterministic showcase (works without API key)**

1. Visit landing page; see meaningful project statement and 2 example buttons.
2. Choose "Explore example circuit" or "Explore example food web".
3. UI clearly labels the result **Pre-annotated demo — no AI used**.
4. Diagram overview presented as visible text plus structured list of objects and relationships.
5. Tab / Shift+Tab between controls, Enter / Space to activate native buttons.
6. Selecting a node shows long description, neighbors and actions; status updates announced by assistive technology.
7. Run domain action; read exact state changes and reason; reset.

**Mode B: live AI analysis (requires key)**

1. Choose domain and upload allowed image (PNG/JPEG/WEBP, maximum 5 MB).
2. Before sending, see consent notice: image is shared with the configured AI provider; avoid personal/sensitive content.
3. User explicitly starts analysis; backend sends the image to provider.
4. Provider returns structured proposal; Pydantic/graph validator verifies shape and semantics.
5. Show result as **AI-generated — review required** with warnings; editable labels/connections and domain parameters.
6. User confirms the verified structure. Invalid/ambiguous diagrams cannot be simulated.
7. Enter Explore/Experiment mode; reset must restore confirmed baseline (not model output edited behind the scenes).

## 6. UX requirements

- Homepage: project purpose; two example actions; image upload section; notice that voice is optional.
- Explorer: heading with diagram type, concise overview, summary stats, **numbered objects list**, selected-object detail and **relationship list**, domain-specific action panel, status region, reset button.
- All information necessary to understand a diagram available as text, not only SVG/canvas/colors.
- Distinguish diagram interpretation from verified outcome: "AI proposes...", "Confirmed graph...", "Simulation result...".
- Visible labels for every button and input; avoid icon-only interactions.
- Keep UI English-first for simple international demo, use plain language.
- No authentication, profiles, student records, storage of uploaded personal data or analytics in MVP.

## 7. AI responsibilities vs deterministic responsibilities

| Component | Responsibility | Must never do |
|---|---|---|
| Vision model | Extract tentative diagram type, labels, entities, relations, flags for ambiguity | Invent unseen connections, claim guaranteed accuracy |
| Schema & validator | Reject malformed IDs/edges/domain models and impossible P0 topology | Quietly patch uncertain science concepts |
| Human review | Confirm/correct labels, edges and domain-specific values | Automatically approve unsupported graphs |
| Physics engine | Evaluate simple series-loop switch/bulb state | Compute unsupported current or brightness |
| Biology engine | Traverse feeding graph / remove and restore nodes & edges | Predict ecological population changes |
| Accessible UI | Present readable structure, keyboard interactions and status | Force user to rely on sight or speech input |

## 8. Requirements with priority IDs

| ID | Priority | Requirement | Acceptance |
|---|---|---|---|
| FR-01 | P0 | Load 2 bundled pre-annotated diagrams | Both load without external keys/network |
| FR-02 | P0 | Render graph as semantic list and long description | Every node/edge discoverable via keyboard |
| FR-03 | P0 | Physics toggle updates bulb state | Series open -> off, closed -> on, reset -> initial |
| FR-04 | P0 | Food-web remove node updates edges | Only incident edges removed; reset restores |
| FR-05 | P0 | Selection shows direct neighbors | Labels and arrow direction announced |
| FR-06 | P0 | Validate diagram before simulations | Bad ref/type/domain rejected with actionable error |
| FR-07 | P0 | Distinguish fixture vs live AI mode | Honest source badge + text in view and README |
| FR-08 | P0 | Accessible keyboard navigation and status | Critical journey possible without mouse |
| FR-09 | P1 | Upload image & actual Gemini model extraction | Model called only if configured and consented |
| FR-10 | P1 | Human correction of AI proposal | Change node names/edges, revalidate, confirm |
| FR-11 | P1 | Handle AI provider failure gracefully | No crash, retries not infinite, clear fallback |
| FR-12 | P1 | Test, README, demo/video story | Tests and public repo ready for Devpost |
| FR-13 | P2 | Flowchart exploration | Only if P0 and P1 stable |
| FR-14 | P2 | Optional text-to-speech control | OFF by default; no duplicated involuntary speech |

## 9. Non-functional requirements

- Python >=3.11 (prefer support for user's Python 3.13); no Node build requirement.
- Simple local setup on Windows PowerShell; single FastAPI server serves static frontend and JSON API.
- Dependencies listed in `requirements.txt`, `.env.example` committed, `.env` and secrets ignored.
- Unit tests for validators and simulators; integration tests for endpoints; manual tests for keyboard + NVDA/VoiceOver if available.
- Upload limit 5MB; MIME and image bytes checked; reject corrupt files; avoid upload persistence.
- Gemini key only on backend; never hardcode or expose in browser.
- External request duration limited; meaningful error codes; model output considered untrusted.

## 10. Evaluation plan (no fabricated metrics)

**Functional:** 2 curated fixtures; at least 20 automated unit/integration assertions; full no-mouse walkthrough in one browser.

**Extraction:** Prepare 5–10 different simple input images per supported domain, manually annotate expected nodes/edges; evaluate extraction only on inputs actually run, reporting: node precision/recall, relation precision/recall, percentage of diagrams needing correction. Do not claim a percentage until measured. Record at least two actual successful live AI analyses if provider access exists.

**Accessibility:** keyboard walk-through with Tab/Shift+Tab/Enter/Space; verify focus order, status announcements, long descriptions and no keyboard trap; manual screen reader check if available. Report gaps candidly.

**Educational learning:** only claim *potential*, not demonstrated learning outcomes, until user studies are conducted.

## 11. Exclusions / honest limitations

- Arbitrary STEM image recognition, complex charts, handwriting, OCR-heavy textbooks, all circuit types, advanced biology simulation.
- Production safety critical use, medical decisions, automatic curriculum grading.
- Guarantees of screen reader behavior on all devices, WCAG certification, or validation by real blind participants without conducting study.
- A general AI assistant, multilingual speech tutor, accounts, cloud hosting as core scope.

## 12. Definition of done for the hackathon

A judge can launch the application locally, experience two working accessible examples, see meaningful domain actions that can be explained and tested, and—if a provider key is configured—upload an image and observe an actual AI-produced graph with human review. The public repo includes run steps, credits, AI disclosure, demo and limitations.


---

# SOURCE: docs/TECHNICAL_SPEC.md

# SenseGraph — Technical Architecture & API Contract

## 1. Chosen stack

- Backend: **Python, FastAPI, Pydantic**. Python 3.11+ (prefer compatibility with Python 3.13).
- Frontend: **semantic HTML5 + CSS + vanilla JavaScript**, served by FastAPI StaticFiles/HTMLResponse. Avoid heavy frontend bundlers for hackathon MVP.
- Vision extraction: **Google Gemini** image understanding + structured JSON, using `google-genai`; keep interface replaceable.
- Tests: `pytest` + `httpx`/FastAPI TestClient; browser keyboard and screen-reader manual acceptance.
- Storage: No database for P0; frontend retains currently confirmed diagram + pristine baseline in memory. Fixtures as local JSON. No raw uploaded image persisted by default.

Suggested source layout **to be generated by Codex**:

```text
SenseGraph/
  AGENTS.md
  START_HERE_VI.md
  README.md
  requirements.txt             # Codex creates
  .env.example                 # Codex creates
  .gitignore                   # Codex creates
  app/
    __init__.py
    main.py                     # FastAPI app, endpoints, static frontend
    models.py                   # Pydantic schema
    settings.py                 # env variables, provider adapter
    services/
      validators.py            # contract/domain checks
      ai_vision.py             # real Gemini image extraction adapter
      description.py           # reliable textual summaries from graph
    domains/
      physics.py               # qualitative single-loop engine
      biology.py               # directed food-web graph engine
    static/
      index.html
      styles.css
      app.js
  tests/
    test_models.py
    test_physics.py
    test_biology.py
    test_api.py
  contracts/
    diagram.schema.json
  fixtures/
    physics_series.json
    biology_food_web.json
    images/
      physics_series.png
      biology_food_web.png
  docs/
    PRODUCT_SPEC.md
    TECHNICAL_SPEC.md
    ACCESSIBILITY_AND_TESTS.md
    ROADMAP_AND_SUBMISSION.md
```

## 2. Semantic graph contract

Authoritative JSON schema: `contracts/diagram.schema.json`. Implement with Pydantic, and regenerate/compare schema where practical.

Top-level `DiagramDocument`:

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | fixed `1.0` | API/data schema compatibility |
| `id` | non-empty string | Identifier; not filesystem path |
| `title` | string | Accessible title |
| `domain` | enum | `physics_circuit` or `biology_food_web` |
| `summary` | string | Useful long-ish plain-language description |
| `source` | object | `mode`: `fixture` or `ai`, filename, optional provider |
| `review_status` | enum | `unreviewed` or `confirmed` |
| `nodes` | `Node[]` | Objects, with unique IDs |
| `edges` | `Edge[]` | Relationships, with valid node IDs |
| `domain_model` | union object | `series_circuit` or `food_web` payload |
| `warnings` | `string[]` | Ambiguities, unsupported features, review issues |

`Node`: `id`, `kind`, `label`, `description`, `attributes` (object).

`Edge`: `id`, `source`, `target`, `relation`, `description`.

**Common graph is the exploratory interface**, not the source of scientific truth for all domains. Domain simulators must validate/interpret it according to their own semantics.

### 2.1 Physics domain semantics

- Node kinds: `battery`, `switch`, `bulb` only.
- Edge relation: `wire`. Edge is **undirected for circuit connectivity**, regardless of stored source/target ordering.
- `domain_model`: `{ "kind":"series_circuit", "sequence":["battery_1","switch_1","bulb_1"], "switch_states":{"switch_1":"open"}, "loop_wired":true }`.
- `sequence` lists exactly all components in the order of the proposed simple single loop (one battery, one switch, 1–2 bulbs).
- Validator requires exactly the expected number/type of components; every `sequence` ID unique and present; edges form **exactly one ring** through the sequence (unordered pairs, including last to first), with no extra wires or disconnected nodes. In the 3-component fixture, the connections are battery–switch, switch–bulb, bulb–battery.
- `loop_wired` is **derived/verified by backend validator**, never blindly trusted from AI.
- If graph does not meet series ring invariant, `simulation_ready=false`, explanation states unsupported/unclear topology. Do not force an inaccurate series simplification.
- Physics engine `toggle_switch`: change switch state from `open` to `closed` or back. `bulbs_on = loop_wired && all_switches_closed`; report each bulb ON/OFF and why. This is a qualitative educational model only.
- Action must not change the graph wiring; do not use live electricity terminology such as precise voltage/current when unsupported.

### 2.2 Biology domain semantics

- Node kind: `organism` only.
- Edge relation: `energy_to` only, directed **food/prey -> consumer/predator**.
- `domain_model`: `{ "kind":"food_web", "arrow_convention":"food_to_consumer" }`.
- Before interpreting an uploaded food-web image, confirm direction of arrows. If ambiguous, warn user and require review/correction.
- `remove_organism`: delete selected organism and all incident edges in returned working graph; report removed edge count/names plus remaining relation count. Does **not** infer effect on population or extinction.
- `reset` is implemented by restoring the original confirmed diagram (never mutate baseline).
- Support directed neighbor queries, paths and counts only from confirmed edges; if none, say so.

## 3. REST API contract (suggested, stateless)

All JSON in UTF-8. Errors follow:

```json
{"error": {"code":"VALIDATION_ERROR", "message":"Human-readable reason", "details":[]}}
```

### `GET /api/health`

Response `200`:

```json
{"status":"ok", "ai_configured":false, "supported_domains":["physics_circuit","biology_food_web"]}
```

Only boolean is exposed, no API key or token.

### `GET /api/examples`

`200`: list of `[{"id":"physics-series","title":"Basic Series Circuit","domain":"physics_circuit"}, ...]`.

### `GET /api/examples/{example_id}`

`200`: complete pre-annotated `DiagramDocument`, source.mode=`fixture`, review_status=`confirmed`. If unknown `404`.

### `POST /api/analyze`

`multipart/form-data` with:

- `file`: image PNG/JPEG/WEBP, max 5 MB (actual signature/decode validated).
- `domain`: `physics_circuit` or `biology_food_web` (explicit selection reduces ambiguity).
- `consent`: `true` required (server rejects absent/false).

`200`: **genuine** model-generated `DiagramDocument` with `source.mode=ai`, `source.provider=gemini`, `review_status=unreviewed`. Warnings include unsupported graph topology / ambiguous arrows. No model result may be silently substituted with fixtures.

Errors: `400` wrong domain/consent, `413` oversize, `415` MIME/invalid image type, `422` image not suitable or AI result invalid, `503` no configured provider or provider unavailable, `504` provider timed out. Return meaningful messages for screen readers.

### `POST /api/validate`

Body: complete `DiagramDocument`, usually edited in frontend.

Response `200`:

```json
{
  "valid":true,
  "simulation_ready":true,
  "warnings":[],
  "errors":[]
}
```

Shape and domain validation are separate: JSON may be well-formed while topology is unsupported. Use `valid` for schema/graph structural validity and `simulation_ready` for domain action support. Wrong edges must not crash server.

### `POST /api/confirm`

Body: `DiagramDocument` with review_status `unreviewed`; validates and returns `DiagramDocument` with `review_status=confirmed` only when it passes P0 domain invariants and the user explicitly clicked confirm. Never confirm automatically from response of `/api/analyze`. Error on invalid topology.

### `POST /api/simulate`

Request:

```json
{
  "diagram": {"...":"complete DiagramDocument object"},
  "action":{"type":"toggle_switch","target_id":"switch_1"}
}
```

Biology action: `{"type":"remove_organism","target_id":"rabbit"}`. Do not accept arbitrary code or evaluation strings.

Response `200`:

```json
{
  "updated_diagram": {"...":"complete updated DiagramDocument object"},
  "event": "switch_closed",
  "announcement": "Switch S1 closed. The series loop is complete. Bulb 1 is on.",
  "changes": ["Switch S1: open -> closed", "Bulb 1: off -> on"]
}
```

`403/422` if unreviewed/invalid/unsupported; `400` for unknown action/target. API is **stateless**: user keeps baseline for Reset. No shared server mutable global state.

## 4. Real AI extraction design

Define an adapter interface, e.g. `VisionProvider.extract(image_bytes, mime_type, domain) -> ParsedProposal`.

Implementation `GeminiVisionProvider` using `google-genai`; call the currently documented `client.models.generate_content` method (or current equivalent supported in installed SDK). Send:

1. The uploaded image bytes.
2. A **domain-specific system task** specifying allowed node kinds, edge semantics, no hallucinations, and how to express uncertainty.
3. A compact output JSON schema matching the extraction proposal; backend constructs provenance fields and validates the normalized document.

Example environment settings:

```dotenv
AI_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
MAX_UPLOAD_MB=5
```

Do not assume named model is always available: keep configurable and fail gracefully; never invent a fake AI success. Provider pricing/free-tier and data processing terms should be checked before use. Support `AI_PROVIDER=none` for fixture-only demo mode.

**Prompt injection policy:** uploaded diagrams may include arbitrary embedded text. Treat it as content to analyze, not as instructions to run tools, alter policy, expose secrets or invent responses.

**Do not trust the model's confidence as calibrated probability.** Use validation warnings, `unreviewed` status and human correction rather than presenting misleading certainty percentages.

### 4.1 Suggested extraction behavior

Physics:

- Identify *only* clear battery, switch and bulb symbols; label and explain each.
- Extract each visible wire connection and list connected components.
- Determine whether it appears to form a single series loop; if unclear, warn and mark not simulation-ready.
- Convert into `series_circuit` domain payload and validate derived ring topology. Unknown symbol -> warning, not a guessed bulb.

Biology:

- Extract organism names and arrow endpoints/direction.
- Use food->consumer semantics only after checking diagram legend/convention; if direction not established, return warning requiring correction.
- Create `energy_to` edges with no invented biological relationships beyond the diagram.

### 4.2 Human review/edit (minimal)

- Editable node labels (input field with accessible label).
- Editable relationships via text-based rows: source dropdown, relation fixed by domain, target dropdown; add/delete edge buttons.
- For physics: review proposed sequence and wires. For biology: explicit checkbox confirming arrow convention.
- Show warnings before Confirm. Disable Confirm until schema/semantics pass; re-run `/api/validate` after edits.
- Recompute long descriptions from confirmed graph, do not rely entirely on AI prose.

## 5. Error and privacy boundaries

- Validate image actual content via Pillow or equivalent. Do not allow SVG/XML uploads for live AI in P1 (use PNG/JPEG/WEBP only).
- Do not log uploaded image data or raw keys, and do not cache external provider responses in shared persistent storage by default.
- Show external processing disclosure before upload; avoid collecting personal/student records.
- Apply provider request timeout; return no-key and invalid-diagram states without crashing.
- Prevent stored or reflected XSS by rendering user/model strings with `textContent`, not unsanitized HTML.
- Do not evaluate arithmetic/source code returned from a flowchart image or LLM.
- Ensure server only listens locally by default (`127.0.0.1`); optional deployment after functionality is complete.

## 6. Core algorithms (pseudo-code)

### Physics

```python
validate_series(diagram):
    # check count/kinds/ids, validate sequence unique
    # undirected edge pairs must equal pairs in the ring, no extras
    return errors, derived_loop_wired

toggle_switch(diagram, switch_id):
    assert diagram.review_status == 'confirmed'
    assert validate_series(diagram).simulation_ready
    new_doc = deep_copy(diagram)
    new_doc.domain_model.switch_states[switch_id] = flip(old)
    bulbs_on = all(s == 'closed' for s in new_doc.domain_model.switch_states.values())
    return new_doc, plain_language_announcement(bulbs_on)
```

### Biology

```python
remove_organism(diagram, organism_id):
    assert diagram.review_status == 'confirmed'
    assert node_exists_and_is_organism(organism_id)
    new_doc = deep_copy(diagram)
    removed = [e for e in new_doc.edges if organism_id in (e.source, e.target)]
    new_doc.edges = [e for e in new_doc.edges if e not in removed]
    new_doc.nodes = [n for n in new_doc.nodes if n.id != organism_id]
    return new_doc, exact_removed_relationships(removed)
```

## 7. Explicit dependencies between modules

1. Pydantic models + JSON schema -> validators -> deterministic engines/tests.
2. Engines + verified fixtures -> static accessible UI -> integration test.
3. Provider adapter + image upload -> normalization -> review editor -> confirm -> existing explorer.
4. Optional TTS and flowchart only after 1–3 are working.

## 8. Useful official docs

- Gemini image understanding: https://ai.google.dev/gemini-api/docs/image-understanding
- Python GenAI SDK: https://googleapis.github.io/python-genai/
- W3C keyboard authoring practices: https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- W3C complex diagram descriptions: https://www.w3.org/WAI/tutorials/images/complex/


---

# SOURCE: docs/ACCESSIBILITY_AND_TESTS.md

# SenseGraph — Accessibility Requirements & Test Plan

## 1. Accessibility is a core feature

SenseGraph must work for keyboard-only and screen reader users. Design target: **WCAG 2.2 AA principles**, without claiming audited compliance. Prefer semantic HTML and native controls over custom ARIA widgets.

## 2. Page semantics

- `<html lang="en">`; correct main heading H1 and hierarchical H2/H3.
- Skip-to-content link visible on focus; one main landmark.
- `<label>` for file input, domain selection, editing fields.
- Use `<button>` for actions; do not simulate button behavior using generic `div`/`span`.
- Images receive concise alternate text and a **separate long textual description** of essential diagram structure.
- Node/edge data shown in actual HTML lists/definition lists. Images and canvas are supplementary; users never need to inspect a picture to access relationships.
- Every scientific change conveys state by words, not color alone. Example: "Switch S1: closed; Bulb 1: on".
- Good contrast, readable font, avoid small grey body text; support browser zoom 200%.

## 3. Keyboard contract

| Key | Required behavior |
|---|---|
| `Tab` | Move forward across native links, buttons, inputs, node selectors, actions |
| `Shift+Tab` | Move backward without traps |
| `Enter` | Activate focused button / submit labeled form |
| `Space` | Activate focused native button or checkbox |
| `Esc` | Exit optional modal; P0 avoid modals entirely |
| Arrow keys | **Not custom-required** for P0; if using complex tree/graph widgets later, implement established WAI-ARIA patterns and test them |

Selecting a node displays its name, category, description, connected neighbors and available actions. The new information should be discoverable by screen reader and a concise summary announced in `aria-live="polite"`/`role="status"`. Avoid reading the whole page repeatedly. Focus stays predictable; after changing context, position focus only when it helps the user, and do not steal it during typing.

## 4. Proposed screen layout

1. Skip link + app title.
2. Domain selection and Example / Upload mode.
3. Current diagram title, provenance label (Fixture vs Live AI), review state, long overview.
4. Structured **Objects** list with native Select buttons.
5. **Selected object detail** and connected objects list with Navigate buttons.
6. **Experiment controls** (e.g. toggle switch / remove organism), result status area.
7. Reset button restoring confirmed baseline.
8. Image preview for sighted users with linked textual long description; NOT required for core function.

## 5. Screen reader behavior examples

**Physics:** "Switch S1, button. Open. Connected to battery and bulb. Press Enter for details." When action is activated: "Switch S1 closed. Series circuit complete. Bulb 1 is now on."

**Biology:** "Rabbit, organism. Receives energy from grass. Provides energy to fox." After removing rabbit: "Rabbit removed from this diagram. Removed two relationships: grass to rabbit; rabbit to fox. This does not predict population changes."

The exact wording can differ, but it must be understandable without visual inspection.

## 6. Manual keyboard acceptance sequence

1. Load page. Press Tab; skip link appears and works.
2. Without mouse, choose "Explore example circuit" and activate with Enter.
3. Listen/read diagram overview and domain/source label.
4. Navigate to each object; select Switch S1 using Tab + Enter.
5. Activate "Close switch" using Space or Enter. Verify status announced and bulb shows ON in text.
6. Activate "Reset". State returns to switch OPEN, bulb OFF.
7. Switch to food web example; navigate rabbit relationships.
8. Remove rabbit. Verify exact removed relations read out, graph updates, reset restores.
9. Tab through *all* controls; no keyboard trap or invisible action.
10. If live AI configured: keyboard-only upload, visible consent, analyze, review/edit, confirm and explore.

Where possible test Windows Chrome + NVDA and macOS Safari + VoiceOver; document which combinations were **actually** tested.

## 7. Automated tests (minimum coverage)

### Model and validator tests

- Accept both valid bundled fixtures.
- Reject duplicate node IDs, duplicate edge IDs and edges referencing unknown nodes.
- Reject bad domain, bad component kinds, invalid `energy_to` direction field/missing IDs.
- Physics: accept exactly 1 battery + 1 switch + 1 or 2 bulbs with exactly one ring.
- Physics: reject missing wire, extra edge, non-series branch, two batteries, unknown switch ID, dangling node.
- Biology: reject feeding edge with nonexistent organism; reject `wire` in food web.
- Reject simulation when `review_status=unreviewed`.

### Simulation tests

- Physics default switch OPEN -> bulb OFF.
- Toggle switch -> CLOSED and bulbs ON; toggle -> OPEN and OFF.
- Physics two bulbs in same series -> both ON only if loop complete and switch closed.
- Biology removal of rabbit removes rabbit and exactly all incident edges; unrelated edges remain.
- Original source diagram remains unchanged (deep copy / immutability).
- Reset restores baseline in frontend or relevant state helper.

### API tests

- `/api/health` indicates correct provider configuration, no secret leakage.
- Both example endpoints return correct source.mode `fixture`.
- Unsupported example returns 404.
- Invalid upload MIME/oversize/corrupt image returns proper error, not 500.
- Missing API key -> explicit 503; never returns fake fixture graph as AI response.
- Mock Gemini response -> parser+validator -> `unreviewed` document; explicit confirmation required.
- Unknown action/type/target -> graceful 400/422.

### Accessibility smoke checks

- Keyboard focus indicator shown, no elements with click-only handlers.
- Key controls have accessible names, results in `role=status`/`aria-live=polite`.
- `axe-core` browser check if feasible; manual verification still required.

## 8. Empirical evaluation protocol

For an extraction benchmark, label a small set of test images (5–10 unique images/domain) manually with expected node names and edge pairs. Use the exact same evaluation convention (physics undirected wires; biology directed energy edges). Report:

- `node_precision = correct_extracted_nodes / extracted_nodes`
- `node_recall = correct_extracted_nodes / expected_nodes`
- `edge_precision = correct_extracted_edges / extracted_edges`
- `edge_recall = correct_extracted_edges / expected_edges`

Handle empty denominators explicitly. Also report number of invalid/ambiguous extractions and number of corrections required. **Do not invent accuracy scores**, and don't use fixture cases to claim vision extraction performance.

## 9. Test log template

| Date | Environment | Test | Pass/Fail | Evidence/Notes |
|---|---|---|---|---|
| YYYY-MM-DD | Windows/Chrome + NVDA | Full keyboard circuit walkthrough | Not run | ... |
| YYYY-MM-DD | Windows/Chrome | Food-web remove/reset | Not run | ... |
| YYYY-MM-DD | Gemini configured | Live image extraction | Not run | ... |

## 10. Official references

- https://www.w3.org/WAI/tutorials/images/complex/
- https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- https://www.w3.org/WAI/fundamentals/accessibility-principles/


---

# SOURCE: docs/ROADMAP_AND_SUBMISSION.md

# SenseGraph — 7-Day Engineering Roadmap & Devpost Checklist

## Timeline (local time: Asia/Ho_Chi_Minh)

**Official submission deadline:** 2026-11-21 23:59 EST = **2026-11-22 11:59 ICT**. Aim to submit **on November 21 Vietnam time** with a buffer. Demo Day November 24 EST; refer to Discord for live or prerecorded logistics.

| Day | Objective | Acceptance gate |
|---|---|---|
| Nov 15 | Finalize scope, fixtures, contracts, set up Git repo | PRD clear, repo initialized |
| Nov 16 | Scaffold FastAPI, fixtures, models, validators, tests | Two example APIs return valid graphs |
| Nov 17 | Physics + Biology deterministic engines | All tests for scientific actions pass |
| Nov 18 | Accessible UI, keyboard exploration | Full fixture walkthrough without mouse |
| Nov 19 | Real Gemini upload integration, review & edit | At least 1 genuine image extraction works if key configured |
| Nov 20 | Test live sample images, fix major errors, README | Known limitations documented, tests pass |
| Nov 21 | Demo recording (<=6m), upload public/unlisted, Devpost | Repository, video, project form submitted |

**Fallback if behind:** Make the two fixture journeys reliable, then prioritize genuine AI image extraction of one supported image and disclosure. Do not trade away a functional project for untested new modules.

## Must-have submission assets

- [ ] Public GitHub repository with source code.
- [ ] README: project goal, setup (Windows), screenshots, supported/unsupported diagrams, architecture and tests.
- [ ] README disclosures: external AI provider, AI coding assistants (e.g. Codex), attribution for libraries/diagram images, work created during event.
- [ ] Demo video <= 6 minutes on YouTube or Vimeo, publicly accessible or unlisted.
- [ ] Devpost description: problem, target users, primary **Education** track, AI use, product features, challenges, learning and next steps.
- [ ] Individual participant added to Devpost submission.
- [ ] Demo Day participation November 24 EST, live or prerecorded instructions checked in Discord.
- [ ] If participation certificate desired, request it after complete submission + Demo Day participation, per organizers' guidance.
- [ ] Do not publish personal/sensitive diagrams or unauthorized copyrighted material.

## Suggested 5-minute demo (adapt after actual implementation)

| Approx time | Content |
|---|---|
| 0:00–0:35 | Real challenge: visual STEM diagrams and access barriers |
| 0:35–1:00 | SenseGraph overview and supported scope |
| 1:00–2:05 | Load circuit fixture, keyboard navigation, switch on/off and explanation |
| 2:05–3:00 | Load food-web fixture, navigate directional relations, remove & reset |
| 3:00–4:00 | Actual live AI extraction: upload image, show review/correction and confirm (only if truly working) |
| 4:00–4:35 | Architecture: vision -> semantic graph -> deterministic domain engine |
| 4:35–5:00 | Testing, what was learned, remaining limits, future work |

Do not record claims of live AI or accessibility validation without actually carrying them out. When live AI isn't available, make that transparent and focus on genuine accessible interaction and documented AI development contribution.

## Suggested Devpost copy starter (edit to match the finished implementation)

**Project title:** SenseGraph — Explore STEM Beyond Sight

**Elevator pitch:** SenseGraph turns selected STEM diagrams into interactive, accessible structures that learners can explore with a keyboard and screen reader. Instead of only captioning an image, it makes relationships navigable and enables simple verified experiments.

**Problem:** Important STEM concepts are often encoded visually as wires, arrows, nodes and spatial relations. A short alt-text caption may not let a blind learner explore each relation or modify a model independently.

**Solution:** For basic series circuits and food webs, SenseGraph represents a diagram as a semantic graph, offers accessible descriptions and navigation, and uses deterministic domain logic to explain changes. When configured, a vision model proposes a graph from a user-uploaded image; the user reviews it before simulations.

**AI disclosure:** [Fill in the real image model, exact SDK/service, Codex assistance, which features were implemented and tested. If live extraction is not delivered, state this explicitly.]

**Challenges & lessons:** [Actual, specific technical problems encountered and resolutions; not fictional achievements.]

**Limitations:** Physics supports simple series loops, Biology supports direct food-web relationships, extracted diagram structure needs review, and formal user studies are future work.

**What's next:** Flowcharts, graph/chart sonification, user testing with blind learners and educators, improved error recovery, optional voice control.

## Judging alignment (20% each per official rules)

1. Problem & Impact — educational accessibility, narrow user journey, honest research limitations.
2. Use of AI — actual image-to-graph interpretation if available; transparently disclose AI coding assistance.
3. Functionality — fully working deterministic exploration and simulation on two domains.
4. Learning & Growth — show actual errors, tests, corrections and research learnings.
5. Presentation — clear keyboard-first user story and truthful video.

Official rules: https://stem2connect-online-hackathon.devpost.com/rules


---

# SOURCE: docs/DECISIONS.md

# Architecture Decisions & Open Risks

## Chosen decisions (2026-11-15)

- D1: **Simple web app**, no auth. Reasons: one solo developer and short hackathon deadline.
- D2: **Two P0 domains**, flowcharts a stretch goal. Reasons: demonstrated depth beats shallow support of many domains.
- D3: **Semantic graph + domain-specific payload**. Reasons: reuse accessible explorer while respecting different science semantics.
- D4: **Single-loop series physics** only. Reasons: honest deterministic simulation within deadline; electrical network analysis is much harder.
- D5: **Directed food web, food -> consumer** and relationship-change simulation only. Reasons: avoid fabricated population predictions.
- D6: **Native keyboard widgets first**, no custom graph keyboard shortcuts. Reasons: predictable browser + screen reader support.
- D7: **Explicit fixture vs live AI provenance**. Reasons: do not misrepresent the capability to judges or end users.
- D8: **Provider adapter** with Gemini as initial multimodal implementation. Reasons: swap if availability/pricing changes.

## Open risks and mitigation

| Risk | Mitigation |
|---|---|
| AI mistakes a wire or food web arrow | Require human review, validation; block unsupported simulation |
| User has no API key / quota | Fixture mode remains useful, but accurately disclose lack of live extraction |
| Inconsistent AI structured output | Pydantic schema, constrained prompt, robust 422 error |
| Hard to test with blind students in one week | Test keyboard + available screen reader, disclose lack of formal user studies |
| Two domains delay final submission | Deliver physics slice first, then biology; stop feature work before video day |
| Public demo exposes private image | Prefer original/curated non-sensitive diagrams, no persistent upload/logging |
| Model is changed/deprecated | Configurable `GEMINI_MODEL`, documented provider errors |

