"""ReviewService for HeartGuard Professional Review module (Phase 11).

Provides secure, audited create/read/update operations on professional_reviews.

OWNERSHIP RULES:
  - A reviewer may only UPDATE their own review records (reviewer_id match enforced).
  - Any authenticated REVIEWER may READ all pending assessments (reviewer assignment
    is first-come-first-served: the first reviewer to open an assessment claims it).
  - ADMINs may read all reviews for audit purposes via get_all_reviews().

SAFETY INVARIANT:
  - No method in this service mutates the `assessments` table.
  - No medical diagnosis, prescription, or clinical decision logic is implemented.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config.settings import ASSESSMENTS_DB_PATH, REVIEWS_DB_PATH
from src.analytics.history_service import _get_connection as _get_assessment_conn
from src.analytics.models import Assessment, init_assessment_db
from src.review.models import ProfessionalReview, init_review_db
from src.review.review_constants import (
    PROFESSIONAL_NOTES_MAX_LENGTH,
    REVIEW_STATUSES,
    STATUS_IN_REVIEW,
    STATUS_PENDING,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_review_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open a connection to the reviews database, initializing schema if needed."""
    target = db_path if db_path is not None else REVIEWS_DB_PATH
    init_review_db(target)
    conn = sqlite3.connect(str(target), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_review(row: sqlite3.Row) -> ProfessionalReview:
    """Map a database row to a ProfessionalReview domain object."""
    return ProfessionalReview(
        id=row["id"],
        review_id=row["review_id"],
        assessment_id=row["assessment_id"],
        reviewer_id=row["reviewer_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        review_status=row["review_status"],
        professional_notes=row["professional_notes"] or "",
        follow_up_required=bool(row["follow_up_required"]),
        urgency_flag=bool(row["urgency_flag"]),
    )


def _assessment_row_to_obj(row: sqlite3.Row) -> Assessment:
    """Map a raw assessment row to an Assessment domain object."""
    from src.analytics.history_service import _row_to_assessment
    return _row_to_assessment(row)


# ---------------------------------------------------------------------------
# ReviewService
# ---------------------------------------------------------------------------


class ReviewService:
    """Service layer for the professional review workflow.

    All public methods accept an optional ``review_db_path`` and
    ``assessment_db_path`` for test isolation without touching production DBs.
    """

    # -----------------------------------------------------------------------
    # Create
    # -----------------------------------------------------------------------

    @staticmethod
    def create_review(
        reviewer_id: int,
        assessment_id: str,
        review_db_path: Optional[Path] = None,
        assessment_db_path: Optional[Path] = None,
    ) -> ProfessionalReview:
        """Create a new PENDING professional review for an assessment.

        If a review already exists for this assessment, returns the existing
        review instead of creating a duplicate (idempotent).

        Args:
            reviewer_id:        ID of the REVIEWER creating the review.
            assessment_id:      Assessment to be reviewed.
            review_db_path:     DB path override for tests.
            assessment_db_path: Assessment DB path override for tests.

        Returns:
            ProfessionalReview: Newly created (or existing) review record.

        Raises:
            ValueError: If assessment_id does not exist in the assessments table.
        """
        # Verify the assessment exists before creating a review
        if not ReviewService._assessment_exists(assessment_id, assessment_db_path):
            raise ValueError(
                f"Assessment '{assessment_id}' not found. Cannot create review."
            )

        # Idempotency: return existing review if one already exists
        existing = ReviewService.get_review_for_assessment(
            assessment_id, review_db_path
        )
        if existing is not None:
            logger.info(
                "Review already exists for assessment %s — returning existing review_id=%s",
                assessment_id,
                existing.review_id,
            )
            return existing

        now_iso = datetime.now(timezone.utc).isoformat()
        review_id = uuid.uuid4().hex[:12]

        review = ProfessionalReview(
            id=None,
            review_id=review_id,
            assessment_id=assessment_id,
            reviewer_id=reviewer_id,
            created_at=now_iso,
            updated_at=now_iso,
            review_status=STATUS_PENDING,
            professional_notes="",
            follow_up_required=False,
            urgency_flag=False,
        )

        sql = """
        INSERT INTO professional_reviews (
            review_id, assessment_id, reviewer_id, created_at, updated_at,
            review_status, professional_notes, follow_up_required, urgency_flag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        with _get_review_connection(review_db_path) as conn:
            cursor = conn.execute(
                sql,
                (
                    review.review_id,
                    review.assessment_id,
                    review.reviewer_id,
                    review.created_at,
                    review.updated_at,
                    review.review_status,
                    review.professional_notes,
                    int(review.follow_up_required),
                    int(review.urgency_flag),
                ),
            )
            review.id = cursor.lastrowid
            conn.commit()

        logger.info(
            "Review created: review_id=%s assessment_id=%s reviewer_id=%s",
            review_id,
            assessment_id,
            reviewer_id,
        )
        return review

    # -----------------------------------------------------------------------
    # Update
    # -----------------------------------------------------------------------

    @staticmethod
    def update_review(
        review_id: str,
        reviewer_id: int,
        review_status: Optional[str] = None,
        professional_notes: Optional[str] = None,
        follow_up_required: Optional[bool] = None,
        urgency_flag: Optional[bool] = None,
        review_db_path: Optional[Path] = None,
    ) -> ProfessionalReview:
        """Update an existing review.  The reviewer_id must match the record owner.

        Args:
            review_id:          Review to update.
            reviewer_id:        Must match review.reviewer_id (ownership check).
            review_status:      Optional new status (must be in REVIEW_STATUSES).
            professional_notes: Optional updated notes (NOT a diagnosis).
            follow_up_required: Optional follow-up flag.
            urgency_flag:       Optional urgency flag.
            review_db_path:     DB path override for tests.

        Returns:
            ProfessionalReview: Updated review record.

        Raises:
            ValueError: If review not found, ownership mismatch, or invalid status.
        """
        existing = ReviewService.get_review_by_id(review_id, review_db_path)
        if existing is None:
            raise ValueError(f"Review '{review_id}' not found.")
        if existing.reviewer_id != reviewer_id:
            raise PermissionError(
                f"Reviewer {reviewer_id} does not own review '{review_id}'. "
                "Access denied."
            )

        # Apply field updates, keeping existing values where not specified
        new_status = existing.review_status
        if review_status is not None:
            if review_status not in REVIEW_STATUSES:
                raise ValueError(
                    f"Invalid review_status '{review_status}'. "
                    f"Must be one of: {REVIEW_STATUSES}"
                )
            new_status = review_status

        new_notes = existing.professional_notes
        if professional_notes is not None:
            if len(professional_notes) > PROFESSIONAL_NOTES_MAX_LENGTH:
                raise ValueError(
                    f"professional_notes exceeds maximum length of {PROFESSIONAL_NOTES_MAX_LENGTH}."
                )
            new_notes = professional_notes

        new_follow_up = existing.follow_up_required
        if follow_up_required is not None:
            new_follow_up = follow_up_required

        new_urgency = existing.urgency_flag
        if urgency_flag is not None:
            new_urgency = urgency_flag

        now_iso = datetime.now(timezone.utc).isoformat()

        sql = """
        UPDATE professional_reviews
        SET review_status = ?, professional_notes = ?, follow_up_required = ?,
            urgency_flag = ?, updated_at = ?
        WHERE review_id = ? AND reviewer_id = ?;
        """
        with _get_review_connection(review_db_path) as conn:
            conn.execute(
                sql,
                (
                    new_status,
                    new_notes,
                    int(new_follow_up),
                    int(new_urgency),
                    now_iso,
                    review_id,
                    reviewer_id,
                ),
            )
            conn.commit()

        logger.info(
            "Review updated: review_id=%s status=%s urgency=%s follow_up=%s",
            review_id,
            new_status,
            new_urgency,
            new_follow_up,
        )

        return ProfessionalReview(
            id=existing.id,
            review_id=review_id,
            assessment_id=existing.assessment_id,
            reviewer_id=reviewer_id,
            created_at=existing.created_at,
            updated_at=now_iso,
            review_status=new_status,
            professional_notes=new_notes,
            follow_up_required=new_follow_up,
            urgency_flag=new_urgency,
        )

    # -----------------------------------------------------------------------
    # Read — reviews
    # -----------------------------------------------------------------------

    @staticmethod
    def get_review_by_id(
        review_id: str,
        review_db_path: Optional[Path] = None,
    ) -> Optional[ProfessionalReview]:
        """Fetch a review by its unique review_id."""
        with _get_review_connection(review_db_path) as conn:
            row = conn.execute(
                "SELECT * FROM professional_reviews WHERE review_id = ?",
                (review_id,),
            ).fetchone()
        return _row_to_review(row) if row else None

    @staticmethod
    def get_review_for_assessment(
        assessment_id: str,
        review_db_path: Optional[Path] = None,
    ) -> Optional[ProfessionalReview]:
        """Fetch the review for a given assessment_id (at most one review per assessment)."""
        with _get_review_connection(review_db_path) as conn:
            row = conn.execute(
                "SELECT * FROM professional_reviews WHERE assessment_id = ?",
                (assessment_id,),
            ).fetchone()
        return _row_to_review(row) if row else None

    @staticmethod
    def get_reviews_by_reviewer(
        reviewer_id: int,
        review_db_path: Optional[Path] = None,
    ) -> list[ProfessionalReview]:
        """Return all review records created by a specific reviewer, newest first."""
        with _get_review_connection(review_db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM professional_reviews WHERE reviewer_id = ? ORDER BY updated_at DESC",
                (reviewer_id,),
            ).fetchall()
        return [_row_to_review(r) for r in rows]

    @staticmethod
    def get_all_reviews(
        review_db_path: Optional[Path] = None,
    ) -> list[ProfessionalReview]:
        """Return all review records (ADMIN audit use only), newest first."""
        with _get_review_connection(review_db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM professional_reviews ORDER BY updated_at DESC"
            ).fetchall()
        return [_row_to_review(r) for r in rows]

    # -----------------------------------------------------------------------
    # Read — assessments (reviewer-oriented queries)
    # -----------------------------------------------------------------------

    @staticmethod
    def get_pending_assessments(
        assessment_db_path: Optional[Path] = None,
        review_db_path: Optional[Path] = None,
        limit: int = 100,
    ) -> list[Assessment]:
        """Return assessments that have NOT yet been assigned a review record.

        These are assessments in the `assessments` table for which no row
        exists in `professional_reviews`.

        Args:
            assessment_db_path: Assessment DB path override for tests.
            review_db_path:     Review DB path override for tests.
            limit:              Maximum records to return.

        Returns:
            list[Assessment]: Assessments awaiting professional review, newest first.
        """
        assess_target = assessment_db_path or ASSESSMENTS_DB_PATH
        review_target = review_db_path or REVIEWS_DB_PATH

        # Ensure both DBs are initialised
        init_assessment_db(assess_target)
        init_review_db(review_target)

        # Attach reviews.db to the assessments connection for a cross-DB query
        with sqlite3.connect(str(assess_target), timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute(f"ATTACH DATABASE '{str(review_target)}' AS rdb;")
            sql = """
            SELECT a.*
            FROM assessments a
            LEFT JOIN rdb.professional_reviews r ON a.assessment_id = r.assessment_id
            WHERE r.review_id IS NULL
            ORDER BY a.created_at DESC
            LIMIT ?;
            """
            rows = conn.execute(sql, (limit,)).fetchall()

        return [_assessment_row_to_obj(r) for r in rows]

    @staticmethod
    def get_all_assessments_with_review_status(
        assessment_db_path: Optional[Path] = None,
        review_db_path: Optional[Path] = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Return all assessments with their associated review status (or PENDING if none).

        Used by the reviewer dashboard to display a unified list with review
        status without duplicating assessment data.

        Returns:
            list[dict]: Each dict contains assessment fields plus 'review_status',
                        'review_id', 'urgency_flag', 'follow_up_required'.
        """
        assess_target = assessment_db_path or ASSESSMENTS_DB_PATH
        review_target = review_db_path or REVIEWS_DB_PATH

        init_assessment_db(assess_target)
        init_review_db(review_target)

        with sqlite3.connect(str(assess_target), timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute(f"ATTACH DATABASE '{str(review_target)}' AS rdb;")
            sql = """
            SELECT
                a.assessment_id,
                a.user_id,
                a.created_at,
                a.overall_risk,
                a.risk_category,
                a.model_version,
                COALESCE(r.review_status, 'PENDING') AS review_status,
                r.review_id,
                r.urgency_flag,
                r.follow_up_required,
                r.updated_at AS review_updated_at
            FROM assessments a
            LEFT JOIN rdb.professional_reviews r ON a.assessment_id = r.assessment_id
            ORDER BY
                CASE WHEN r.urgency_flag = 1 THEN 0 ELSE 1 END,
                a.created_at DESC
            LIMIT ?;
            """
            rows = conn.execute(sql, (limit,)).fetchall()

        return [dict(r) for r in rows]

    @staticmethod
    def get_assessment_with_review(
        assessment_id: str,
        assessment_db_path: Optional[Path] = None,
        review_db_path: Optional[Path] = None,
    ) -> dict[str, Any]:
        """Return a combined dict with assessment data and its review (if any).

        This is the primary data accessor for the reviewer detail panel.
        The assessment fields are READ-ONLY — this method never mutates them.

        Returns:
            dict with keys 'assessment' (Assessment | None) and
                           'review' (ProfessionalReview | None).
        """
        assess_conn = _get_assessment_conn(assessment_db_path)
        row = assess_conn.execute(
            "SELECT * FROM assessments WHERE assessment_id = ?",
            (assessment_id,),
        ).fetchone()
        assess_conn.close()

        assessment = _assessment_row_to_obj(row) if row else None
        review = ReviewService.get_review_for_assessment(assessment_id, review_db_path)

        return {"assessment": assessment, "review": review}

    @staticmethod
    def get_review_statistics(
        reviewer_id: Optional[int] = None,
        review_db_path: Optional[Path] = None,
        assessment_db_path: Optional[Path] = None,
    ) -> dict[str, int]:
        """Aggregate review statistics for reviewer and admin dashboards.

        Args:
            reviewer_id: Optional reviewer ID filter. If None, aggregates system-wide.
            review_db_path: Review DB path override for tests.
            assessment_db_path: Assessment DB path override for tests.

        Returns:
            dict containing pending, in_review, accepted, modified, rejected,
            reviewed, follow_up_recommended, urgency_count, total_assigned,
            and unassigned_pending counts.
        """
        review_target = review_db_path or REVIEWS_DB_PATH
        init_review_db(review_target)

        where_clause = "WHERE reviewer_id = ?" if reviewer_id is not None else ""
        params = (reviewer_id,) if reviewer_id is not None else ()

        with _get_review_connection(review_db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT
                    review_status,
                    COUNT(*) as count,
                    SUM(follow_up_required) as follow_up_count,
                    SUM(urgency_flag) as urgency_count
                FROM professional_reviews
                {where_clause}
                GROUP BY review_status;
                """,
                params,
            ).fetchall()

            status_counts = {r["review_status"]: int(r["count"]) for r in rows}
            follow_up_total = sum(int(r["follow_up_count"] or 0) for r in rows)
            urgency_total = sum(int(r["urgency_count"] or 0) for r in rows)
            total_assigned = sum(status_counts.values())

            pending_count = status_counts.get("PENDING", 0)
            in_review_count = status_counts.get("IN_REVIEW", 0)
            reviewed_standard = status_counts.get("REVIEWED", 0)
            accepted_count = status_counts.get("ACCEPTED", 0)
            modified_count = status_counts.get("MODIFIED", 0)
            rejected_count = status_counts.get("REJECTED", 0)
            reviewed_count = reviewed_standard + accepted_count + modified_count + rejected_count

        unassigned_pending = 0
        try:
            unassigned_pending = len(
                ReviewService.get_pending_assessments(
                    assessment_db_path=assessment_db_path,
                    review_db_path=review_db_path,
                )
            )
        except Exception as exc:
            logger.debug("Could not compute unassigned pending count: %s", exc)

        return {
            "pending": pending_count,
            "in_review": in_review_count,
            "accepted": accepted_count,
            "modified": modified_count,
            "rejected": rejected_count,
            "reviewed": reviewed_count,
            "follow_up_recommended": follow_up_total,
            "urgency_count": urgency_total,
            "total_assigned": total_assigned,
            "unassigned_pending": unassigned_pending,
            "total_reviews": total_assigned,
            "status_distribution": status_counts,
        }

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _assessment_exists(
        assessment_id: str,
        assessment_db_path: Optional[Path] = None,
    ) -> bool:
        """Verify that an assessment_id exists in the assessments table."""
        target = assessment_db_path or ASSESSMENTS_DB_PATH
        init_assessment_db(target)
        with sqlite3.connect(str(target), timeout=10.0) as conn:
            row = conn.execute(
                "SELECT 1 FROM assessments WHERE assessment_id = ?",
                (assessment_id,),
            ).fetchone()
        return row is not None

