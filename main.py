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
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

from app.api.routes.export import router as export_router
from app.api.routes.iso import router as iso_router
from app.core.config import API_TITLE
from app.core.pdf_fonts import register_pdf_fonts
from app.db import seed as iso_seed
from app.db.database import Base, engine, get_db
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
# Mật khẩu được băm bằng bcrypt trước khi lưu vào "CSDL".
# Danh sách tài khoản gồm:
#   - giangvien, gv01, gv02 / 123  -> role: lecturer (toàn quyền, được xuất Word/PDF)
#   - sinhvien, 2110481..2110485 / 123 -> role: student (chỉ tra cứu / học tập)
# (username 211048x trùng MSSV Sinh viên — đồng bộ với MOCK_USERS ở index.html)
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
    # ------------------------------------------------------------------
    # 2 GIẢNG VIÊN (role: lecturer) - đồng bộ với MOCK_USERS ở index.html
    # ------------------------------------------------------------------
    "gv01": {
        "username": "gv01",
        "password_hash": _hash_password("123"),
        "full_name": "TS. Nguyễn Văn Giảng",
        "role": "lecturer",
        "department": "Khoa Cơ khí - Bộ môn Kỹ thuật Cơ khí",
    },
    "gv02": {
        "username": "gv02",
        "password_hash": _hash_password("123"),
        "full_name": "ThS. Trần Thị Dạy",
        "role": "lecturer",
        "department": "Khoa Cơ khí - Bộ môn Cơ khí Chế tạo",
    },
    # ------------------------------------------------------------------
    # 5 SINH VIÊN (role: student) - đồng bộ với MOCK_USERS ở index.html
    # username trùng MSSV để demo đăng nhập nhanh.
    # ------------------------------------------------------------------
    "sinhvien": {
        "username": "sinhvien",
        "password_hash": _hash_password("123"),
        "full_name": "Sinh viên Cơ khí",
        "role": "student",
        "department": "Lớp CK - Kỹ thuật",
    },
    "2110481": {
        "username": "2110481",
        "password_hash": _hash_password("123"),
        "full_name": "Nguyễn Văn An",
        "role": "student",
        "department": "21CK1",
    },
    "2110482": {
        "username": "2110482",
        "password_hash": _hash_password("123"),
        "full_name": "Trần Thị Bình",
        "role": "student",
        "department": "21CK1",
    },
    "2110483": {
        "username": "2110483",
        "password_hash": _hash_password("123"),
        "full_name": "Lê Văn Cường",
        "role": "student",
        "department": "21CK2",
    },
    "2110484": {
        "username": "2110484",
        "password_hash": _hash_password("123"),
        "full_name": "Phạm Thị Dung",
        "role": "student",
        "department": "21CK2",
    },
"2110485": {
        "username": "2110485",
        "password_hash": _hash_password("123"),
        "full_name": "Vũ Văn Em",
        "role": "student",
        "department": "21CK3",
    },
}


