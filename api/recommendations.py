"""Recommendations router for HeartGuard API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.deps import CurrentUser, get_current_user
from src.recommendations.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class RecommendationResponse(BaseModel):
    recommendation_id: str
    assessment_id: str
    user_id: int
    category: str
    title: str
    description: str
    priority: str
    source: str
    rule_id: str | None
    version: str
    created_at: str


def _rec_to_response(rec) -> RecommendationResponse:
    return RecommendationResponse(
        recommendation_id=rec.recommendation_id,
        assessment_id=rec.assessment_id,
        user_id=rec.user_id,
        category=rec.category,
        title=rec.title,
        description=rec.description,
        priority=rec.priority,
        source=rec.source,
        rule_id=rec.rule_id,
        version=rec.version,
        created_at=rec.created_at,
    )


class InsightResponse(BaseModel):
    summary_text: str
    top_factors: list[dict]
    recommendations: list[RecommendationResponse]


@router.get("/{assessment_id}", response_model=InsightResponse)
async def get_recommendations(
    assessment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        insights = RecommendationService.get_or_create_insights(
            assessment_id=assessment_id,
            user_id=current_user.user_id,
            user_role=current_user.role,
        )
        recs = [_rec_to_response(r) for r in insights.recommendations]
        return InsightResponse(
            summary_text=insights.summary_text,
            top_factors=insights.top_factors,
            recommendations=recs,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("", response_model=list[RecommendationResponse])
async def get_all_recommendations(
    current_user: CurrentUser = Depends(get_current_user),
):
    recs = RecommendationService.get_user_recommendations(user_id=current_user.user_id)
    return [_rec_to_response(r) for r in recs]
