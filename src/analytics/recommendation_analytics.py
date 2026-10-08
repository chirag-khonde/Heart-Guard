"""Recommendation Analytics Service (Phase 17).

Analyzes recommendation records: counts, categories, frequency,
and effectiveness metrics (where outcome data is available).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config.settings import RECOMMENDATIONS_DB_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _get_recommendation_connection(db_path: Path | None = None) -> sqlite3.Connection:
    target = db_path or RECOMMENDATIONS_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class RecommendationAnalytics:
    """Aggregate recommendation analytics."""

    @staticmethod
    def get_recommendation_summary(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get aggregate recommendation statistics."""
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_recommendation_connection(db_path) as conn:
            total_row = conn.execute(
                f"SELECT COUNT(*) as total FROM recommendations {where_clause}", tuple(params)
            ).fetchone()

            category_rows = conn.execute(
                f"SELECT category, COUNT(*) as count FROM recommendations {where_clause} GROUP BY category ORDER BY count DESC",
                tuple(params),
            ).fetchall()

            priority_rows = conn.execute(
                f"SELECT priority, COUNT(*) as count FROM recommendations {where_clause} GROUP BY priority ORDER BY count DESC",
                tuple(params),
            ).fetchall()

            source_rows = conn.execute(
                f"SELECT source, COUNT(*) as count FROM recommendations {where_clause} GROUP BY source ORDER BY count DESC",
                tuple(params),
            ).fetchall()

            unique_users_row = conn.execute(
                f"SELECT COUNT(DISTINCT user_id) as count FROM recommendations {where_clause}", tuple(params)
            ).fetchone()

            unique_assessments_row = conn.execute(
                f"SELECT COUNT(DISTINCT assessment_id) as count FROM recommendations {where_clause}", tuple(params)
            ).fetchone()

        return {
            "total_recommendations": int(total_row["total"]) if total_row else 0,
            "unique_users": int(unique_users_row["count"]) if unique_users_row else 0,
            "unique_assessments": int(unique_assessments_row["count"]) if unique_assessments_row else 0,
            "by_category": {r["category"]: int(r["count"]) for r in category_rows},
            "by_priority": {r["priority"]: int(r["count"]) for r in priority_rows},
            "by_source": {r["source"]: int(r["count"]) for r in source_rows},
        }

    @staticmethod
    def get_recommendation_trend(
        interval: str = "daily",
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Get recommendation counts over time."""
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff)

        if interval == "daily":
            date_expr = "strftime('%Y-%m-%d', created_at)"
        elif interval == "weekly":
            date_expr = "strftime('%Y-W%W', created_at)"
        else:
            date_expr = "strftime('%Y-%m', created_at)"

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_recommendation_connection(db_path) as conn:
            rows = conn.execute(
                f"""SELECT {date_expr} as period, COUNT(*) as rec_count,
                    COUNT(DISTINCT user_id) as user_count
                    FROM recommendations {where_clause}
                    GROUP BY period ORDER BY period""",
                tuple(params),
            ).fetchall()

        return [
            {
                "period": r["period"],
                "recommendation_count": int(r["rec_count"]),
                "user_count": int(r["user_count"]),
            }
            for r in rows
        ]

    @staticmethod
    def get_average_recommendations_per_assessment(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Calculate average recommendations per assessment."""
        summary = RecommendationAnalytics.get_recommendation_summary(date_range, db_path)
        total_recs = summary["total_recommendations"]
        total_assessments = summary["unique_assessments"]

        avg = total_recs / total_assessments if total_assessments > 0 else 0.0

        return {
            "total_recommendations": total_recs,
            "total_assessments": total_assessments,
            "avg_per_assessment": round(avg, 2),
            "effectiveness_note": (
                "Outcome effectiveness cannot currently be determined. "
                "This metric describes recommendation volume, not health outcomes."
            ),
        }
