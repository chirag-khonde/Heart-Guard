"""Data Quality Monitoring Service (Phase 17).

Monitors assessment data quality: missing values, invalid values,
out-of-range values, duplicate records, unexpected categories,
and schema changes.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.monitoring import (
    DQ_DUPLICATE_RATE_WARNING,
    DQ_MIN_RECORDS,
    DQ_MISSING_RATE_CRITICAL,
    DQ_MISSING_RATE_WARNING,
    DQ_OUT_OF_RANGE_WARNING,
    STATUS_DEGRADED,
    STATUS_HEALTHY,
    STATUS_INSUFFICIENT_DATA,
    STATUS_WARNING,
)
from config.settings import ASSESSMENTS_DB_PATH
from src.analytics.history_service import _get_connection
from src.data.features import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    VALIDATION_BOUNDS,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataQualityMonitor:
    """Monitors data quality in assessment records."""

    @staticmethod
    def assess_data_quality(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Run comprehensive data quality assessment on assessment records."""
        from datetime import timedelta

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
            total = int(total_row["total"]) if total_row else 0

            if total < DQ_MIN_RECORDS:
                return {
                    "status": STATUS_INSUFFICIENT_DATA,
                    "total_records": total,
                    "message": f"Insufficient records for quality analysis (need {DQ_MIN_RECORDS})",
                }

            clinical_conditions = list(conditions) + ["clinical_data_json IS NOT NULL"]
            clinical_where = f"WHERE {' AND '.join(clinical_conditions)}"
            clinical_rows = conn.execute(
                f"SELECT clinical_data_json FROM assessments {clinical_where}",
                tuple(params),
            ).fetchall()

            dup_row = conn.execute(
                f"""SELECT COUNT(*) as dups FROM (
                    SELECT assessment_id, user_id, created_at
                    FROM assessments {where_clause}
                    GROUP BY assessment_id, user_id, created_at HAVING COUNT(*) > 1
                )""",
                tuple(params),
            ).fetchone()

        missing_analysis = DataQualityMonitor._analyze_missing(clinical_rows)
        invalid_analysis = DataQualityMonitor._analyze_invalid(clinical_rows)
        range_analysis = DataQualityMonitor._analyze_out_of_range(clinical_rows)
        schema_analysis = DataQualityMonitor._analyze_schema(clinical_rows)

        duplicate_count = int(dup_row["dups"]) if dup_row else 0
        duplicate_rate = duplicate_count / total if total > 0 else 0.0

        overall_status = STATUS_HEALTHY
        issues = []

        if missing_analysis["max_missing_rate"] > DQ_MISSING_RATE_CRITICAL:
            overall_status = STATUS_DEGRADED
            issues.append(f"Critical missing data rate: {missing_analysis['max_missing_rate']:.1%}")
        elif missing_analysis["max_missing_rate"] > DQ_MISSING_RATE_WARNING:
            if overall_status == STATUS_HEALTHY:
                overall_status = STATUS_WARNING
            issues.append(f"Elevated missing data rate: {missing_analysis['max_missing_rate']:.1%}")

        if duplicate_rate > DQ_DUPLICATE_RATE_WARNING:
            if overall_status == STATUS_HEALTHY:
                overall_status = STATUS_WARNING
            issues.append(f"Duplicate rate: {duplicate_rate:.1%}")

        if range_analysis["out_of_range_count"] > 0:
            oor_rate = range_analysis["out_of_range_count"] / total
            if oor_rate > DQ_OUT_OF_RANGE_WARNING:
                if overall_status == STATUS_HEALTHY:
                    overall_status = STATUS_WARNING
                issues.append(f"Out-of-range values: {range_analysis['out_of_range_count']}")

        if schema_analysis["unexpected_categories"]:
            if overall_status == STATUS_HEALTHY:
                overall_status = STATUS_WARNING
            issues.append(f"Unexpected categories found in {len(schema_analysis['unexpected_categories'])} features")

        return {
            "status": overall_status,
            "total_records": total,
            "valid_records": total - duplicate_count,
            "invalid_records": duplicate_count,
            "duplicate_rate": round(duplicate_rate, 4),
            "missing_analysis": missing_analysis,
            "invalid_analysis": invalid_analysis,
            "out_of_range_analysis": range_analysis,
            "schema_analysis": schema_analysis,
            "issues": issues,
        }

    @staticmethod
    def _analyze_missing(clinical_rows: list) -> dict[str, Any]:
        """Analyze missing values per feature."""
        feature_missing: dict[str, int] = {f: 0 for f in NUMERICAL_FEATURES + CATEGORICAL_FEATURES}
        total_parsed = 0

        for row in clinical_rows:
            try:
                data = json.loads(row["clinical_data_json"])
                if not isinstance(data, dict):
                    continue
                total_parsed += 1
                for feat in NUMERICAL_FEATURES + CATEGORICAL_FEATURES:
                    if data.get(feat) is None or data.get(feat) == "":
                        feature_missing[feat] += 1
            except Exception:
                continue

        missing_rates = {}
        for feat, count in feature_missing.items():
            rate = count / total_parsed if total_parsed > 0 else 0.0
            missing_rates[feat] = {"count": count, "rate": round(rate, 4)}

        max_rate = max((v["rate"] for v in missing_rates.values()), default=0.0)

        return {
            "total_parsed": total_parsed,
            "per_feature": missing_rates,
            "max_missing_rate": max_rate,
            "features_with_missing": [f for f, v in missing_rates.items() if v["count"] > 0],
        }

    @staticmethod
    def _analyze_invalid(clinical_rows: list) -> dict[str, Any]:
        """Analyze invalid values (None, empty, non-numeric for numeric features)."""
        invalid_counts: dict[str, int] = {f: 0 for f in NUMERICAL_FEATURES}
        total_parsed = 0

        for row in clinical_rows:
            try:
                data = json.loads(row["clinical_data_json"])
                if not isinstance(data, dict):
                    continue
                total_parsed += 1
                for feat in NUMERICAL_FEATURES:
                    val = data.get(feat)
                    if val is None or val == "":
                        continue
                    try:
                        float(val)
                    except (ValueError, TypeError):
                        invalid_counts[feat] += 1
            except Exception:
                continue

        return {
            "total_parsed": total_parsed,
            "per_feature": invalid_counts,
            "total_invalid": sum(invalid_counts.values()),
        }

    @staticmethod
    def _analyze_out_of_range(clinical_rows: list) -> dict[str, Any]:
        """Analyze values outside expected validation bounds."""
        out_of_range: dict[str, int] = {f: 0 for f in NUMERICAL_FEATURES}
        total_out = 0

        for row in clinical_rows:
            try:
                data = json.loads(row["clinical_data_json"])
                if not isinstance(data, dict):
                    continue
                for feat in NUMERICAL_FEATURES:
                    val = data.get(feat)
                    if val is None:
                        continue
                    try:
                        fval = float(val)
                        bounds = VALIDATION_BOUNDS.get(feat)
                        if bounds and (fval < bounds[0] or fval > bounds[1]):
                            out_of_range[feat] += 1
                            total_out += 1
                    except (ValueError, TypeError):
                        pass
            except Exception:
                continue

        return {
            "out_of_range_count": total_out,
            "per_feature": out_of_range,
        }

    @staticmethod
    def _analyze_schema(clinical_rows: list) -> dict[str, Any]:
        """Detect unexpected categories in categorical features."""
        expected_categories = {
            "sex": {"0", "1"},
            "chest_pain_type": {"0", "1", "2", "3"},
            "fasting_blood_sugar": {"0", "1"},
            "resting_ecg": {"0", "1", "2"},
            "exercise_angina": {"0", "1"},
        }

        observed_categories: dict[str, set[str]] = {f: set() for f in CATEGORICAL_FEATURES}
        total_parsed = 0

        for row in clinical_rows:
            try:
                data = json.loads(row["clinical_data_json"])
                if not isinstance(data, dict):
                    continue
                total_parsed += 1
                for feat in CATEGORICAL_FEATURES:
                    val = data.get(feat)
                    if val is not None:
                        observed_categories[feat].add(str(val))
            except Exception:
                continue

        unexpected = {}
        for feat in CATEGORICAL_FEATURES:
            expected = expected_categories.get(feat, set())
            observed = observed_categories[feat]
            unexpected_vals = observed - expected
            if unexpected_vals:
                unexpected[feat] = list(unexpected_vals)

        return {
            "total_parsed": total_parsed,
            "unexpected_categories": unexpected,
            "schema_status": "WARNING" if unexpected else "OK",
        }

    @staticmethod
    def get_schema_snapshot(db_path: Path | None = None) -> dict[str, Any]:
        """Get a snapshot of the current assessment schema."""
        with _get_connection(db_path) as conn:
            row = conn.execute("PRAGMA table_info(assessments)").fetchall()

        columns = {}
        for col in row:
            columns[col["name"]] = {
                "type": col["type"],
                "not_null": bool(col["notnull"]),
                "is_pk": bool(col["pk"]),
            }

        return {
            "table": "assessments",
            "columns": columns,
            "column_count": len(columns),
            "snapshot_time": datetime.now(timezone.utc).isoformat(),
        }
