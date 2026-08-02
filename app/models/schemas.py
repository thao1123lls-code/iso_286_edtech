"""Lớp Mô hình dữ liệu (Data Model Layer) - Pydantic Schemas.

Các schema này khớp 1-1 với JSON gửi từ index.html.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Student(BaseModel):
    mssv: str
    name: str
    className: str
    classCode: str


class ToleranceParams(BaseModel):
    sym: str
    it: int
    ES: Optional[float] = None
    EI: Optional[float] = None
    es: Optional[float] = None
    ei: Optional[float] = None
    Dmax: Optional[float] = None
    Dmin: Optional[float] = None
    dmax: Optional[float] = None
    dmin: Optional[float] = None
    T: float


class FitParams(BaseModel):
    type: str
    Smax: Optional[float] = None
    Smin: Optional[float] = None
    Nmax: Optional[float] = None
    Nmin: Optional[float] = None
    TN: float


class Question(BaseModel):
    student: Student
    diffLabel: str
    examCode: str
    D: float
    hole: ToleranceParams
    shaft: ToleranceParams
    fit: FitParams


class Task(BaseModel):
    id: str
    name: str
    points: float


class ExamData(BaseModel):
    stats: Dict[str, Any]
    questions: List[Question]
    activeTasks: List[Task]

