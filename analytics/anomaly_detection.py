"""Anomaly Detection Service (Phase 17).

Lightweight anomaly detection for operational analytics:
- Unusual request volume
- Unusual prediction distribution
- Unusual assessment volume
- Unusual latency
- Unusual error rate

Statistical anomaly detection only. Does NOT create medical diagnoses.
"""

from __future__ import annotations

import math
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

from config.monitoring import (
    ANOMALY_ERROR_RATE_THRESHOLD,
    ANOMALY_MIN_HISTORY,
    ANOMALY_VOLUME_SPIKE_FACTOR,
    ANOMALY_ZSCORE_THRESHOLD,
    STATUS_HEALTHY,
    STATUS_INSUFFICIENT_DATA,
    STATUS_WARNING,
)
from config.settings import ASSESSMENTS_DB_PATH
from src.analytics.history_service import _get_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnomalyDetector:
    """Detects operational anomalies using statistical methods."""

    @staticmethod
    def detect_volume_anomaly(
        daily_counts: list[int],
        current_count: int,
    ) -> dict[str, Any]:
        """Detect if current count is anomalous compared to history."""
        if len(daily_counts) < ANOMALY_MIN_HISTORY:
            return {
                "status": STATUS_INSUFFICIENT_DATA,
                "message": f"Need at least {ANOMALY_MIN_HISTORY} data points",
            }

        arr = np.array(daily_counts, dtype=float)
        mean = float(np.mean(arr))
        std = float(np.std(arr))

        if std == 0:
            zscore = 0.0 if current_count == mean else float("inf")
        else:
            zscore = (current_count - mean) / std

        is_anomaly = abs(zscore) > ANOMALY_ZSCORE_THRESHOLD
        is_spike = current_count > mean * ANOMALY_VOLUME_SPIKE_FACTOR if mean > 0 else False

        status = STATUS_WARNING if (is_anomaly or is_spike) else STATUS_HEALTHY

        return {
            "status": status,
            "current_count": current_count,
            "mean": round(mean, 2),
            "std": round(std, 2),
            "z_score": round(zscore, 2),
            "is_anomaly": is_anomaly,
            "is_spike": is_spike,
            "threshold": ANOMALY_ZSCORE_THRESHOLD,
        }

    @staticmethod
    def detect_distribution_anomaly(
        reference_distribution: dict[str, int],
        current_distribution: dict[str, int],
        label: str = "distribution",
    ) -> dict[str, Any]:
        """Detect if a distribution has shifted anomalously."""
        all_keys = set(reference_distribution.keys()) | set(current_distribution.keys())
        ref_total = sum(reference_distribution.values()) or 1
        cur_total = sum(current_distribution.values()) or 1

        max_shift = 0.0
        for key in all_keys:
            ref_pct = reference_distribution.get(key, 0) / ref_total
            cur_pct = current_distribution.get(key, 0) / cur_total
            shift = abs(ref_pct - cur_pct)
            max_shift = max(max_shift, shift)

        is_anomaly = max_shift > 0.25

        return {
            "status": STATUS_WARNING if is_anomaly else STATUS_HEALTHY,
            "label": label,
            "max_shift": round(max_shift, 4),
            "is_anomaly": is_anomaly,
            "reference_total": ref_total,
            "current_total": cur_total,
        }

    @staticmethod
    def detect_assessment_volume_anomaly(
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Detect anomalous assessment creation volume."""
        with _get_connection(db_path) as conn:
            rows = conn.execute(
                """SELECT strftime('%Y-%m-%d', created_at) as day, COUNT(*) as count
                   FROM assessments
                   GROUP BY day ORDER BY day"""
            ).fetchall()

        if len(rows) < ANOMALY_MIN_HISTORY:
            return {
                "status": STATUS_INSUFFICIENT_DATA,
                "component": "assessment_volume",
                "message": "Insufficient history for volume anomaly detection",
            }

        daily_counts = [int(r["count"]) for r in rows]
        current_count = daily_counts[-1] if daily_counts else 0
        history = daily_counts[:-1] if len(daily_counts) > 1 else daily_counts

        result = AnomalyDetector.detect_volume_anomaly(history, current_count)
        result["component"] = "assessment_volume"
        result["total_days"] = len(rows)
        return result

    @staticmethod
    def detect_prediction_distribution_anomaly(
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Detect anomalous shifts in prediction category distribution."""
        with _get_connection(db_path) as conn:
            recent_rows = conn.execute(
                """SELECT risk_category, COUNT(*) as count
                   FROM assessments
                   WHERE created_at >= date('now', '-30 days')
                   GROUP BY risk_category"""
            ).fetchall()

            historical_rows = conn.execute(
                """SELECT risk_category, COUNT(*) as count
                   FROM assessments
                   WHERE created_at < date('now', '-30 days')
                   GROUP BY risk_category"""
            ).fetchall()

        if not historical_rows or not recent_rows:
            return {
                "status": STATUS_INSUFFICIENT_DATA,
                "component": "prediction_distribution",
                "message": "Insufficient data for distribution anomaly detection",
            }

        ref_dist = {r["risk_category"]: int(r["count"]) for r in historical_rows}
        cur_dist = {r["risk_category"]: int(r["count"]) for r in recent_rows}

        return AnomalyDetector.detect_distribution_anomaly(ref_dist, cur_dist, "prediction_distribution")

    @staticmethod
    def detect_error_rate_anomaly(
        total_events: int,
        error_events: int,
    ) -> dict[str, Any]:
        """Detect anomalous error rates."""
        if total_events == 0:
            return {
                "status": STATUS_INSUFFICIENT_DATA,
                "component": "error_rate",
                "message": "No events to analyze",
            }

        error_rate = error_events / total_events
        is_anomaly = error_rate > ANOMALY_ERROR_RATE_THRESHOLD

        return {
            "status": STATUS_WARNING if is_anomaly else STATUS_HEALTHY,
            "component": "error_rate",
            "error_rate": round(error_rate, 4),
            "error_events": error_events,
            "total_events": total_events,
            "is_anomaly": is_anomaly,
            "threshold": ANOMALY_ERROR_RATE_THRESHOLD,
        }

    @staticmethod
    def run_comprehensive_anomaly_detection(
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Run all anomaly detection checks."""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall_status": STATUS_HEALTHY,
        }

        vol_result = AnomalyDetector.detect_assessment_volume_anomaly(db_path)
        results["checks"]["assessment_volume"] = vol_result

        dist_result = AnomalyDetector.detect_prediction_distribution_anomaly(db_path)
        results["checks"]["prediction_distribution"] = dist_result

        any_warning = any(
            check.get("status") == STATUS_WARNING
            for check in results["checks"].values()
            if isinstance(check, dict)
        )
        if any_warning:
            results["overall_status"] = STATUS_WARNING

        return results
