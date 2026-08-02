"""Nghiệp vụ xuất tài liệu PDF (ReportLab) - Business Logic Layer.

Chuyển toàn bộ logic tạo PDF từ main.py vào đây:
- Font Unicode Times New Roman (đăng ký TTF) hiển thị tiếng Việt có dấu.
- Header/footer trên từng trang, trang bìa, bảng đáp án,
  sơ đồ vector ToleranceDiagram, bảng BAREM 10.0.
"""
import io
from typing import Any, List

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import (
    SCHOOL_NAME,
    FACULTY_NAME,
    COURSE_NAME,
    PAGE_SIZE,
    PDF_MARGIN_LEFT,
    PDF_MARGIN_RIGHT,
    PDF_MARGIN_TOP,
    PDF_MARGIN_BOTTOM,
)
from app.core.pdf_fonts import (
    PDF_FONT,
    PDF_FONT_B,
    pdf_page_decorator,
    build_pdf_styles,
)
from app.core.utils import esc, fmt_signed
from app.models.schemas import ExamData, Question, Task


def _make_table(data, col_widths, header_bg=colors.HexColor("#D9E2F3"), styles=None):
    pdf_normal = ParagraphStyle(
        "pdf_normal_local", fontName=PDF_FONT, fontSize=10, leading=13, alignment=1
    )
    rows = []
    for r_i, row in enumerate(data):
        cells = []
        for val in row:
            st = ParagraphStyle(
                "cell", parent=pdf_normal, fontSize=10, leading=13, alignment=1
            )
            cells.append(Paragraph(esc(val), st))
        rows.append(cells)
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("FONTNAME", (0, 0), (-1, 0), PDF_FONT_B),
    ]
    if styles:
        style += styles
    if len(data) > 1:
        style.append(("BACKGROUND", (0, 1), (-1, -1), colors.white))
    t.setStyle(TableStyle(style))
    return t


def _build_rubric_table(active_tasks: List[Task], pdf_normal):
    total = sum(float(t.points) for t in active_tasks)
    header = ["STT", "Tiêu chí đánh giá (Rubric Criterion)", "Điểm tối đa", "Mô tả mức độ Đạt / Không đạt"]
    rows = [header]
    for i, t in enumerate(active_tasks):
        rows.append([
            str(i + 1),
            t.name,
            f"{float(t.points):.1f}đ",
            "Đạt 100%: Đúng trị số + đơn vị (μm/mm)\nĐạt 50%: Sai dấu (+/-) hoặc nhầm đơn vị",
        ])
    rows.append(["", "CỘNG TỔNG ĐIỂM BÀI THI:", f"{total:.1f}đ",
                 "Quy chuẩn linh hoạt theo thang điểm 10 đại học."])

    table_rows = []
    for r_i, row in enumerate(rows):
        cell_paras = []
        for c_i, val in enumerate(row):
            al = 1 if c_i in (0, 2) else 0
            is_bold = r_i == 0 or r_i == len(rows) - 1
            st = ParagraphStyle(
                "rub", parent=pdf_normal, fontSize=9, leading=12,
                alignment=al, fontName=PDF_FONT_B if is_bold else PDF_FONT,
            )
            cell_paras.append(Paragraph(esc(val).replace("\n", "<br/>"), st))
        table_rows.append(cell_paras)

    t = Table(table_rows, colWidths=[1.2 * cm, 6.8 * cm, 2.2 * cm, 6.8 * cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E2F3")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F2F2F2")),
    ]))
    return t