# ===========================================================================
# MOCK ASSIGNMENTS - 3 ĐỀ THI MẪU (gán cho 3 Sinh viên đầu tiên)
# ===========================================================================
# Cấu trúc JSON tuân thủ đúng shape mà Frontend (index.html) cần:
#   buildExamDataFromBatch() / saveHistoryToBackend() dùng để "Xem lại" &
#   "Xuất Word/PDF". Mỗi phần tử gồm:
#   D, hole{sym,it,ES,EI,T,Dmax,Dmin}, shaft{sym,it,es,ei,T,dmax,dmin},
#   fit{type,class,colorTheme,Smax,Smin,Nmax,Nmin,TN},
#   student{mssv,name,className,classCode}, diffLabel, examCode, activeTasks[]
# Giá trị ES/EI es/ei (µm) và Dmax..dmin (mm) được tính theo chuẩn ISO 286
# (khớp với output của DualEngineMath.calculate trong index.html).
mock_assignments_db = [
    # ------------------------------------------------------------------
    # ĐỀ 1 - SV 2110481 : ϕ45 H7/g6  (Lắp lỏng - Clearance)
    # ------------------------------------------------------------------
    {
        "D": 45,
        "hole": {
            "sym": "H", "it": 7,
            "ES": 25, "EI": 0, "T": 25,
            "Dmax": 45.025, "Dmin": 45.000,
        },
        "shaft": {
            "sym": "g", "it": 6,
            "es": -9, "ei": -25, "T": 16,
            "dmax": 44.991, "dmin": 44.975,
        },
        "fit": {
            "type": "Lắp lỏng (Có độ hở)", "class": "clearance", "colorTheme": "emerald",
            "Smax": 50, "Smin": 9, "Nmax": -50, "Nmin": -9, "TN": 41,
        },
        "student": {
            "mssv": "2110481", "name": "Nguyễn Văn An",
            "className": "21CK1", "classCode": "ME2026",
        },
        "diffLabel": "Trung bình",
        "examCode": "ME2026-2110481",
        "activeTasks": [],
    },
    # ------------------------------------------------------------------
    # ĐỀ 2 - SV 2110482 : ϕ40 H7/k6  (Lắp trung gian - Transition)
    # ------------------------------------------------------------------
    {
        "D": 40,
        "hole": {
            "sym": "H", "it": 7,
            "ES": 25, "EI": 0, "T": 25,
            "Dmax": 40.025, "Dmin": 40.000,
        },
        "shaft": {
            "sym": "k", "it": 6,
            "es": 18, "ei": 2, "T": 16,
            "dmax": 40.018, "dmin": 40.002,
        },
        "fit": {
            "type": "Lắp trung gian", "class": "transition", "colorTheme": "amber",
            "Smax": 23, "Smin": -18, "Nmax": 18, "Nmin": -23, "TN": 41,
        },
        "student": {
            "mssv": "2110482", "name": "Trần Thị Bình",
            "className": "21CK1", "classCode": "ME2026",
        },
        "diffLabel": "Trung bình",
        "examCode": "ME2026-2110482",
        "activeTasks": [],
    },
    # ------------------------------------------------------------------
    # ĐỀ 3 - SV 2110483 : ϕ30 H7/p6  (Lắp chặt - Interference)
    # ------------------------------------------------------------------
    {
        "D": 30,
        "hole": {
            "sym": "H", "it": 7,
            "ES": 21, "EI": 0, "T": 21,
            "Dmax": 30.021, "Dmin": 30.000,
        },
        "shaft": {
            "sym": "p", "it": 6,
            "es": 35, "ei": 22, "T": 13,
            "dmax": 30.035, "dmin": 30.022,
        },
        "fit": {
            "type": "Lắp chặt (Có độ dôi)", "class": "interference", "colorTheme": "rose",
            "Smax": -35, "Smin": -1, "Nmax": 35, "Nmin": 1, "TN": 34,
        },
        "student": {
            "mssv": "2110483", "name": "Lê Văn Cường",
            "className": "21CK2", "classCode": "ME2026",
        },
        "diffLabel": "Trung bình",
        "examCode": "ME2026-2110483",
        "activeTasks": [],
    },
]


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
# ORM MODEL - LƯU TRỮ LỊCH SỬ ĐỀ THI (generated_questions)
# ===========================================================================
class GeneratedQuestion(Base):
    """Bảng lưu lịch sử các đề thi đã tạo (mỗi hàng = 1 bài đề của 1 SV)."""

    __tablename__ = "generated_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_code = Column(String(32), nullable=False, index=True)
    student_mssv = Column(String(32), nullable=False)
    student_name = Column(String(128), nullable=False)
    exam_data = Column(Text, nullable=False, default="{}")  # JSON string chi tiết D, Lỗ, Trục
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ===========================================================================
# PYDANTIC SCHEMAS (History)
# ===========================================================================
class HistoryItem(BaseModel):
    """Một bài đề trong payload POST /api/history."""

    student_mssv: str
    student_name: str
    exam_data: dict  # chi tiết D, Miền Lỗ, Miền Trục (JSON-serializable)


class HistoryCreateRequest(BaseModel):
    """Payload POST /api/history: lô đề + danh sách bài đề."""

    batch_code: str
    questions: List[HistoryItem]


