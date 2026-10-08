"""Data models and database initialization for Patient Assessment History (Phase 10).

Defines the Assessment domain entity, serialization helpers, and SQLite schema.
Uses parameterized statements exclusively to prevent SQL injection.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Any

from config.settings import ASSESSMENTS_DB_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)

_CREATE_ASSESSMENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS assessments (
    id                         INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id              TEXT    NOT NULL UNIQUE,
    user_id                    INTEGER NOT NULL,
    created_at                 TEXT    NOT NULL,
    clinical_risk              REAL    NOT NULL,
    lifestyle_risk             REAL    NOT NULL,
    overall_risk               REAL    NOT NULL,
    risk_category              TEXT    NOT NULL,
    recommendation             TEXT    NOT NULL,
    model_version              TEXT    NOT NULL,
    narrative_summary          TEXT,
    alert_status               TEXT    NOT NULL DEFAULT 'NOT_TRIGGERED',
    top_clinical_factors_json  TEXT,
    lifestyle_factors_json     TEXT,
    clinical_data_json         TEXT
);
"""

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_assessments_user ON assessments (user_id, created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_assessments_aid ON assessments (assessment_id);",
]


@dataclass
class Assessment:
    """Represents a single completed HeartGuard multimodal assessment."""

    assessment_id: str
    user_id: int
    created_at: str
    clinical_risk: float
    lifestyle_risk: float
    overall_risk: float
    risk_category: str
    recommendation: str
    model_version: str
    narrative_summary: str
    alert_status: str
    top_clinical_factors_json: str | None = None
    lifestyle_factors_json: str | None = None
    clinical_data_json: str | None = None
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize assessment record to dictionary."""
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "clinical_risk": self.clinical_risk,
            "lifestyle_risk": self.lifestyle_risk,
            "overall_risk": self.overall_risk,
            "risk_category": self.risk_category,
            "recommendation": self.recommendation,
            "model_version": self.model_version,
            "narrative_summary": self.narrative_summary,
            "alert_status": self.alert_status,
            "top_clinical_factors": self.get_top_clinical_factors(),
            "lifestyle_factors": self.get_lifestyle_factors(),
            "clinical_data": self.get_clinical_data(),
        }

    def get_top_clinical_factors(self) -> list[dict[str, Any]]:
        """Parse stored top clinical SHAP drivers safely."""
        if not self.top_clinical_factors_json:
            return []
        try:
            parsed = json.loads(self.top_clinical_factors_json)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    def get_lifestyle_factors(self) -> list[dict[str, Any]]:
        """Parse stored lifestyle factor summary safely."""
        if not self.lifestyle_factors_json:
            return []
        try:
            parsed = json.loads(self.lifestyle_factors_json)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    def get_clinical_data(self) -> dict[str, Any]:
        """Parse stored clinical inputs safely."""
        if not self.clinical_data_json:
            return {}
        try:
            parsed = json.loads(self.clinical_data_json)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}


def init_assessment_db(db_path: Path | None = None) -> None:
    """Initialize the assessments table and indexes if not present.

    Args:
        db_path: Optional path override (used for test isolation).
    """
    target = Path(db_path) if db_path is not None else ASSESSMENTS_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(target), timeout=10.0) as conn:
        conn.execute(_CREATE_ASSESSMENTS_TABLE_SQL)
        for idx_sql in _CREATE_INDEXES_SQL:
            conn.execute(idx_sql)
        conn.commit()
    logger.debug("Assessment database initialized at %s", target)
