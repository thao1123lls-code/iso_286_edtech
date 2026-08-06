"""Xuất Header đề thi chuẩn Trường ĐH Công nghệ Đồng Nai (DNTU) ra PDF.

Hàm chính (Story-friendly):
    build_exam_header(ma_de, ma_lo_dot) -> list[Flowable]  (5 phần Form DNTU)

Cấu trúc 5 phần:
    1. Bảng thông tin phê duyệt      (1 dòng x 2 cột, không viền ngoài)
    2. Dòng text phân cách            (in nghiêng, căn giữa, size nhỏ)
    3. Bảng Header Đề Thi             (bảng phức tạp dùng SPAN cell, Mã đề đỏ)
    4. Bảng thông tin Thí sinh        (BOX + Nested Table MSSV 7 ô vuông, Mã lô đỏ)
    5. Bảng Điểm số & Chữ ký + Khung GHI CHÚ & QUY ĐỊNH THI (bullet points)

Font sử dụng: Times New Roman (đã đăng ký trong app/core/pdf_fonts.py).
"""
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import (
    PAGE_SIZE,
    PDF_MARGIN_BOTTOM,
    PDF_MARGIN_LEFT,
    PDF_MARGIN_RIGHT,
    PDF_MARGIN_TOP,
)
from app.core.pdf_fonts import PDF_FONT, PDF_FONT_B, PDF_FONT_I

# ---------------------------------------------------------------------------
# Hằng số nội dung Header (có thể chỉnh sửa trực tiếp)
# ---------------------------------------------------------------------------
DNTU_SCHOOL    = "TRƯỜNG ĐH CÔNG NGHỆ ĐỒNG NAI"
DNTU_FACULTY   = "KHOA KỸ THUẬT"
DNTU_DEPT      = "Bộ môn Thiết kế máy"
EXAM_TITLE     = "BÀI KIỂM TRA 01"
SUBJECT_CODE   = "ME2007"
SUBJECT_NAME   = "CHI TIẾT MÁY"
DURATION       = "60 phút"
SEMESTER       = "1"
ACADEMIC_YEAR  = "2026-2027"
EXAM_DAY       = "25/8/2026"
EXAM_CODE      = "101"          # Mã đề thi mặc định (màu đỏ)
LOT_CODE       = "LD-2026-A1"   # Mã lô/đợt đề mặc định (màu đỏ)

LECTURER_NAME   = "THÂN TRỌNG KHÁNH ĐẠT"
APPROVER_TITLE  = "Trưởng bộ môn"
APPROVER_NAME   = "PGS. TS. BÙI TRỌNG HIẾU"
ISSUE_DATE      = "18/8/2026"
APPROVE_DATE    = "18/8/2026"
DOC_CODE        = "FL051.1"

RED    = colors.HexColor("#C00000")
GRAY   = colors.HexColor("#999999")
BLACK  = colors.black

# Chiều rộng nội dung khả dụng của trang
CONTENT_W = PAGE_SIZE[0] - PDF_MARGIN_LEFT - PDF_MARGIN_RIGHT


# ---------------------------------------------------------------------------
# Helper: tạo ParagraphStyle nhanh
# ---------------------------------------------------------------------------
def _st(name, fontName=PDF_FONT, size=10, leading=13,
        align=TA_LEFT, color=BLACK, spaceAfter=0):
    return ParagraphStyle(
        name, fontName=fontName, fontSize=size, leading=leading,
        alignment=align, textColor=color, spaceAfter=spaceAfter,
    )


# ---------------------------------------------------------------------------
# Helper: bọc text/chuỗi thành Paragraph (LUÔN dùng font Unicode đã đăng ký)
# ---------------------------------------------------------------------------
def _cell(text, name="cell", fontName=PDF_FONT, size=10, leading=13,
          align=TA_LEFT, color=BLACK):
    """Bọc một chuỗi UTF-8 thành Paragraph để cell Bảng dùng font Unicode.

    Việc truyền chuỗi trần (plain str) vào cell Table khiến ReportLab dùng
    font mặc định (Helvetica) -> ký tự tiếng Việt có dấu bị hiển thị thành
    ô vuông đen (■). Hàm này ép fontName=PDF_FONT (TimesNewRoman) cho mọi ô.
    """
    return Paragraph(str(text), _st(name, fontName=fontName, size=size,
                                    leading=leading, align=align, color=color))


