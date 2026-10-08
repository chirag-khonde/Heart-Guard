"""Alert Analytics Service (Phase 17).

Analyzes existing HeartGuard alert records: aggregate counts,
categories, trends over time, and acknowledgment status.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config.settings import ALERTS_DB_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _get_alert_connection(db_path: Path | None = None) -> sqlite3.Connection:
    target = db_path or ALERTS_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class AlertAnalytics:
    """Aggregate alert analytics from alert history records."""

    @staticmethod
    def get_alert_summary(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get aggregate alert statistics."""
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("timestamp >= ?")
            params.append(cutoff)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_alert_connection(db_path) as conn:
            total_row = conn.execute(
                f"SELECT COUNT(*) as total FROM alerts {where_clause}", tuple(params)
            ).fetchone()

            status_rows = conn.execute(
                f"SELECT status, COUNT(*) as count FROM alerts {where_clause} GROUP BY status",
                tuple(params),
            ).fetchall()

            type_rows = conn.execute(
                f"SELECT recipient_type, COUNT(*) as count FROM alerts {where_clause} GROUP BY recipient_type",
                tuple(params),
            ).fetchall()

            level_rows = conn.execute(
                f"SELECT risk_level, COUNT(*) as count FROM alerts {where_clause} GROUP BY risk_level",
                tuple(params),
            ).fetchall()

        return {
            "total_alerts": int(total_row["total"]) if total_row else 0,
            "by_status": {r["status"]: int(r["count"]) for r in status_rows},
            "by_recipient_type": {r["recipient_type"]: int(r["count"]) for r in type_rows},
            "by_risk_level": {r["risk_level"]: int(r["count"]) for r in level_rows},
        }

    @staticmethod
    def get_alert_trend(
        interval: str = "daily",
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Get alert counts over time."""
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("timestamp >= ?")
            params.append(cutoff)

        if interval == "daily":
            date_expr = "strftime('%Y-%m-%d', timestamp)"
        elif interval == "weekly":
            date_expr = "strftime('%Y-W%W', timestamp)"
        else:
            date_expr = "strftime('%Y-%m', timestamp)"

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_alert_connection(db_path) as conn:
            rows = conn.execute(
                f"""SELECT {date_expr} as period, COUNT(*) as alert_count,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_count
                    FROM alerts {where_clause}
                    GROUP BY period ORDER BY period""",
                tuple(params),
            ).fetchall()

        return [
            {
                "period": r["period"],
                "alert_count": int(r["alert_count"]),
                "success_count": int(r["success_count"]) if r["success_count"] else 0,
                "failed_count": int(r["failed_count"]) if r["failed_count"] else 0,
            }
            for r in rows
        ]

    @staticmethod
    def get_alert_success_rate(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Calculate alert delivery success rate."""
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("timestamp >= ?")
            params.append(cutoff)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_alert_connection(db_path) as conn:
            row = conn.execute(
                f"""SELECT COUNT(*) as total,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status IN ('DISABLED', 'NOT_TRIGGERED') THEN 1 ELSE 0 END) as skipped
                    FROM alerts {where_clause}""",
                tuple(params),
            ).fetchone()

        total = int(row["total"]) if row else 0
        success = int(row["success"]) if row and row["success"] else 0
        failed = int(row["failed"]) if row and row["failed"] else 0
        active = success + failed

        return {
            "total_alerts": total,
            "successful": success,
            "failed": failed,
            "skipped": int(row["skipped"]) if row and row["skipped"] else 0,
            "success_rate": round(success / active, 4) if active > 0 else None,
        }
