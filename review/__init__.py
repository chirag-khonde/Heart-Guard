"""HeartGuard Professional Review package (Phase 11).

Public API:
    from src.review import ProfessionalReview, ReviewService, REVIEW_STATUSES
"""

from src.review.models import ProfessionalReview, init_review_db
from src.review.review_constants import (
    PROFESSIONAL_NOTES_MAX_LENGTH,
    REVIEW_STATUSES,
    REVIEW_STATUS_LABELS,
    STATUS_CLOSED,
    STATUS_FOLLOW_UP_RECOMMENDED,
    STATUS_IN_REVIEW,
    STATUS_PENDING,
    STATUS_REVIEWED,
    URGENCY_LABELS,
)
from src.review.review_service import ReviewService

__all__ = [
    # Domain model
    "ProfessionalReview",
    "init_review_db",
    # Service
    "ReviewService",
    # Constants
    "REVIEW_STATUSES",
    "REVIEW_STATUS_LABELS",
    "URGENCY_LABELS",
    "PROFESSIONAL_NOTES_MAX_LENGTH",
    "STATUS_PENDING",
    "STATUS_IN_REVIEW",
    "STATUS_REVIEWED",
    "STATUS_FOLLOW_UP_RECOMMENDED",
    "STATUS_CLOSED",
]
