"""Risk Distribution Analytics (Phase 17).

Provides aggregate risk distribution analysis across the platform,
including time-based trends, category transitions, and risk statistics.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config.settings import ASSESSMENTS_DB_PATH
from src.analytics.history_service import _get_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RiskAnalytics:
    """Aggregate risk distribution analytics."""

    @staticmethod
    def get_risk_distribution(
        date_range: str | None = None,
        user_id: int | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get risk category distribution counts."""
        conditions = []
        params: list[Any] = []

        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_connection(db_path) as conn:
            rows = conn.execute(
                f"""SELECT risk_category, COUNT(*) as count,
                    AVG(overall_risk) as avg_risk,
                    MIN(overall_risk) as min_risk,
                    MAX(overall_risk) as max_risk
                    FROM assessments {where_clause}
                    GROUP BY risk_category ORDER BY count DESC""",
                tuple(params),
            ).fetchall()

            total_row = conn.execute(
                f"SELECT COUNT(*) as total FROM assessments {where_clause}", tuple(params)
            ).fetchone()

        total = int(total_row["total"]) if total_row else 0
        categories = {}
        for r in rows:
            cat = r["risk_category"]
            count = int(r["count"])
            categories[cat] = {
                "count": count,
                "percentage": round(count / total * 100, 1) if total > 0 else 0.0,
                "avg_risk": round(float(r["avg_risk"]), 2) if r["avg_risk"] else 0.0,
                "min_risk": round(float(r["min_risk"]), 2) if r["min_risk"] else 0.0,
                "max_risk": round(float(r["max_risk"]), 2) if r["max_risk"] else 0.0,
            }

        return {
            "total": total,
            "categories": categories,
        }

    @staticmethod
    def get_risk_trend_over_time(
        interval: str = "daily",
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Get risk distribution trend over time."""
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

        with _get_connection(db_path) as conn:
            rows = conn.execute(
                f"""SELECT {date_expr} as period,
                    risk_category, COUNT(*) as count
                    FROM assessments {where_clause}
                    GROUP BY period, risk_category ORDER BY period""",
                tuple(params),
            ).fetchall()

        period_data: dict[str, dict[str, int]] = {}
        for r in rows:
            period = r["period"]
            if period not in period_data:
                period_data[period] = {}
            period_data[period][r["risk_category"]] = int(r["count"])

        result = []
        for period, cats in sorted(period_data.items()):
            entry = {"period": period}
            entry.update(cats)
            entry["total"] = sum(cats.values())
            result.append(entry)

        return result

    @staticmethod
    def get_risk_statistics(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get aggregate risk score statistics."""
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_connection(db_path) as conn:
            row = conn.execute(
                f"""SELECT
                    COUNT(*) as total,
                    AVG(overall_risk) as mean_risk,
                    MIN(overall_risk) as min_risk,
                    MAX(overall_risk) as max_risk,
                    AVG(clinical_risk) as mean_clinical,
                    AVG(lifestyle_risk) as mean_lifestyle
                    FROM assessments {where_clause}""",
                tuple(params),
            ).fetchone()

        if not row or row["total"] == 0:
            return {"total": 0, "mean_risk": 0.0, "min_risk": 0.0, "max_risk": 0.0}

        return {
            "total": int(row["total"]),
            "mean_risk": round(float(row["mean_risk"]), 2) if row["mean_risk"] else 0.0,
            "min_risk": round(float(row["min_risk"]), 2) if row["min_risk"] else 0.0,
            "max_risk": round(float(row["max_risk"]), 2) if row["max_risk"] else 0.0,
            "mean_clinical_risk": round(float(row["mean_clinical"]), 2) if row["mean_clinical"] else 0.0,
            "mean_lifestyle_risk": round(float(row["mean_lifestyle"]), 2) if row["mean_lifestyle"] else 0.0,
        }

    @staticmethod
    def get_category_transitions(
        user_id: int | None = None,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Detect risk category transitions between consecutive assessments."""
        conditions = []
        params: list[Any] = []

        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_connection(db_path) as conn:
            rows = conn.execute(
                f"""SELECT assessment_id, user_id, risk_category, created_at,
                    LAG(risk_category) OVER (PARTITION BY user_id ORDER BY created_at) as prev_category
                    FROM assessments {where_clause}
                    ORDER BY user_id, created_at""",
                tuple(params),
            ).fetchall()

        transitions = []
        for r in rows:
            if r["prev_category"] and r["prev_category"] != r["risk_category"]:
                transitions.append({
                    "assessment_id": r["assessment_id"],
                    "from_category": r["prev_category"],
                    "to_category": r["risk_category"],
                    "timestamp": r["created_at"],
                })

        return transitions