class ToleranceDiagram(Flowable):
    """Sơ đồ miền dung sai vector cho PDF (đúng tỷ lệ μm)."""

    def __init__(self, q: Question, width=16 * cm, height=7 * cm):
        super().__init__()
        self.q = q
        self.width = width
        self.height = height

    def draw(self):
        q = self.q
        hole, shaft = q.hole, q.shaft
        devs = [int(round(float(x))) for x in (hole.ES, hole.EI, shaft.es, shaft.ei, 0)]
        max_dev, min_dev = max(devs), min(devs)
        span = max_dev - min_dev
        if span <= 0:
            span = 10
        pad = span * 0.15
        ymax, ymin = max_dev + pad, min_dev - pad

        c = self.canv
        w, h = self.width, self.height
        x0 = 1.2 * cm
        x1 = w - 1.2 * cm
        plot_h = h - 2 * cm
        y_axis = 1 * cm

        def map_y(v):
            return y_axis + ((ymax - v) / (ymax - ymin)) * plot_h

        c.setStrokeColor(colors.black)
        c.setLineWidth(1.2)
        yz = map_y(0)
        c.setDash(4, 3)
        c.line(x0, yz, x1, yz)
        c.setDash()
        c.setFont(PDF_FONT, 8)
        c.drawString(x0 - 0.3 * cm, yz - 3, "0")

        hole_w = 5.5 * cm
        hx0 = x0 + 0.5 * cm
        hy0, hy1 = map_y(hole.EI), map_y(hole.ES)
        c.setFillColor(colors.HexColor("#DCE6F1"))
        c.setStrokeColor(colors.HexColor("#2E74B5"))
        c.setLineWidth(1.4)
        c.rect(hx0, hy0, hole_w, hy1 - hy0, stroke=1, fill=1)
        c.setFillColor(colors.HexColor("#1F4E79"))
        c.setFont(PDF_FONT_B, 9)
        c.drawCentredString(hx0 + hole_w / 2, (hy0 + hy1) / 2 - 4, f"LỖ {hole.sym}{hole.it}")
        c.setFont(PDF_FONT, 8)
        c.drawString(hx0, hy1 + 3, f"ES = {fmt_signed(hole.ES)} μm")
        c.drawString(hx0, hy0 - 10, f"EI = {fmt_signed(hole.EI)} μm")

        shaft_w = 5.5 * cm
        sx0 = x1 - shaft_w - 0.5 * cm
        sy0, sy1 = map_y(shaft.ei), map_y(shaft.es)
        c.setFillColor(colors.HexColor("#FDE9D9"))
        c.setStrokeColor(colors.HexColor("#C55A11"))
        c.setLineWidth(1.4)
        c.rect(sx0, sy0, shaft_w, sy1 - sy0, stroke=1, fill=1)
        c.setFillColor(colors.HexColor("#843C0C"))
        c.setFont(PDF_FONT_B, 9)
        c.drawCentredString(sx0 + shaft_w / 2, (sy0 + sy1) / 2 - 4, f"TRỤC {shaft.sym}{shaft.it}")
        c.setFont(PDF_FONT, 8)
        c.drawString(sx0, sy1 + 3, f"es = {fmt_signed(shaft.es)} μm")
        c.drawString(sx0, sy0 - 10, f"ei = {fmt_signed(shaft.ei)} μm")

        c.setFont(PDF_FONT, 8)
        c.drawString(x0, y_axis - 0.5 * cm, "Đơn vị: μm (trục đứng)")


