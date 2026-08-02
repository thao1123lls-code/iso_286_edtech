"""Lớp truy xuất dữ liệu ISO 286 (Data Access Layer).

Mọi hàm tra cứu trả về None nếu không tìm thấy dữ liệu trong CSDL,
giúp Business Logic Layer dùng công thức ISO 286 làm fallback.
"""
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import IsoDeviation, IsoFitLibrary, IsoItGrade, IsoSizeRange


def _get_session(db: Optional[Session] = None) -> Session:
    """Dùng session có sẵn hoặc tự mở session mới (tự đóng khi không truyền vào)."""
    return db if db is not None else SessionLocal()


def _close_if_owned(db: Optional[Session], s: Session):
    if db is None:
        s.close()


# ---------------------------------------------------------------------------
# KHOẢNG KÍCH THƯỚC
# ---------------------------------------------------------------------------
def get_range_id(D: float, db: Optional[Session] = None) -> Optional[int]:
    """Trả về id khoảng kích thước chứa D (min < D <= max), hoặc None."""
    s = _get_session(db)
    try:
        row = (
            s.query(IsoSizeRange)
            .filter(IsoSizeRange.min_mm < D, IsoSizeRange.max_mm >= D)
            .order_by(IsoSizeRange.id)
            .first()
        )
        return row.id if row else None
    finally:
        _close_if_owned(db, s)


def get_size_ranges(db: Optional[Session] = None) -> List[Dict]:
    s = _get_session(db)
    try:
        rows = s.query(IsoSizeRange).order_by(IsoSizeRange.id).all()
        return [r.to_dict() for r in rows]
    finally:
        _close_if_owned(db, s)


# ---------------------------------------------------------------------------
# DUNG SAI TIÊU CHUẨN IT
# ---------------------------------------------------------------------------
def get_it_value(grade: str, D: float, db: Optional[Session] = None) -> Optional[float]:
    """Tra dung sai IT (μm) theo cấp (VD: 'IT6', 'IT01') và kích thước D."""
    rid = get_range_id(D, db)
    if rid is None:
        return None
    s = _get_session(db)
    try:
        row = (
            s.query(IsoItGrade)
            .filter_by(grade=grade, range_id=rid)
            .first()
        )
        return row.value_um if row else None
    finally:
        _close_if_owned(db, s)


def get_it_grades(db: Optional[Session] = None) -> Dict[str, List[float]]:
    """Trả về toàn bộ bảng IT dạng {grade: [value_um x 13 khoảng]}."""
    s = _get_session(db)
    try:
        ranges = s.query(IsoSizeRange).order_by(IsoSizeRange.id).all()
        grades = s.query(IsoItGrade).order_by(IsoItGrade.grade, IsoItGrade.range_id).all()
        result: Dict[str, List[float]] = {}
        for g in grades:
            key = g.grade.replace("IT", "")
            result.setdefault(key, [None] * len(ranges))
            result[key][g.range_id - 1] = g.value_um
        return result
    finally:
        _close_if_owned(db, s)


# ---------------------------------------------------------------------------
# SAI LỆCH CƠ BẢN
# ---------------------------------------------------------------------------
def get_shaft_deviation(letter: str, D: float, db: Optional[Session] = None) -> Optional[Dict]:
    """Tra sai lệch cơ bản của Trục. Trả về {kind: 'es'|'ei', value_um} hoặc None."""
    rid = get_range_id(D, db)
    if rid is None:
        return None
    s = _get_session(db)
    try:
        row = (
            s.query(IsoDeviation)
            .filter_by(part_type="shaft", letter=letter.lower(), range_id=rid)
            .first()
        )
        if row:
            return {"kind": row.deviation_kind, "value_um": row.value_um}
        return None
    finally:
        _close_if_owned(db, s)


def get_hole_deviation(letter: str, D: float, db: Optional[Session] = None) -> Optional[Dict]:
    """Tra sai lệch cơ bản của Lỗ. Trả về {kind: 'ES'|'EI', value_um} hoặc None."""
    rid = get_range_id(D, db)
    if rid is None:
        return None
    s = _get_session(db)
    try:
        row = (
            s.query(IsoDeviation)
            .filter_by(part_type="hole", letter=letter.upper(), range_id=rid)
            .first()
        )
        if row:
            return {"kind": row.deviation_kind, "value_um": row.value_um}
        return None
    finally:
        _close_if_owned(db, s)


def get_shaft_deviations(db: Optional[Session] = None) -> Dict[str, List[float]]:
    """Trả về toàn bộ sai lệch Trục dạng {letter: [value_um x 13 khoảng]}."""
    s = _get_session(db)
    try:
        ranges = s.query(IsoSizeRange).order_by(IsoSizeRange.id).all()
        devs = (
            s.query(IsoDeviation)
            .filter_by(part_type="shaft")
            .order_by(IsoDeviation.letter, IsoDeviation.range_id)
            .all()
        )
        result: Dict[str, List[float]] = {}
        for d in devs:
            result.setdefault(d.letter, [None] * len(ranges))
            result[d.letter][d.range_id - 1] = d.value_um
        return result
    finally:
        _close_if_owned(db, s)


# ---------------------------------------------------------------------------
# THƯ VIỆN KIỂU LẮP & TOÀN BỘ BẢNG
# ---------------------------------------------------------------------------
def get_fit_library(db: Optional[Session] = None) -> List[Dict]:
    s = _get_session(db)
    try:
        rows = s.query(IsoFitLibrary).order_by(IsoFitLibrary.id).all()
        return [r.to_dict() for r in rows]
    finally:
        _close_if_owned(db, s)


def get_all_tables(db: Optional[Session] = None) -> Dict:
    """Trả về toàn bộ dữ liệu ISO 286 cho frontend (định dạng giống ISO_DB cũ)."""
    s = _get_session(db)
    try:
        return {
            "sizeRanges": get_size_ranges(s),
            "itGrades": get_it_grades(s),
            "shaftDeviations": get_shaft_deviations(s),
            "fitLibrary": get_fit_library(s),
        }
    finally:
        _close_if_owned(db, s)

