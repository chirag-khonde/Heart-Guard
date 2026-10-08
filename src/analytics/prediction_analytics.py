"""Prediction Analytics Service (Phase 17).

Tracks aggregate prediction metrics: counts, risk categories, success/failure,
model version usage, inference duration, and confidence distributions.
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


class PredictionAnalytics:
    """Aggregate prediction analytics from assessment records."""

    @staticmethod
    def get_prediction_summary(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get aggregate prediction summary.

        Args:
            date_range: '7d', '30d', '90d', or None for all.
            db_path: Override database path.
        """
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_connection(db_path) as conn:
            total_row = conn.execute(
                f"SELECT COUNT(*) as total FROM assessments {where_clause}", tuple(params)
            ).fetchone()

            risk_rows = conn.execute(
                f"SELECT risk_category, COUNT(*) as count FROM assessments {where_clause} GROUP BY risk_category",
                tuple(params),
            ).fetchall()

            model_rows = conn.execute(
                f"SELECT model_version, COUNT(*) as count FROM assessments {where_clause} GROUP BY model_version ORDER BY count DESC",
                tuple(params),
            ).fetchall()

            alert_rows = conn.execute(
                f"SELECT alert_status, COUNT(*) as count FROM assessments {where_clause} GROUP BY alert_status",
                tuple(params),
            ).fetchall()

            risk_stats = conn.execute(
                f"SELECT AVG(overall_risk) as avg_risk, MIN(overall_risk) as min_risk, MAX(overall_risk) as max_risk FROM assessments {where_clause}",
                tuple(params),
            ).fetchone()

            unique_patients_row = conn.execute(
                f"SELECT COUNT(DISTINCT user_id) as count FROM assessments {where_clause}", tuple(params)
            ).fetchone()

        return {
            "total_predictions": int(total_row["total"]) if total_row else 0,
            "unique_patients": int(unique_patients_row["count"]) if unique_patients_row else 0,
            "risk_category_distribution": {r["risk_category"]: int(r["count"]) for r in risk_rows},
            "model_version_distribution": {r["model_version"]: int(r["count"]) for r in model_rows},
            "alert_status_distribution": {r["alert_status"]: int(r["count"]) for r in alert_rows},
            "risk_statistics": {
                "mean": round(float(risk_stats["avg_risk"]), 2) if risk_stats and risk_stats["avg_risk"] else 0.0,
                "min": round(float(risk_stats["min_risk"]), 2) if risk_stats and risk_stats["min_risk"] else 0.0,
                "max": round(float(risk_stats["max_risk"]), 2) if risk_stats and risk_stats["max_risk"] else 0.0,
            } if risk_stats else {},
        }

    @staticmethod
    def get_prediction_trend(
        interval: str = "daily",
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Get prediction counts over time.

        Args:
            interval: 'daily', 'weekly', or 'monthly'.
            date_range: '7d', '30d', '90d', or None.
        """
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
                    COUNT(*) as prediction_count,
                    AVG(overall_risk) as avg_risk,
                    COUNT(DISTINCT user_id) as patient_count
                    FROM assessments {where_clause}
                    GROUP BY period ORDER BY period""",
                tuple(params),
            ).fetchall()

        return [
            {
                "period": r["period"],
                "prediction_count": int(r["prediction_count"]),
                "avg_risk": round(float(r["avg_risk"]), 2) if r["avg_risk"] else 0.0,
                "patient_count": int(r["patient_count"]),
            }
            for r in rows
        ]

    @staticmethod
    def get_model_version_analytics(
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Get predictions grouped by model version."""
        with _get_connection(db_path) as conn:
            rows = conn.execute(
                """SELECT model_version,
                    COUNT(*) as prediction_count,
                    AVG(overall_risk) as avg_risk,
                    AVG(clinical_risk) as avg_clinical_risk,
                    COUNT(DISTINCT user_id) as patient_count,
                    MIN(created_at) as first_used,
                    MAX(created_at) as last_used
                    FROM assessments GROUP BY model_version ORDER BY prediction_count DESC"""
            ).fetchall()

        return [
            {
                "model_version": r["model_version"],
                "prediction_count": int(r["prediction_count"]),
                "avg_risk": round(float(r["avg_risk"]), 2) if r["avg_risk"] else 0.0,
                "avg_clinical_risk": round(float(r["avg_clinical_risk"]), 2) if r["avg_clinical_risk"] else 0.0,
                "patient_count": int(r["patient_count"]),
                "first_used": r["first_used"],
                "last_used": r["last_used"],
            }
            for r in rows
        ]

    @staticmethod
    def get_prediction_distribution(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get distribution of prediction risk scores."""
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_connection(db_path) as conn:
            rows = conn.execute(
                f"""SELECT
                    CASE
                        WHEN overall_risk < 25 THEN '0-24%'
                        WHEN overall_risk < 50 THEN '25-49%'
                        WHEN overall_risk < 60 THEN '50-59%'
                        WHEN overall_risk < 75 THEN '60-74%'
                        WHEN overall_risk < 85 THEN '75-84%'
                        ELSE '85-100%'
                    END as risk_bucket,
                    COUNT(*) as count
                    FROM assessments {where_clause}
                    GROUP BY risk_bucket ORDER BY MIN(overall_risk)""",
                tuple(params),
            ).fetchall()

        return {r["risk_bucket"]: int(r["count"]) for r in rows}
