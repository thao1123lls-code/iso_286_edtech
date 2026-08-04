# TODO - Xây dựng hàm build_dntu_exam_header() (Form Đề thi chuẩn DNTU)

## Steps
- [x] Step 1: Thêm hàm `build_dntu_exam_header()` vào `app/services/pdf_exam_header.py` (giữ nguyên toàn bộ code cũ).
  - [x] Phần 1: Bảng Phê duyệt (1 dòng x 2 cột, kẻ dọc giữa, không viền ngoài).
  - [x] Phần 2: Dòng phân cách (in nghiêng, size 9, căn giữa, Spacer trên dưới).
  - [x] Phần 3: Bảng Thông tin Đề thi (5 cột, dùng SPAN, Mã đề thi màu đỏ).
  - [x] Phần 4: Bảng Thông tin Thí sinh (BOX, Nested Table MSSV 7 ô).
  - [x] Phần 5: Bảng Điểm số & Ghi chú (Grid 2x4 + Box bullet points).
- [x] Step 2: Thêm demo trong `__main__` để tạo file mẫu `_exam_header_form_dntu.pdf`.
- [x] Step 3: Chạy `python app/services/pdf_exam_header.py` để kiểm tra (đã tạo thành công).
