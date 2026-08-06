"""API Endpoints xuất tài liệu (Presentation Layer).

Các route này CHỈ làm nhiệm vụ nhận request/trả response.
Toàn bộ quy tắc nghiệp vụ được uỷ quyền cho Business Logic Layer (app.services).
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import ExamData
from app.services.export_service import export_service
from app.services.tolerance_service import ToleranceValidationError

router = APIRouter(prefix="/export", tags=["export"])


def _stream(content: bytes, media_type: str, filename: str) -> StreamingResponse:
    """Bọc bytes thành StreamingResponse (bytes cần được iterate theo chunk)."""
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/docx")
async def export_docx(data: ExamData, include_answers: bool = True):
    """Xuất bộ đề thi ra file Word (.docx).

    include_answers=True  (default): render đầy đủ câu hỏi + ĐÁP ÁN + BAREM.
    include_answers=False         : chỉ Header chuẩn + ĐỀ BÀI + YÊU CẦU
                                    (dùng làm đề thi thật, không lộ đáp án).
    """
    try:
        content, media_type, filename = export_service.export_docx(
            data, include_answers=include_answers
        )
    except ToleranceValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return _stream(content, media_type, filename)


@router.post("/pdf")
async def export_pdf(data: ExamData, include_answers: bool = True):
    """Xuất bộ đề thi ra file PDF thực (ReportLab).

    include_answers=True  (default): render đầy đủ câu hỏi + ĐÁP ÁN + BAREM.
    include_answers=False         : chỉ Header chuẩn + ĐỀ BÀI + YÊU CẦU
                                    (dùng làm đề thi thật, không lộ đáp án).
    """
    try:
        content, media_type, filename = export_service.export_pdf(
            data, include_answers=include_answers
        )
    except ToleranceValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return _stream(content, media_type, filename)

