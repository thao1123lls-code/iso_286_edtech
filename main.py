"""
ISO 286 EdTech - Backend FastAPI (Layered Architecture + JWT Auth/RBAC)

Kiến trúc 3 lớp (Layered Architecture):
- Presentation Layer : app.api        -> router /api/export/docx, /api/export/pdf, /api/iso/tables
- Business Logic     : app.services   -> ⭐ LỚP NGHIỆP VỤ (BLL)
- Configuration      : app.core       -> config, utils, pdf_fonts
- Data Model Layer   : app.models     -> Pydantic schemas
- Database Layer     : app.db         -> SQLAlchemy (iso_size_ranges, iso_it_grades, iso_deviations)
- Auth & RBAC        : tại file main.py (JWT login, get_current_user, require_lecturer)

==> Chạy:  uvicorn main:app --reload
"""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from app.api.routes.export import router as export_router
from app.api.routes.iso import router as iso_router
from app.core.config import API_TITLE
from app.core.pdf_fonts import register_pdf_fonts
from app.db import seed as iso_seed
from app.db.database import Base, engine
from app.db import models as iso_models  # noqa: F401 (đảm bảo ORM models được đăng ký)


# ===========================================================================
# CẤU HÌNH JWT AUTH
# ===========================================================================
# ⚠️ Trong môi trường production hãy đặt biến môi trường JWT_SECRET_KEY
# để không dùng secret mặc định này.
SECRET_KEY = "iso286-edtech-secret-key-2026-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 8 * 60  # 8 giờ (1 buổi thi / học)


# ===========================================================================
# MOCK DATABASE - TÀI KHOẢN NGƯỜI DÙNG
# ===========================================================================
# 2 user mẫu theo yêu cầu:
#   - giangvien / 123  -> role: lecturer (toàn quyền, được xuất Word/PDF)
#   - sinhvien  / 123  -> role: student  (chỉ tra cứu / học tập)
# Mật khẩu được băm bằng bcrypt trước khi lưu vào "CSDL".
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(plain: str) -> str:
    """Băm mật khẩu bằng bcrypt (passlib)."""
    return _pwd_context.hash(plain)


# Role hiển thị tiếng Việt cho frontend
ROLE_LABELS = {
    "lecturer": "Giảng viên",
    "student": "Sinh viên",
}

USERS = {
    "giangvien": {
        "username": "giangvien",
        "password_hash": _hash_password("123"),
        "full_name": "Giảng viên Cơ khí",
        "role": "lecturer",
        "department": "Khoa Cơ khí",
    },
    "sinhvien": {
        "username": "sinhvien",
        "password_hash": _hash_password("123"),
        "full_name": "Sinh viên Cơ khí",
        "role": "student",
        "department": "Lớp CK - Kỹ thuật",
    },
}


# ===========================================================================
# PYDANTIC SCHEMAS (Auth)
# ===========================================================================
class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    username: str
    full_name: str
    role: str
    department: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


# ===========================================================================
# AUTHENTICATION HELPERS
# ===========================================================================
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(username: str) -> str:
    """Tạo JWT token HS256 cho user (thời hạn cấu hình ở trên)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire, "role": USERS[username]["role"]}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> UserInfo:
    """FastAPI dependency: xác thực JWT -> trả về user đang đăng nhập.

    Nếu token thiếu / sai / hết hạn -> HTTP 401.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bạn cần đăng nhập để truy cập tài nguyên này.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username = payload.get("sub")
        if username not in USERS:
            raise jwt.InvalidTokenError()
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã bị chỉnh sửa.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserInfo(**USERS[username])


def require_lecturer(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """FastAPI dependency: yêu cầu role = lecturer (chặn student).

    Dùng cho /api/export/docx và /api/export/pdf.
    """
    if user.role != "lecturer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Giảng viên (lecturer) mới được sử dụng tính năng xuất file Word/PDF.",
        )
    return user


# ===========================================================================
# LOGIN ENDPOINT
# ===========================================================================
def _login_handler(payload: LoginRequest) -> LoginResponse:
    """Xử lý đăng nhập: kiểm tra user + mật khẩu -> cấp JWT."""
    user = USERS.get(payload.username)
    if user is None or not _pwd_context.verify(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu.",
        )
    token = create_access_token(payload.username)
    return LoginResponse(
        access_token=token,
        user=UserInfo(
            username=user["username"],
            full_name=user["full_name"],
            role=user["role"],
            department=user["department"],
        ),
    )


# ===========================================================================
# LIFESPAN (KHỞI TẠO DB + SEED)
# ===========================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo CSDL + seed dữ liệu ISO 286 khi ứng dụng khởi động."""
    Base.metadata.create_all(bind=engine)
    seeded = iso_seed.seed_if_empty()
    print(f"[ISO 286 DB] Bảng tra đã sẵn sàng. Seed mới: {seeded}")
    print("[AUTH] JWT + RBAC đã sẵn sàng. User mẫu: giangvien / sinhvien (mật khẩu: 123)")
    yield


app = FastAPI(title=API_TITLE, lifespan=lifespan)

# Đăng ký font PDF (Times New Roman Unicode) một lần khi khởi động.
register_pdf_fonts()

# CORS: cho phép mọi origin để nút "Xuất Word/PDF" hoạt động
# dù trang được mở từ Live Server (5500), localhost (3000) hay file://
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# ĐĂNG KÝ ROUTER
# ---------------------------------------------------------------------------
# /api/login - công khai, không cần token
app.add_api_route(
    "/api/login",
    _login_handler,
    methods=["POST"],
    response_model=LoginResponse,
    tags=["auth"],
    summary="Đăng nhập hệ thống (cấp JWT token)",
)

# /api/iso/* - MỌI user đã đăng nhập (lecturer & student) đều truy cập được.
#   -> bảo vệ bằng Depends(get_current_user)
app.include_router(
    iso_router,
    prefix="/api",
    dependencies=[Depends(get_current_user)],
)

# /api/export/* - CHỈ lecturer mới được gọi.
#   -> bảo vệ bằng Depends(require_lecturer)
app.include_router(
    export_router,
    prefix="/api",
    dependencies=[Depends(require_lecturer)],
)

