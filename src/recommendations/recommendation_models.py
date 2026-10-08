"""Data models, constants, and SQLite schema for HeartGuard AI Recommendations (Phase 13).

Defines:
  - Recommendation domain entity and priorities (HIGH, MEDIUM, LOW, INFO)
  - AssessmentInsights container model
  - Database table initialization for separate recommendations storage
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sqlite3
from typing import Any, Optional

from config.settings import RECOMMENDATIONS_DB_PATH, RECOMMENDATION_ENGINE_VERSION
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Priority controlled vocabulary
PRIORITY_HIGH = "HIGH"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_LOW = "LOW"
PRIORITY_INFO = "INFO"

PRIORITIES: list[str] = [
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
    PRIORITY_INFO,
]

PRIORITY_ORDER: dict[str, int] = {p: i for i, p in enumerate(PRIORITIES)}

# Standard disclaimer
RECOMMENDATION_DISCLAIMER = (
    "HeartGuard AI-generated insights and recommendations are informational estimates "
    "and do not constitute a medical diagnosis, prescription, or clinical treatment plan. "
    "Always consult a qualified healthcare professional before making health-related changes."
)

_CREATE_RECOMMENDATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS recommendations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id TEXT    NOT NULL UNIQUE,
    assessment_id     TEXT    NOT NULL,
    user_id           INTEGER NOT NULL,
    category          TEXT    NOT NULL,
    title             TEXT    NOT NULL,
    description       TEXT    NOT NULL,
    priority          TEXT    NOT NULL,
    source            TEXT    NOT NULL,
    rule_id           TEXT    NOT NULL,
    version           TEXT    NOT NULL,
    created_at        TEXT    NOT NULL
);
"""

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_recs_user ON recommendations (user_id, created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_recs_aid ON recommendations (assessment_id);",
]


@dataclass
class Recommendation:
    """Represents an individual personalized non-diagnostic recommendation."""

    assessment_id: str = ""
    category: str = ""
    title: str = ""
    description: str = ""
    priority: str = "INFO"
    source: str = "Rule Engine"
    rule_id: str = ""
    version: str = RECOMMENDATION_ENGINE_VERSION
    user_id: int = 1
    recommendation_id: str = ""
    created_at: str = ""
    id: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.recommendation_id:
            import uuid
            self.recommendation_id = uuid.uuid4().hex[:12]
        if not self.created_at:
            from datetime import datetime, timezone
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize recommendation to dictionary."""
        return asdict(self)


@dataclass
class AssessmentInsights:
    """Consolidated AI insights and recommendations for an assessment."""

    assessment_id: str
    summary_text: str
    top_factors: list[dict[str, Any]]
    comparison_summary: Optional[str]
    recommendations: list[Recommendation]
    disclaimer: str = RECOMMENDATION_DISCLAIMER
    version: str = RECOMMENDATION_ENGINE_VERSION
    comparison: Optional[dict[str, Any]] = None

    @property
    def trend_summary(self) -> str:
        return self.comparison_summary or ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize insights object to dictionary."""
        return {
            "assessment_id": self.assessment_id,
            "summary_text": self.summary_text,
            "top_factors": self.top_factors,
            "comparison_summary": self.comparison_summary,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "disclaimer": self.disclaimer,
            "version": self.version,
            "comparison": self.comparison,
        }


def init_recommendation_db(db_path: Optional[Path] = None) -> None:
    """Initialize the recommendations database and schema if needed."""
    target = Path(db_path) if db_path is not None else RECOMMENDATIONS_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(target), timeout=10.0) as conn:
        conn.execute(_CREATE_RECOMMENDATIONS_TABLE_SQL)
        for idx in _CREATE_INDEXES_SQL:
            conn.execute(idx)
        conn.commit()
    logger.debug("Recommendations database initialized at %s", target)
