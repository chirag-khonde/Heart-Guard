"""Tests for Phase 17 Security Analytics."""

from __future__ import annotations

import gc
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.analytics.security_analytics import SecurityAnalytics


@pytest.fixture
def temp_audit_db():
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = Path(tmpdir) / "test_audit.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                user_id INTEGER,
                role TEXT,
                status TEXT NOT NULL,
                detail TEXT,
                resource_type TEXT,
                resource_id TEXT,
                category TEXT,
                severity TEXT DEFAULT 'INFO',
                ip_hash TEXT
            )
        """)
        now = datetime.now(timezone.utc).isoformat()
        events = [
            ("login", 1, "PATIENT", "SUCCESS", "INFO"),
            ("login", 2, "PATIENT", "FAILED", "WARNING"),
            ("authorization", 1, "PATIENT", "DENIED", "WARNING"),
            ("admin_access", 3, "ADMIN", "SUCCESS", "INFO"),
            ("logout", 1, "PATIENT", "SUCCESS", "INFO"),
        ]
        for i, (etype, uid, role, status, sev) in enumerate(events):
            conn.execute(
                """INSERT INTO audit_log
                   (timestamp, event_type, user_id, role, status, detail, severity)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (now, etype, uid, role, status, f"Event {i}", sev),
            )
        conn.commit()
        conn.close()
        gc.collect()
        yield db_path
    finally:
        gc.collect()
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestSecurityAnalytics:
    def test_get_security_summary(self, temp_audit_db):
        result = SecurityAnalytics.get_security_summary(db_path=temp_audit_db)
        assert result["total_events"] == 5
        assert result["failed_logins"] == 1
        assert result["authorization_failures"] == 1

    def test_get_security_event_trend(self, temp_audit_db):
        result = SecurityAnalytics.get_security_event_trend(db_path=temp_audit_db)
        assert isinstance(result, list)

    def test_get_login_analytics(self, temp_audit_db):
        result = SecurityAnalytics.get_login_analytics(db_path=temp_audit_db)
        assert result["total_login_attempts"] == 2
        assert result["successful_logins"] == 1
        assert result["failed_logins"] == 1
        assert result["success_rate"] == pytest.approx(0.5, abs=0.01)

    def test_get_security_summary_with_date_range(self, temp_audit_db):
        result = SecurityAnalytics.get_security_summary(date_range="7d", db_path=temp_audit_db)
        assert "total_events" in result
