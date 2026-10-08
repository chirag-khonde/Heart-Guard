"""Tests for Phase 17 Alert Analytics."""

from __future__ import annotations

import gc
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.analytics.alert_analytics import AlertAnalytics


@pytest.fixture
def temp_alerts_db():
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = Path(tmpdir) / "test_alerts.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE alerts (
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
        """)
        now = datetime.now(timezone.utc).isoformat()
        for i in range(10):
            status = "SUCCESS" if i < 7 else "FAILED"
            conn.execute(
                """INSERT INTO alerts
                   (assessment_id, timestamp, risk_score, risk_level,
                    recipient_type, recipient_masked, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f"alert-{i}", now, 85.0 + i, "CRITICAL", "doctor", "***1234", status),
            )
        conn.commit()
        conn.close()
        gc.collect()
        yield db_path
    finally:
        gc.collect()
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestAlertAnalytics:
    def test_get_alert_summary(self, temp_alerts_db):
        result = AlertAnalytics.get_alert_summary(db_path=temp_alerts_db)
        assert result["total_alerts"] == 10
        assert "by_status" in result
        assert result["by_status"]["SUCCESS"] == 7

    def test_get_alert_trend(self, temp_alerts_db):
        result = AlertAnalytics.get_alert_trend(db_path=temp_alerts_db)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_alert_success_rate(self, temp_alerts_db):
        result = AlertAnalytics.get_alert_success_rate(db_path=temp_alerts_db)
        assert result["total_alerts"] == 10
        assert result["successful"] == 7
        assert result["failed"] == 3
        assert result["success_rate"] == pytest.approx(7 / 10, abs=0.01)

    def test_get_alert_summary_with_date_range(self, temp_alerts_db):
        result = AlertAnalytics.get_alert_summary(date_range="7d", db_path=temp_alerts_db)
        assert "total_alerts" in result
