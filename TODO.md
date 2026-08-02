# TODO - Phát triển Cơ sở dữ liệu SQL cho bảng tra ISO 286

## Kiến trúc mục tiêu (Layered Architecture + Database Layer)
```
d:/iso-286-edtech/
├── main.py                          # Entry point (uvicorn main:app --reload) + lifespan seed DB
├── index.html                       # Frontend: tải bảng ISO 286 từ API (giữ fallback nhúng)
├── requirements.txt                 # Thêm sqlalchemy, pymysql, psycopg2-binary
├── schema.sql                       # DDL chuẩn MySQL/PostgreSQL cho bảng tra ISO 286
└── app/
    ├── core/
    │   ├── config.py                # + DATABASE_URL (mặc định SQLite, đổi biến môi trường -> MySQL/PostgreSQL)
    │   ├── utils.py                 # esc(), fmt_signed()
    │   └── pdf_fonts.py             # Đăng ký font TNR + styles PDF
    ├── db/                          # ⭐ TẦNG CƠ SỞ DỮ LIỆU MỚI
    │   ├── database.py              # engine + session (SQLAlchemy)
    │   ├── models.py                # ORM: IsoSizeRange, IsoItGrade, IsoDeviation, IsoFitLibrary
    │   ├── seed.py                  # Số hóa toàn bộ bảng tra ISO 286 (IT01-IT18, trục/lỗ a-zc/A-ZC)
    │   └── repository.py            # Data Access Layer (tra IT, sai lệch, khoảng kích thước)
    ├── models/
    │   └── schemas.py               # Pydantic models (không đổi)
    ├── services/
    │   ├── tolerance_service.py     # ⭐ ĐỌC DỮ LIỆU TỪ CSDL (repository), công thức làm fallback
    │   ├── docx_service.py          # Không đổi
    │   ├── pdf_service.py           # Không đổi
    │   └── export_service.py        # Không đổi
    └── api/
        └── routes/
            ├── export.py            # Không đổi
            └── iso.py               # ⭐ MỚI: GET /api/iso/tables trả bảng ISO 286 từ CSDL
```

## Các bước thực hiện
- [x] 0. Phân tích task & duyệt kế hoạch với người dùng
- [x] 1. Thêm thư viện SQL vào `requirements.txt` (sqlalchemy, pymysql, psycopg2-binary)
- [x] 2. Tạo `app/db/database.py` - engine + session (SQLite mặc định, hỗ trợ MySQL/PostgreSQL)
- [x] 3. Tạo `app/db/models.py` - ORM models: iso_size_ranges, iso_it_grades, iso_deviations (+ iso_fit_library)
- [x] 4. Tạo `app/db/seed.py` - số hóa toàn bộ bảng tra ISO 286 (IT01→IT18, sai lệch trục/lỗ a→zc, A→ZC)
- [x] 5. Tạo `app/db/repository.py` - Data Access Layer (tra cứu IT, sai lệch, khoảng kích thước)
- [x] 6. Cập nhật `app/core/config.py` - thêm `DATABASE_URL`
- [x] 7. Tái cấu trúc `app/services/tolerance_service.py` - truy vấn CSDL là nguồn chính, công thức làm fallback
- [x] 8. Tạo `schema.sql` - DDL chuẩn cho MySQL/PostgreSQL
- [x] 9. Tạo `app/api/routes/iso.py` - endpoint GET /api/iso/tables
- [x] 10. Cập nhật `main.py` - lifespan tự tạo bảng + seed, gắn router iso
- [x] 11. Cập nhật `index.html` - tải bảng ISO 286 từ API `GET /api/iso/tables`, giữ dữ liệu nhúng làm fallback
- [x] 12. Kiểm thử: cài dependencies, seed DB, chạy uvicorn, gọi API `/api/iso/tables`, kiểm tra tính toán vẫn đúng
  - [x] Smoke test DB: tạo bảng + seed 260 IT + 663 sai lệch + 12 fit (PASSED)
  - [x] Smoke test động cơ: ϕ40 H7/g6, ϕ100 H7/k6, ϕ50 H7/p6 khớp bảng chuẩn (PASSED)
  - [x] API test: GET /api/iso/tables, POST /api/export/docx, POST /api/export/pdf (PASSED)

