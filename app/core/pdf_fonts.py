"""Đăng ký font & styles cho PDF (Configuration Layer).

- Ưu tiên font Times New Roman (Unicode, hỗ trợ tiếng Việt có dấu).
- Fallback sang Liberation/DejaVu nếu không có TNR.
- Fallback cuối cùng: Helvetica (built-in của ReportLab).
"""
import os

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont

from app.core.config import SCHOOL_NAME, FACULTY_NAME, PAGE_SIZE
from app.core.utils import esc as _esc  # noqa: F401 (re-export convenience)

# Tên font mặc định (sẽ được gán lại sau khi đăng ký thành công)
PDF_FONT = "TNR"
PDF_FONT_B = "TNR-Bold"
PDF_FONT_I = "TNR-Italic"
PDF_FONT_BI = "TNR-BoldItalic"

_FONT_DIRS = [
    r"C:\Windows\Fonts",
    "/usr/share/fonts/truetype/msttcorefonts",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/dejavu",
    "/System/Library/Fonts/Supplemental",
    "/Library/Fonts",
]

_FONT_FALLBACKS = {
    "normal": [
        "times.ttf", "Times_New_Roman.ttf", "LiberationSerif-Regular.ttf",
        "DejaVuSerif.ttf", "DejaVuSans.ttf", "Vera.ttf",
    ],
    "bold": [
        "timesbd.ttf", "Times_New_Roman_Bold.ttf", "LiberationSerif-Bold.ttf",
        "DejaVuSerif-Bold.ttf", "DejaVuSans-Bold.ttf", "VeraBd.ttf",
    ],
    "italic": [
        "timesi.ttf", "Times_New_Roman_Italic.ttf", "LiberationSerif-Italic.ttf",
        "DejaVuSerif-Italic.ttf", "DejaVuSans-Oblique.ttf", "VeraIt.ttf",
    ],
    "boldItalic": [
        "timesbi.ttf", "Times_New_Roman_Bold_Italic.ttf",
        "LiberationSerif-BoldItalic.ttf", "DejaVuSerif-BoldItalic.ttf",
        "DejaVuSans-BoldOblique.ttf", "VeraBI.ttf",
    ],
}

try:
    import reportlab
    # Font kèm theo ReportLab chỉ dùng làm fallback CUỐI CÙNG,
    # ưu tiên font hệ thống (Times New Roman...) để tiếng Việt có dấu đúng.
    _FONT_DIRS.append(os.path.join(os.path.dirname(reportlab.__file__), "fonts"))
except Exception:  # pragma: no cover
    pass


def _find_font(style_key: str):
    for d in _FONT_DIRS:
        for name in _FONT_FALLBACKS[style_key]:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    return None


def register_pdf_fonts():
    """Đăng ký font TTF cho ReportLab. Gọi 1 lần khi khởi động ứng dụng."""
    global PDF_FONT, PDF_FONT_B, PDF_FONT_I, PDF_FONT_BI
    normal = _find_font("normal")
    if normal is None:
        # Không tìm thấy TTF -> dùng font built-in (tiếng Việt sẽ không có dấu).
        PDF_FONT = "Helvetica"
        PDF_FONT_B = "Helvetica-Bold"
        PDF_FONT_I = "Helvetica-Oblique"
        PDF_FONT_BI = "Helvetica-BoldOblique"
        return
    bold = _find_font("bold") or normal
    italic = _find_font("italic") or normal
    bold_italic = _find_font("boldItalic") or bold
    pdfmetrics.registerFont(TTFont("TNR", normal))
    pdfmetrics.registerFont(TTFont("TNR-Bold", bold))
    pdfmetrics.registerFont(TTFont("TNR-Italic", italic))
    pdfmetrics.registerFont(TTFont("TNR-BoldItalic", bold_italic))
    registerFontFamily(
        "TNR", normal="TNR", bold="TNR-Bold",
        italic="TNR-Italic", boldItalic="TNR-BoldItalic",
    )
    PDF_FONT, PDF_FONT_B = "TNR", "TNR-Bold"
    PDF_FONT_I, PDF_FONT_BI = "TNR-Italic", "TNR-BoldItalic"


def build_pdf_styles():
    """Tạo bộ style chuẩn cho PDF dựa trên font đã đăng ký."""
    _STYLES = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "PdfTitle", parent=_STYLES["Title"], fontName=PDF_FONT_B, fontSize=16,
            leading=20, alignment=1, textColor=colors.black, spaceAfter=6,
        ),
        "sub": ParagraphStyle(
            "PdfSub", parent=_STYLES["Normal"], fontName=PDF_FONT,
            fontSize=12, leading=16, alignment=1,
        ),
        "h2": ParagraphStyle(
            "PdfH2", parent=_STYLES["Heading2"], fontName=PDF_FONT_B, fontSize=14,
            leading=18, textColor=colors.black, spaceBefore=8, spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "PdfH3", parent=_STYLES["Heading3"], fontName=PDF_FONT_B, fontSize=12,
            leading=15, textColor=colors.black, spaceBefore=6, spaceAfter=3,
        ),
        "normal": ParagraphStyle(
            "PdfNormal", parent=_STYLES["Normal"], fontName=PDF_FONT,
            fontSize=11, leading=15,
        ),
    }


def pdf_page_decorator(canvas, doc):
    """Header + Footer cho mỗi trang PDF."""
    canvas.saveState()
    w, h = PAGE_SIZE
    canvas.setFont(PDF_FONT_B, 10)
    canvas.drawString(2 * cm, h - 1.1 * cm, SCHOOL_NAME)
    canvas.setFont(PDF_FONT, 9)
    canvas.drawString(2 * cm, h - 1.5 * cm, FACULTY_NAME)
    canvas.setLineWidth(0.8)
    canvas.setStrokeColor(colors.black)
    canvas.line(2 * cm, h - 1.7 * cm, w - 2 * cm, h - 1.7 * cm)
    canvas.setFont(PDF_FONT, 10)
    canvas.drawCentredString(w / 2, 1.0 * cm, f"Trang {doc.page}")
    canvas.restoreState()

