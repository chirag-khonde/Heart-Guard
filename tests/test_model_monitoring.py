"""Tests for Phase 17 Model Monitoring."""

from __future__ import annotations

import gc
import json
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.analytics.model_monitoring import ModelMonitoringService


@pytest.fixture
def temp_eval_db():
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = Path(tmpdir) / "test_eval.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE evaluation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL DEFAULT 'v1',
                dataset_version TEXT NOT NULL DEFAULT 'cleveland_v1',
                evaluation_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'RUNNING',
                metrics_json TEXT,
                confusion_matrix_json TEXT,
                cv_results_json TEXT,
                threshold_analysis_json TEXT,
                feature_importance_json TEXT,
                calibration_json TEXT,
                error_analysis_json TEXT,
                nlp_evaluation_json TEXT,
                multimodal_evaluation_json TEXT,
                notes TEXT,
                evaluation_version TEXT DEFAULT '1.0.0'
            )
        """)
        now = datetime.now(timezone.utc).isoformat()
        metrics = json.dumps({
            "accuracy": 0.75, "precision": 0.80, "recall": 0.70,
            "f1": 0.75, "roc_auc": 0.82, "pr_auc": 0.78
        })
        conn.execute(
            """INSERT INTO evaluation_runs
               (run_id, model_name, model_version, evaluation_date, status, metrics_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("eval-001", "random_forest", "v1", now, "COMPLETED", metrics),
        )
        conn.execute(
            """INSERT INTO evaluation_runs
               (run_id, model_name, model_version, evaluation_date, status, metrics_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("eval-002", "logistic_regression", "v1", now, "COMPLETED", metrics),
        )
        conn.commit()
        conn.close()
        gc.collect()
        yield db_path
    finally:
        gc.collect()
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestModelMonitoringService:
    def test_get_model_performance_history(self, temp_eval_db):
        result = ModelMonitoringService.get_model_performance_history(db_path=temp_eval_db)
        assert len(result) == 2

    def test_get_model_performance_history_filtered(self, temp_eval_db):
        result = ModelMonitoringService.get_model_performance_history(
            model_name="random_forest", db_path=temp_eval_db
        )
        assert len(result) == 1
        assert result[0]["model_name"] == "random_forest"

    def test_get_latest_metrics(self, temp_eval_db):
        result = ModelMonitoringService.get_latest_metrics(db_path=temp_eval_db)
        assert result is not None
        assert result.get("accuracy") == 0.75
        assert result.get("f1") == 0.75

    def test_get_latest_metrics_empty(self):
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "empty_eval.db"
            gc.collect()
            result = ModelMonitoringService.get_latest_metrics(db_path=db_path)
            assert result is None
        finally:
            gc.collect()
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_get_model_comparison(self, temp_eval_db):
        result = ModelMonitoringService.get_model_comparison(db_path=temp_eval_db)
        assert len(result) == 2
        names = {m["model_name"] for m in result}
        assert "random_forest" in names
        assert "logistic_regression" in names

    def test_get_metric_history(self, temp_eval_db):
        result = ModelMonitoringService.get_metric_history(
            "random_forest", "accuracy", db_path=temp_eval_db
        )
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["value"] == 0.75

    def test_get_model_status_summary(self):
        result = ModelMonitoringService.get_model_status_summary()
        assert "best_model" in result
        assert "models" in result
        assert "total_loaded" in result
