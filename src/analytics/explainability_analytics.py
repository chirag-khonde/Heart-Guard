"""Explainability Analytics Service (Phase 17).

Provides aggregate feature importance analysis from stored SHAP data:
most frequently influential features, average absolute SHAP values,
and feature importance distribution across assessments.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

from config.settings import ASSESSMENTS_DB_PATH
from src.analytics.history_service import _get_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExplainabilityAnalytics:
    """Aggregate explainability analytics from SHAP data."""

    @staticmethod
    def get_feature_importance_summary(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get aggregate feature importance from stored SHAP factors."""
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff)

        conditions.append("top_clinical_factors_json IS NOT NULL")
        where_clause = f"WHERE {' AND '.join(conditions)}"

        with _get_connection(db_path) as conn:
            rows = conn.execute(
                f"SELECT top_clinical_factors_json FROM assessments {where_clause}",
                tuple(params),
            ).fetchall()

        if not rows:
            return {
                "total_assessments_with_shap": 0,
                "status": "NO_DATA",
                "message": "No SHAP data available for analysis",
            }

        feature_counts: Counter[str] = Counter()
        feature_shap_sums: dict[str, list[float]] = {}
        total_with_shap = 0

        for row in rows:
            try:
                factors = json.loads(row["top_clinical_factors_json"])
                if not isinstance(factors, list):
                    continue
                total_with_shap += 1
                for factor in factors:
                    feature = factor.get("feature", "unknown")
                    shap_val = factor.get("shap_value", factor.get("importance", 0.0))
                    try:
                        shap_float = float(shap_val)
                    except (ValueError, TypeError):
                        shap_float = 0.0
                    feature_counts[feature] += 1
                    if feature not in feature_shap_sums:
                        feature_shap_sums[feature] = []
                    feature_shap_sums[feature].append(abs(shap_float))
            except Exception:
                continue

        feature_stats = []
        for feature, count in feature_counts.most_common():
            abs_vals = feature_shap_sums.get(feature, [])
            feature_stats.append({
                "feature": feature,
                "frequency": count,
                "frequency_pct": round(count / total_with_shap * 100, 1) if total_with_shap > 0 else 0.0,
                "avg_abs_shap": round(float(np.mean(abs_vals)), 4) if abs_vals else 0.0,
                "max_abs_shap": round(float(np.max(abs_vals)), 4) if abs_vals else 0.0,
                "std_abs_shap": round(float(np.std(abs_vals)), 4) if len(abs_vals) > 1 else 0.0,
            })

        return {
            "total_assessments_with_shap": total_with_shap,
            "unique_features": len(feature_stats),
            "features": feature_stats,
            "top_features": feature_stats[:10],
            "privacy_note": (
                "This is an aggregate statistical view. "
                "Individual patient SHAP values are not exposed in this dashboard."
            ),
        }

    @staticmethod
    def get_feature_frequency_distribution(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get how often each feature appears in top factors."""
        summary = ExplainabilityAnalytics.get_feature_importance_summary(date_range, db_path)
        return {
            "features": [
                {"feature": f["feature"], "frequency_pct": f["frequency_pct"]}
                for f in summary.get("features", [])
            ]
        }

    @staticmethod
    def get_shap_value_distribution(
        feature_name: str,
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get distribution of SHAP values for a specific feature."""
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff)

        conditions.append("top_clinical_factors_json IS NOT NULL")
        where_clause = f"WHERE {' AND '.join(conditions)}"

        with _get_connection(db_path) as conn:
            rows = conn.execute(
                f"SELECT top_clinical_factors_json FROM assessments {where_clause}",
                tuple(params),
            ).fetchall()

        values = []
        for row in rows:
            try:
                factors = json.loads(row["top_clinical_factors_json"])
                if not isinstance(factors, list):
                    continue
                for factor in factors:
                    if factor.get("feature") == feature_name:
                        val = factor.get("shap_value", factor.get("importance", 0.0))
                        values.append(float(val))
            except Exception:
                continue

        if not values:
            return {"feature": feature_name, "count": 0, "message": "No data for this feature"}

        arr = np.array(values)
        return {
            "feature": feature_name,
            "count": len(values),
            "mean": round(float(np.mean(arr)), 4),
            "std": round(float(np.std(arr)), 4) if len(arr) > 1 else 0.0,
            "min": round(float(np.min(arr)), 4),
            "max": round(float(np.max(arr)), 4),
            "median": round(float(np.median(arr)), 4),
        }
