# ISO 286 EdTech — Dung Sai Kỹ Thuật & Đo Lường

Ứng dụng web phục vụ học tập **Dung sai Kỹ thuật** dựa trên tiêu chuẩn **ISO 286-1:2010**.
Cho phép tra cứu bảng dung sai, tạo bộ đề thi tự động, lưu lịch sử và xuất file **Word / PDF**.

- **Frontend**: giao diện đơn file `index.html` (HTML + CSS + JS thuần)
- **Backend**: **FastAPI** — kiến trúc 3 lớp (Layered Architecture) + JWT Auth/RBAC

---

## ✨ Tính năng chính

- 🔍 Tra cứu bảng tra ISO 286 đã số hóa (khoảng kích thước, dung sai IT, sai lệch trục/lỗ, thư viện kiểu lắp)
- 🧮 Tự động sinh bộ đề thi theo chuẩn ISO 286 (kích thước danh nghĩa, lỗ, trục, kiểu lắp)
- 📝 Lưu lịch sử lô đề thi (`/api/history`)
- 📄 Xuất đề thi ra **Word (.docx)** và **PDF** (chỉ Giảng viên)
- 🔐 Phân quyền: **Giảng viên** (lecturer) / **Sinh viên** (student)

---

## 🛠️ Công nghệ

| Thành phần            | Công nghệ                                        |
| --------------------- | ------------------------------------------------ |
| Backend               | FastAPI, Uvicorn                                 |
| ORM / Database        | SQLAlchemy (SQLite / MySQL / PostgreSQL)         |
| Xuất Word             | python-docx                                      |
| Xuất PDF              | ReportLab (Times New Roman Unicode)              |
| Xác thực              | JWT (PyJWT) + RBAC                               |
| Băm mật khẩu          | passlib + bcrypt                                 |
| Frontend              | HTML / CSS / JavaScript (đơn file `index.html`)  |

---

## 📁 Cấu trúc dự án

```
iso-286-edtech/
├── main.py                    # Entry point FastAPI (auth, RBAC, routes, lifespan)
├── index.html                 # Frontend (mở trực tiếp trong trình duyệt)
├── requirements.txt           # Danh sách thư viện Python
├── schema.sql                 # DDL mô tả CSDL ISO 286 (tham khảo)
├── app/
│   ├── api/routes/            # Presentation Layer (iso.py, export.py)
│   ├── core/                  # config.py, utils.py, pdf_fonts.py
│   ├── models/                # Pydantic schemas (schemas.py)
│   ├── services/              # Business Logic Layer (docx/pdf/export/tolerance)
│   └── db/                    # database.py, models.py, repository.py, seed.py
└── iso286.db                  # CSDL SQLite (tự tạo khi chạy lần đầu)
```

---

## ✅ Yêu cầu

- **Python 3.10+**
- Trình duyệt hiện đại (Chrome / Edge / Firefox)

---

## 🚀 Hướng dẫn cài đặt & chạy

### 1. Clone / vào thư mục dự án

```bash
cd iso-286-edtech
```

### 2. Tạo môi trường ảo (khuyến nghị)

**Windows (CMD):**

```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

> ⚠️ Nếu gặp lỗi cài `bcrypt==4.0.1` trên máy mới, hãy nâng cấp pip:
> `python -m pip install --upgrade pip setuptools wheel`

### 4. Chạy Backend

```bash
uvicorn main:app --reload
```

- API sẽ chạy tại: **http://127.0.0.1:8000**
- Tài liệu tương tác (Swagger UI): **http://127.0.0.1:8000/docs**
- **CSDL tự động tạo và seed dữ liệu ISO 286** khi khởi động (file `iso286.db`).

### 5. Mở Frontend

Mở file **`index.html`** trực tiếp trong trình duyệt, **hoặc** dùng **Live Server** (VS Code) / bất kỳ static server nào.

> Frontend gọi API về `http://127.0.0.1:8000` (CORS đã bật cho mọi origin).

---

## 👤 Tài khoản demo

Mật khẩu của **tất cả** tài khoản đều là: `123`

| Tên đăng nhập | Vai trò      | Ghi chú                                  |
| ------------- | ------------ | ---------------------------------------- |
| `giangvien`   | Giảng viên   | Tài khoản chung                           |
| `gv01`        | Giảng viên   | TS. Nguyễn Văn Giảng — Khoa Cơ khí        |
| `gv02`        | Giảng viên   | ThS. Trần Thị Dạy — Khoa Cơ khí           |
| `sinhvien`    | Sinh viên    | Tài khoản chung                           |
| `2110481`     | Sinh viên    | Nguyễn Văn An — 21CK1                     |
| `2110482`     | Sinh viên    | Trần Thị Bình — 21CK1                     |
| `2110483`     | Sinh viên    | Lê Văn Cường — 21CK2                      |
| `2110484`     | Sinh viên    | Phạm Thị Dung — 21CK2                     |
| `2110485`     | Sinh viên    | Vũ Văn Em — 21CK3                         |

> **Giảng viên** có toàn quyền (bao gồm xuất Word/PDF). **Sinh viên** chỉ tra cứu / học tập.

---

## 🗄️ Cấu hình cơ sở dữ liệu

Mặc định ứng dụng dùng **SQLite** (file `iso286.db`) — chạy ngay không cần cài DB server.

Để dùng **MySQL** hoặc **PostgreSQL**, đặt biến môi trường `DATABASE_URL` trước khi chạy:

```bash
# MySQL
export DATABASE_URL="mysql+pymysql://user:pass@localhost:3306/iso286"

# PostgreSQL
export DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/iso286"
```

**Windows (CMD):**

```cmd
set DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/iso286
```

> Tham khảo DDL tại `schema.sql`. Seed dữ liệu thủ công: `python -m app.db.seed`

---

## 🔌 Danh sách API

| Method | Endpoint          | Mô tả                                      | Quyền        |
| ------ | ----------------- | ------------------------------------------ | ------------ |
| POST   | `/api/login`      | Đăng nhập, cấp JWT token                   | Công khai    |
| GET    | `/api/iso/tables` | Lấy toàn bộ bảng tra ISO 286               | Có token     |
| POST   | `/api/history`    | Lưu lô đề thi (bulk insert)                | Có token     |
| GET    | `/api/history`    | Lấy danh sách lô đề đã tạo                 | Có token     |
| POST   | `/api/export/docx`| Xuất bộ đề ra file Word (.docx)            | **Lecturer** |
| POST   | `/api/export/pdf` | Xuất bộ đề ra file PDF                     | **Lecturer** |

---

## 🧪 Scripts kiểm tra

| Script                | Mục đích                                  |
| --------------------- | ----------------------------------------- |
| `_smoke_test.py`      | Smoke test import chính `main.py`         |
| `_api_test.py`        | Kiểm tra các API endpoint                 |
| `_auth_test.py`       | Kiểm tra đăng nhập / JWT                  |
| `_history_test.py`    | Kiểm tra lưu & truy xuất lịch sử đề thi   |
| `_verify_header.py`   | Kiểm tra header file Word                 |
| `_verify_nanometer_math.js` | Kiểm tra tính toán BLL (JS)          |

---

## 📝 Ghi chú

- Secret JWT mặc định trong `main.py` chỉ dùng cho demo. **Trong production hãy đặt biến môi trường `JWT_SECRET_KEY`.**
- SQLite cần `check_same_thread=False` (đã cấu hình trong `app/db/database.py`) để hoạt động với FastAPI multi-thread.
