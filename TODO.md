# TODO — Mock Data ISO 286 EdTech

## Yêu cầu 1: index.html (Frontend)
- [x] Phân tích cấu trúc hiện tại (MOCK_USERS không tồn tại, studentListText có sẵn)
- [x] Thêm biến `MOCK_USERS` (2 teacher + 5 student có mssv/className)
- [x] Sửa LoginScreen quick-fill dùng MOCK_USERS
- [x] Thay `studentListText` bằng 5 SV mới

## Yêu cầu 2: main.py (Backend)
- [x] Đồng bộ `USERS` (thêm 2 GV + 5 SV)
- [x] Tạo biến `mock_assignments_db` (3 đề thi đầy đủ thông số)

## Follow-up
- [x] Smoke test (import main.py) — OK: 9 users, 3 assignments, exam codes ME2026-2110481/2/3
