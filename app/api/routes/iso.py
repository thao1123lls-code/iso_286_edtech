"""API tra cứu dữ liệu ISO 286 từ CSDL (Presentation Layer).

Cung cấp endpoint cho frontend tải bảng tra từ Backend (SQL)
thay vì hardcode trong JavaScript.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import repository as iso_repo
from app.db.database import get_db

router = APIRouter(prefix="/iso", tags=["iso"])


@router.get("/tables")
def get_iso_tables(db: Session = Depends(get_db)):
    """Trả về toàn bộ bảng tra ISO 286 đã số hóa:
    sizeRanges, itGrades, shaftDeviations, fitLibrary.
    """
    return iso_repo.get_all_tables(db)

