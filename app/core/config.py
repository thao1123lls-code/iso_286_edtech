"""Cấu hình chung (Configuration Layer).

Tập trung toàn bộ hằng số dùng chung cho ứng dụng ISO 286 EdTech.
Có thể chỉnh sửa trực tiếp tại đây.
"""
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# ---------------------------------------------------------------------------
# THÔNG TIN TRƯỜNG / KHOA / HỌC PHẦN
# ---------------------------------------------------------------------------
SCHOOL_NAME = "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ ĐỒNG NAI"
FACULTY_NAME = "KHOA CƠ KHÍ"
COURSE_NAME = "HỌC PHẦN: DUNG SAI KỸ THUẬT VÀ ĐO LƯỜNG"

# ---------------------------------------------------------------------------
# MEDIA TYPE (Content-Type trả về cho client)
# ---------------------------------------------------------------------------
MEDIA_TYPE_DOCX = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
MEDIA_TYPE_PDF = "application/pdf"

# ---------------------------------------------------------------------------
# ĐỊNH DẠNG PDF (A4 + lề)
# ---------------------------------------------------------------------------
PAGE_SIZE = A4
PDF_MARGIN_LEFT = 2 * cm
PDF_MARGIN_RIGHT = 2 * cm
PDF_MARGIN_TOP = 2.2 * cm
PDF_MARGIN_BOTTOM = 1.8 * cm

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
API_PREFIX = "/api"
API_TITLE = "ISO 286 Exporter API"

# ---------------------------------------------------------------------------
# CƠ SỞ DỮ LIỆU (SQLAlchemy)
# ---------------------------------------------------------------------------
# Mặc định SQLite (file iso286.db) để chạy ngay không cần cài DB server.
# Muốn dùng MySQL/PostgreSQL chỉ cần đặt biến môi trường DATABASE_URL, ví dụ:
#   MySQL:      mysql+pymysql://user:pass@localhost:3306/iso286
#   PostgreSQL: postgresql+psycopg2://user:pass@localhost:5432/iso286
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./iso286.db")

