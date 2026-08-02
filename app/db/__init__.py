"""Tầng Cơ sở dữ liệu (Database Layer).

Số hóa toàn bộ bảng tra ISO 286 vào CSDL quan hệ:
- database.py    : engine + session (SQLAlchemy, hỗ trợ SQLite/MySQL/PostgreSQL)
- models.py      : ORM models (iso_size_ranges, iso_it_grades, iso_deviations, iso_fit_library)
- seed.py        : dữ liệu chuẩn ISO 286-1:2010 (IT01-IT18, sai lệch trục/lỗ)
- repository.py  : Data Access Layer (tra cứu IT, sai lệch, khoảng kích thước)
"""

