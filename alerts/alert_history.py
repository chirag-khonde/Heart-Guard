"""Alert History and Deduplication Repository for HeartGuard.

Stores alert audit metadata in a local SQLite database (data/alerts/alerts.db)
with deduplication and idempotency key checks (assessment_id + recipient_type).
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
from typing import Any

from config.settings import DATA_DIRECTORY
from src.alerts.alert_validation import mask_phone_number
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default alerts database path
ALERTS_DIR = DATA_DIRECTORY / "alerts"
DB_PATH = ALERTS_DIR / "alerts.db"


def _get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Ensure database directory exists and return a SQLite connection."""
    target_path = db_path if db_path is not None else DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_alert_db(db_path: Path | None = None) -> None:
    """Initialize the alerts database table and indexes if not present."""
    target_path = db_path if db_path is not None else DB_PATH
    with _get_connection(target_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                recipient_type TEXT NOT NULL,
                recipient_masked TEXT NOT NULL,
                status TEXT NOT NULL,
                message_sid TEXT,
                error_message TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assessment_id ON alerts (assessment_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON alerts (timestamp)")
        conn.commit()


def record_alert(
    assessment_id: str,
    risk_score: float,
    risk_level: str,
    recipient_type: str,
    recipient_phone: str,
    status: str,
    message_sid: str | None = None,
    error_message: str | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Record an alert event into the persistent audit repository.

    Args:
        assessment_id: Unique identifier for the multimodal risk assessment.
        risk_score: Overall risk score (0 - 100).
        risk_level: Risk level category string (e.g., 'CRITICAL').
        recipient_type: Type of recipient ('doctor', 'emergency_contact', or 'test').
        recipient_phone: Phone number (automatically masked before persistence).
        status: Delivery status ('SUCCESS', 'FAILED', 'DISABLED', 'SIMULATED').
        message_sid: Twilio Message SID if available.
        error_message: Error details if delivery failed.
        db_path: SQLite DB file path.

    Returns:
        dict: The persisted record dictionary.
    """
    target_path = db_path if db_path is not None else DB_PATH
    init_alert_db(target_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    masked_phone = mask_phone_number(recipient_phone)

    with _get_connection(target_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO alerts (
                assessment_id, timestamp, risk_score, risk_level,
                recipient_type, recipient_masked, status, message_sid, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assessment_id,
                now_iso,
                float(risk_score),
                risk_level,
                recipient_type,
                masked_phone,
                status,
                message_sid,
                error_message,
            ),
        )
        record_id = cursor.lastrowid
        conn.commit()

    logger.info(
        "Alert recorded: id=%s, assessment_id=%s, type=%s, status=%s",
        record_id,
        assessment_id,
        recipient_type,
        status,
    )

    return {
        "id": record_id,
        "assessment_id": assessment_id,
        "timestamp": now_iso,
        "risk_score": float(risk_score),
        "risk_level": risk_level,
        "recipient_type": recipient_type,
        "recipient_masked": masked_phone,
        "status": status,
        "message_sid": message_sid,
        "error_message": error_message,
    }


def is_alert_already_sent(
    assessment_id: str,
    recipient_type: str,
    db_path: Path | None = None,
) -> bool:
    """Check whether a successful alert was already dispatched for assessment and recipient.

    Acts as an idempotency guard preventing duplicate SMS transmissions.

    Args:
        assessment_id: Unique assessment identifier.
        recipient_type: 'doctor' or 'emergency_contact'.
        db_path: SQLite DB file path.

    Returns:
        bool: True if already sent successfully.
    """
    target_path = db_path if db_path is not None else DB_PATH
    init_alert_db(target_path)
    with _get_connection(target_path) as conn:
        cursor = conn.execute(
            """
            SELECT 1 FROM alerts
            WHERE assessment_id = ? AND recipient_type = ? AND status = 'SUCCESS'
            LIMIT 1
            """,
            (assessment_id, recipient_type),
        )
        return cursor.fetchone() is not None


def get_alert_history(limit: int = 50, db_path: Path | None = None) -> list[dict[str, Any]]:
    """Retrieve recent alert audit history records.

    Args:
        limit: Maximum number of rows to return (default: 50).
        db_path: SQLite DB path.

    Returns:
        list[dict]: List of alert record dictionaries sorted by timestamp desc.
    """
    target_path = db_path if db_path is not None else DB_PATH
    init_alert_db(target_path)
    with _get_connection(target_path) as conn:
        cursor = conn.execute(
            """
            SELECT id, assessment_id, timestamp, risk_score, risk_level,
                   recipient_type, recipient_masked, status, message_sid, error_message
            FROM alerts
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def clear_alert_history(db_path: Path | None = None) -> None:
    """Clear all records from alerts table (used for test setup/teardown)."""
    target_path = db_path if db_path is not None else DB_PATH
    init_alert_db(target_path)
    with _get_connection(target_path) as conn:
        conn.execute("DELETE FROM alerts")
        conn.commit()