def _build_pdf(elements: list, data: ExamData, styles: dict):
    stats = data.stats
    total = stats.get("total", 0)
    batch = stats.get("batchCode", "N/A")
    pdf_title = styles["title"]
    pdf_sub = styles["sub"]
    pdf_h2 = styles["h2"]
    pdf_h3 = styles["h3"]
    pdf_normal = styles["normal"]

    elements.append(Paragraph(esc(SCHOOL_NAME), pdf_title))
    elements.append(Paragraph(esc(FACULTY_NAME), pdf_sub))
    elements.append(Paragraph(esc(COURSE_NAME), pdf_sub))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(esc("BỘ ĐỀ THI & ĐÁP ÁN"), pdf_title))
    elements.append(Paragraph(esc("DUNG SAI KỸ THUẬT & ĐO LƯỜNG (ISO 286)"), pdf_sub))
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(f"Mã lô kiểm tra: {esc(batch)}", pdf_sub))
    elements.append(Paragraph(f"Tổng số đề: {total} bài", pdf_sub))
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Ngày ...... tháng ...... năm 20......", pdf_sub))
    elements.append(PageBreak())

    for idx, q in enumerate(data.questions):
        if idx > 0:
            elements.append(PageBreak())

        elements.append(Paragraph(f"MÃ ĐỀ: #{idx + 1} - {esc(q.examCode)}", pdf_h2))
        elements.append(Paragraph(f"<b>Họ &amp; Tên:</b> {esc(q.student.name)}", pdf_normal))
        elements.append(Paragraph(
            f"<b>MSSV:</b> {esc(q.student.mssv)} | <b>Lớp:</b> {esc(q.student.className)} | "
            f"<b>Mã lớp:</b> {esc(q.student.classCode)} | <b>Mức độ:</b> {esc(q.diffLabel)}",
            pdf_normal,
        ))
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("I. ĐỀ BÀI", pdf_h3))
        elements.append(Paragraph(
            f"Cho mối ghép trụ tròn trơn tiêu chuẩn ISO 286: "
            f"<b>Φ{esc(q.D)} {esc(q.hole.sym)}{esc(q.hole.it)}/{esc(q.shaft.sym)}{esc(q.shaft.it)}</b>",
            pdf_normal,
        ))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("II. YÊU CẦU THỰC HIỆN", pdf_h3))
        for task in data.activeTasks:
            elements.append(Paragraph(f"• {esc(task.name)}", pdf_normal))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("III. ĐÁP ÁN & BÀI GIẢI CHI TIẾT", pdf_h3))

        ans_data = [
            ["Thông số", f"LỖ Φ{q.D} {q.hole.sym}{q.hole.it}", f"TRỤC Φ{q.D} {q.shaft.sym}{q.shaft.it}"],
            ["Cấp chính xác", f"IT{q.hole.it}", f"IT{q.shaft.it}"],
            ["Dung sai", f"TD = {fmt_signed(q.hole.T)} μm", f"Td = {fmt_signed(q.shaft.T)} μm"],
            ["Sai lệch trên", f"ES = {fmt_signed(q.hole.ES)} μm", f"es = {fmt_signed(q.shaft.es)} μm"],
            ["Sai lệch dưới", f"EI = {fmt_signed(q.hole.EI)} μm", f"ei = {fmt_signed(q.shaft.ei)} μm"],
            ["KT lớn nhất", f"Dmax = {float(q.hole.Dmax):.3f} mm", f"dmax = {float(q.shaft.dmax):.3f} mm"],
            ["KT nhỏ nhất", f"Dmin = {float(q.hole.Dmin):.3f} mm", f"dmin = {float(q.shaft.dmin):.3f} mm"],
        ]
        elements.append(_make_table(ans_data, col_widths=[3.2 * cm, 5.4 * cm, 5.4 * cm]))
        elements.append(Spacer(1, 8))

        fit_parts = []
        if q.fit.Smax is not None:
            fit_parts.append(f"Smax = {fmt_signed(q.fit.Smax)} μm")
        if q.fit.Smin is not None:
            fit_parts.append(f"Smin = {fmt_signed(q.fit.Smin)} μm")
        if q.fit.Nmax is not None:
            fit_parts.append(f"Nmax = {fmt_signed(q.fit.Nmax)} μm")
        if q.fit.Nmin is not None:
            fit_parts.append(f"Nmin = {fmt_signed(q.fit.Nmin)} μm")
        elements.append(Paragraph(f"<b>3. Đặc tính lắp ghép: {esc(q.fit.type.upper())}</b>", pdf_normal))
        elements.append(Paragraph("&nbsp;• " + "<br/>&nbsp;• ".join(fit_parts), pdf_normal))
        elements.append(Paragraph(f"&nbsp;• Dung sai lắp ghép TS,N = {fmt_signed(q.fit.TN)} μm", pdf_normal))
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("4. Sơ đồ miền dung sai mối ghép", pdf_h3))
        elements.append(ToleranceDiagram(q))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("5. BẢNG BAREM CHẤM ĐIỂM (THANG ĐIỂM 10.0)", pdf_h3))
        elements.append(_build_rubric_table(data.activeTasks, pdf_normal))


def build_pdf_bytes(data: ExamData) -> io.BytesIO:
    """Tạo tài liệu PDF từ ExamData và trả về BytesIO."""
    bio = io.BytesIO()
    doc = SimpleDocTemplate(
        bio,
        pagesize=PAGE_SIZE,
        rightMargin=PDF_MARGIN_RIGHT,
        leftMargin=PDF_MARGIN_LEFT,
        topMargin=PDF_MARGIN_TOP,
        bottomMargin=PDF_MARGIN_BOTTOM,
        title=f"De Thi ISO 286 {data.stats.get('batchCode', '')}",
        author=SCHOOL_NAME,
    )
    elements: List[Any] = []
    _build_pdf(elements, data, build_pdf_styles())
    doc.build(elements, onFirstPage=pdf_page_decorator, onLaterPages=pdf_page_decorator)
    bio.seek(0)
    return bio


def filename_pdf(data: ExamData) -> str:
    """Tạo tên file PDF theo mã lô kiểm tra."""
    return f"De_Thi_ISO286_{data.stats.get('batchCode')}.pdf"

