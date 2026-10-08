"""Tests for Phase 17 Explainability Analytics."""

from __future__ import annotations

import gc
import json
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.analytics.explainability_analytics import ExplainabilityAnalytics


@pytest.fixture
def temp_shap_db():
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = Path(tmpdir) / "test_shap.db"
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
        factors1 = json.dumps([
            {"feature": "age", "shap_value": 0.15},
            {"feature": "cholesterol", "shap_value": 0.10},
            {"feature": "max_heart_rate", "shap_value": -0.05},
        ])
        factors2 = json.dumps([
            {"feature": "age", "shap_value": 0.12},
            {"feature": "resting_bp", "shap_value": 0.08},
        ])
        for i in range(5):
            conn.execute(
                """INSERT INTO assessments
                   (assessment_id, user_id, created_at, clinical_risk, lifestyle_risk,
                    overall_risk, risk_category, recommendation, model_version,
                    narrative_summary, alert_status, top_clinical_factors_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"shap-{i}", i + 1, now, 50.0, 30.0, 44.0, "Low", "Monitor", "v1",
                 "Test", "NOT_TRIGGERED", factors1 if i % 2 == 0 else factors2),
            )
        conn.commit()
        conn.close()
        gc.collect()
        yield db_path
    finally:
        gc.collect()
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestExplainabilityAnalytics:
    def test_get_feature_importance_summary(self, temp_shap_db):
        result = ExplainabilityAnalytics.get_feature_importance_summary(db_path=temp_shap_db)
        assert result["total_assessments_with_shap"] == 5
        assert len(result["features"]) > 0
        assert result["features"][0]["frequency"] > 0

    def test_get_feature_importance_summary_empty(self):
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "empty_shap.db"
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
            gc.collect()
            result = ExplainabilityAnalytics.get_feature_importance_summary(db_path=db_path)
            assert result["total_assessments_with_shap"] == 0
        finally:
            gc.collect()
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_get_shap_value_distribution(self, temp_shap_db):
        result = ExplainabilityAnalytics.get_shap_value_distribution("age", db_path=temp_shap_db)
        assert result["count"] > 0
        assert result["mean"] > 0

    def test_get_shap_value_distribution_unknown_feature(self, temp_shap_db):
        result = ExplainabilityAnalytics.get_shap_value_distribution("unknown", db_path=temp_shap_db)
        assert result["count"] == 0
