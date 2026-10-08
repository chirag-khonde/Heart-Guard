"""Monitoring Events Database and Service (Phase 17).

Manages monitoring event lifecycle: creation, querying, filtering,
acknowledgment, and retention. Events never contain patient-level data.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config.monitoring import (
    EVENT_MAX_PER_PAGE,
    EVENT_RETENTION_DAYS,
    MONITORING_DB_DIR,
    MONITORING_DB_PATH,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

_CREATE_EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS monitoring_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        TEXT    NOT NULL UNIQUE,
    timestamp       TEXT    NOT NULL,
    event_type      TEXT    NOT NULL,
    severity        TEXT    NOT NULL,
    component       TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'OPEN',
    metric_name     TEXT,
    metric_value    REAL,
    threshold_value REAL,
    model_version   TEXT,
    message         TEXT    NOT NULL,
    details_json    TEXT,
    acknowledged_by TEXT,
    acknowledged_at TEXT
);
"""

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON monitoring_events (timestamp DESC);",
    "CREATE INDEX IF NOT EXISTS idx_events_type ON monitoring_events (event_type);",
    "CREATE INDEX IF NOT EXISTS idx_events_severity ON monitoring_events (severity);",
    "CREATE INDEX IF NOT EXISTS idx_events_status ON monitoring_events (status);",
    "CREATE INDEX IF NOT EXISTS idx_events_component ON monitoring_events (component);",
]


def init_monitoring_db(db_path: Path | None = None) -> None:
    """Initialize monitoring events database."""
    target = db_path or MONITORING_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=10.0)
    try:
        conn.execute(_CREATE_EVENTS_TABLE_SQL)
        for idx_sql in _CREATE_INDEXES_SQL:
            conn.execute(idx_sql)
        conn.commit()
    finally:
        conn.close()


def _get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    target = db_path or MONITORING_DB_PATH
    init_monitoring_db(target)
    conn = sqlite3.connect(str(target), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class MonitoringEventService:
    """Service for managing monitoring events."""

    @staticmethod
    def create_event(
        event_type: str,
        severity: str,
        component: str,
        message: str,
        metric_name: str | None = None,
        metric_value: float | None = None,
        threshold_value: float | None = None,
        model_version: str | None = None,
        details: dict[str, Any] | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Create a new monitoring event."""
        import json

        event_id = f"evt-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        details_json = json.dumps(details) if details else None

        with _get_connection(db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO monitoring_events
                   (event_id, timestamp, event_type, severity, component, status,
                    metric_name, metric_value, threshold_value, model_version, message, details_json)
                   VALUES (?, ?, ?, ?, ?, 'OPEN', ?, ?, ?, ?, ?, ?)""",
                (event_id, now_iso, event_type, severity, component,
                 metric_name, metric_value, threshold_value, model_version, message, details_json),
            )
            conn.commit()

        logger.info("Monitoring event created: id=%s type=%s severity=%s", event_id, event_type, severity)
        return {
            "event_id": event_id,
            "timestamp": now_iso,
            "event_type": event_type,
            "severity": severity,
            "component": component,
            "status": "OPEN",
            "message": message,
        }

    @staticmethod
    def get_events(
        event_type: str | None = None,
        severity: str | None = None,
        component: str | None = None,
        status: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        offset: int = 0,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Query monitoring events with filters."""
        import json

        conditions = []
        params: list[Any] = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        if component:
            conditions.append("component = ?")
            params.append(component)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM monitoring_events {where_clause} ORDER BY timestamp DESC"
        params_list = list(params)

        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params_list.extend([limit, offset])

        with _get_connection(db_path) as conn:
            rows = conn.execute(sql, tuple(params_list)).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                if d.get("details_json"):
                    try:
                        d["details"] = json.loads(d["details_json"])
                    except Exception:
                        d["details"] = None
                del d["details_json"]
                results.append(d)
            return results

    @staticmethod
    def acknowledge_event(
        event_id: str,
        acknowledged_by: str,
        db_path: Path | None = None,
    ) -> bool:
        """Acknowledge a monitoring event."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with _get_connection(db_path) as conn:
            cursor = conn.execute(
                """UPDATE monitoring_events SET status = 'ACKNOWLEDGED',
                   acknowledged_by = ?, acknowledged_at = ?
                   WHERE event_id = ? AND status = 'OPEN'""",
                (acknowledged_by, now_iso, event_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def get_event_counts(
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get aggregate event counts by severity and status."""
        with _get_connection(db_path) as conn:
            severity_rows = conn.execute(
                "SELECT severity, COUNT(*) as count FROM monitoring_events GROUP BY severity"
            ).fetchall()
            status_rows = conn.execute(
                "SELECT status, COUNT(*) as count FROM monitoring_events GROUP BY status"
            ).fetchall()
            type_rows = conn.execute(
                "SELECT event_type, COUNT(*) as count FROM monitoring_events GROUP BY event_type ORDER BY count DESC"
            ).fetchall()
            component_rows = conn.execute(
                "SELECT component, COUNT(*) as count FROM monitoring_events GROUP BY component ORDER BY count DESC"
            ).fetchall()

            return {
                "by_severity": {r["severity"]: r["count"] for r in severity_rows},
                "by_status": {r["status"]: r["count"] for r in status_rows},
                "by_type": {r["event_type"]: r["count"] for r in type_rows},
                "by_component": {r["component"]: r["count"] for r in component_rows},
                "total": sum(r["count"] for r in severity_rows),
            }

    @staticmethod
    def get_recent_events(
        limit: int = 20,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Get most recent monitoring events."""
        return MonitoringEventService.get_events(limit=limit, db_path=db_path)

    @staticmethod
    def cleanup_old_events(
        retention_days: int | None = None,
        db_path: Path | None = None,
    ) -> int:
        """Remove events older than retention period. Returns count deleted."""
        days = retention_days or EVENT_RETENTION_DAYS
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with _get_connection(db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM monitoring_events WHERE timestamp < ?",
                (cutoff,),
            )
            conn.commit()
            return cursor.rowcount
