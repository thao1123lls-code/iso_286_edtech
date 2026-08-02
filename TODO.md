# TODO - Nâng cấp Loading State (MouseLoadingOverlay) + Login & Phân quyền (RBAC)

## A. Nâng cấp Loading State - Con chuột chạy trên vòng quay (MouseLoadingOverlay)

- [x] 1. Thêm keyframes `wheelSpin` & `loadingBar` vào `tailwind.config` (animation mới)
- [x] 2. Tạo component `<MouseLoadingOverlay/>` trong `index.html`:
  - [x] 2a. Toàn màn hình `fixed inset-0 z-50`, nền `bg-slate-900/60 backdrop-blur-sm`
  - [x] 2b. Ảnh GIF con chuột/hamster chạy (danh sách `MOUSE_GIF_SOURCES`, tự fallback link kế tiếp)
  - [x] 2c. Fallback vòng quay hamster thuần CSS 🐹 khi mọi link GIF bị chặn
  - [x] 2d. Dòng thông báo `animate-pulse` + thanh tiến trình chạy (`animate-loadingBar`)
- [x] 3. Tích hợp vào `<GeneratorScreen/>`:
  - [x] 3a. Render overlay khi `isGenerating` (title: "Đang thiết kế bộ đề thi...")
  - [x] 3b. Render overlay khi `isExportingDocx` (title: "Đang đóng gói file Word...")
  - [x] 3c. Render overlay khi `isExportingPdf` (title: "Đang kết xuất file PDF...")
- [x] 4. Kéo dài `setTimeout` trong `handleGenerate` từ `400ms` → `2500ms` để thấy rõ hoạt ảnh
- [ ] 5. (Tùy chọn) Thay link GIF ưng ý trong mảng `MOUSE_GIF_SOURCES` nếu muốn

## B. Tích hợp Login & Phân quyền (RBAC) vào Hệ thống ISO 286 EdTech

### Các bước triển khai

- [x] 1. Cập nhật `requirements.txt`: thêm `pyjwt`, `passlib[bcrypt]`, `bcrypt`, `python-multipart`
- [x] 2. Viết lại `main.py`:
  - [x] 2a. Cấu hình JWT (SECRET_KEY, thuật toán HS256, thời hạn token)
  - [x] 2b. Mock Database `USERS` (giangvien/123/lecturer, sinhvien/123/student) với bcrypt
  - [x] 2c. Endpoint `POST /api/login` trả về JWT token + thông tin user
  - [x] 2d. Dependency `get_current_user` và `require_lecturer`
  - [x] 2e. Bảo vệ router: `/api/iso/*` cần đăng nhập, `/api/export/*` cần lecturer
- [x] 3. Cập nhật `index.html`:
  - [x] 3a. State `currentUser`, `token`; lưu/khôi phục từ `localStorage`
  - [x] 3b. Component `<LoginScreen/>` form đăng nhập Tailwind đẹp mắt
  - [x] 3c. Chưa đăng nhập -> hiển thị LoginScreen
  - [x] 3d. Sidebar: ẩn "Tạo Đề Tự Động" nếu role = student
  - [x] 3e. Header: hiển thị tên/role user + nút "Đăng xuất"
  - [x] 3f. `loadIsoDbFromApi` & `handleExportServer` gửi `Authorization: Bearer <token>`
- [x] 4. Kiểm thử:
  - [x] 4a. Cài dependencies: `pip install -r requirements.txt`
  - [x] 4b. Chạy server: `uvicorn main:app --reload`
  - [x] 4c. Test đăng nhập `giangvien` (có tab Tạo Đề) và `sinhvien` (không có tab Tạo Đề)



