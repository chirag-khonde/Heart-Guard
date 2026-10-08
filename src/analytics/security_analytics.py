"""Security Analytics Service (Phase 17).

Integrates with Phase 15 audit logs to provide aggregate security analytics:
failed logins, authorization failures, security events, admin actions,
and report access events. Never displays passwords, tokens, or session IDs.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config.settings import AUDIT_DB_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _get_audit_connection(db_path: Path | None = None) -> sqlite3.Connection:
    target = db_path or AUDIT_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class SecurityAnalytics:
    """Aggregate security analytics from audit logs."""

    @staticmethod
    def get_security_summary(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get aggregate security event statistics."""
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("timestamp >= ?")
            params.append(cutoff)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_audit_connection(db_path) as conn:
            total_row = conn.execute(
                f"SELECT COUNT(*) as total FROM audit_log {where_clause}", tuple(params)
            ).fetchone()

            type_rows = conn.execute(
                f"SELECT event_type, COUNT(*) as count FROM audit_log {where_clause} GROUP BY event_type ORDER BY count DESC",
                tuple(params),
            ).fetchall()

            status_rows = conn.execute(
                f"SELECT status, COUNT(*) as count FROM audit_log {where_clause} GROUP BY status",
                tuple(params),
            ).fetchall()

            severity_rows = conn.execute(
                f"SELECT severity, COUNT(*) as count FROM audit_log {where_clause} GROUP BY severity ORDER BY count DESC",
                tuple(params),
            ).fetchall()

            failed_conditions = list(conditions) + ["event_type = 'login'", "status = 'FAILED'"]
            failed_where = f"WHERE {' AND '.join(failed_conditions)}"
            failed_logins = conn.execute(
                f"SELECT COUNT(*) as count FROM audit_log {failed_where}",
                tuple(params),
            ).fetchone()

            auth_conditions = list(conditions) + ["event_type = 'authorization'", "status = 'DENIED'"]
            auth_where = f"WHERE {' AND '.join(auth_conditions)}"
            auth_failures = conn.execute(
                f"SELECT COUNT(*) as count FROM audit_log {auth_where}",
                tuple(params),
            ).fetchone()

            admin_conditions = list(conditions) + ["event_type LIKE 'admin%'"]
            admin_where = f"WHERE {' AND '.join(admin_conditions)}"
            admin_actions = conn.execute(
                f"SELECT COUNT(*) as count FROM audit_log {admin_where}",
                tuple(params),
            ).fetchone()

        return {
            "total_events": int(total_row["total"]) if total_row else 0,
            "failed_logins": int(failed_logins["count"]) if failed_logins else 0,
            "authorization_failures": int(auth_failures["count"]) if auth_failures else 0,
            "admin_actions": int(admin_actions["count"]) if admin_actions else 0,
            "by_type": {r["event_type"]: int(r["count"]) for r in type_rows},
            "by_status": {r["status"]: int(r["count"]) for r in status_rows},
            "by_severity": {r["severity"]: int(r["count"]) for r in severity_rows},
        }

    @staticmethod
    def get_security_event_trend(
        interval: str = "daily",
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Get security events over time."""
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

        with _get_audit_connection(db_path) as conn:
            rows = conn.execute(
                f"""SELECT {date_expr} as period, COUNT(*) as event_count,
                    SUM(CASE WHEN status = 'FAILED' OR status = 'DENIED' THEN 1 ELSE 0 END) as failure_count
                    FROM audit_log {where_clause}
                    GROUP BY period ORDER BY period""",
                tuple(params),
            ).fetchall()

        return [
            {
                "period": r["period"],
                "event_count": int(r["event_count"]),
                "failure_count": int(r["failure_count"]) if r["failure_count"] else 0,
            }
            for r in rows
        ]

    @staticmethod
    def get_login_analytics(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get login-specific analytics."""
        conditions = ["event_type = 'login'"]
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("timestamp >= ?")
            params.append(cutoff)

        where_clause = f"WHERE {' AND '.join(conditions)}"

        with _get_audit_connection(db_path) as conn:
            row = conn.execute(
                f"""SELECT COUNT(*) as total,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed
                    FROM audit_log {where_clause}""",
                tuple(params),
            ).fetchone()

        total = int(row["total"]) if row else 0
        success = int(row["success"]) if row and row["success"] else 0
        failed = int(row["failed"]) if row and row["failed"] else 0

        return {
            "total_login_attempts": total,
            "successful_logins": success,
            "failed_logins": failed,
            "success_rate": round(success / total, 4) if total > 0 else None,
        }
