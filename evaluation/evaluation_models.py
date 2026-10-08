"""HeartGuard evaluation models — SQLite schema and dataclasses (Phase 14)."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import EVALUATION_DB_PATH


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_evaluation_db(db_path: Path | None = None) -> None:
    """Idempotently create the evaluation_runs table."""
    target = db_path or EVALUATION_DB_PATH
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id           TEXT    NOT NULL UNIQUE,
                model_name       TEXT    NOT NULL,
                model_version    TEXT    NOT NULL DEFAULT 'v1',
                dataset_version  TEXT    NOT NULL DEFAULT 'cleveland_v1',
                evaluation_date  TEXT    NOT NULL,
                status           TEXT    NOT NULL DEFAULT 'RUNNING',
                metrics_json                TEXT,
                confusion_matrix_json       TEXT,
                cv_results_json             TEXT,
                threshold_analysis_json     TEXT,
                feature_importance_json     TEXT,
                calibration_json            TEXT,
                error_analysis_json         TEXT,
                nlp_evaluation_json         TEXT,
                multimodal_evaluation_json  TEXT,
                notes            TEXT,
                evaluation_version TEXT   DEFAULT '1.0.0'
            )
        """)
        conn.commit()
    finally:
        conn.close()


def new_run_id() -> str:
    return f"eval-{uuid.uuid4().hex[:12]}"


@dataclass
class EvaluationRun:
    """Represents a single model evaluation run."""

    model_name: str
    model_version: str = "v1"
    dataset_version: str = "cleveland_v1"
    run_id: str = field(default_factory=new_run_id)
    evaluation_date: str = field(default_factory=_iso_now)
    status: str = "COMPLETED"
    metrics: dict[str, Any] = field(default_factory=dict)
    confusion_matrix: dict[str, Any] = field(default_factory=dict)
    cv_results: dict[str, Any] = field(default_factory=dict)
    threshold_analysis: list[dict] = field(default_factory=list)
    feature_importance: list[dict] = field(default_factory=list)
    calibration: dict[str, Any] = field(default_factory=dict)
    error_analysis: dict[str, Any] = field(default_factory=dict)
    nlp_evaluation: dict[str, Any] = field(default_factory=dict)
    multimodal_evaluation: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    evaluation_version: str = "1.0.0"
