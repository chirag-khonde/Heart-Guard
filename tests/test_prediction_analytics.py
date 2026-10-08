"""Tests for Phase 17 Prediction Analytics."""

from __future__ import annotations

import gc
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.analytics.prediction_analytics import PredictionAnalytics


@pytest.fixture
def temp_assessments_db():
    """Create a temporary assessments database with test data."""
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = Path(tmpdir) / "test_assessments.db"
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
        for i in range(20):
            risk = 30.0 + (i * 3.0)
            category = "Low" if risk < 60 else ("Elevated" if risk < 75 else "High")
            alert = "SUCCESS" if risk > 85 else "NOT_TRIGGERED"
            conn.execute(
                """INSERT INTO assessments
                   (assessment_id, user_id, created_at, clinical_risk, lifestyle_risk,
                    overall_risk, risk_category, recommendation, model_version,
                    narrative_summary, alert_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"test-{i:04d}", i % 3 + 1, now, risk * 0.7, risk * 0.3, risk,
                 category, "Monitor", "HeartGuard-ML (v1.0.0)", "Test", alert),
            )
        conn.commit()
        conn.close()
        gc.collect()
        yield db_path
    finally:
        gc.collect()
        shutil.rmtree(tmpdir, ignore_errors=True)


def _create_empty_assessments_db(tmpdir: str, filename: str = "empty.db") -> Path:
    db_path = Path(tmpdir) / filename
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


class TestPredictionAnalytics:
    """Test suite for PredictionAnalytics."""

    def test_get_prediction_summary(self, temp_assessments_db):
        result = PredictionAnalytics.get_prediction_summary(db_path=temp_assessments_db)
        assert result["total_predictions"] == 20
        assert result["unique_patients"] == 3
        assert "risk_category_distribution" in result
        assert "model_version_distribution" in result

    def test_get_prediction_summary_empty_db(self):
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = _create_empty_assessments_db(tmpdir)
            gc.collect()
            result = PredictionAnalytics.get_prediction_summary(db_path=db_path)
            assert result["total_predictions"] == 0
        finally:
            gc.collect()
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_get_prediction_summary_with_date_range(self, temp_assessments_db):
        result = PredictionAnalytics.get_prediction_summary(
            date_range="7d", db_path=temp_assessments_db
        )
        assert "total_predictions" in result

    def test_get_prediction_trend(self, temp_assessments_db):
        result = PredictionAnalytics.get_prediction_trend(
            interval="daily", db_path=temp_assessments_db
        )
        assert isinstance(result, list)

    def test_get_model_version_analytics(self, temp_assessments_db):
        result = PredictionAnalytics.get_model_version_analytics(db_path=temp_assessments_db)
        assert isinstance(result, list)
        if result:
            assert "model_version" in result[0]
            assert "prediction_count" in result[0]

    def test_get_prediction_distribution(self, temp_assessments_db):
        result = PredictionAnalytics.get_prediction_distribution(db_path=temp_assessments_db)
        assert isinstance(result, dict)
        assert len(result) > 0
