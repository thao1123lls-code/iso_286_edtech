"""
ISO 286 EdTech - Backend FastAPI (Layered Architecture)

Kiến trúc 3 lớp (Layered Architecture):
- Presentation Layer : app.api        -> router /api/export/docx, /api/export/pdf, /api/iso/tables
- Business Logic     : app.services   -> ⭐ LỚP NGHIỆP VỤ (BLL)
- Configuration      : app.core       -> config, utils, pdf_fonts
- Data Model Layer   : app.models     -> Pydantic schemas
- Database Layer     : app.db         -> SQLAlchemy (iso_size_ranges, iso_it_grades, iso_deviations)

==> Chạy:  uvicorn main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.export import router as export_router
from app.api.routes.iso import router as iso_router
from app.core.config import API_TITLE
from app.core.pdf_fonts import register_pdf_fonts
from app.db import seed as iso_seed
from app.db.database import Base, engine
from app.db import models as iso_models  # noqa: F401 (đảm bảo ORM models được đăng ký)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo CSDL + seed dữ liệu ISO 286 khi ứng dụng khởi động."""
    # Tạo toàn bộ bảng (idempotent)
    Base.metadata.create_all(bind=engine)
    # Seed dữ liệu nếu bảng chưa có (an toàn chạy lại nhiều lần)
    seeded = iso_seed.seed_if_empty()
    print(f"[ISO 286 DB] Bảng tra đã sẵn sàng. Seed mới: {seeded}")
    yield


app = FastAPI(title=API_TITLE, lifespan=lifespan)

# Đăng ký font PDF (Times New Roman Unicode) một lần khi khởi động.
register_pdf_fonts()

# CORS: cho phép mọi origin để nút "Xuất Word/PDF" hoạt động
# dù trang được mở từ Live Server (5500), localhost (3000) hay file://
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn router xuất tài liệu (Presentation Layer gọi xuống BLL).
app.include_router(export_router, prefix="/api")
# Gắn router tra cứu bảng ISO 286 từ CSDL (cho frontend).
app.include_router(iso_router, prefix="/api")

