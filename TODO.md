# TODO - Làm lại Đăng nhập & Upload (Xóa Mock Data)

## Frontend (index.html)
- [ ] 1. Xóa hoàn toàn khối `MOCK_USERS` (no mock data trong Login UI)
- [ ] 2. Viết lại `LoginScreen`: 2 tab [Đăng nhập Sinh Viên] / [Đăng nhập Giảng Viên]
       - Tab Sinh Viên: Input MSSV + Mật khẩu
       - Tab Giảng Viên: Input Tên đăng nhập + Mật khẩu
       - UI tĩnh, chỉ gọi /api/login khi bấm Submit
- [ ] 3. Thêm upload UI cho Giảng viên (`input type=file accept=".csv,.xlsx"` + nút upload)
       vào `GeneratorScreen` (gọi POST /api/students/upload)

## Backend (main.py)
- [ ] 4. Rà soát: không có endpoint GET /users hoặc GET /mock-data (đảm bảo không fetch user tự do)
- [ ] 5. Đảm bảo POST /api/students/upload hoàn chỉnh:
       - Dùng UploadFile đọc CSV
       - try-except xử lý đàng hoàng
       - Trích xuất 3 cột (MSSV, HoTen, Lop) và insert vào database

## Follow-up
- [ ] 6. Validate syntax main.py & index.html
