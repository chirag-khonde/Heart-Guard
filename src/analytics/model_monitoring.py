"""Model Monitoring Service (Phase 17).

Integrates with Phase 14 evaluation results to track model performance metrics
over time: accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix.
Provides model status tracking and comparison capabilities.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import EVALUATION_DB_PATH, MODEL_DIRECTORY, REPORT_DIRECTORY
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Model status constants
MODEL_PRODUCTION = "PRODUCTION"
MODEL_VALIDATION = "VALIDATION"
MODEL_RETIRED = "RETIRED"
MODEL_UNKNOWN = "UNKNOWN"


def _get_evaluation_connection(db_path: Path | None = None) -> sqlite3.Connection:
    target = db_path or EVALUATION_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class ModelMonitoringService:
    """Service for monitoring model performance and status."""

    @staticmethod
    def get_model_performance_history(
        model_name: str | None = None,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Get model evaluation history with metrics."""
        conn = _get_evaluation_connection(db_path)
        try:
            if model_name:
                rows = conn.execute(
                    """SELECT * FROM evaluation_runs WHERE model_name = ? AND status = 'COMPLETED'
                       ORDER BY evaluation_date DESC""",
                    (model_name,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM evaluation_runs WHERE status = 'COMPLETED'
                       ORDER BY evaluation_date DESC"""
                ).fetchall()

            results = []
            for row in rows:
                d = dict(row)
                for field_name in ("metrics_json", "confusion_matrix_json", "cv_results_json",
                                   "threshold_analysis_json", "feature_importance_json",
                                   "calibration_json", "error_analysis_json"):
                    if d.get(field_name):
                        try:
                            d[field_name] = json.loads(d[field_name])
                        except Exception:
                            d[field_name] = {}
                results.append(d)
            return results
        finally:
            conn.close()

    @staticmethod
    def get_latest_metrics(
        model_name: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any] | None:
        """Get the most recent evaluation metrics for a model."""
        try:
            history = ModelMonitoringService.get_model_performance_history(model_name, db_path)
        except Exception:
            return None
        if not history:
            return None

        latest = history[0]
        metrics = latest.get("metrics_json", {})
        if not isinstance(metrics, dict):
            metrics = {}
        confusion = latest.get("confusion_matrix_json", {})
        return {
            "model_name": latest.get("model_name"),
            "model_version": latest.get("model_version"),
            "evaluation_date": latest.get("evaluation_date"),
            "run_id": latest.get("run_id"),
            "accuracy": metrics.get("accuracy"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
            "f1": metrics.get("f1"),
            "roc_auc": metrics.get("roc_auc"),
            "pr_auc": metrics.get("pr_auc"),
            "specificity": metrics.get("specificity"),
            "balanced_accuracy": metrics.get("balanced_accuracy"),
            "brier_score": metrics.get("brier_score"),
            "confusion_matrix": latest.get("confusion_matrix_json"),
            "cv_results": latest.get("cv_results_json"),
        }

    @staticmethod
    def get_model_comparison(
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Compare metrics across all evaluated models."""
        history = ModelMonitoringService.get_model_performance_history(db_path=db_path)

        model_metrics: dict[str, dict[str, Any]] = {}
        for run in history:
            name = run.get("model_name", "unknown")
            if name not in model_metrics:
                metrics = run.get("metrics_json", {})
                if not isinstance(metrics, dict):
                    metrics = {}
                model_metrics[name] = {
                    "model_name": name,
                    "model_version": run.get("model_version"),
                    "accuracy": metrics.get("accuracy"),
                    "precision": metrics.get("precision"),
                    "recall": metrics.get("recall"),
                    "f1": metrics.get("f1"),
                    "roc_auc": metrics.get("roc_auc"),
                    "pr_auc": metrics.get("pr_auc"),
                    "evaluation_date": run.get("evaluation_date"),
                }

        return list(model_metrics.values())

    @staticmethod
    def get_metric_history(
        model_name: str,
        metric_name: str,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Get history of a specific metric for a model over evaluations."""
        history = ModelMonitoringService.get_model_performance_history(model_name, db_path)
        result = []
        for run in history:
            metrics = run.get("metrics_json", {})
            if not isinstance(metrics, dict):
                metrics = {}
            value = metrics.get(metric_name)
            if value is not None:
                result.append({
                    "evaluation_date": run.get("evaluation_date"),
                    "run_id": run.get("run_id"),
                    "metric_name": metric_name,
                    "value": value,
                })
        return result

    @staticmethod
    def get_model_status_summary() -> dict[str, Any]:
        """Get current model status from best_model.json and model_metadata.json."""
        best_model_path = REPORT_DIRECTORY / "best_model.json"
        metadata_path = MODEL_DIRECTORY / "model_metadata.json"
        manifest_path = MODEL_DIRECTORY / "model_manifest.json"

        result = {
            "best_model": None,
            "models": {},
            "total_loaded": 0,
            "status": MODEL_UNKNOWN,
        }

        try:
            if best_model_path.exists():
                best_data = json.loads(best_model_path.read_text(encoding="utf-8"))
                result["best_model"] = best_data.get("best_model")
                result["best_model_cv_auc"] = best_data.get("cv_roc_auc")
        except Exception:
            pass

        try:
            if metadata_path.exists():
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                for model_name, model_data in metadata.get("models", {}).items():
                    cv_metrics = model_data.get("cv_metrics", {})
                    test_metrics = model_data.get("test_metrics", {})
                    result["models"][model_name] = {
                        "status": MODEL_PRODUCTION if model_name == result.get("best_model") else MODEL_VALIDATION,
                        "cv_roc_auc": cv_metrics.get("roc_auc"),
                        "test_roc_auc": test_metrics.get("roc_auc"),
                        "test_f1": test_metrics.get("f1"),
                        "n_features": model_data.get("n_features"),
                    }
                    result["total_loaded"] += 1
        except Exception:
            pass

        try:
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                result["integrity_verified"] = len(manifest.get("models", {})) > 0
        except Exception:
            pass

        return result

    @staticmethod
    def get_model_feature_importance(
        model_name: str | None = None,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Get feature importance from the most recent evaluation."""
        history = ModelMonitoringService.get_model_performance_history(model_name, db_path)
        for run in history:
            fi = run.get("feature_importance")
            if fi and isinstance(fi, list) and len(fi) > 0:
                return fi
        return []

    @staticmethod
    def get_cv_results(
        model_name: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Get cross-validation results from most recent evaluation."""
        history = ModelMonitoringService.get_model_performance_history(model_name, db_path)
        for run in history:
            cv = run.get("cv_results")
            if cv and isinstance(cv, dict):
                return cv
        return {}
