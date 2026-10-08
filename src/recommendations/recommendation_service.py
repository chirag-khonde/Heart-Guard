"""Service layer for HeartGuard AI Recommendations (Phase 13).

Provides secure, user-isolated operations for:
  - Generating and retrieving assessment recommendations
  - Persisting recommendation snapshots into recommendations.db
  - Querying recommendation history with strict ownership checks (IDOR protection)
  - Admin aggregated recommendation statistics
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any, Optional

from config.settings import ASSESSMENTS_DB_PATH, RECOMMENDATIONS_DB_PATH
from src.analytics.history_service import HistoryService
from src.recommendations.recommendation_engine import RecommendationEngine
from src.recommendations.recommendation_models import (
    AssessmentInsights,
    Recommendation,
    init_recommendation_db,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _get_connection(db_path: Optional[Path | str] = None) -> sqlite3.Connection:
    target = Path(db_path) if db_path is not None else RECOMMENDATIONS_DB_PATH
    init_recommendation_db(target)
    conn = sqlite3.connect(str(target), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_recommendation(row: sqlite3.Row) -> Recommendation:
    return Recommendation(
        id=row["id"],
        recommendation_id=row["recommendation_id"],
        assessment_id=row["assessment_id"],
        user_id=row["user_id"],
        category=row["category"],
        title=row["title"],
        description=row["description"],
        priority=row["priority"],
        source=row["source"],
        rule_id=row["rule_id"],
        version=row["version"],
        created_at=row["created_at"],
    )


class RecommendationService:
    """Service layer managing recommendation lifecycle, authorization, and persistence."""

    @staticmethod
    def get_or_create_insights(
        assessment_id: str,
        user_id: int,
        is_staff_override: bool = False,
        user_role: Optional[str] = None,
        assess_db_path: Optional[Path | str] = None,
        assessment_db_path: Optional[Path | str] = None,
        rec_db_path: Optional[Path | str] = None,
        db_path: Optional[Path | str] = None,
    ) -> AssessmentInsights:
        """Fetch or generate AI insights and recommendations for an assessment.

        Enforces ownership: user_id must own the assessment unless is_staff_override is True.

        Args:
            assessment_id: Target assessment ID.
            user_id: Authenticated requesting user ID.
            is_staff_override: Set to True for authorized REVIEWER or ADMIN.
            user_role: Optional role string (e.g. 'reviewer', 'admin').
            assess_db_path: Assessments DB path override for tests.
            assessment_db_path: Assessments DB path alias for tests.
            rec_db_path: Recommendations DB path override for tests.
            db_path: Recommendations DB path alias for tests.

        Returns:
            AssessmentInsights

        Raises:
            ValueError: If assessment not found.
            PermissionError: If user does not own the assessment (IDOR protection).
        """
        effective_assess_db = assess_db_path or assessment_db_path
        effective_rec_db = rec_db_path or db_path
        if user_role and user_role.lower() in ("admin", "reviewer"):
            is_staff_override = True

        assessment = HistoryService.get_assessment_by_id(assessment_id, db_path=effective_assess_db)
        if assessment is None:
            raise ValueError(f"Assessment '{assessment_id}' not found.")

        if not is_staff_override and assessment.user_id != user_id:
            raise PermissionError(
                f"Access denied. User {user_id} does not own assessment '{assessment_id}'."
            )

        # Retrieve prior assessment for trend comparison if available
        user_assessments = HistoryService.get_user_assessments(
            user_id=assessment.user_id, sort_order="desc", limit=10, db_path=effective_assess_db
        )
        previous_assessment = None
        for idx, a in enumerate(user_assessments):
            if a.assessment_id == assessment_id and idx + 1 < len(user_assessments):
                previous_assessment = user_assessments[idx + 1]
                break

        # Generate fresh insights object
        insights = RecommendationEngine.generate_insights(
            assessment=assessment, previous_assessment=previous_assessment
        )

        # Persist generated recommendations if not already in recommendations.db
        RecommendationService._persist_recommendations_if_absent(
            insights.recommendations, rec_db_path=effective_rec_db
        )

        return insights

    @staticmethod
    def _persist_recommendations_if_absent(
        arg1: Any,
        arg2: Any = None,
        rec_db_path: Optional[Path | str] = None,
        db_path: Optional[Path | str] = None,
    ) -> None:
        """Insert recommendations into the database if not already stored."""
        if isinstance(arg1, list):
            recommendations = arg1
            aid = recommendations[0].assessment_id if recommendations else ""
        else:
            aid = str(arg1)
            recommendations = arg2 or []

        target_db = db_path or rec_db_path
        if not recommendations:
            return

        if not aid and recommendations:
            aid = recommendations[0].assessment_id

        with _get_connection(target_db) as conn:
            existing = conn.execute(
                "SELECT 1 FROM recommendations WHERE assessment_id = ? LIMIT 1;", (aid,)
            ).fetchone()
            if existing:
                return

            sql = """
            INSERT OR IGNORE INTO recommendations (
                recommendation_id, assessment_id, user_id, category, title,
                description, priority, source, rule_id, version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            for r in recommendations:
                conn.execute(
                    sql,
                    (
                        r.recommendation_id,
                        r.assessment_id,
                        r.user_id,
                        r.category,
                        r.title,
                        r.description,
                        r.priority,
                        r.source,
                        r.rule_id,
                        r.version,
                        r.created_at,
                    ),
                )
            conn.commit()

    @staticmethod
    def get_user_recommendations(
        user_id: int,
        limit: int = 50,
        rec_db_path: Optional[Path | str] = None,
        db_path: Optional[Path | str] = None,
    ) -> list[Recommendation]:
        """Fetch past recommendations for an authenticated user, newest first."""
        target_db = db_path or rec_db_path
        with _get_connection(target_db) as conn:
            rows = conn.execute(
                """
                SELECT * FROM recommendations
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?;
                """,
                (user_id, limit),
            ).fetchall()
            return [_row_to_recommendation(r) for r in rows]

    @staticmethod
    def get_admin_recommendation_statistics(
        rec_db_path: Optional[Path] = None,
    ) -> dict[str, Any]:
        """Aggregate platform recommendation statistics for administrators."""
        with _get_connection(rec_db_path) as conn:
            total_row = conn.execute("SELECT COUNT(*) as count FROM recommendations;").fetchone()
            total = int(total_row["count"]) if total_row else 0

            cat_rows = conn.execute(
                "SELECT category, COUNT(*) as count FROM recommendations GROUP BY category ORDER BY count DESC;"
            ).fetchall()
            cat_dist = {r["category"]: int(r["count"]) for r in cat_rows}

            prio_rows = conn.execute(
                "SELECT priority, COUNT(*) as count FROM recommendations GROUP BY priority ORDER BY count DESC;"
            ).fetchall()
            prio_dist = {r["priority"]: int(r["count"]) for r in prio_rows}

            return {
                "total_recommendations": total,
                "category_distribution": cat_dist,
                "priority_distribution": prio_dist,
            }
