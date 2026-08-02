"""Quy tắc nghiệp vụ ISO 286 (Business Logic Layer).

Lớp này chịu trách nhiệm:
1. Tính toán dung sai (IT, sai lệch, kích thước giới hạn, đặc tính lắp ghép).
2. Kiểm tra ràng buộc nghiệp vụ (business rules) trước khi xuất tài liệu:
   - ES - EI == TD ; es - ei == Td
   - Dmax/Dmin, dmax/dmin khớp với sai lệch
   - Đặc tính lắp ghép nhất quán (Smax/Smin/Nmax/Nmin)
   - Tổng điểm BAREM == 10.0
3. Nâng cao chất lượng dữ liệu đầu vào.
"""
from typing import Dict, List, Optional

from app.models.schemas import ExamData, FitParams, Question, Task, ToleranceParams

# Ngưỡng sai số cho phép khi so sánh số thực (μm)
_EPSILON = 1e-6


class ToleranceValidationError(ValueError):
    """Ngoại lệ nghiệp vụ: dữ liệu đề thi vi phạm quy tắc ISO 286."""


def validate_exam_data(data: ExamData) -> List[str]:
    """Kiểm tra toàn bộ bộ đề. Trả về danh sách cảnh báo (không có -> hợp lệ).

    Các lỗi nghiêm trọng (invalid) sẽ raise ToleranceValidationError,
    các cảnh báo nhẹ (warning) sẽ được trả về để ghi log.
    """
    warnings: List[str] = []

    if not data.questions:
        raise ToleranceValidationError("Bộ đề không chứa câu hỏi nào.")

    for idx, q in enumerate(data.questions):
        warnings.extend(_validate_question(q, idx))

    total_points = sum(float(t.points) for t in data.activeTasks)
    if abs(total_points - 10.0) > _EPSILON:
        warnings.append(
            f"Tổng điểm BAREM = {total_points:.2f}, khác 10.0. "
            "Có thể gây lệch thang điểm khi chấm."
        )

    return warnings


def validate_question(q: Question) -> List[str]:
    """Kiểm tra một câu hỏi duy nhất."""
    return _validate_question(q, 0)


def _validate_question(q: Question, idx: int) -> List[str]:
    """Kiểm tra ràng buộc nghiệp vụ cho từng câu hỏi."""
    w: List[str] = []
    hole, shaft, fit = q.hole, q.shaft, q.fit

    # 1. Dung sai lỗ
    if None not in (hole.ES, hole.EI):
        td = abs(hole.ES - hole.EI)
        if abs(td - hole.T) > _EPSILON:
            w.append(f"[Q{idx + 1}] TD = ES - EI = {td} μm khác T = {hole.T} μm.")

    # 2. Dung sai trục
    if None not in (shaft.es, shaft.ei):
        td = abs(shaft.es - shaft.ei)
        if abs(td - shaft.T) > _EPSILON:
            w.append(f"[Q{idx + 1}] Td = es - ei = {td} μm khác T = {shaft.T} μm.")

    # 3. Kích thước giới hạn lỗ
    if None not in (hole.Dmax, hole.Dmin, hole.ES, hole.EI):
        _check_limit_size(w, idx, "Lỗ", "Dmax", hole.Dmax, q.D, hole.ES)
        _check_limit_size(w, idx, "Lỗ", "Dmin", hole.Dmin, q.D, hole.EI)

    # 4. Kích thước giới hạn trục
    if None not in (shaft.dmax, shaft.dmin, shaft.es, shaft.ei):
        _check_limit_size(w, idx, "Trục", "dmax", shaft.dmax, q.D, shaft.es)
        _check_limit_size(w, idx, "Trục", "dmin", shaft.dmin, q.D, shaft.ei)

    # 5. Đặc tính lắp ghép
    _validate_fit(w, idx, hole, shaft, fit)

    return w


def _check_limit_size(w, idx, part, label, actual, nominal, dev):
    expected = nominal + (dev / 1000.0)
    if abs(actual - expected) > _EPSILON:
        w.append(
            f"[Q{idx + 1}] {part} {label} = {actual} mm, "
            f"kỳ vọng {expected:.4f} mm (D + {dev}μm)."
        )


