"""ORM Models cho bảng tra ISO 286.

Ba bảng chính theo yêu cầu:
- iso_size_ranges : 13 khoảng kích thước danh nghĩa (0-500 mm)
- iso_it_grades   : giá trị dung sai tiêu chuẩn IT01 -> IT18 (μm)
- iso_deviations  : sai lệch cơ bản của Trục (es/ei) & Lỗ (ES/EI)

Bảng bổ trợ:
- iso_fit_library : thư viện kiểu lắp khuyến cáo công nghiệp
"""
from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint

from app.db.database import Base


class IsoSizeRange(Base):
    """Khoảng kích thước danh nghĩa (cận dưới mở, cận trên đóng)."""

    __tablename__ = "iso_size_ranges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    min_mm = Column(Float, nullable=False)   # cận dưới (exclusive)
    max_mm = Column(Float, nullable=False)   # cận trên (inclusive)

    def to_dict(self):
        return {"id": self.id, "min": self.min_mm, "max": self.max_mm}


class IsoItGrade(Base):
    """Dung sai tiêu chuẩn IT theo cấp chính xác và khoảng kích thước."""

    __tablename__ = "iso_it_grades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    grade = Column(String(4), nullable=False)          # IT01, IT0, IT1 ... IT18
    range_id = Column(Integer, ForeignKey("iso_size_ranges.id"), nullable=False)
    value_um = Column(Float, nullable=False)           # dung sai (μm)

    __table_args__ = (
        UniqueConstraint("grade", "range_id", name="uq_it_grade_range"),
    )


class IsoDeviation(Base):
    """Sai lệch cơ bản của Trục (es/ei) hoặc Lỗ (ES/EI)."""

    __tablename__ = "iso_deviations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    part_type = Column(String(8), nullable=False)      # 'shaft' | 'hole'
    letter = Column(String(2), nullable=False)         # a..zc (trục) / A..ZC (lỗ)
    deviation_kind = Column(String(4), nullable=False)  # es/ei (trục), ES/EI (lỗ)
    range_id = Column(Integer, ForeignKey("iso_size_ranges.id"), nullable=False)
    value_um = Column(Float, nullable=False)           # sai lệch cơ bản (μm)

    __table_args__ = (
        UniqueConstraint("part_type", "letter", "range_id", name="uq_dev_plr"),
    )


class IsoFitLibrary(Base):
    """Thư viện kiểu lắp khuyến cáo trong công nghiệp."""

    __tablename__ = "iso_fit_library"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(16), nullable=False)        # VD: H7/g6
    category = Column(String(16), nullable=False)      # clearance|transition|interference
    fit_type = Column(String(64), nullable=False)      # tên kiểu lắp
    application = Column(String(255), nullable=False)  # ứng dụng thực tế
    feature = Column(String(255), nullable=False)      # đặc tính cơ học

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "category": self.category,
            "fit_type": self.fit_type,
            "application": self.application,
            "feature": self.feature,
        }

