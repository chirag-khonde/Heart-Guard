"""Performance Monitoring Service (Phase 17).

Monitors application performance metrics: request counts, error counts,
response times, inference latency, report generation time, and database latency.
"""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config.monitoring import (
    PERF_CACHE_TTL_SECONDS,
    PERF_ERROR_RATE_CRITICAL,
    PERF_ERROR_RATE_WARNING,
    PERF_LATENCY_CRITICAL_MS,
    PERF_LATENCY_WARNING_MS,
    STATUS_DEGRADED,
    STATUS_HEALTHY,
    STATUS_UNAVAILABLE,
    STATUS_WARNING,
    MONITORING_DB_DIR,
    MONITORING_DB_PATH,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

_CREATE_PERF_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS performance_metrics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,
    metric_type TEXT    NOT NULL,
    metric_name TEXT    NOT NULL,
    value       REAL    NOT NULL,
    unit        TEXT,
    details_json TEXT
);
"""

_CREATE_PERF_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON performance_metrics (timestamp DESC);",
    "CREATE INDEX IF NOT EXISTS idx_perf_type ON performance_metrics (metric_type, metric_name);",
]


def _init_perf_db(db_path: Path | None = None) -> None:
    target = db_path or MONITORING_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=10.0)
    try:
        conn.execute(_CREATE_PERF_TABLE_SQL)
        for idx in _CREATE_PERF_INDEXES:
            conn.execute(idx)
        conn.commit()
    finally:
        conn.close()


def _get_perf_connection(db_path: Path | None = None) -> sqlite3.Connection:
    target = db_path or MONITORING_DB_PATH
    _init_perf_db(target)
    conn = sqlite3.connect(str(target), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class PerformanceMonitor:
    """Records and analyzes application performance metrics."""

    _cache: dict[str, tuple[float, Any]] = {}

    @staticmethod
    def record_metric(
        metric_type: str,
        metric_name: str,
        value: float,
        unit: str | None = None,
        details: dict[str, Any] | None = None,
        db_path: Path | None = None,
    ) -> None:
        """Record a performance metric."""
        details_json = json.dumps(details) if details else None
        now_iso = datetime.now(timezone.utc).isoformat()

        with _get_perf_connection(db_path) as conn:
            conn.execute(
                """INSERT INTO performance_metrics
                   (timestamp, metric_type, metric_name, value, unit, details_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (now_iso, metric_type, metric_name, value, unit, details_json),
            )
            conn.commit()

    @staticmethod
    def record_inference_latency(
        model_name: str,
        latency_ms: float,
        db_path: Path | None = None,
    ) -> None:
        """Record model inference latency."""
        PerformanceMonitor.record_metric(
            "inference", f"{model_name}_latency", latency_ms, "ms", db_path=db_path
        )

    @staticmethod
    def record_request(
        endpoint: str,
        status_code: int,
        latency_ms: float,
        db_path: Path | None = None,
    ) -> None:
        """Record an API request metric."""
        PerformanceMonitor.record_metric(
            "request", endpoint, latency_ms, "ms",
            details={"status_code": status_code}, db_path=db_path
        )

    @staticmethod
    def record_error(
        component: str,
        error_type: str,
        db_path: Path | None = None,
    ) -> None:
        """Record an error event."""
        PerformanceMonitor.record_metric(
            "error", f"{component}_{error_type}", 1.0, "count", db_path=db_path
        )

    @staticmethod
    def get_metric_summary(
        metric_type: str,
        metric_name: str | None = None,
        hours: int = 24,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get summary statistics for a metric type."""
        cache_key = f"{metric_type}:{metric_name}:{hours}"
        cached = PerformanceMonitor._cache.get(cache_key)
        if cached and (time.monotonic() - cached[0]) < PERF_CACHE_TTL_SECONDS:
            return cached[1]

        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        with _get_perf_connection(db_path) as conn:
            if metric_name:
                row = conn.execute(
                    """SELECT COUNT(*) as count, AVG(value) as avg_val,
                       MIN(value) as min_val, MAX(value) as max_val
                       FROM performance_metrics
                       WHERE metric_type = ? AND metric_name = ? AND timestamp >= ?""",
                    (metric_type, metric_name, cutoff),
                ).fetchone()
            else:
                row = conn.execute(
                    """SELECT COUNT(*) as count, AVG(value) as avg_val,
                       MIN(value) as min_val, MAX(value) as max_val
                       FROM performance_metrics
                       WHERE metric_type = ? AND timestamp >= ?""",
                    (metric_type, cutoff),
                ).fetchone()

        result = {
            "count": int(row["count"]) if row else 0,
            "avg_value": round(float(row["avg_val"]), 2) if row and row["avg_val"] else 0.0,
            "min_value": round(float(row["min_val"]), 2) if row and row["min_val"] else 0.0,
            "max_value": round(float(row["max_val"]), 2) if row and row["max_val"] else 0.0,
        }

        PerformanceMonitor._cache[cache_key] = (time.monotonic(), result)
        return result

    @staticmethod
    def get_latency_trend(
        metric_name: str | None = None,
        hours: int = 24,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Get latency trend over time."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        with _get_perf_connection(db_path) as conn:
            if metric_name:
                rows = conn.execute(
                    """SELECT strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                       AVG(value) as avg_latency, COUNT(*) as sample_count
                       FROM performance_metrics
                       WHERE metric_type = 'inference' AND metric_name = ? AND timestamp >= ?
                       GROUP BY hour ORDER BY hour""",
                    (metric_name, cutoff),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                       AVG(value) as avg_latency, COUNT(*) as sample_count
                       FROM performance_metrics
                       WHERE metric_type = 'inference' AND timestamp >= ?
                       GROUP BY hour ORDER BY hour""",
                    (cutoff,),
                ).fetchall()

        return [
            {
                "period": r["hour"],
                "avg_latency_ms": round(float(r["avg_latency"]), 2),
                "sample_count": int(r["sample_count"]),
            }
            for r in rows
        ]

    @staticmethod
    def get_error_summary(
        hours: int = 24,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get error summary for the specified period."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        with _get_perf_connection(db_path) as conn:
            error_rows = conn.execute(
                """SELECT metric_name, COUNT(*) as error_count
                   FROM performance_metrics
                   WHERE metric_type = 'error' AND timestamp >= ?
                   GROUP BY metric_name ORDER BY error_count DESC""",
                (cutoff,),
            ).fetchall()

            total_errors = sum(int(r["error_count"]) for r in error_rows)

            request_row = conn.execute(
                """SELECT COUNT(*) as total
                   FROM performance_metrics
                   WHERE metric_type = 'request' AND timestamp >= ?""",
                (cutoff,),
            ).fetchone()

        total_requests = int(request_row["total"]) if request_row else 0
        error_rate = total_errors / total_requests if total_requests > 0 else 0.0

        status = STATUS_HEALTHY
        if error_rate >= PERF_ERROR_RATE_CRITICAL:
            status = STATUS_DEGRADED
        elif error_rate >= PERF_ERROR_RATE_WARNING:
            status = STATUS_WARNING

        return {
            "status": status,
            "total_errors": total_errors,
            "total_requests": total_requests,
            "error_rate": round(error_rate, 4),
            "errors_by_type": {r["metric_name"]: int(r["error_count"]) for r in error_rows},
        }

    @staticmethod
    def get_system_performance_summary(
        hours: int = 24,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get overall system performance summary."""
        inference = PerformanceMonitor.get_metric_summary("inference", hours=hours, db_path=db_path)
        requests = PerformanceMonitor.get_metric_summary("request", hours=hours, db_path=db_path)
        errors = PerformanceMonitor.get_error_summary(hours=hours, db_path=db_path)

        latency_status = STATUS_HEALTHY
        if inference["avg_value"] > PERF_LATENCY_CRITICAL_MS:
            latency_status = STATUS_DEGRADED
        elif inference["avg_value"] > PERF_LATENCY_WARNING_MS:
            latency_status = STATUS_WARNING

        return {
            "period_hours": hours,
            "inference_latency": {
                "status": latency_status,
                **inference,
            },
            "requests": requests,
            "errors": errors,
            "overall_status": STATUS_HEALTHY if (
                latency_status == STATUS_HEALTHY and errors["status"] == STATUS_HEALTHY
            ) else STATUS_DEGRADED,
        }
