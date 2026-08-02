"""Tiện ích dùng chung (Shared Utilities)."""
import html


def esc(v) -> str:
    """Escape HTML/XML để dùng trong Paragraph của ReportLab."""
    return html.escape(str(v))


def fmt_signed(v):
    """Định dạng sai lệch: 0 -> '0'; 25 -> '+25'; -25 -> '-25'."""
    if v is None:
        return "—"
    try:
        v = int(round(float(v)))
    except (TypeError, ValueError):
        return str(v)
    if v == 0:
        return "0"
    return f"{v:+d}"

