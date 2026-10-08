"""Reports router for HeartGuard API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import io

from typing import Any
from api.deps import CurrentUser, get_current_user
from src.analytics.history_service import HistoryService
from src.reports.report_generator import ReportGenerator

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("", response_model=list[dict[str, Any]])
async def list_reports(current_user: CurrentUser = Depends(get_current_user)):
    assessments = HistoryService.get_user_assessments(
        user_id=current_user.user_id,
        sort_order="desc",
        limit=50,
    )
    items = []
    for a in assessments:
        items.append({
            "id": a.assessment_id,
            "assessment_id": a.assessment_id,
            "title": f"Cardiovascular Risk Report — {a.risk_category.title()}",
            "created_at": a.created_at,
            "risk_score": a.overall_risk,
            "risk_category": a.risk_category,
            "filename": f"HeartGuard-Report-{a.assessment_id}.pdf",
        })
    return items


def _stream_pdf(assessment_id: str, user_id: int):
    try:
        pdf_bytes = ReportGenerator.generate_assessment_report(
            assessment_id=assessment_id,
            user_id=user_id,
        )
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="HeartGuard-Report-{assessment_id}.pdf"'
            },
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{assessment_id}/generate")
@router.post("/generate/{assessment_id}")
async def generate_report(
    assessment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    return _stream_pdf(assessment_id, current_user.user_id)


@router.get("/{assessment_id}/download")
@router.get("/download/{assessment_id}")
async def download_report(
    assessment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    return _stream_pdf(assessment_id, current_user.user_id)
