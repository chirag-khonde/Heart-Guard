"""Tests for Phase 17 Data Quality Monitoring."""

from __future__ import annotations

import gc
import json
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.analytics.data_quality_monitoring import DataQualityMonitor


@pytest.fixture
def temp_db_with_data():
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = Path(tmpdir) / "test_dq.db"
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
        for i in range(15):
            clinical = json.dumps({
                "age": 50 + i,
                "resting_bp": 120 + i,
                "cholesterol": 200 + i,
                "max_heart_rate": 150 - i,
                "st_depression": 1.0 + i * 0.1,
                "num_major_vessels": i % 4,
                "sex": str(i % 2),
                "chest_pain_type": str(i % 4),
                "fasting_blood_sugar": str(i % 2),
                "resting_ecg": str(i % 3),
                "exercise_angina": str(i % 2),
            })
            conn.execute(
                """INSERT INTO assessments
                   (assessment_id, user_id, created_at, clinical_risk, lifestyle_risk,
                    overall_risk, risk_category, recommendation, model_version,
                    narrative_summary, alert_status, clinical_data_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"dq-{i:04d}", i % 3 + 1, now, 50.0, 30.0, 44.0,
                 "Low", "Monitor", "v1", "Test", "NOT_TRIGGERED", clinical),
            )
        conn.commit()
        conn.close()
        gc.collect()
        yield db_path
    finally:
        gc.collect()
        shutil.rmtree(tmpdir, ignore_errors=True)


def _create_dq_db(tmpdir: str, rows: int = 1) -> Path:
    db_path = Path(tmpdir) / "small.db"
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
    for i in range(rows):
        conn.execute(
            """INSERT INTO assessments
               (assessment_id, user_id, created_at, clinical_risk, lifestyle_risk,
                overall_risk, risk_category, recommendation, model_version,
                narrative_summary, alert_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f"small-{i}", 1, "2024-01-01", 50.0, 30.0, 44.0, "Low", "Monitor", "v1", "Test", "NOT_TRIGGERED"),
        )
    conn.commit()
    conn.close()
    return db_path


class TestDataQualityMonitor:
    def test_assess_data_quality(self, temp_db_with_data):
        result = DataQualityMonitor.assess_data_quality(db_path=temp_db_with_data)
        assert result["total_records"] == 15
        assert result["status"] in ("HEALTHY", "WARNING", "DEGRADED")

    def test_assess_data_quality_insufficient(self):
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = _create_dq_db(tmpdir, rows=1)
            gc.collect()
            result = DataQualityMonitor.assess_data_quality(db_path=db_path)
            assert result["status"] == "INSUFFICIENT_DATA"
        finally:
            gc.collect()
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_missing_analysis(self, temp_db_with_data):
        result = DataQualityMonitor.assess_data_quality(db_path=temp_db_with_data)
        missing = result.get("missing_analysis", {})
        assert "per_feature" in missing
        assert "max_missing_rate" in missing

    def test_schema_analysis(self, temp_db_with_data):
        result = DataQualityMonitor.assess_data_quality(db_path=temp_db_with_data)
        schema = result.get("schema_analysis", {})
        assert "schema_status" in schema

    def test_get_schema_snapshot(self, temp_db_with_data):
        result = DataQualityMonitor.get_schema_snapshot(db_path=temp_db_with_data)
        assert result["table"] == "assessments"
        assert result["column_count"] > 0
