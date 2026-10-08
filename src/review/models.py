"""ProfessionalReview data model and SQLite schema for HeartGuard Phase 11.

Defines the ProfessionalReview domain entity and database initialisation.

IMPORTANT CONSTRAINTS:
  - This table stores REVIEW NOTES ONLY.
  - It does NOT modify the original assessment record in any way.
  - It is NOT a diagnostic, prescription, or treatment system.
  - Only REVIEWER-role users may create / update review records.
  - Only the review's own reviewer_id may update it (ownership enforced
    in the service layer, not here).

Database: data/assessments/reviews.db  (separate from assessments.db)
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config.settings import REVIEWS_DB_PATH
from src.review.review_constants import (
    PROFESSIONAL_NOTES_MAX_LENGTH,
    REVIEW_STATUSES,
    STATUS_PENDING,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# SQL schema
# ---------------------------------------------------------------------------

_CREATE_REVIEWS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS professional_reviews (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           TEXT    NOT NULL UNIQUE,
    assessment_id       TEXT    NOT NULL,
    reviewer_id         INTEGER NOT NULL,
    created_at          TEXT    NOT NULL,
    updated_at          TEXT    NOT NULL,
    review_status       TEXT    NOT NULL DEFAULT 'PENDING',
    professional_notes  TEXT    NOT NULL DEFAULT '',
    follow_up_required  INTEGER NOT NULL DEFAULT 0,
    urgency_flag        INTEGER NOT NULL DEFAULT 0
);
"""

_CREATE_REVIEW_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_reviews_assessment ON professional_reviews (assessment_id);",
    "CREATE INDEX IF NOT EXISTS idx_reviews_reviewer   ON professional_reviews (reviewer_id, updated_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_reviews_status     ON professional_reviews (review_status);",
]


# ---------------------------------------------------------------------------
# Domain dataclass
# ---------------------------------------------------------------------------


@dataclass
class ProfessionalReview:
    """Represents a single professional review record for a HeartGuard assessment.

    A review record stores the REVIEWER's observations and status decision
    about an AI-generated assessment.  It does NOT store, duplicate, or
    modify any AI-generated risk scores, SHAP values, or recommendations.

    Attributes:
        id:                  Auto-incremented database primary key (None before save).
        review_id:           Unique string identifier for this review.
        assessment_id:       Foreign key matching assessments.assessment_id.
        reviewer_id:         User ID of the REVIEWER who created this record.
        created_at:          UTC ISO-8601 creation timestamp (immutable after creation).
        updated_at:          UTC ISO-8601 last-update timestamp.
        review_status:       One of REVIEW_STATUSES controlled vocabulary.
        professional_notes:  Free-text observations from the reviewer (NOT a diagnosis).
        follow_up_required:  Whether the reviewer recommends scheduling follow-up.
        urgency_flag:        Whether the reviewer flags this case for urgent attention.
    """

    id: Optional[int]
    review_id: str
    assessment_id: str
    reviewer_id: int
    created_at: str
    updated_at: str
    review_status: str = STATUS_PENDING
    professional_notes: str = ""
    follow_up_required: bool = False
    urgency_flag: bool = False

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        if self.review_status not in REVIEW_STATUSES:
            raise ValueError(
                f"Invalid review_status '{self.review_status}'. "
                f"Must be one of: {REVIEW_STATUSES}"
            )
        if len(self.professional_notes) > PROFESSIONAL_NOTES_MAX_LENGTH:
            raise ValueError(
                f"professional_notes exceeds maximum length of {PROFESSIONAL_NOTES_MAX_LENGTH}."
            )

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a safe dictionary representation of this review."""
        return {
            "id": self.id,
            "review_id": self.review_id,
            "assessment_id": self.assessment_id,
            "reviewer_id": self.reviewer_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "review_status": self.review_status,
            "professional_notes": self.professional_notes,
            "follow_up_required": self.follow_up_required,
            "urgency_flag": self.urgency_flag,
        }


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------


def init_review_db(db_path: Optional[Path] = None) -> None:
    """Initialise the professional_reviews table and indexes if not present.

    Args:
        db_path: Optional path override for test isolation.
                 Defaults to REVIEWS_DB_PATH from config.
    """
    target = db_path if db_path is not None else REVIEWS_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(target), timeout=10.0) as conn:
        conn.execute(_CREATE_REVIEWS_TABLE_SQL)
        for idx_sql in _CREATE_REVIEW_INDEXES_SQL:
            conn.execute(idx_sql)
        conn.commit()
    logger.debug("Review database initialized at %s", target)
