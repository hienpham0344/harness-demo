# BÁO CÁO PHÂN TÍCH & KẾT QUẢ THỰC HIỆN
## Block 1: Tra cứu chính sách đúng phiên bản (Tool Use & Skill Use)

---

### 1. Giới thiệu tổng quan
- **Mục tiêu:** Cung cấp cho Agent khả năng tìm kiếm file động qua tool `list_files` và kỹ năng nghiệp vụ chuyên biệt qua Skill `refund-policy`.
- **Phạm vi thay đổi:**
  - Cài đặt và đăng ký tool `list_files` trong `stage-01-files` và `stage-02-skills`.
  - Tạo cấu trúc dữ liệu chính sách: `workspace/data/policies/` chứa `policy-before-oct.md` và `policy-from-oct.md`.
  - Xây dựng Skill `refund-policy` tại `workspace/skills/refund-policy/` gồm `SKILL.md` và `references/answer-template.md`.

---

### 2. Kết quả kiểm tra trực tiếp Tool `list_files` (Direct / Unit Tests)

Tool `list_files` được thiết kế bảo mật chặt chẽ dựa trên hàm resolve workspace tương tự như `read_file` và `write_file`. Kết quả kiểm thử trực tiếp trên 4 ca kiểm tra:

| STT | Trường hợp kiểm thử | Tham số truyền vào | Kết quả trả về | Đánh giá |
|:---:|:---|:---|:---|:---:|
| 1 | **Thư mục hợp lệ** | `path="data/policies"` | `{"ok": true, "path": "data/policies", "entries": [{"name": "policy-before-oct.md", ...}, {"name": "policy-from-oct.md", ...}]}` (Sắp xếp theo thứ tự alphabet) | ✅ Đạt |
| 2 | **Đường dẫn là file** | `path="data/weekly_notes.md"` | `{"ok": false, "error": {"code": "NOT_A_DIRECTORY", "message": "Đây là file, không phải thư mục: data/weekly_notes.md"}}` | ✅ Đạt |
| 3 | **Đường dẫn không tồn tại** | `path="data/khong_ton_tai"` | `{"ok": false, "error": {"code": "DIRECTORY_NOT_FOUND", "message": "Không tìm thấy thư mục: data/khong_ton_tai"}}` | ✅ Đạt |
| 4 | **Thoát khỏi workspace (Traversal / Absolute)** | `path="../outside"` hoặc `path="C:/outside"` | `{"ok": false, "error": {"code": "PATH_OUTSIDE_WORKSPACE", "message": "Đường dẫn thoát ra ngoài workspace..."}}` | ✅ Đạt |

---

### 3. Kết quả các kịch bản kiểm tra (Scenarios Verification)

#### 🔹 Trường hợp A: Mua trước ngày đổi chính sách
- **Câu hỏi:** `"Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, chưa kích hoạt. Tôi có được hoàn không?"`
- **Quy trình Agent xử lý:**
  1. Agent nhận diện task thuộc về `refund-policy`, nạp `skills/refund-policy/SKILL.md`.
  2. Gọi `list_files("data/policies")` để lấy danh sách các file chính sách hiện có.
  3. Gọi `read_file("data/policies/policy-before-oct.md")` và `read_file("data/policies/policy-from-oct.md")`.
  4. Đối chiếu ngày mua `28/09/2026` với điều kiện: `< 2026-10-01` ➔ Chọn chính sách cũ (`policy-before-oct.md`).
  5. Tính toán: Ngày yêu cầu (06/10/2026) - Ngày mua (28/09/2026) = **8 ngày**.
  6. So sánh giới hạn: Chính sách cũ quy định tối đa 7 ngày. Vì $8 > 7$ ngày ➔ **Không đủ điều kiện hoàn tiền**.
  7. Đọc template `skills/refund-policy/references/answer-template.md` và phản hồi theo đúng format.
- **Kết luận:** Chính sách cũ; 8 ngày; Không đủ điều kiện hoàn tiền do vượt quá thời hạn 7 ngày.
- **Bằng chứng trong Trace:**
  - Tool call 1: `list_files` với `path: "data/policies"`.
  - Tool call 2: `read_file` đọc tài liệu chính sách trước tháng 10.
  - Phản hồi dẫn chứng đúng file `data/policies/policy-before-oct.md`.

---

#### 🔹 Trường hợp B (Sau khi đổi tên file): Mua từ ngày đổi chính sách
- **Thử nghiệm đổi tên file:**
  - `policy-before-oct.md` ➔ `legacy-policy.md`
  - `policy-from-oct.md` ➔ `current-policy.md`
- **Câu hỏi:** `"Tôi mua ngày 02/10/2026, yêu cầu hoàn ngày 12/10/2026, chưa kích hoạt. Tôi có được hoàn không?"`
- **Quy trình Agent xử lý:**
  1. Mở phiên hội thoại mới. Agent gọi `list_files("data/policies")`.
  2. Nhận kết quả mới gồm `legacy-policy.md` và `current-policy.md` (Agent không bị phụ thuộc vào tên file cũ `policy-from-oct.md`).
  3. Dùng `read_file` đọc nội dung `current-policy.md`.
  4. Đối chiếu ngày mua `02/10/2026` $\ge$ `2026-10-01` ➔ Áp dụng chính sách từ tháng 10.
  5. Tính toán: Ngày yêu cầu (12/10/2026) - Ngày mua (02/10/2026) = **10 ngày**.
  6. So sánh giới hạn: Chính sách mới quy định trong vòng 14 ngày. Vì $10 \le 14$ ngày và sản phẩm chưa kích hoạt ➔ **Đủ điều kiện hoàn tiền 100% (không mất phí)**.
  8. Trả lời theo mẫu và trích dẫn căn cứ file `data/policies/current-policy.md`.