# ---------------------------------------------------------------------------
# HÀM CHÍNH: build_exam_header(ma_de, ma_lo_dot)
# ---------------------------------------------------------------------------
def build_exam_header(ma_de, ma_lo_dot):
    """Trả về list Flowable (5 phần) - Form Header chuẩn DNTU (dành cho PDF).

    Đây là hàm dạng **Story-friendly**: chỉ cần `story += build_exam_header(...)`.

    Tham số:
        ma_de      : str -> Mã đề thi   (hiển thị màu ĐỎ ở Phần 3).
        ma_lo_dot  : str -> Mã lô/đợt đề (hiển thị màu ĐỎ ở Phần 4).

    Bố cục 5 phần:
      1. Bảng Phê duyệt        (1 dòng x 2 cột, căn giữa, không viền ngoài)
      2. Dòng text phân cách    (in nghiêng, size 9, căn giữa)
      3. Bảng Header Đề Thi    (4 cột x 4 hàng, GRID + SPAN, Mã đề màu đỏ)
      4. Bảng Thông tin Thí sinh (BOX, Nested Table MSSV 7 ô vuông, Mã lô đỏ)
      5. Bảng Điểm số & Chữ ký  (Grid 2x4) + Khung GHI CHÚ & QUY ĐỊNH THI (BOX)
    """
    from app.core.pdf_fonts import register_pdf_fonts
    register_pdf_fonts()  # đảm bảo font TimesNewRoman đã được đăng ký

    flowables = []

    # =====================================================================
    # PHẦN 1: BẢNG PHÊ DUYỆT (1 dòng x 2 cột, kẻ dọc giữa, không viền ngoài)
    # =====================================================================
    st_left = _st("appr_left", fontName=PDF_FONT, size=10, leading=14,
                  align=TA_CENTER)
    left_para = Paragraph(
        f"Giảng viên ra đề: {ISSUE_DATE} (Ngày ra đề)<br/>"
        f'<font color="#999999"><i>(Nhấp để tải chữ ký)</i></font><br/>'
        f"<br/>"
        f".....................<br/>"
        f"<b>{LECTURER_NAME}</b>",
        st_left,
    )
    right_para = Paragraph(
        f"Người phê duyệt: {APPROVE_DATE} (Ngày duyệt)<br/>"
        f'<font color="#999999"><i>(Nhấp để tải chữ ký)</i></font><br/>'
        f"<b>{APPROVER_TITLE}</b><br/>"
        f"<b>{APPROVER_NAME}</b><br/>"
        f".....................<br/>",
        st_left,
    )
    tbl_approval = Table(
        [[left_para, right_para]],
        colWidths=[CONTENT_W / 2.0, CONTENT_W / 2.0],
    )
    tbl_approval.setStyle(TableStyle([
        # Chỉ kẻ dọc giữa (LINEBEFORE ở cột 1), KHÔNG viền ngoài (BOX)
        ("LINEBEFORE", (1, 0), (1, 0), 0.6, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flowables.append(tbl_approval)
    flowables.append(Spacer(1, 0.15 * cm))

    # =====================================================================
    # PHẦN 2: DÒNG TEXT PHÂN CÁCH (in nghiêng, size 9, căn giữa)
    # =====================================================================
    flowables.append(Spacer(1, 0.15 * cm))
    sep = Paragraph(
        '<font color="#999999"><i>(Phần phía trên cần che đi khi in sao đề thi)</i></font>',
        _st("sep", size=9, leading=11, align=TA_CENTER),
    )
    flowables.append(sep)
    flowables.append(Spacer(1, 0.2 * cm))

    # =====================================================================
    # PHẦN 3: BẢNG HEADER ĐỀ THI (4 cột x 4 hàng, GRID + SPAN)
    # =====================================================================
    # Cột:    0            1                2             3
    # +-------------------+-----------------+--------------+-------------+
    # | LOGO / Tên trường | BÀI KIỂM TRA 01 | Học kỳ/năm   | 1/2026-2027 |
    # | (sp rows 0-3)      | (sp rows 0-1)   | Ngày thi     | 25/8/2026   |
    # |                   |                 | Mã môn học   | ME2007      |
    # |                   |                 | Mã đề thi    | <ma_de> (đỏ)|
    # +-------------------+-----------------+--------------+-------------+
    logo_para = Paragraph(
        f'<font color="#999999" size="8"><i>[LOGO]</i></font><br/>'
        f"<b>{DNTU_SCHOOL}</b><br/>"
        f"<b>{DNTU_FACULTY}</b><br/>"
        f"{DNTU_DEPT}",
        _st("logo", size=9.5, leading=12, align=TA_CENTER),
    )
    title_para = Paragraph(
        f"<b>{EXAM_TITLE}</b>",
        _st("title", fontName=PDF_FONT_B, size=16, leading=20, align=TA_CENTER),
    )
    # TẤT CẢ các ô có text đều bọc trong Paragraph (font Unicode TimesNewRoman)
    # để tránh hiển thị ô vuông đen (■) do dùng font mặc định Helvetica.
    data_exam = [
        [logo_para, title_para,
         _cell("Học kỳ/năm học", "lbl_hk", align=TA_CENTER),
         _cell(f"{SEMESTER} / {ACADEMIC_YEAR}", "val_hk", align=TA_CENTER)],
        ["", "",
         _cell("Ngày thi", "lbl_day", align=TA_CENTER),
         _cell(EXAM_DAY, "val_day", align=TA_CENTER)],
        ["", "",
         _cell("Mã môn học", "lbl_code", align=TA_CENTER),
         _cell(SUBJECT_CODE, "val_subj", align=TA_CENTER)],
        ["", "",
         _cell("Mã đề thi", "lbl_examcode", align=TA_CENTER),
         _cell(ma_de, "val_examcode",
               fontName=PDF_FONT_B, color=RED, align=TA_CENTER)],
    ]
    w_left = 3.4 * cm
    w_title = 4.0 * cm
    w_right = (CONTENT_W - w_left - w_title) / 2.0
    tbl_exam = Table(
        data_exam,
        colWidths=[w_left, w_title, w_right, w_right],
    )
    tbl_exam.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        # Cột 0 (Logo/Tên trường) trải 4 hàng
        ("SPAN", (0, 0), (0, 3)),
        # Cột 1 (BÀI KIỂM TRA 01) trải 2 hàng
        ("SPAN", (1, 0), (1, 1)),
        # Mã đề thi: màu đỏ, đậm
        ("TEXTCOLOR", (3, 3), (3, 3), RED),
        ("FONTNAME", (3, 3), (3, 3), PDF_FONT_B),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flowables.append(tbl_exam)
    flowables.append(Spacer(1, 0.15 * cm))

    # =====================================================================
    # PHẦN 4: BẢNG THÔNG TIN THÍ SINH (BOX) + Nested Table MSSV
    # =====================================================================
    st_stu = _st("stu", size=10, leading=13, align=TA_LEFT)
    st_stu_c = _st("stu_c", size=10, leading=13, align=TA_CENTER)

    # Dòng 1: Tiêu đề
    stu_title = Paragraph(
        "PHẦN DÀNH CHO THÍ SINH ĐIỀN THÔNG TIN",
        _st("stu_title", fontName=PDF_FONT_B, size=11, leading=14,
            align=TA_CENTER),
    )
    # Dòng 2: Họ và tên (trái) + MSSV (nested 7 ô vuông, phải)
    name_para = Paragraph(
        "Họ và tên thí sinh: ................................", st_stu,
    )
    # Nested table 7 ô vuông nối liền nhau
    mssv_boxes = Table(
        [["", "", "", "", "", "", ""]],
        colWidths=[0.5 * cm] * 7,
        rowHeights=[0.5 * cm],
    )
    mssv_boxes.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    mssv_cell = Table(
        [[Paragraph("MSSV:", _st("mssv", size=10, align=TA_LEFT)), mssv_boxes]],
        colWidths=[1.3 * cm, 7.0 * cm],
    )
    mssv_cell.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    # Dòng 3: Lớp/Nhóm, STT phòng, Phòng thi, Mã lô/đợt đề (Mã đỏ)
    class_para = Paragraph(
        f"Lớp/Nhóm: ...............&nbsp;&nbsp; STT phòng: ........&nbsp;&nbsp; "
        f"Phòng thi: ........&nbsp;&nbsp; "
        f"Mã lô/đợt đề: <font color='#C00000'><b>{ma_lo_dot}</b></font>",
        st_stu_c,
    )
    # Dòng 4: Ghi chú (trái) + Chữ ký thí sinh (phải)
    note_para = Paragraph(
        '<i>Thí sinh kiểm tra kỹ Mã đề thi trước khi làm bài.</i>',
        _st("note", size=9, leading=12, align=TA_LEFT),
    )
    sign_para = Paragraph(
        "Chữ ký thí sinh: _________________",
        _st("sign", size=10, align=TA_RIGHT),
    )

    data_stu = [
        [stu_title, "", "", ""],
        [name_para, "", mssv_cell, ""],
        [class_para, "", "", ""],
        [note_para, "", "", sign_para],
    ]
    tbl_stu = Table(
        data_stu,
        colWidths=[4.5 * cm, 3.5 * cm, 3.0 * cm, 6.0 * cm],
    )
    tbl_stu.setStyle(TableStyle([
        # Chỉ kẻ khung ngoài (BOX), KHÔNG kẻ lưới bên trong
        ("BOX", (0, 0), (-1, -1), 0.6, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        # Tiêu đề trải 4 cột
        ("SPAN", (0, 0), (3, 0)),
        # Họ tên trải cột 0-1
        ("SPAN", (0, 1), (1, 1)),
        # MSSV trải cột 2-3
        ("SPAN", (2, 1), (3, 1)),
        # Dòng 3 trải 4 cột
        ("SPAN", (0, 2), (3, 2)),
        # Ghi chú trải cột 0-2
        ("SPAN", (0, 3), (2, 3)),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flowables.append(tbl_stu)
    flowables.append(Spacer(1, 0.15 * cm))

    # =====================================================================
    # PHẦN 5A: BẢNG ĐIỂM SỐ & CHỮ KÝ (Grid 2 dòng x 4 cột bằng nhau)
    # =====================================================================
    score_headers = [
        "Điểm số bằng số", "Điểm số bằng chữ",
        "Chữ ký CB chấm thi 1", "Chữ ký CB chấm thi 2",
    ]
    data_score = [
        [Paragraph(f"<b>{h}</b>",
                   _st("score_h", fontName=PDF_FONT_B, size=10,
                       align=TA_CENTER)) for h in score_headers],
        [Paragraph("", _st("score_v", size=10)) for _ in score_headers],
    ]
    tbl_score = Table(
        data_score,
        colWidths=[CONTENT_W / 4.0] * 4,
        rowHeights=[None, 1.0 * cm],
    )
    tbl_score.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F2F2")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flowables.append(tbl_score)
    flowables.append(Spacer(1, 0.15 * cm))

    # =====================================================================
    # PHẦN 5B: Ô GHI CHÚ & QUY ĐỊNH THI (Box, bullet points)
    # =====================================================================
    notes_text = (
        "<b>GHI CHÚ &amp; QUY ĐỊNH THI:</b><br/>"
        "&nbsp;&nbsp;• Được sử dụng tài liệu giấy (Không sử dụng thiết bị điện tử).<br/>"
        "&nbsp;&nbsp;• Được sử dụng bút chì để vẽ hình và lập sơ đồ.<br/>"
        "&nbsp;&nbsp;• Thí sinh nộp lại toàn bộ đề thi cùng bài làm khi hết giờ làm bài."
    )
    note_box = Paragraph(
        notes_text,
        _st("note_box", size=10, leading=14, align=TA_LEFT),
    )
    tbl_note = Table([[note_box]], colWidths=[CONTENT_W])
    tbl_note.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, BLACK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flowables.append(tbl_note)

    return flowables


# ---------------------------------------------------------------------------
# Wrapper tương thích ngược: build_pdf_header() / build_dntu_exam_header()
# ---------------------------------------------------------------------------
def build_pdf_header():
    """Wrapper: gọi build_exam_header với Mã đề & Mã lô mặc định (hằng số)."""
    return build_exam_header(EXAM_CODE, LOT_CODE)


# ----- Alias giữ tên cũ cho tương thích ngược -----
build_dntu_exam_header = build_pdf_header


# ---------------------------------------------------------------------------
# Chạy thử độc lập:  python app/services/pdf_exam_header.py
#   -> tạo _exam_header_sample.pdf
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from app.core.pdf_fonts import register_pdf_fonts

    register_pdf_fonts()

    # --- Demo: build_exam_header(ma_de, ma_lo_dot) (Story-friendly) ---
    bio2 = io.BytesIO()
    doc2 = SimpleDocTemplate(
        bio2,
        pagesize=PAGE_SIZE,
        rightMargin=PDF_MARGIN_RIGHT,
        leftMargin=PDF_MARGIN_LEFT,
        topMargin=PDF_MARGIN_TOP,
        bottomMargin=PDF_MARGIN_BOTTOM,
        title="Form De Thi DNTU (build_exam_header)",
    )
    story2 = build_exam_header("101", "LD-2026-A1")
    story2.append(Spacer(1, 0.5 * cm))
    story2.append(Paragraph("[Nội dung câu hỏi bắt đầu từ đây...]",
                            _st("body", size=11, leading=15)))
    doc2.build(story2)
    with open("_exam_header_form_dntu.pdf", "wb") as f:
        f.write(bio2.getvalue())
    print("Đã tạo file mẫu: _exam_header_form_dntu.pdf")
