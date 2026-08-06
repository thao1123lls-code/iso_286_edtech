"""Bộ điều phối quy trình xuất bản (Export Orchestrator) - Business Logic Layer.

Lớp này tổ chức pipeline:
  1. Validate dữ liệu đề thi (tolerance_service.validate_exam_data)
  2. Chọn nghiệp vụ xuất (docx/pdf) và tạo bytes
  3. Trả về (bytes, media_type, filename) cho Presentation Layer

API Layer chỉ việc gọi export_service và bọc kết quả trong StreamingResponse.
"""
from typing import Tuple

from app.core.config import MEDIA_TYPE_DOCX, MEDIA_TYPE_PDF
from app.models.schemas import ExamData
from app.services import docx_service, pdf_service
from app.services.tolerance_service import ToleranceValidationError, validate_exam_data


class ExportService:
    """Facade cho toàn bộ quy trình xuất tài liệu."""

    @staticmethod
    def validate(data: ExamData) -> list:
        """Kiểm tra ràng buộc nghiệp vụ. Raise nếu dữ liệu không hợp lệ."""
        warnings = validate_exam_data(data)
        return warnings

    @staticmethod
    def export_docx(data: ExamData, include_answers: bool = True) -> Tuple[bytes, str, str]:
        """Xuất Word (.docx). Trả về (bytes, media_type, filename).

        include_answers=False -> file chỉ có Header chuẩn + ĐỀ BÀI + YÊU CẦU
        (bỏ phần ĐÁP ÁN & BAREM để dùng làm đề thi thật).
        """
        validate_exam_data(data)  # raise nếu vi phạm ràng buộc nghiệp vụ
        bio = docx_service.build_docx_bytes(data, include_answers=include_answers)
        return bio.getvalue(), MEDIA_TYPE_DOCX, docx_service.filename_docx(data)

    @staticmethod
    def export_pdf(data: ExamData, include_answers: bool = True) -> Tuple[bytes, str, str]:
        """Xuất PDF thực (ReportLab). Trả về (bytes, media_type, filename).

        include_answers=False -> file chỉ có Header chuẩn + ĐỀ BÀI + YÊU CẦU
        (bỏ phần ĐÁP ÁN & BAREM để dùng làm đề thi thật).
        """
        validate_exam_data(data)  # raise nếu vi phạm ràng buộc nghiệp vụ
        bio = pdf_service.build_pdf_bytes(data, include_answers=include_answers)
        return bio.getvalue(), MEDIA_TYPE_PDF, pdf_service.filename_pdf(data)


# Singleton tiện dùng
export_service = ExportService()

__all__ = [
    "ExportService",
    "export_service",
    "ToleranceValidationError",
    "validate_exam_data",
]
