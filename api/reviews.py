"""Review router for HeartGuard API."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.deps import CurrentUser, get_current_user, require_role
from src.review.review_service import ReviewService

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


class ReviewCreateRequest(BaseModel):
    assessment_id: str


class ReviewUpdateRequest(BaseModel):
    review_status: Optional[str] = None
    professional_notes: Optional[str] = None
    follow_up_required: Optional[bool] = None
    urgency_flag: Optional[bool] = None


class ReviewResponse(BaseModel):
    id: int | None
    review_id: str
    assessment_id: str
    reviewer_id: int
    created_at: str
    updated_at: str
    review_status: str
    professional_notes: str
    follow_up_required: bool
    urgency_flag: bool


class ReviewStatsResponse(BaseModel):
    pending: int
    in_review: int
    accepted: int
    modified: int
    rejected: int
    reviewed: int
    follow_up_recommended: int
    urgency_count: int
    total_assigned: int
    unassigned_pending: int


def _review_to_response(review) -> ReviewResponse:
    return ReviewResponse(
        id=review.id,
        review_id=review.review_id,
        assessment_id=review.assessment_id,
        reviewer_id=review.reviewer_id,
        created_at=review.created_at,
        updated_at=review.updated_at,
        review_status=review.review_status,
        professional_notes=review.professional_notes,
        follow_up_required=review.follow_up_required,
        urgency_flag=review.urgency_flag,
    )


@router.get("/queue", response_model=list[dict[str, Any]])
async def get_review_queue(
    current_user: CurrentUser = Depends(require_role("REVIEWER", "ADMIN")),
):
    items = ReviewService.get_all_assessments_with_review_status()
    return items


@router.get("/pending", response_model=list[dict[str, Any]])
async def get_pending_reviews(
    current_user: CurrentUser = Depends(require_role("REVIEWER", "ADMIN")),
):
    assessments = ReviewService.get_pending_assessments()
    return [a.to_dict() for a in assessments]


@router.post("/{assessment_id}", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    assessment_id: str,
    current_user: CurrentUser = Depends(require_role("REVIEWER", "ADMIN")),
):
    try:
        review = ReviewService.create_review(
            reviewer_id=current_user.user_id,
            assessment_id=assessment_id,
        )
        return _review_to_response(review)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    body: ReviewUpdateRequest,
    current_user: CurrentUser = Depends(require_role("REVIEWER", "ADMIN")),
):
    try:
        review = ReviewService.update_review(
            review_id=review_id,
            reviewer_id=current_user.user_id,
            review_status=body.review_status,
            professional_notes=body.professional_notes,
            follow_up_required=body.follow_up_required,
            urgency_flag=body.urgency_flag,
        )
        return _review_to_response(review)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    current_user: CurrentUser = Depends(require_role("REVIEWER", "ADMIN")),
):
    stats = ReviewService.get_review_statistics()
    return ReviewStatsResponse(**stats)
