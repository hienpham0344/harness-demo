# 📋 Báo Cáo & Bài Nộp Block 1: Tra cứu chính sách đúng phiên bản (Tool Use & Skill Use)

> **Môn học / Chuyên đề:** Agentic AI  
> **Nội dung:** Block 1 – Tích hợp Tool Use động (`list_files`) và Skill chuyên biệt (`refund-policy`) xử lý nghiệp vụ tra cứu chính sách theo mốc thời gian.

---

## 📑 Mục lục
1. [Giới thiệu tổng quan](#1-giới-thiệu-tổng-quan)
2. [Cấu trúc thư mục bài nộp](#2-cấu-trúc-thư-mục-bài-nộp)
3. [Thiết kế & Bảo mật Tool `list_files`](#3-thiết-kế--bảo-mật-tool-list_files)
4. [Thiết kế Kỹ năng nghiệp vụ (`Skill: refund-policy`)](#4-thiết-kế-kỹ-năng-nghiệp-vụ-skill-refund-policy)
5. [Kết quả thực nghiệm & Traces](#5-kết-quả-thực-nghiệm--traces)
6. [Trả lời các câu hỏi phân tích cốt lõi](#6-trả-lời-các-câu-hỏi-phân-tích-cốt-lõi)
7. [Hướng dẫn cài đặt & Chạy thử nghiệm](#7-hướng-dẫn-cài-đặt--chạy-thử-nghiệm)

---

## 1. Giới thiệu tổng quan
Trong môi trường thực tế, hệ thống tệp và tài liệu chính sách của doanh nghiệp luôn biến động theo thời gian (chính sách mới ban hành, chính sách cũ hết hiệu lực, file bị đổi tên hoặc phân loại lại). Nếu Agent chỉ hoạt động dựa trên các quy tắc tĩnh được nhồi nhét sẵn trong prompt, hệ thống sẽ gặp các vấn đề nghiêm trọng:
- **Tràn ngữ cảnh (Context Bloat):** Prompt bị phình to làm giảm độ tập trung và tăng chi phí token.
- **Dễ gãy vỡ (Fragility):** Khi file bị đổi tên hoặc thay đổi đường dẫn, Agent sẽ lập tức báo lỗi do không thể tự tìm kiếm.
- **Suy diễn sai lệch:** Agent có xu hướng tự đoán kết quả khi dữ liệu đầu vào chưa rõ ràng.

**Mục tiêu bài nộp:**
- Xây dựng tool `list_files` an toàn để Agent tự động khám phá cấu trúc thư mục tại runtime.
- Xây dựng Skill `refund-policy` theo kiến trúc **Skill On-demand** (chỉ tải hướng dẫn và template khi có yêu cầu liên quan).
- Đảm bảo Agent tuân thủ nghiêm ngặt nguyên tắc **"Không tự suy diễn khi thiếu dữ kiện"**.

---

## 2. Cấu trúc thư mục bài nộp

```text
submission-block-1/
├── code/
│   ├── stage-01/                     # Stage 01: Triển khai các Tool cơ bản
│   │   ├── agent.py                  # Khởi tạo model và agent LangChain
│   │   ├── tools_files.py            # Hàm xử lý file (read_file, write_file, list_files)
│   │   └── tools_init.py             # Export các tool đã đăng ký
│   └── stage-02/                     # Stage 02: Tích hợp Skill Catalog
│       ├── agent.py                  # Agent tích hợp Skill Catalog trong System Prompt
│       ├── tools_files.py            # Kế thừa và mở rộng công cụ thao tác file
│       └── tools_init.py             # Export toolset đầy đủ
├── data/
│   └── policies/                     # Dữ liệu chính sách thực tế
│       ├── policy-before-oct.md      # Chính sách áp dụng cho đơn mua trước 01/10/2026
│       └── policy-from-oct.md        # Chính sách mới áp dụng từ ngày 01/10/2026
├── skills/
│   └── refund-policy/                # Kỹ năng xử lý chính sách hoàn tiền
│       ├── SKILL.md                  # Hướng dẫn quy trình 7 bước nghiệp vụ
│       └── references/
│           └── answer-template.md    # Template Markdown phản hồi chuẩn mực
├── traces/                           # Nhật ký hội thoại & bằng chứng tool calling
│   ├── 20261006-234553_...jsonl      # Trace chạy stage-02 ban đầu
│   ├── 20261007-110218_...jsonl      # Trace kịch bản Case A (mua trước tháng 10)
│   ├── 20261007-110331_...jsonl      # Trace kịch bản Case B (sau khi đổi tên file)
│   └── 20261007-110411_...jsonl      # Trace kịch bản Case C (thiếu thông tin)
├── analysis.md                       # Báo cáo phân tích chuyên sâu
├── test_agent.py                     # Script kiểm thử Agent độc lập qua Groq API
├── .env.example                      # Mẫu cấu hình biến môi trường
├── .gitignore                        # Loại trừ file .env bảo vệ API Key
└── README.md                         # Báo cáo tổng hợp bài nộp
```

---

## 3. Thiết kế & Bảo mật Tool `list_files`

Tool `list_files` được xây dựng với cơ chế phân giải đường dẫn tương đối an toàn (`_resolve`), bảo vệ hệ thống trước các kỹ thuật tấn công phổ biến:

```python
def _list(workspace: Path, path: str) -> dict:
    target, error = _resolve(workspace, path)
    if error:
        return error
    ...
```

### Kết quả kiểm thử trực tiếp (Direct Unit Tests):

| STT | Trường hợp kiểm thử | Tham số truyền vào | Kết quả trả về | Đánh giá |
|:---:|:---|:---|:---|:---:|
| 1 | **Thư mục hợp lệ** | `path="data/policies"` | `{"ok": true, "path": "data/policies", "entries": [...]}` (Sắp xếp alphabet) | ✅ Đạt |
| 2 | **Đường dẫn là file** | `path="data/weekly_notes.md"` | `{"ok": false, "error": {"code": "NOT_A_DIRECTORY"}}` | ✅ Đạt |
| 3 | **Đường dẫn không tồn tại** | `path="data/khong_ton_tai"` | `{"ok": false, "error": {"code": "DIRECTORY_NOT_FOUND"}}` | ✅ Đạt |
| 4 | **Thoát khỏi workspace (Traversal)** | `path="../outside"` hoặc `path="C:/outside"` | `{"ok": false, "error": {"code": "PATH_OUTSIDE_WORKSPACE"}}` | ✅ Đạt |

---

## 4. Thiết kế Kỹ năng nghiệp vụ (`Skill: refund-policy`)

Skill được thiết kế theo chuẩn **Agentic Skill Architecture**:
1. **Metadata trong Catalog:** Chỉ nạp `name` và `description` vào System Prompt ban đầu để Model nhận diện khi nào cần dùng.
2. **Quy trình nạp On-demand (`SKILL.md`):** Khi task liên quan đến hoàn tiền, Agent tự động gọi `read_file("skills/refund-policy/SKILL.md")`.
3. **Quy tắc 3 dữ kiện bắt buộc:**
   - Ngày mua hàng (`purchase_date`).
   - Ngày yêu cầu hoàn tiền (`request_date`).
   - Trạng thái kích hoạt sản phẩm (`is_activated`).
   - *Ràng buộc:* **Tuyệt đối không tự suy diễn hoặc giả định nếu thiếu bất kỳ dữ kiện nào.**
4. **Phản hồi theo khuôn mẫu:** Tải template `references/answer-template.md` để đảm bảo định dạng nhất quán.

---

## 5. Kết quả thực nghiệm & Traces

### 🔹 Kịch bản A: Mua trước ngày đổi chính sách
- **Câu hỏi:** *"Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, chưa kích hoạt. Tôi có được hoàn không?"*
- **Thực thi:**
  1. Agent gọi `list_files("data/policies")` $\rightarrow$ nhận danh sách file.
  2. Đọc `policy-before-oct.md` (vì ngày mua $28/09/2026 < 01/10/2026$).
  3. Tính toán: Ngày yêu cầu (06/10) - Ngày mua (28/09) = **8 ngày**.
  4. Giới hạn chính sách cũ: tối đa 7 ngày. Vì $8 > 7$ ngày $\rightarrow$ **Không đủ điều kiện hoàn tiền**.
- **Kết quả:** Trả lời chính xác, trích dẫn căn cứ file `data/policies/policy-before-oct.md`.

### 🔹 Kịch bản B: Khả năng thích ứng khi đổi tên file động
- **Thử nghiệm:** Đổi tên file trong kho dữ liệu:
  - `policy-before-oct.md` $\rightarrow$ `legacy-policy.md`
  - `policy-from-oct.md` $\rightarrow$ `current-policy.md`
- **Câu hỏi:** *"Tôi mua ngày 02/10/2026, yêu cầu hoàn ngày 12/10/2026, chưa kích hoạt. Tôi có được hoàn không?"*
- **Thực thi:**
  1. Agent không bị phụ thuộc vào tên file cũ nhờ gọi `list_files("data/policies")`.
  2. Đọc file tên mới `current-policy.md`.
  3. Tính toán: $12/10 - 02/10 =$ **10 ngày** $\le 14$ ngày $\rightarrow$ **Đủ điều kiện hoàn tiền 100% (phí 0%)**.
- **Kết quả:** Vượt qua xuất sắc thử nghiệm đổi tên file mà không cần chỉnh sửa code hay prompt.

### 🔹 Kịch bản C: Xử lý khi thiếu dữ kiện đầu vào
- **Câu hỏi:** *"Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026."*
- **Thực thi:** Agent kiểm tra thấy thiếu trạng thái kích hoạt $\rightarrow$ **Dừng lại và đặt câu hỏi làm rõ**, không tự giả định sản phẩm chưa kích hoạt.

---

## 6. Trả lời các câu hỏi phân tích cốt lõi

### 1. Vì sao cần tool để tìm file (`list_files`)?
- **Khám phá môi trường (Environment Discovery):** Hệ thống tệp là môi trường động bên ngoài model. Model không thể tự nhìn thấy các file hiện hữu nếu không có công cụ quan sát. `list_files` đóng vai trò là "mắt" giúp Agent quan sát thực tế tại thời điểm chạy thay vì phỏng đoán.
- **Tách biệt dữ liệu và mã nguồn:** Loại bỏ hoàn toàn việc hardcode tên file tĩnh trong prompt.

### 2. Vì sao cần skill để hướng dẫn chọn chính sách (`refund-policy`)?
- **Quy trình nghiệp vụ nhiều bước (Multi-step Business Logic):** Xử lý chính sách đòi hỏi các bước xác định phiên bản, tính toán thời gian và định dạng kết quả.
- **Tiết kiệm Context Window & Kiểm soát hành vi:** Chỉ nạp hướng dẫn chi tiết khi cần, tránh làm loãng ngữ cảnh và giảm nguy cơ hallucination.

### 3. Nếu chưa có tool tìm file, việc sửa prompt có giải quyết được yêu cầu đổi tên file không?
- **Câu trả lời:** **KHÔNG THỂ giải quyết một cách tự động và tổng quát.**
- **Giải thích:** Việc sửa prompt chỉ là giải pháp tĩnh (static workaround) cho các tên file đã biết trước. Khi hệ sinh thái file tiếp tục thay đổi ở runtime, Agent thiếu công cụ khám phá sẽ ngay lập tức gặp lỗi `FILE_NOT_FOUND`. Chỉ có tool `list_files` mới mang lại khả năng thích ứng động (Dynamic Adaptation).

---

## 7. Hướng dẫn cài đặt & Chạy thử nghiệm

### 1. Yêu cầu môi trường
- Python 3.10+
- Khóa API của Groq (hoặc OpenAI-compatible endpoint)

### 2. Thiết lập biến môi trường
Tạo file `.env` tại thư mục gốc:
```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# OpenAI-compatible Configuration (dùng cho LangChain ChatOpenAI)
OPENAI_API_KEY=your_groq_api_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
MODEL_NAME=openai/gpt-oss-120b
```

### 3. Chạy kiểm thử Agent trực tiếp
Bài nộp đã chuẩn bị sẵn file script độc lập [test_agent.py](test_agent.py) tích hợp sẵn vòng lặp Agent Tool Calling:
```powershell
python test_agent.py
```
Script sẽ tự động kết nối mô hình `openai/gpt-oss-120b` trên Groq, thực thi chuỗi tool call `list_files` $\rightarrow$ `read_file` và đưa ra kết luận nghiệp vụ chính xác.
