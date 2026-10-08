"""Tests for Phase 17 Risk Distribution Analytics."""

from __future__ import annotations

import gc
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.analytics.risk_analytics import RiskAnalytics


@pytest.fixture
def temp_db():
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = Path(tmpdir) / "test_risk.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                clinical_risk REAL NOT NULL,
                lifestyle_risk REAL NOT NULL,
                overall_risk REAL NOT NULL,
                risk_category TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                model_version TEXT NOT NULL,
                narrative_summary TEXT,
                alert_status TEXT NOT NULL DEFAULT 'NOT_TRIGGERED',
                top_clinical_factors_json TEXT,
                lifestyle_factors_json TEXT,
                clinical_data_json TEXT
            )
        """)
        now = datetime.now(timezone.utc).isoformat()
        data = [
            ("a1", 1, now, 30.0, 20.0, 27.0, "Low", "Monitor", "v1"),
            ("a2", 1, now, 45.0, 25.0, 39.0, "Low", "Monitor", "v1"),
            ("a3", 2, now, 55.0, 30.0, 48.5, "Low", "Monitor", "v1"),
            ("a4", 2, now, 65.0, 35.0, 56.0, "Elevated", "Review", "v1"),
            ("a5", 3, now, 75.0, 40.0, 64.5, "Elevated", "Review", "v1"),
            ("a6", 3, now, 85.0, 45.0, 73.0, "High", "Appointment", "v1"),
        ]
        for row in data:
            conn.execute(
                """INSERT INTO assessments
                   (assessment_id, user_id, created_at, clinical_risk, lifestyle_risk,
                    overall_risk, risk_category, recommendation, model_version,
                    narrative_summary, alert_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (*row, "", "NOT_TRIGGERED"),
            )
        conn.commit()
        conn.close()
        gc.collect()
        yield db_path
    finally:
        gc.collect()
        shutil.rmtree(tmpdir, ignore_errors=True)


def _create_empty_risk_db(tmpdir: str) -> Path:
    db_path = Path(tmpdir) / "empty.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            clinical_risk REAL NOT NULL,
            lifestyle_risk REAL NOT NULL,
            overall_risk REAL NOT NULL,
            risk_category TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            model_version TEXT NOT NULL,
            narrative_summary TEXT,
            alert_status TEXT NOT NULL DEFAULT 'NOT_TRIGGERED',
            top_clinical_factors_json TEXT,
            lifestyle_factors_json TEXT,
            clinical_data_json TEXT
        )
    """)
    conn.commit()
    conn.close()
    return db_path


class TestRiskAnalytics:
    def test_get_risk_distribution(self, temp_db):
        result = RiskAnalytics.get_risk_distribution(db_path=temp_db)
        assert result["total"] == 6
        assert "categories" in result
        assert "Low" in result["categories"]

    def test_get_risk_distribution_with_user_filter(self, temp_db):
        result = RiskAnalytics.get_risk_distribution(user_id=1, db_path=temp_db)
        assert result["total"] == 2

    def test_get_risk_trend_over_time(self, temp_db):
        result = RiskAnalytics.get_risk_trend_over_time(interval="daily", db_path=temp_db)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_risk_statistics(self, temp_db):
        result = RiskAnalytics.get_risk_statistics(db_path=temp_db)
        assert result["total"] == 6
        assert result["mean_risk"] > 0

    def test_get_risk_statistics_empty(self):
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = _create_empty_risk_db(tmpdir)
            gc.collect()
            result = RiskAnalytics.get_risk_statistics(db_path=db_path)
            assert result["total"] == 0
        finally:
            gc.collect()
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_get_category_transitions(self, temp_db):
        result = RiskAnalytics.get_category_transitions(db_path=temp_db)
        assert isinstance(result, list)
