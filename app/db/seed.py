"""Số hóa toàn bộ bảng tra ISO 286-1:2010 vào CSDL quan hệ.

Bao gồm:
- 13 khoảng kích thước danh nghĩa (0 - 500 mm)            -> iso_size_ranges
- Dung sai tiêu chuẩn IT01 -> IT18 (273 giá trị)           -> iso_it_grades
- Sai lệch cơ bản Trục a..zc (es/ei) & Lỗ A..ZC (ES/EI)    -> iso_deviations
- Thư viện kiểu lắp khuyến cáo công nghiệp                 -> iso_fit_library
"""
from typing import Dict, List, Optional, Tuple

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import (
    IsoDeviation,
    IsoFitLibrary,
    IsoItGrade,
    IsoSizeRange,
    User,
)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# 1. KHOẢNG KÍCH THƯỚC DANH NGHĨA (13 khoảng, cận dưới mở - cận trên đóng)
# ---------------------------------------------------------------------------
SIZE_RANGES: List[Tuple[float, float]] = [
    (0, 3), (3, 6), (6, 10), (10, 18), (18, 30), (30, 50), (50, 80),
    (80, 120), (120, 180), (180, 250), (250, 315), (315, 400), (400, 500),
]

# ---------------------------------------------------------------------------
# 2. DUNG SAI TIÊU CHUẨN IT01 -> IT18 (μm), đúng thứ tự 13 khoảng
# ---------------------------------------------------------------------------
IT_GRADES: Dict[str, List[float]] = {
    "IT01": [0.3, 0.4, 0.4, 0.5, 0.6, 0.6, 0.8, 1, 1.2, 2, 2.5, 3, 4],
    "IT0": [0.5, 0.6, 0.6, 0.8, 1, 1, 1.2, 1.5, 2, 3, 4, 5, 6],
    "IT1": [0.8, 1, 1, 1.2, 1.5, 1.5, 2, 2.5, 3.5, 4.5, 6, 7, 8],
    "IT2": [1.2, 1.5, 1.5, 2, 2.5, 2.5, 3, 4, 5, 7, 8, 9, 10],
    "IT3": [2, 2.5, 2.5, 3, 4, 4, 5, 6, 8, 10, 12, 13, 15],
    "IT4": [3, 4, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20],
    "IT5": [4, 5, 6, 8, 9, 11, 13, 15, 18, 20, 23, 25, 27],
    "IT6": [6, 8, 9, 11, 13, 16, 19, 22, 25, 29, 32, 36, 40],
    "IT7": [10, 12, 15, 18, 21, 25, 30, 35, 40, 46, 52, 57, 63],
    "IT8": [14, 18, 22, 27, 33, 39, 46, 54, 63, 72, 81, 89, 97],
    "IT9": [25, 30, 36, 43, 52, 62, 74, 87, 100, 115, 130, 140, 155],
    "IT10": [40, 48, 58, 70, 84, 100, 120, 140, 160, 185, 210, 230, 250],
    "IT11": [60, 75, 90, 110, 130, 160, 190, 220, 250, 290, 320, 360, 400],
    "IT12": [100, 120, 150, 180, 210, 250, 300, 350, 400, 460, 520, 570, 630],
    "IT13": [140, 180, 220, 270, 330, 390, 460, 540, 630, 720, 810, 890, 970],
    "IT14": [250, 300, 360, 430, 520, 620, 740, 870, 1000, 1150, 1300, 1400, 1550],
    "IT15": [400, 480, 580, 700, 840, 1000, 1200, 1400, 1600, 1850, 2100, 2300, 2500],
    "IT16": [600, 750, 900, 1100, 1300, 1600, 1900, 2200, 2500, 2900, 3200, 3600, 4000],
    "IT17": [1000, 1200, 1500, 1800, 2100, 2500, 3000, 3500, 4000, 4600, 5200, 5700, 6300],
    "IT18": [1400, 1800, 2200, 2700, 3300, 3900, 4600, 5400, 6300, 7200, 8100, 8900, 9700],
}