def _validate_fit(w, idx, hole: ToleranceParams, shaft: ToleranceParams, fit: FitParams):
    """Kiểm tra nhất quán của các thông số lắp ghép."""
    if None in (hole.ES, hole.EI, shaft.es, shaft.ei):
        return  # Thiếu dữ liệu, bỏ qua kiểm tra lắp ghép

    ES, EI, es, ei = hole.ES, hole.EI, shaft.es, shaft.ei
    expected_Smax = ES - ei
    expected_Smin = EI - es
    expected_Nmax = es - EI
    expected_Nmin = ei - ES
    expected_TN = abs(hole.T) + abs(shaft.T)

    pairs = [
        ("Smax", fit.Smax, expected_Smax),
        ("Smin", fit.Smin, expected_Smin),
        ("Nmax", fit.Nmax, expected_Nmax),
        ("Nmin", fit.Nmin, expected_Nmin),
    ]
    for label, actual, expected in pairs:
        if actual is not None and abs(actual - expected) > _EPSILON:
            w.append(
                f"[Q{idx + 1}] {label} = {actual} μm, "
                f"kỳ vọng {expected} μm (từ ES/EI/es/ei)."
            )

    if abs(fit.TN - expected_TN) > _EPSILON:
        w.append(
            f"[Q{idx + 1}] TS,N = {fit.TN} μm, kỳ vọng {expected_TN} μm (TD + Td)."
        )


def validate_rubric_total(tasks: List[Task]) -> float:
    """Kiểm tra tổng điểm BAREM. Trả về tổng điểm."""
    total = sum(float(t.points) for t in tasks)
    if abs(total - 10.0) > _EPSILON:
        raise ToleranceValidationError(
            f"Tổng điểm BAREM = {total:.2f} phải bằng 10.0 (thang điểm đại học)."
        )
    return total


# ---------------------------------------------------------------------------
# ĐỘNG CƠ TÍNH TOÁN ISO 286 (dùng cho backend, độc lập với frontend)
#
# NGUỒN DỮ LIỆU CHÍNH: Cơ sở dữ liệu quan hệ SQL
#   - iso_size_ranges (app.db.models.IsoSizeRange)
#   - iso_it_grades   (app.db.models.IsoItGrade)
#   - iso_deviations  (app.db.models.IsoDeviation)
# Tra cứu qua app.db.repository (Data Access Layer).
# Công thức ISO 286 chỉ dùng làm FALLBACK khi:
#   - Ngoài khoảng bảng (D > 500mm)
#   - Cấp IT không có trong bảng (VD: IT4, IT12... chỉ dùng công thức)
#   - CSDL chưa được seed / truy vấn lỗi
# ---------------------------------------------------------------------------
from app.db import repository as iso_repo

# Sai lệch cơ bản của Trục a..h quy định es (sai lệch trên)
_UPPER_DEV_LETTERS = {'a', 'b', 'c', 'cd', 'd', 'e', 'ef', 'f', 'fg', 'g', 'h'}

# Các cấp IT có trong bảng ISO 286 (từ CSDL). Ngoài ra -> công thức fallback.
_IT_TABLE_GRADES = {"IT01", "IT0", "IT1", "IT2", "IT3", "IT4", "IT5", "IT6",
                    "IT7", "IT8", "IT9", "IT10", "IT11", "IT12", "IT13",
                    "IT14", "IT15", "IT16", "IT17", "IT18"}

# Hệ số nhân cấp chính xác cho công thức fallback (dựa trên IT5=7i)
_MULTIPLIERS = {
    1: 0.8, 2: 1.25, 3: 2, 4: 3.2, 5: 7, 6: 10, 7: 16, 8: 25,
    9: 40, 10: 64, 11: 100, 12: 160, 13: 250, 14: 400, 15: 640,
    16: 1000, 17: 1600, 18: 2500,
}


def _get_range_index(D: float) -> int:
    """Tra id khoảng kích thước từ CSDL. Trả về 0-based index hoặc -1."""
    rid = iso_repo.get_range_id(D)
    return (rid - 1) if rid else -1


def _lookup_it_from_db(grade: str, D: float) -> Optional[float]:
    """Tra dung sai IT từ CSDL. Trả về None nếu không có."""
    try:
        return iso_repo.get_it_value(grade, D)
    except Exception:
        return None


def fallback_calculate_it(D: float, grade: int) -> int:
    """Công thức ISO 286 dự phòng khi ngoài bảng / DB lỗi.

    i = 0.45 * D^(1/3) + 0.001*D  (μm, D tính mm)
    ITn = k * i  với k theo cấp chính xác.
    """
    i = 0.45 * (D ** (1 / 3)) + 0.001 * D
    k = _MULTIPLIERS.get(grade, 10)
    return round(i * k)


def _it_grade_label(it: int) -> str:
    """'6' -> 'IT6'."""
    return f"IT{it}"


