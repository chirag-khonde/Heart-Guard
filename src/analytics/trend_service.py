"""Trend analysis service for HeartGuard historical assessments (Phase 10).

Calculates chronologically ordered risk trajectories, percentage-point deltas,
and non-diagnostic trend interpretations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.analytics.history_service import HistoryService
from src.analytics.models import Assessment

TREND_DISCLAIMER = (
    "Changes in HeartGuard risk scores represent changes in the model's assessment "
    "inputs and outputs. They do not by themselves establish a medical diagnosis "
    "or disease progression."
)


class TrendService:
    """Service for computing cardiovascular risk trends over time."""

    @staticmethod
    def get_risk_trends(
        user_id: int,
        db_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch historical risk data chronologically sorted (oldest first) for graphing.

        Args:
            user_id: Authenticated user ID.
            db_path: SQLite DB path override.

        Returns:
            list[dict]: Chronological trend records.
        """
        assessments = HistoryService.get_user_assessments(
            user_id=user_id, sort_order="asc", limit=None, db_path=db_path
        )
        trends = []
        for a in assessments:
            trends.append(
                {
                    "assessment_id": a.assessment_id,
                    "date": a.created_at[:10],  # YYYY-MM-DD
                    "timestamp": a.created_at,
                    "clinical_risk": a.clinical_risk,
                    "lifestyle_risk": a.lifestyle_risk,
                    "overall_risk": a.overall_risk,
                    "risk_category": a.risk_category,
                    "alert_status": a.alert_status,
                }
            )
        return trends

    @staticmethod
    def compare_assessments(
        latest: Assessment | None,
        previous: Assessment | None,
    ) -> dict[str, Any] | None:
        """Compare the most recent assessment with the preceding one.

        Args:
            latest: The most recent Assessment object.
            previous: The prior Assessment object.

        Returns:
            dict containing percentage-point deltas, category change, and interpretation.
        """
        if latest is None or previous is None:
            return None

        overall_delta = round(latest.overall_risk - previous.overall_risk, 2)
        clinical_delta = round(latest.clinical_risk - previous.clinical_risk, 2)
        lifestyle_delta = round(latest.lifestyle_risk - previous.lifestyle_risk, 2)

        def _format_delta(delta: float) -> str:
            sign = "+" if delta > 0 else ("" if delta < 0 else "")
            return f"{sign}{delta:.1f} percentage points"

        if overall_delta > 0.05:
            trend_dir = "INCREASED"
            interpretation = "Overall model-based risk has increased compared with the previous assessment."
        elif overall_delta < -0.05:
            trend_dir = "DECREASED"
            interpretation = "Overall model-based risk has decreased compared with the previous assessment."
        else:
            trend_dir = "UNCHANGED"
            interpretation = "Overall model-based risk is unchanged compared with the previous assessment."

        return {
            "latest_id": latest.assessment_id,
            "previous_id": previous.assessment_id,
            "latest_date": latest.created_at[:10],
            "previous_date": previous.created_at[:10],
            "overall_risk": {
                "latest": latest.overall_risk,
                "previous": previous.overall_risk,
                "delta": overall_delta,
                "delta_str": _format_delta(overall_delta),
            },
            "clinical_risk": {
                "latest": latest.clinical_risk,
                "previous": previous.clinical_risk,
                "delta": clinical_delta,
                "delta_str": _format_delta(clinical_delta),
            },
            "lifestyle_risk": {
                "latest": latest.lifestyle_risk,
                "previous": previous.lifestyle_risk,
                "delta": lifestyle_delta,
                "delta_str": _format_delta(lifestyle_delta),
            },
            "category": {
                "latest": latest.risk_category,
                "previous": previous.risk_category,
                "changed": latest.risk_category != previous.risk_category,
            },
            "trend_direction": trend_dir,
            "interpretation": interpretation,
            "disclaimer": TREND_DISCLAIMER,
        }