# ---------------------------------------------------------------------------
# 3. SAI LỆCH CƠ BẢN CỦA TRỤC (μm) theo ISO 286-1
#    a..h  : quy định es (sai lệch trên)
#    k..zc : quy định ei (sai lệch dưới)
#    js    : đối xứng ±IT/2 (lưu 0)
# ---------------------------------------------------------------------------
SHAFT_DEVIATIONS: Dict[str, List[float]] = {
    'a': [-270, -270, -280, -290, -300, -320, -340, -380, -410, -460, -520, -580, -640],
    'b': [-140, -140, -150, -150, -160, -180, -200, -220, -240, -260, -290, -320, -350],
    'c': [-60, -70, -80, -95, -110, -130, -150, -180, -210, -230, -260, -290, -320],
    'cd': [-34, -46, -56, -64, -76, -90, -106, -125, -145, -170, -190, -210, -230],
    'd': [-20, -30, -40, -50, -65, -80, -100, -120, -145, -170, -190, -210, -230],
    'e': [-14, -20, -25, -32, -40, -50, -60, -72, -85, -100, -110, -125, -135],
    'ef': [-10, -14, -18, -24, -30, -38, -45, -54, -64, -75, -84, -94, -104],
    'f': [-6, -10, -13, -16, -20, -25, -30, -36, -43, -50, -56, -62, -68],
    'fg': [-4, -6, -8, -10, -12, -14, -18, -22, -26, -30, -34, -38, -42],
    'g': [-2, -4, -5, -6, -7, -9, -10, -12, -14, -15, -17, -18, -20],
    'h': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'js': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'j': [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24],
    'k': [0, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4, 5],
    'm': [2, 4, 6, 7, 8, 9, 11, 13, 15, 17, 20, 21, 23],
    'n': [4, 8, 10, 12, 15, 17, 20, 23, 27, 31, 34, 37, 40],
    'p': [6, 12, 15, 18, 22, 26, 32, 37, 43, 50, 56, 62, 68],
    'r': [10, 16, 21, 28, 35, 43, 53, 65, 79, 94, 108, 122, 136],
    's': [14, 23, 28, 37, 48, 60, 74, 93, 114, 136, 158, 180, 202],
    't': [18, 28, 35, 45, 54, 68, 87, 112, 140, 168, 196, 224, 252],
    'u': [20, 33, 40, 56, 70, 88, 112, 144, 180, 218, 258, 298, 338],
    'v': [24, 38, 48, 68, 86, 110, 142, 186, 232, 282, 334, 386, 438],
    'x': [28, 46, 58, 84, 110, 140, 182, 240, 300, 366, 434, 502, 570],
    'z': [36, 60, 76, 112, 148, 190, 250, 330, 410, 500, 590, 680, 770],
    'za': [44, 72, 92, 136, 180, 232, 310, 410, 510, 620, 730, 840, 950],
    'zc': [56, 90, 116, 172, 228, 294, 390, 520, 650, 780, 920, 1060, 1200],
}

# Trục a..h -> es; k..zc -> ei (loại trừ js đối xứng)
_UPPER_DEV_LETTERS = {'a', 'b', 'c', 'cd', 'd', 'e', 'ef', 'f', 'fg', 'g', 'h'}


def _build_hole_deviations() -> List[Tuple[str, str, List[float]]]:
    """Sai lệch cơ bản của Lỗ theo quy tắc đảo dấu so với Trục cùng ký tự:
    - Lỗ A..H : EI = -es (Trục a..h)
    - Lỗ K..ZC: ES = -ei (Trục k..zc)
    - Lỗ JS   : đối xứng ±IT/2 (không lưu bảng, xử lý đặc biệt)
    """
    holes: List[Tuple[str, str, List[float]]] = []
    for letter, values in SHAFT_DEVIATIONS.items():
        if letter == 'js':
            continue
        upper = letter.upper()
        kind = 'EI' if letter in _UPPER_DEV_LETTERS else 'ES'
        holes.append((upper, kind, [-v for v in values]))
    return holes


