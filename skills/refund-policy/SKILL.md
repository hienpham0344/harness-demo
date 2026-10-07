---
name: refund-policy
description: Tra cứu và áp dụng chính sách hoàn tiền cho khách hàng dựa trên ngày mua hàng. Dùng khi người dùng hỏi về hoàn tiền, điều kiện đổi trả/hoàn tiền, yêu cầu hoàn tiền hoặc kiểm tra chính sách hoàn tiền.
---

# Refund Policy

Hướng dẫn tra cứu và áp dụng chính sách hoàn tiền phù hợp theo ngày mua hàng của khách hàng.

## Các bước thực hiện

1. **Kiểm tra thông tin đầu vào:**
   Kiểm tra xem người dùng đã cung cấp đủ 3 thông tin sau hay chưa:
   - Ngày mua hàng.
   - Ngày yêu cầu hoàn tiền.
   - Trạng thái kích hoạt của sản phẩm (đã kích hoạt hay chưa kích hoạt).

   ⚠️ **QUAN TRỌNG:** Nếu thiếu bất kỳ thông tin nào trong 3 thông tin trên (ví dụ: chưa cung cấp trạng thái kích hoạt), **KHÔNG ĐƯỢC TỰ GIẢ ĐỊNH**. Hãy dừng lại và hỏi người dùng để làm rõ thông tin còn thiếu trước khi đưa ra kết luận.

2. **Tìm kiếm danh sách tài liệu chính sách:**
   - Dùng tool `list_files` với đường dẫn `data/policies` để liệt kê các file chính sách hiện có trong thư mục này.
   - Không được tự đoán trước tên file hay phụ thuộc vào một tên file cố định, vì tên file chính sách có thể bị thay đổi.

3. **Đọc nội dung chính sách và xác định chính sách áp dụng:**
   - Dùng tool `read_file` để đọc nội dung từng file tìm được trong `data/policies`.
   - Đọc kỹ phạm vi ngày hiệu lực trong từng tài liệu.
   - Chọn chính sách áp dụng dựa trên **ngày mua hàng** của khách hàng (không dựa trên ngày yêu cầu hoàn).

4. **Kiểm tra điều kiện và tính toán:**
   - Số ngày đã qua = khoảng cách số ngày lịch giữa ngày yêu cầu hoàn tiền và ngày mua hàng (ngày yêu cầu hoàn trừ ngày mua hàng). Dùng ngày yêu cầu trong câu hỏi, không dùng ngày hiện tại của hệ thống.
   - So sánh số ngày đã qua với thời hạn cho phép hoàn tiền trong chính sách:
     - Nếu số ngày đã qua nhỏ hơn hoặc bằng đúng giới hạn thời gian (ví dụ: bằng đúng 7 ngày hoặc 14 ngày), vẫn đủ điều kiện về thời gian.
     - Nếu vượt quá giới hạn, không đủ điều kiện hoàn tiền vì đã quá thời hạn.
   - Kiểm tra điều kiện kích hoạt: Nếu sản phẩm đã kích hoạt, không được hoàn tiền.
   - Xác định mức phí hoàn tiền theo chính sách áp dụng nếu đủ điều kiện (ví dụ: không thu phí hoặc thu 10% giá trị đơn hàng).

5. **Đọc mẫu định dạng câu trả lời:**
   - Đọc file template tham khảo `skills/refund-policy/references/answer-template.md` bằng tool `read_file`.
   - Trả lời người dùng theo đúng cấu trúc của template, bao gồm:
     - Tên chính sách áp dụng
     - Đường dẫn tài liệu làm căn cứ (đường dẫn tương đối thực tế đã đọc, ví dụ: `data/policies/...`)
     - Số ngày đã qua
     - Trạng thái kích hoạt
     - Kết luận (đủ điều kiện hoặc không đủ điều kiện)
     - Mức phí hoàn tiền (nếu đủ điều kiện)