class HistoryQuestionOut(BaseModel):
    """Một bài đề khi trả về cho frontend (GET /api/history)."""

    student_mssv: str
    student_name: str
    exam_data: dict


class HistoryBatchOut(BaseModel):
    """Một lô đề thi đã tạo (nhóm theo batch_code)."""

    batch_code: str
    created_at: datetime
    count: int
    questions: List[HistoryQuestionOut]


class HistorySaveResponse(BaseModel):
    """Response của POST /api/history: tóm tắt lô đề vừa lưu."""

    batch_code: str
    created_at: Optional[datetime] = None
    count: int


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
# HISTORY ENDPOINTS (LƯU TRỮ LỊCH SỬ ĐỀ THI)
# ===========================================================================
def _save_history(payload: HistoryCreateRequest, db: Session = Depends(get_db)) -> dict:
    """POST /api/history: bulk insert lô đề thi vào bảng generated_questions.

    Nhận payload từ Frontend sau khi tạo đề xong và lưu hàng loạt.
    """
    if not payload.batch_code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="batch_code không được để trống.",
        )
    if not payload.questions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Lô đề không chứa bài thi nào.",
        )

    rows = [
        GeneratedQuestion(
            batch_code=payload.batch_code,
            student_mssv=q.student_mssv,
            student_name=q.student_name,
            exam_data=json.dumps(q.exam_data, ensure_ascii=False),
        )
        for q in payload.questions
    ]

    db.add_all(rows)
    db.commit()

    # Trả về batch vừa lưu (để frontend có thể refresh hoặc hiển thị ngay).
    return {
        "batch_code": payload.batch_code,
        "created_at": rows[0].created_at,
        "count": len(rows),
    }


def _list_history(db: Session = Depends(get_db)) -> List[HistoryBatchOut]:
    """GET /api/history: trả về danh sách lô đề đã tạo (nhóm theo batch_code).

    Sắp xếp lô mới nhất lên đầu. Mỗi lô trả kèm:
    - batch_code, created_at (thời điểm tạo lô đầu tiên)
    - count (số bài thi trong lô)
    - questions (chi tiết từng bài: mssv, tên, exam_data JSON)
    """
    # Lấy tất cả bản ghi, sắp theo thời gian tạo mới nhất.
    rows = (
        db.query(GeneratedQuestion)
        .order_by(GeneratedQuestion.created_at.desc(), GeneratedQuestion.id.desc())
        .all()
    )

    # Nhóm theo batch_code (giữ thứ tự mới nhất).
    batches: dict = {}
    for row in rows:
        if row.batch_code not in batches:
            batches[row.batch_code] = {
                "batch_code": row.batch_code,
                "created_at": row.created_at,
                "questions": [],
            }
        try:
            exam_data = json.loads(row.exam_data) if row.exam_data else {}
        except (json.JSONDecodeError, TypeError):
            exam_data = {}
        batches[row.batch_code]["questions"].append(
            {
                "student_mssv": row.student_mssv,
                "student_name": row.student_name,
                "exam_data": exam_data,
            }
        )

    result = []
    for code, batch in batches.items():
        result.append(
            HistoryBatchOut(
                batch_code=batch["batch_code"],
                created_at=batch["created_at"],
                count=len(batch["questions"]),
                questions=batch["questions"],
            )
        )
    return result


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

# /api/history - MỌI user đã đăng nhập (lecturer & student) đều truy cập được.
#   -> bảo vệ bằng Depends(get_current_user)
app.add_api_route(
    "/api/history",
    _save_history,
    methods=["POST"],
    response_model=HistorySaveResponse,
    dependencies=[Depends(get_current_user)],
    tags=["history"],
    summary="Lưu lô đề thi đã tạo vào cơ sở dữ liệu (bulk insert)",
)
app.add_api_route(
    "/api/history",
    _list_history,
    methods=["GET"],
    response_model=List[HistoryBatchOut],
    dependencies=[Depends(get_current_user)],
    tags=["history"],
    summary="Lấy danh sách lô đề thi đã tạo (nhóm theo batch_code)",
)

