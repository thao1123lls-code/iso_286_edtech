"""Kết nối Cơ sở dữ liệu (SQLAlchemy).

- Mặc định SQLite (file iso286.db trong thư mục dự án) -> chạy ngay không cần server.
- Hỗ trợ MySQL/PostgreSQL bằng cách đặt biến môi trường DATABASE_URL:
    MySQL:      DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/iso286
    PostgreSQL: DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/iso286
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL

# SQLite cần check_same_thread=False khi dùng FastAPI (multi-thread).
_connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: mở session, tự đóng sau mỗi request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