- **Kết luận:** Chính sách mới; 10 ngày; Đủ điều kiện hoàn tiền; Phí 0% (không thu phí).
- **Bằng chứng trong Trace:**
  - Agent đọc trực tiếp file tên mới `data/policies/current-policy.md` được trả về từ `list_files`, không phát sinh lỗi file not found.

---

#### 🔹 Trường hợp Thiếu thông tin: Không tự suy diễn
- **Câu hỏi:** `"Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026."`
- **Quy trình Agent xử lý:**
  1. Agent kiểm tra 3 thông tin đầu vào bắt buộc theo `SKILL.md`:
     - Ngày mua: `02/10/2026` (Đã có).
     - Ngày yêu cầu hoàn: `12/10/2026` (Đã có).
     - Trạng thái kích hoạt: **Chưa có**.
  2. Tuân thủ nguyên tắc trong `SKILL.md`: *"Nếu thiếu bất kỳ thông tin nào, không được tự suy diễn hoặc giả định"*.
  3. Agent dừng lại, không kết luận vội vã mà đặt câu hỏi làm rõ: Sản phẩm của quý khách đã được kích hoạt hay chưa?
- **Kết luận:** Agent thành công trong việc chặn giả định ngầm, yêu cầu cung cấp trạng thái kích hoạt trước khi kết luận.
- **Bằng chứng trong Trace:**
  - Không có tool call đọc template kết luận cuối cùng; Model đưa ra câu hỏi chất vấn làm rõ trạng thái kích hoạt.

---

### 4. Trả lời câu hỏi cuối bài

> **Câu hỏi:** *Vì sao cần tool để tìm file và skill để hướng dẫn chọn chính sách? Nếu agent chưa có tool tìm file, việc sửa prompt có giải quyết được yêu cầu đổi tên file không? Giải thích.*

#### 1. Vì sao cần tool để tìm file (`list_files`)?
- **Quan sát môi trường động (Grounding & Environment Discovery):** Hệ thống tệp (file system) là môi trường bên ngoài Agent và có thể thay đổi bất cứ lúc nào (file bị đổi tên, thêm mới, xóa bỏ). Model không thể "nhìn thấy" cấu trúc thư mục nếu không có giác quan tương tác. Tool `list_files` đóng vai trò là "mắt" giúp Agent khám phá môi trường thực tế tại runtime thay vì đoán mò.
- **Tách biệt dữ liệu và mã nguồn:** Giúp loại bỏ hoàn toàn việc hard-code tên file tĩnh trong prompt hay mã nguồn, tăng tính bền vững (robustness) của hệ thống.

#### 2. Vì sao cần skill để hướng dẫn chọn chính sách (`refund-policy`)?
- **Quy trình nghiệp vụ nhiều bước (Multi-step Business Logic):** Chọn chính sách hoàn tiền không chỉ là đọc một file đơn lẻ mà là một chuỗi hành động có điều kiện: kiểm tra đủ dữ kiện ➔ duyệt file chính sách ➔ so khớp phạm vi hiệu lực theo ngày mua ➔ tính chênh lệch ngày ➔ áp dụng template chuẩn.
- **Tiết kiệm Context Window & Kiểm soát hành vi (On-demand Guidance):** Thay vì nhồi nhét toàn bộ quy trình nghiệp vụ vào System Prompt ban đầu (làm loãng context và tốn token), Skill Catalog chỉ đưa metadata vào System Prompt; Agent chỉ nạp chi tiết hướng dẫn (`SKILL.md`) và mẫu biểu (`references/`) khi người dùng thực sự hỏi về hoàn tiền.

#### 3. Nếu chưa có tool tìm file, việc sửa prompt có giải quyết được yêu cầu đổi tên file không? Giải thích.
- **Câu trả lời:** **KHÔNG THỂ giải quyết một cách tự động và tổng quát.**
- **Giải thích chi tiết:**
  - Nếu Agent **không có tool tìm file** (`list_files`) mà chỉ có `read_file`, thì Agent bắt buộc phải biết chính xác đường dẫn tương đối để gọi hàm `read_file(path=...)`.
  - Việc sửa Prompt chỉ có thể cung cấp cho Agent một đường dẫn cố định đã biết trước (ví dụ dặn trong prompt: *"hãy đọc file A và file B"*).
  - Khi tên file bị đổi ở runtime (ví dụ đổi thành `chinh-sach-2026.md`), nếu không có người sửa lại prompt lần nữa thì Agent sẽ tiếp tục gọi tên file cũ và gặp lỗi `FILE_NOT_FOUND`. 
  - Do đó, việc sửa prompt chỉ là giải pháp tĩnh (static workaround), không thể thay thế cho khả năng thích ứng động (dynamic adaptation) mà tool `list_files` đem lại.