# ---------------------------------------------------------------------------
# 4. THƯ VIỆN KIỂU LẮP KHUYẾN CÁO CÔNG NGHIỆP
# ---------------------------------------------------------------------------
FIT_LIBRARY: List[Dict] = [
    {"symbol": "H7/g6", "category": "clearance", "fit_type": "Lắp trượt chính xác",
     "application": "Pít-tông thủy lực, ổ trượt chính xác, trục con lăn máy công cụ",
     "feature": "Có độ hở nhỏ, dịch chuyển dọc trục trơn tru, không lắc rơ."},
    {"symbol": "H7/f7", "category": "clearance", "fit_type": "Lắp quay tự do",
     "application": "Ổ lót trục quay, trục bánh răng tự do, khớp xoay",
     "feature": "Độ hở vừa phải, hoạt động ổn định ở nhiệt độ bình thường."},
    {"symbol": "H8/e8", "category": "clearance", "fit_type": "Lắp hở rộng",
     "application": "Gối đỡ tải trọng lớn, cụm máy làm việc nhiệt độ cao",
     "feature": "Độ hở lớn, bôi trơn dễ dàng, bù nở vì nhiệt."},
    {"symbol": "H8/d9", "category": "clearance", "fit_type": "Lắp hở rất rộng",
     "application": "Khớp nối lỏng, puly truyền động rời, trục đệm",
     "feature": "Độ hở rất lớn, dùng cho chi tiết thô hoặc khoảng cách rộng."},
    {"symbol": "H7/h6", "category": "clearance", "fit_type": "Lắp trượt định vị",
     "application": "Bánh răng di trượt, tay quay điều khiển, khớp nối di động",
     "feature": "Độ hở bằng 0 đến rất nhỏ, tháo lắp bằng tay dễ dàng."},
    {"symbol": "H7/js6", "category": "transition", "fit_type": "Lắp định vị chính xác",
     "application": "Bánh răng cố định trên trục, chốt vị trí tháo lắp",
     "feature": "Xác định tâm chính xác, tháo lắp bằng búa gỗ/đồng."},
    {"symbol": "H7/k6", "category": "transition", "fit_type": "Lắp định vị chịu tải",
     "application": "Chốt định vị, vành đai bánh răng, puly định vị",
     "feature": "Độ dôi nhỏ hoặc độ hở nhỏ, không rơ dọc trục."},
    {"symbol": "H7/m6", "category": "transition", "fit_type": "Lắp định vị chặt",
     "application": "Bánh răng truyền động êm, vành dắt ổ lăn",
     "feature": "Chủ yếu có độ dôi nhỏ, truyền momen xoắn nhẹ."},
    {"symbol": "H7/n6", "category": "transition", "fit_type": "Lắp chặt trung gian",
     "application": "Bánh răng heavy-duty, vành đệm truyền động",
     "feature": "Cần lực ép nhẹ để lắp, chống xoay chi tiết."},
    {"symbol": "H7/p6", "category": "interference", "fit_type": "Lắp ép nhẹ",
     "application": "Bạc lót đồng, vành răng định vị, bánh răng nhỏ",
     "feature": "Truyền momen xoắn vừa, lắp bằng ép lực cơ khí."},
    {"symbol": "H7/r6", "category": "interference", "fit_type": "Lắp ép vừa",
     "application": "Bánh xe lửa, bạc lót chịu tải lớn, đĩa xích",
     "feature": "Cần máy ép thủy lực, mối ghép cố định tuyệt đối."},
    {"symbol": "H7/s6", "category": "interference", "fit_type": "Lắp ép nặng (Nhiệt)",
     "application": "Vành thép đè liền trục, trục khuỷu ghép, bánh răng chịu lực",
     "feature": "Truyền momen lớn không cần key, gia nhiệt lỗ khi lắp."},
]


def seed_all(db: Optional[Session] = None) -> Dict[str, int]:
    """Seed toàn bộ dữ liệu ISO 286. Trả về số bản ghi đã thêm."""
    s: Session = db if db is not None else SessionLocal()
    counts: Dict[str, int] = {"size_ranges": 0, "it_grades": 0, "deviations": 0, "fits": 0}
    try:
        # 1) Khoảng kích thước
        for min_mm, max_mm in SIZE_RANGES:
            s.add(IsoSizeRange(min_mm=min_mm, max_mm=max_mm))
        s.flush()
        counts["size_ranges"] = len(SIZE_RANGES)

        # 2) Dung sai IT
        for grade, values in IT_GRADES.items():
            for range_id, value in enumerate(values, start=1):
                s.add(IsoItGrade(grade=grade, range_id=range_id, value_um=value))
        counts["it_grades"] = sum(len(v) for v in IT_GRADES.values())

        # 3) Sai lệch Trục
        for letter, values in SHAFT_DEVIATIONS.items():
            kind = 'es' if letter in _UPPER_DEV_LETTERS else ('ei' if letter != 'js' else 'es')
            for range_id, value in enumerate(values, start=1):
                s.add(IsoDeviation(
                    part_type="shaft", letter=letter, deviation_kind=kind,
                    range_id=range_id, value_um=value,
                ))
        counts["deviations"] = sum(len(v) for v in SHAFT_DEVIATIONS.values())

        # 4) Sai lệch Lỗ (quy tắc đảo dấu)
        for upper, kind, values in _build_hole_deviations():
            for range_id, value in enumerate(values, start=1):
                s.add(IsoDeviation(
                    part_type="hole", letter=upper, deviation_kind=kind,
                    range_id=range_id, value_um=value,
                ))
        counts["deviations"] += sum(len(v) for _, _, v in _build_hole_deviations())

        # 5) Thư viện kiểu lắp
        for fit in FIT_LIBRARY:
            s.add(IsoFitLibrary(**fit))
        counts["fits"] = len(FIT_LIBRARY)

        s.commit()
    finally:
        if db is None:
            s.close()
    return counts


