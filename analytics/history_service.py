"""History Service for HeartGuard Patient Assessments (Phase 10).

Manages persistence and retrieval of completed multimodal assessments.
Enforces patient data isolation at the database/service layer:
queries filter strictly by the authenticated user's ID.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
import uuid

from config.settings import ASSESSMENTS_DB_PATH, PROJECT_VERSION
from src.analytics.models import Assessment, init_assessment_db
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    target = db_path if db_path is not None else ASSESSMENTS_DB_PATH
    init_assessment_db(target)
    conn = sqlite3.connect(str(target), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_assessment(row: sqlite3.Row) -> Assessment:
    return Assessment(
        id=row["id"],
        assessment_id=row["assessment_id"],
        user_id=row["user_id"],
        created_at=row["created_at"],
        clinical_risk=float(row["clinical_risk"]),
        lifestyle_risk=float(row["lifestyle_risk"]),
        overall_risk=float(row["overall_risk"]),
        risk_category=row["risk_category"],
        recommendation=row["recommendation"],
        model_version=row["model_version"],
        narrative_summary=row["narrative_summary"] or "",
        alert_status=row["alert_status"],
        top_clinical_factors_json=row["top_clinical_factors_json"],
        lifestyle_factors_json=row["lifestyle_factors_json"],
        clinical_data_json=row["clinical_data_json"],
    )


class HistoryService:
    """Service providing secure, user-isolated patient assessment history."""

    init_db = staticmethod(init_assessment_db)

    @staticmethod
    def save_assessment(
        user_id: int | Assessment,
        multimodal_result: dict[str, Any] | None = None,
        alert_status: str = "NOT_TRIGGERED",
        assessment_id: str | None = None,
        db_path: Path | None = None,
    ) -> Assessment:
        """Persist a completed multimodal risk assessment.

        Args:
            user_id: Authenticated user ID or an Assessment instance.
            multimodal_result: Dictionary returned from MultimodalRiskEngine.assess().
            alert_status: Alert delivery status ('NOT_TRIGGERED', 'DISABLED', 'SUCCESS', etc.).
            assessment_id: Optional unique assessment ID (generates 8-char hex if omitted).
            db_path: Optional SQLite DB path override.

        Returns:
            Assessment: Persisted domain model instance.
        """
        if isinstance(user_id, Assessment):
            asmt = user_id
            target_db = db_path
            if target_db is None and isinstance(multimodal_result, (Path, str)):
                target_db = Path(multimodal_result)
            sql = """
            INSERT INTO assessments (
                assessment_id, user_id, created_at, clinical_risk, lifestyle_risk,
                overall_risk, risk_category, recommendation, model_version,
                narrative_summary, alert_status, top_clinical_factors_json,
                lifestyle_factors_json, clinical_data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            with _get_connection(target_db) as conn:
                cursor = conn.execute(
                    sql,
                    (
                        asmt.assessment_id,
                        asmt.user_id,
                        asmt.created_at,
                        asmt.clinical_risk,
                        asmt.lifestyle_risk,
                        asmt.overall_risk,
                        asmt.risk_category,
                        asmt.recommendation,
                        asmt.model_version,
                        asmt.narrative_summary,
                        asmt.alert_status,
                        asmt.top_clinical_factors_json,
                        asmt.lifestyle_factors_json,
                        asmt.clinical_data_json,
                    ),
                )
                conn.commit()
                asmt.id = cursor.lastrowid
            logger.info("Assessment record persisted: aid=%s user_id=%s", asmt.assessment_id, asmt.user_id)
            return asmt

        multimodal_result = multimodal_result or {}
        aid = assessment_id or uuid.uuid4().hex[:8]
        now_iso = datetime.now(timezone.utc).isoformat()

        comb = multimodal_result.get("combined", {})
        clin = multimodal_result.get("clinical", {})
        life = multimodal_result.get("lifestyle", {})

        overall_risk = float(comb.get("risk", 0.0))
        clinical_risk = float(clin.get("risk", 0.0))
        lifestyle_risk = float(life.get("risk", 0.0))

        risk_category = comb.get("category", "LOWER_RISK")
        recommendation = comb.get("recommended_action", "Regular monitoring recommended.")
        model_name = str(clin.get("model", "HeartGuard-ML"))
        model_version = f"{model_name} (v{PROJECT_VERSION})"
        narrative_summary = multimodal_result.get("overall_explanation", "")

        # Extract top SHAP factors if available
        top_factors_json: str | None = None
        c_exp = multimodal_result.get("clinical_explanation")
        if c_exp and isinstance(c_exp, dict):
            top_factors = c_exp.get("top_risk_factors", [])
            if top_factors:
                top_factors_json = json.dumps(top_factors)

        # Extract detected lifestyle signals (safe summary factors, never raw narrative)
        lifestyle_factors_json: str | None = None
        det_factors = life.get("detected_factors", [])
        if det_factors:
            safe_factors = [
                {
                    "display_name": f.get("display_name"),
                    "severity": f.get("severity"),
                    "risk_points": f.get("risk_points"),
                }
                for f in det_factors
            ]
            lifestyle_factors_json = json.dumps(safe_factors)

        # Extract clinical features (physiological metrics only)
        clinical_data_json: str | None = None
        clin_data = clin.get("clinical_data")
        if clin_data and isinstance(clin_data, dict):
            clinical_data_json = json.dumps(clin_data)

        sql = """
        INSERT INTO assessments (
            assessment_id, user_id, created_at, clinical_risk, lifestyle_risk,
            overall_risk, risk_category, recommendation, model_version,
            narrative_summary, alert_status, top_clinical_factors_json,
            lifestyle_factors_json, clinical_data_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        with _get_connection(db_path) as conn:
            cursor = conn.execute(
                sql,
                (
                    aid,
                    user_id,
                    now_iso,
                    clinical_risk,
                    lifestyle_risk,
                    overall_risk,
                    risk_category,
                    recommendation,
                    model_version,
                    narrative_summary,
                    alert_status,
                    top_factors_json,
                    lifestyle_factors_json,
                    clinical_data_json,
                ),
            )
            rec_id = cursor.lastrowid
            conn.commit()

        logger.info(
            "Assessment saved: id=%s aid=%s user_id=%s overall_risk=%.2f%%",
            rec_id,
            aid,
            user_id,
            overall_risk,
        )

        return Assessment(
            id=rec_id,
            assessment_id=aid,
            user_id=user_id,
            created_at=now_iso,
            clinical_risk=clinical_risk,
            lifestyle_risk=lifestyle_risk,
            overall_risk=overall_risk,
            risk_category=risk_category,
            recommendation=recommendation,
            model_version=model_version,
            narrative_summary=narrative_summary,
            alert_status=alert_status,
            top_clinical_factors_json=top_factors_json,
            lifestyle_factors_json=lifestyle_factors_json,
            clinical_data_json=clinical_data_json,
        )

    @staticmethod
    def get_user_assessments(
        user_id: int,
        date_range: str | None = None,
        category: str | None = None,
        sort_order: str = "desc",
        limit: int | None = 50,
        db_path: Path | None = None,
    ) -> list[Assessment]:
        """Fetch historical assessments belonging strictly to the given user.

        Args:
            user_id: Authenticated user ID.
            date_range: Optional filter ('7d', '30d', '90d', or None/'all').
            category: Optional risk category filter.
            sort_order: 'desc' (newest first) or 'asc' (oldest first).
            limit: Maximum records to return (defaults to 50).
            db_path: SQLite DB path override.

        Returns:
            list[Assessment]: Filtered assessments.
        """
        conditions = ["user_id = ?"]
        params: list[Any] = [user_id]

        if date_range in ("7d", "30d", "90d"):
            days = 7 if date_range == "7d" else (30 if date_range == "30d" else 90)
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff)

        if category and category.strip().upper() != "ALL":
            conditions.append("risk_category = ?")
            params.append(category.strip().upper())

        direction = "ASC" if sort_order.lower() == "asc" else "DESC"
        sql = f"SELECT * FROM assessments WHERE {' AND '.join(conditions)} ORDER BY created_at {direction}"
        if limit is not None and limit > 0:
            sql += " LIMIT ?"
            params.append(limit)

        with _get_connection(db_path) as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
            return [_row_to_assessment(r) for r in rows]

    @staticmethod
    def get_assessment_by_id(
        assessment_id: str,
        user_id: int | None = None,
        db_path: Path | None = None,
    ) -> Assessment | None:
        """Fetch assessment by ID, enforcing user ownership if user_id is provided.

        Args:
            assessment_id: Assessment unique string.
            user_id: If provided, enforces that the assessment belongs to this user.
            db_path: SQLite DB path override.

        Returns:
            Assessment or None if not found or unauthorized.
        """
        sql = "SELECT * FROM assessments WHERE assessment_id = ?"
        params: list[Any] = [assessment_id]

        if user_id is not None:
            sql += " AND user_id = ?"
            params.append(user_id)

        with _get_connection(db_path) as conn:
            row = conn.execute(sql, tuple(params)).fetchone()
            if row is None:
                return None
            return _row_to_assessment(row)

    @staticmethod
    def user_owns_assessment(
        user_id: int,
        assessment_id: str,
        db_path: Path | None = None,
    ) -> bool:
        """Verify if a user owns a specific assessment."""
        with _get_connection(db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM assessments WHERE assessment_id = ? AND user_id = ?",
                (assessment_id, user_id),
            ).fetchone()
            return row is not None

    @staticmethod
    def get_latest_assessment(
        user_id: int,
        db_path: Path | None = None,
    ) -> Assessment | None:
        """Return the most recent assessment for the given user."""
        assessments = HistoryService.get_user_assessments(
            user_id=user_id, sort_order="desc", limit=1, db_path=db_path
        )
        return assessments[0] if assessments else None

    @staticmethod
    def get_previous_assessment(
        user_id: int,
        db_path: Path | None = None,
    ) -> Assessment | None:
        """Return the assessment immediately preceding the latest one for the user."""
        assessments = HistoryService.get_user_assessments(
            user_id=user_id, sort_order="desc", limit=2, db_path=db_path
        )
        return assessments[1] if len(assessments) >= 2 else None

    @staticmethod
    def count_assessments(
        user_id: int,
        db_path: Path | None = None,
    ) -> int:
        """Count total assessments belonging to user."""
        with _get_connection(db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM assessments WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return int(row[0]) if row else 0
