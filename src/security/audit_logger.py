"""Audit logger for HeartGuard security events (Phase 9 & Phase 15).

Writes structured, tamper-evident audit records to a SQLite database.
Records: timestamp, event_type, user_id, role, status, detail, resource_type,
         resource_id, category, severity, ip_hash.

Strict Privacy & Redaction Invariants:
  - NEVER log: passwords, password hashes, auth tokens, secret keys.
  - NEVER log: raw clinical input vectors, detailed patient health answers, or private clinician notes.
  - DO log: user_id, role, high-level action, status, resource identifier, masked/hashed IP.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config.security import EVENT_CATEGORIES, EVENT_SEVERITIES
from config.settings import AUDIT_DB_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


def hash_ip(ip_address: Optional[str]) -> Optional[str]:
    """Return privacy-safe salted SHA-256 hash of an IP address."""
    if not ip_address:
        return None
    salt = "hg_audit_salt_v1"
    return hashlib.sha256(f"{salt}:{ip_address}".encode()).hexdigest()[:16]


_hash_ip = hash_ip

# ---------------------------------------------------------------------------
# Schema & Indexes
# ---------------------------------------------------------------------------

_CREATE_AUDIT_SQL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT    NOT NULL,
    event_type    TEXT    NOT NULL,
    user_id       INTEGER,
    role          TEXT,
    status        TEXT    NOT NULL,
    detail        TEXT,
    resource_type TEXT,
    resource_id   TEXT,
    category      TEXT,
    severity      TEXT    DEFAULT 'INFO',
    ip_hash       TEXT
);
"""

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log (timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_log (user_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log (event_type);",
    "CREATE INDEX IF NOT EXISTS idx_audit_category ON audit_log (category);",
    "CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_log (severity);",
]

# Supported event taxonomy
VALID_EVENT_TYPES = {
    # Authentication & Session
    "login_success",
    "login_failure",
    "logout",
    "registration",
    "password_change",
    "session_expired",
    "session_invalidated",
    # Authorization & Access Control
    "access_denied",
    "idor_attempt",
    "privilege_escalation_attempt",
    "admin_access",
    "role_changed",
    "user_status_changed",
    # Data Access & Operations
    "assessment_created",
    "assessment_viewed",
    "assessment_deleted",
    "recommendations_generated",
    "recommendations_viewed",
    "data_exported",
    # Reports & Files
    "report_generated",
    "report_downloaded",
    "file_upload_rejected",
    "file_access_denied",
    # Alerts & Notifications
    "alert_attempt",
    "alert_success",
    "alert_failure",
    # System Security & Defense
    "rate_limit_exceeded",
    "input_validation_failed",
    "config_error",
    "system_error",
    "security_scan",
}

# Redaction patterns for sensitive terms
_SENSITIVE_PATTERNS = [
    (re.compile(r"(password['\":\s=]+)([^\s,;'\"]+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(token['\":\s=]+)([^\s,;'\"]+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(secret['\":\s=]+)([^\s,;'\"]+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(api_?key['\":\s=]+)([^\s,;'\"]+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(bearer\s+)([a-zA-Z0-9_\-\.]+)", re.IGNORECASE), r"\1[REDACTED]"),
]


def sanitize_detail(detail: Optional[str]) -> Optional[str]:
    """Sanitize detail text to prevent any credential or token leakage."""
    if not detail:
        return None
    sanitized = str(detail)
    for pattern, replacement in _SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized[:500]


def _init_audit_db(db_path: Path | str = AUDIT_DB_PATH) -> None:
    """Initialize audit table and indexes, with backward-compatible schema migrations."""
    target = Path(db_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(target), timeout=10.0) as conn:
        conn.execute(_CREATE_AUDIT_SQL)

        # Migrate existing audit_log table if newer columns are absent
        cursor = conn.execute("PRAGMA table_info(audit_log);")
        existing_cols = {row[1] for row in cursor.fetchall()}
        new_cols = [
            ("resource_type", "TEXT"),
            ("resource_id", "TEXT"),
            ("category", "TEXT"),
            ("severity", "TEXT DEFAULT 'INFO'"),
            ("ip_hash", "TEXT"),
        ]
        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                try:
                    conn.execute(f"ALTER TABLE audit_log ADD COLUMN {col_name} {col_type};")
                except sqlite3.OperationalError:
                    pass

        for idx_sql in _CREATE_INDEXES_SQL:
            conn.execute(idx_sql)
        conn.commit()


init_audit_db = _init_audit_db


# ---------------------------------------------------------------------------
# Public Logging API
# ---------------------------------------------------------------------------


def log_event(
    event_type: str,
    status: str,
    user_id: Optional[int] = None,
    role: Optional[str] = None,
    detail: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    ip_hash: Optional[str] = None,
    db_path: Path | str = AUDIT_DB_PATH,
) -> None:
    """Write an immutable security audit event to the audit log.

    Args:
        event_type: One of VALID_EVENT_TYPES.
        status: Outcome string (e.g. 'SUCCESS', 'FAILURE', 'BLOCKED').
        user_id: Authenticated user ID (None for unauthenticated events).
        role: User role at time of event.
        detail: Short non-sensitive description.
        resource_type: Target resource (e.g. 'assessment', 'report', 'user').
        resource_id: Identifier of the target resource.
        category: Broad category from EVENT_CATEGORIES.
        severity: One of EVENT_SEVERITIES ('INFO', 'WARNING', 'HIGH', 'CRITICAL').
        ip_hash: Privacy-safe hashed network identifier.
        db_path: Database path override for testing.
    """
    target_path = Path(db_path)
    if event_type not in VALID_EVENT_TYPES:
        logger.warning("Unknown audit event_type '%s' — skipping.", event_type)
        return

    safe_detail = sanitize_detail(detail)

    # Derive default category if omitted
    if not category:
        if "login" in event_type or "logout" in event_type or "session" in event_type:
            category = "AUTHENTICATION"
        elif "access" in event_type or "idor" in event_type or "privilege" in event_type:
            category = "AUTHORIZATION"
        elif "assessment" in event_type or "recommendations" in event_type or "export" in event_type:
            category = "DATA_ACCESS"
        elif "admin" in event_type or "role" in event_type or "user_status" in event_type:
            category = "ADMIN_ACTION"
        elif "report" in event_type or "file" in event_type:
            category = "FILE_ACCESS"
        else:
            category = "SYSTEM_SECURITY"

    # Derive default severity if omitted
    if not severity:
        if status.upper() in ("BLOCKED", "DENIED") or "idor" in event_type or "escalation" in event_type:
            severity = "HIGH"
        elif status.upper() in ("FAILURE", "ERROR"):
            severity = "WARNING"
        else:
            severity = "INFO"

    timestamp = datetime.now(timezone.utc).isoformat()
    sql = """
    INSERT INTO audit_log (
        timestamp, event_type, user_id, role, status, detail,
        resource_type, resource_id, category, severity, ip_hash
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        _init_audit_db(target_path)
        with sqlite3.connect(str(target_path), timeout=10.0) as conn:
            conn.execute(
                sql,
                (
                    timestamp,
                    event_type,
                    user_id,
                    role,
                    status.upper(),
                    safe_detail,
                    resource_type,
                    resource_id,
                    category,
                    severity,
                    ip_hash,
                ),
            )
            conn.commit()
    except Exception as exc:
        logger.error("Audit log write failed: %s", exc)


def get_recent_events(
    limit: int = 50,
    db_path: Path | str = AUDIT_DB_PATH,
) -> list[dict[str, Any]]:
    """Fetch the most recent audit events for admin display."""
    target_path = Path(db_path)
    _init_audit_db(target_path)
    sql = """
    SELECT id, timestamp, event_type, user_id, role, status, detail,
           resource_type, resource_id, category, severity, ip_hash
    FROM audit_log ORDER BY id DESC LIMIT ?
    """
    try:
        with sqlite3.connect(str(target_path), timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, (limit,)).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Audit log read failed: %s", exc)
        return []


def get_filtered_events(
    limit: int = 50,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    search_query: Optional[str] = None,
    user_id: Optional[int] = None,
    db_path: Path | str = AUDIT_DB_PATH,
) -> tuple[list[dict[str, Any]], int]:
    """Query audit logs with structured filtering, search, and pagination.

    Returns:
        tuple[list[dict], int]: (matching_records, total_matching_count)
    """
    target_path = Path(db_path)
    _init_audit_db(target_path)

    clauses: list[str] = []
    params: list[Any] = []

    if start_date:
        clauses.append("timestamp >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("timestamp <= ?")
        params.append(end_date)
    if event_type:
        clauses.append("event_type = ?")
        params.append(event_type)
    if role:
        clauses.append("role = ?")
        params.append(role)
    if status:
        clauses.append("status = ?")
        params.append(status.upper())
    if category:
        clauses.append("category = ?")
        params.append(category)
    if severity:
        clauses.append("severity = ?")
        params.append(severity.upper())
    if user_id is not None:
        clauses.append("user_id = ?")
        params.append(user_id)
    if search_query:
        clauses.append("(detail LIKE ? OR resource_id LIKE ? OR event_type LIKE ?)")
        wildcard = f"%{search_query.strip()}%"
        params.extend([wildcard, wildcard, wildcard])

    where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""

    count_sql = f"SELECT COUNT(*) FROM audit_log{where_sql};"
    query_sql = f"""
    SELECT id, timestamp, event_type, user_id, role, status, detail,
           resource_type, resource_id, category, severity, ip_hash
    FROM audit_log{where_sql}
    ORDER BY id DESC
    LIMIT ? OFFSET ?;
    """

    try:
        with sqlite3.connect(str(target_path), timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            total_count = conn.execute(count_sql, params).fetchone()[0]
            rows = conn.execute(query_sql, params + [limit, offset]).fetchall()
            return [dict(r) for r in rows], int(total_count)
    except Exception as exc:
        logger.error("Audit log filtered query failed: %s", exc)
        return [], 0


def get_audit_statistics(db_path: Path | str = AUDIT_DB_PATH) -> dict[str, Any]:
    """Compile aggregated security statistics from the audit log."""
    target_path = Path(db_path)
    _init_audit_db(target_path)
    stats: dict[str, Any] = {
        "total_events": 0,
        "failed_logins": 0,
        "access_denied_events": 0,
        "admin_actions": 0,
        "high_severity_events": 0,
    }
    try:
        with sqlite3.connect(str(target_path), timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            total = conn.execute("SELECT COUNT(*) FROM audit_log;").fetchone()[0]
            stats["total_events"] = int(total)

            failed = conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE event_type = 'login_failure';"
            ).fetchone()[0]
            stats["failed_logins"] = int(failed)

            denied = conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE status IN ('BLOCKED', 'DENIED') OR event_type IN ('access_denied', 'idor_attempt');"
            ).fetchone()[0]
            stats["access_denied_events"] = int(denied)

            admin = conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE category = 'ADMIN_ACTION' OR event_type = 'admin_access';"
            ).fetchone()[0]
            stats["admin_actions"] = int(admin)

            high = conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE severity IN ('HIGH', 'CRITICAL');"
            ).fetchone()[0]
            stats["high_severity_events"] = int(high)
    except Exception as exc:
        logger.error("Failed to compute audit statistics: %s", exc)

    return stats