def seed_if_empty(db: Optional[Session] = None) -> bool:
    """Seed nếu bảng iso_size_ranges chưa có dữ liệu (idempotent)."""
    s: Session = db if db is not None else SessionLocal()
    try:
        has_data = s.query(IsoSizeRange).first() is not None
        if not has_data:
            seed_all(s)
            return True
        return False
    finally:
        if db is None:
            s.close()


# ---------------------------------------------------------------------------
# 5. SEED TÀI KHOẢN NGƯỜI DÙNG MẪU (3 GV + 20 SV)
#    Tự động chạy khi DB trống (lifespan ở main.py)
# ---------------------------------------------------------------------------
LECTURER_SEED = [
    {"username": "gv01", "full_name": "TS. Nguyễn Văn Giảng", "department": "Khoa Cơ khí - Bộ môn Kỹ thuật Cơ khí"},
    {"username": "gv02", "full_name": "ThS. Trần Thị Dạy", "department": "Khoa Cơ khí - Bộ môn Cơ khí Chế tạo"},
    {"username": "gv03", "full_name": "PGS.TS. Lê Thị Học", "department": "Khoa Cơ khí - Bộ môn Cơ khí Chế tạo"},
]

_STUDENT_FIRST_NAMES = [
    "Nguyễn Văn", "Trần Thị", "Lê Văn", "Phạm Thị", "Vũ Văn",
    "Hoàng Thị", "Đỗ Văn", "Đặng Thị", "Bùi Văn", "Ngô Thị",
    "Dương Văn", "Lý Thị", "Hồ Văn", "Tô Thị", "Mai Văn",
    "Đinh Thị", "Trịnh Văn", "Phan Thị", "Võ Văn", "Đào Thị",
]
_STUDENT_LAST_NAMES = [
    "An", "Bình", "Cường", "Dung", "Em", "Phúc", "Hà", "Hùng",
    "Linh", "Minh", "Nhung", "Oanh", "Phương", "Quân", "Sơn",
    "Tâm", "Uyên", "Vy", "Xuân", "Yến",
]
_CLASSES = ["21CK1", "21CK2", "21CK3", "21CK4", "22CK1"]


def seed_users_if_empty(db: Optional[Session] = None) -> int:
    """Tạo tài khoản mẫu nếu bảng `users` chưa có dữ liệu (idempotent).

    - 3 Giảng viên (gv01, gv02, gv03; role='lecturer')
    - 20 Sinh viên (MSSV 2110481..2110500; role='student')
    Mật khẩu mặc định: '123' (hash bcrypt).
    Trả về số tài khoản đã tạo.
    """
    s: Session = db if db is not None else SessionLocal()
    created = 0
    try:
        if s.query(User).first() is not None:
            return 0  # Đã có user -> không seed lại.

        # 3 Giảng viên
        for gv in LECTURER_SEED:
            s.add(User(
                username=gv["username"],
                full_name=gv["full_name"],
                role="lecturer",
                department=gv["department"],
                password_hash=_pwd_context.hash("123"),
            ))
            created += 1

        # 20 Sinh viên (MSSV 2110481..2110500)
        for i in range(20):
            start_mssv = 2110481
            mssv = str(start_mssv + i)
            full_name = f"{_STUDENT_FIRST_NAMES[i]} {_STUDENT_LAST_NAMES[i]}"
            s.add(User(
                username=mssv,
                full_name=full_name,
                role="student",
                department=_CLASSES[i % len(_CLASSES)],
                password_hash=_pwd_context.hash("123"),
            ))
            created += 1

        s.commit()
    finally:
        if db is None:
            s.close()
    return created


if __name__ == "__main__":
    result = seed_all()
    print("Đã seed dữ liệu ISO 286:", result)