def calculate(D: float, hole_class: str, shaft_class: str) -> Dict:
    """Tính toán toàn bộ thông số dung sai ISO 286.

    Nguồn dữ liệu ưu tiên: CSDL SQL (bảng iso_it_grades, iso_deviations).
    Fallback: công thức ISO 286 khi ngoài khoảng tra / DB thiếu dữ liệu.

    Args:
        D: Kích thước danh nghĩa (mm).
        hole_class: Miền dung sai Lỗ, ví dụ "H7".
        shaft_class: Miền dung sai Trục, ví dụ "g6".

    Returns:
        Dict chứa hole/shaft/fit tương tự DualEngineMath phía frontend.
    """
    if D is None or D <= 0 or D > 3150:
        return {"error": "Kích thước D phải từ 0 - 3150mm"}

    def _parse(value: str):
        if not value:
            return None
        import re
        m = re.match(r"([a-zA-Z]+)(\d+)", value.strip())
        if not m:
            return None
        return {"sym": m.group(1), "it": int(m.group(2))}

    hole = _parse(hole_class)
    shaft = _parse(shaft_class)
    if not hole or not shaft:
        return {"error": "Định dạng miền dung sai chưa đúng (VD: H7, g6)"}

    # ---- 1. DUNG SAI TIÊU CHUẨN IT (μm) ----
    it_hole_db = _lookup_it_from_db(_it_grade_label(hole["it"]), D)
    it_shaft_db = _lookup_it_from_db(_it_grade_label(shaft["it"]), D)
    it_hole = it_hole_db if it_hole_db is not None else fallback_calculate_it(D, hole["it"])
    it_shaft = it_shaft_db if it_shaft_db is not None else fallback_calculate_it(D, shaft["it"])
    it_hole = round(it_hole)
    it_shaft = round(it_shaft)

    # ---- 2. SAI LỆCH CƠ BẢN TRỤC ----
    s_sym = shaft["sym"].lower()
    try:
        dev = iso_repo.get_shaft_deviation(s_sym, D)
    except Exception:
        dev = None

    if s_sym == 'js':
        # Đối xứng ±IT/2
        es = round(it_shaft / 2)
        ei = -round(it_shaft / 2)
    elif dev is not None:
        fund_dev = dev["value_um"]
        if dev["kind"] == "es":
            es = fund_dev
            ei = es - it_shaft
        else:  # ei
            ei = fund_dev
            es = ei + it_shaft
    else:
        # Fallback công thức (DB chưa seed / ngoài bảng)
        if s_sym < 'h':
            es = -round(5.5 * (D ** 0.41))
            ei = es - it_shaft
        else:
            ei = round(5 * (D ** 0.34))
            es = ei + it_shaft

    # ---- 3. SAI LỆCH CƠ BẢN LỖ ----
    h_sym = hole["sym"].upper()
    if h_sym == 'H':
        EI = 0
        ES = EI + it_hole
    elif h_sym == 'JS':
        ES = round(it_hole / 2)
        EI = -round(it_hole / 2)
    else:
        # Lỗ tra từ CSDL (quy tắc đảo dấu đã được số hóa trong iso_deviations)
        try:
            h_dev = iso_repo.get_hole_deviation(h_sym, D)
        except Exception:
            h_dev = None
        if h_dev is not None:
            if h_dev["kind"] == "EI":
                EI = h_dev["value_um"]
                ES = EI + it_hole
            else:  # ES
                ES = h_dev["value_um"]
                EI = ES - it_hole
        else:
            # Fallback đảo dấu từ trục (giữ nguyên hành vi cũ)
            if h_sym < 'H':
                EI = -es
                ES = EI + it_hole
            else:
                ES = -ei
                EI = ES - it_hole

    # ---- 4. LẮP GHÉP ----
    smax = ES - ei
    smin = EI - es
    nmax = es - EI
    nmin = ei - ES

    if smin >= 0:
        fit_type = "Lắp lỏng (Có độ hở)"
        fit_class = "clearance"
        color_theme = "emerald"
    elif nmin >= 0:
        fit_type = "Lắp chặt (Có độ dôi)"
        fit_class = "interference"
        color_theme = "rose"
    else:
        fit_type = "Lắp trung gian"
        fit_class = "transition"
        color_theme = "amber"

    return {
        "D": D,
        "hole": {
            "sym": h_sym, "it": hole["it"], "ES": ES, "EI": EI, "T": it_hole,
            "Dmax": D + ES / 1000, "Dmin": D + EI / 1000,
        },
        "shaft": {
            "sym": s_sym, "it": shaft["it"], "es": es, "ei": ei, "T": it_shaft,
            "dmax": D + es / 1000, "dmin": D + ei / 1000,
        },
        "fit": {
            "type": fit_type, "class": fit_class, "colorTheme": color_theme,
            "Smax": smax, "Smin": smin, "Nmax": nmax, "Nmin": nmin,
            "TN": it_hole + it_shaft,
        },
    }

