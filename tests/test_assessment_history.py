"""Unit tests for HeartGuard Patient Assessment History & Analytics (Phase 10).

Tests:
  - User isolation (Patient A cannot retrieve Patient B's assessments)
  - Ownership validation (user_owns_assessment)
  - Empty history, single assessment, and multiple assessment handling
  - Date filtering and sorting
  - Pairwise latest vs previous comparisons (percentage points)
  - Category distributions and user summary statistics
  - Admin aggregated metrics (privacy-safe, no patient PII)
"""

from __future__ import annotations

from pathlib import Path
import pytest

from src.analytics.analytics_service import AnalyticsService
from src.analytics.history_service import HistoryService
from src.analytics.models import init_assessment_db
from src.analytics.trend_service import TrendService


@pytest.fixture()
def tmp_assessments_db(tmp_path: Path) -> Path:
    """Fixture providing a fresh isolated assessments SQLite database."""
    db_file = tmp_path / "test_assessments.db"
    init_assessment_db(db_file)
    return db_file


def _create_dummy_result(
    overall_risk: float = 45.0,
    clinical_risk: float = 50.0,
    lifestyle_risk: float = 33.3,
    category: str = "LOWER_RISK",
    recommendation: str = "Regular monitoring recommended.",
    has_shap: bool = True,
) -> dict:
    """Helper to construct a mock multimodal risk engine result."""
    top_factors = (
        [
            {"clinical_label": "Resting Blood Pressure", "shap_value": 0.245},
            {"clinical_label": "Serum Cholesterol", "shap_value": 0.180},
        ]
        if has_shap
        else []
    )

    return {
        "combined": {
            "risk": overall_risk,
            "category": category,
            "alert_level": "MONITORING",
            "recommended_action": recommendation,
        },
        "clinical": {
            "risk": clinical_risk,
            "probability": clinical_risk / 100.0,
            "prediction": 1 if clinical_risk > 50 else 0,
            "model": "logistic_regression",
            "clinical_data": {"age": 55, "trestbps": 140},
        },
        "lifestyle": {
            "risk": lifestyle_risk,
            "category": "LOW",
            "detected_factors": [
                {"display_name": "Sedentary Habit", "severity": "MODERATE", "risk_points": 15}
            ],
            "summary": "Mild inactivity noted.",
        },
        "clinical_explanation": {
            "top_risk_factors": top_factors,
        },
        "overall_explanation": "Multimodal evaluation summary narrative.",
    }


# ---------------------------------------------------------------------------
# 1. Persistence & User Isolation
# ---------------------------------------------------------------------------


def test_save_and_retrieve_own_assessments(tmp_assessments_db: Path):
    """A patient must be able to view their own saved assessments."""
    res = _create_dummy_result(overall_risk=42.0, category="LOWER_RISK")
    saved = HistoryService.save_assessment(
        user_id=101,
        multimodal_result=res,
        alert_status="NOT_TRIGGERED",
        assessment_id="ASSESS_U101_1",
        db_path=tmp_assessments_db,
    )

    assert saved.assessment_id == "ASSESS_U101_1"
    assert saved.overall_risk == 42.0

    assessments = HistoryService.get_user_assessments(user_id=101, db_path=tmp_assessments_db)
    assert len(assessments) == 1
    assert assessments[0].assessment_id == "ASSESS_U101_1"
    assert assessments[0].user_id == 101


def test_patient_isolation_cannot_see_other_patient_data(tmp_assessments_db: Path):
    """Patient A (user_id=1) must never receive Patient B's (user_id=2) records."""
    # User 1 creates an assessment
    HistoryService.save_assessment(
        user_id=1,
        multimodal_result=_create_dummy_result(overall_risk=30.0),
        assessment_id="AID_USER_1",
        db_path=tmp_assessments_db,
    )
    # User 2 creates an assessment
    HistoryService.save_assessment(
        user_id=2,
        multimodal_result=_create_dummy_result(overall_risk=88.0, category="CRITICAL"),
        assessment_id="AID_USER_2",
        db_path=tmp_assessments_db,
    )

    u1_records = HistoryService.get_user_assessments(user_id=1, db_path=tmp_assessments_db)
    assert len(u1_records) == 1
    assert u1_records[0].assessment_id == "AID_USER_1"

    u2_records = HistoryService.get_user_assessments(user_id=2, db_path=tmp_assessments_db)
    assert len(u2_records) == 1
    assert u2_records[0].assessment_id == "AID_USER_2"

    # Verify ownership check
    assert HistoryService.user_owns_assessment(user_id=1, assessment_id="AID_USER_1", db_path=tmp_assessments_db) is True
    assert HistoryService.user_owns_assessment(user_id=1, assessment_id="AID_USER_2", db_path=tmp_assessments_db) is False

    # Attempting to fetch User 2's assessment as User 1 must return None
    fetched = HistoryService.get_assessment_by_id(assessment_id="AID_USER_2", user_id=1, db_path=tmp_assessments_db)
    assert fetched is None


# ---------------------------------------------------------------------------
# 2. Empty State & Null Handling
# ---------------------------------------------------------------------------


def test_empty_history_returns_safe_defaults(tmp_assessments_db: Path):
    """When a patient has no assessments, service returns empty structures without errors."""
    records = HistoryService.get_user_assessments(user_id=999, db_path=tmp_assessments_db)
    assert records == []

    latest = HistoryService.get_latest_assessment(user_id=999, db_path=tmp_assessments_db)
    assert latest is None

    stats = AnalyticsService.calculate_user_statistics(user_id=999, db_path=tmp_assessments_db)
    assert stats["total_assessments"] == 0
    assert stats["latest_risk"] is None
    assert stats["average_overall_risk"] is None
    assert stats["critical_count"] == 0

    cat_dist = AnalyticsService.get_category_distribution(user_id=999, db_path=tmp_assessments_db)
    assert cat_dist == {}

    trends = TrendService.get_risk_trends(user_id=999, db_path=tmp_assessments_db)
    assert trends == []

    comparison = TrendService.compare_assessments(None, None)
    assert comparison is None


# ---------------------------------------------------------------------------
# 3. Multiple Assessments & Chronological Trends
# ---------------------------------------------------------------------------


def test_trend_service_chronological_order(tmp_assessments_db: Path):
    """Trend service must return historical records sorted chronologically (oldest first)."""
    # Create 3 assessments for user 5
    HistoryService.save_assessment(
        user_id=5,
        multimodal_result=_create_dummy_result(overall_risk=40.0, clinical_risk=45.0, lifestyle_risk=30.0),
        assessment_id="ASSESS_1",
        db_path=tmp_assessments_db,
    )
    HistoryService.save_assessment(
        user_id=5,
        multimodal_result=_create_dummy_result(overall_risk=55.0, clinical_risk=60.0, lifestyle_risk=45.0),
        assessment_id="ASSESS_2",
        db_path=tmp_assessments_db,
    )
    HistoryService.save_assessment(
        user_id=5,
        multimodal_result=_create_dummy_result(overall_risk=72.0, clinical_risk=75.0, lifestyle_risk=65.0),
        assessment_id="ASSESS_3",
        db_path=tmp_assessments_db,
    )

    trends = TrendService.get_risk_trends(user_id=5, db_path=tmp_assessments_db)
    assert len(trends) == 3
    # Check chronological ordering: 40.0 -> 55.0 -> 72.0
    assert trends[0]["overall_risk"] == 40.0
    assert trends[1]["overall_risk"] == 55.0
    assert trends[2]["overall_risk"] == 72.0


def test_pairwise_comparison_and_percentage_points(tmp_assessments_db: Path):
    """Test delta calculation uses percentage points and prudent non-diagnostic interpretation."""
    a1 = HistoryService.save_assessment(
        user_id=7,
        multimodal_result=_create_dummy_result(overall_risk=64.0, category="ELEVATED"),
        assessment_id="AID_PREV",
        db_path=tmp_assessments_db,
    )
    a2 = HistoryService.save_assessment(
        user_id=7,
        multimodal_result=_create_dummy_result(overall_risk=72.0, category="ELEVATED"),
        assessment_id="AID_LATEST",
        db_path=tmp_assessments_db,
    )

    comparison = TrendService.compare_assessments(latest=a2, previous=a1)
    assert comparison is not None
    assert comparison["overall_risk"]["delta"] == 8.0
    assert comparison["overall_risk"]["delta_str"] == "+8.0 percentage points"
    assert "increased" in comparison["interpretation"].lower()
    assert "Changes in HeartGuard risk scores" in comparison["disclaimer"]


# ---------------------------------------------------------------------------
# 4. User Summary Metrics and Category Distribution
# ---------------------------------------------------------------------------


def test_user_statistics_and_critical_count(tmp_assessments_db: Path):
    """Ensure average risk and critical counts are calculated correctly."""
    HistoryService.save_assessment(
        user_id=8,
        multimodal_result=_create_dummy_result(overall_risk=30.0, category="LOWER_RISK"),
        db_path=tmp_assessments_db,
    )
    HistoryService.save_assessment(
        user_id=8,
        multimodal_result=_create_dummy_result(overall_risk=90.0, category="CRITICAL"),
        db_path=tmp_assessments_db,
    )

    stats = AnalyticsService.calculate_user_statistics(user_id=8, db_path=tmp_assessments_db)
    assert stats["total_assessments"] == 2
    assert stats["latest_risk"] == 90.0
    assert stats["latest_category"] == "CRITICAL"
    assert stats["critical_count"] == 1
    assert stats["average_overall_risk"] == 60.0


# ---------------------------------------------------------------------------
# 5. Admin Aggregated Analytics (Privacy Preserving)
# ---------------------------------------------------------------------------


def test_admin_aggregated_analytics_contains_no_pii(tmp_assessments_db: Path):
    """Admin analytics must aggregate system totals without leaking individual patient data."""
    # User 10
    HistoryService.save_assessment(
        user_id=10,
        multimodal_result=_create_dummy_result(overall_risk=50.0, category="LOWER_RISK"),
        alert_status="NOT_TRIGGERED",
        db_path=tmp_assessments_db,
    )
    # User 20
    HistoryService.save_assessment(
        user_id=20,
        multimodal_result=_create_dummy_result(overall_risk=92.0, category="CRITICAL"),
        alert_status="SUCCESS",
        db_path=tmp_assessments_db,
    )

    admin_stats = AnalyticsService.get_admin_aggregated_analytics(db_path=tmp_assessments_db)
    assert admin_stats["total_assessments"] == 2
    assert admin_stats["active_patients"] == 2
    assert admin_stats["average_system_risk"] == 71.0
    assert "CRITICAL" in admin_stats["category_distribution"]
    assert "LOWER_RISK" in admin_stats["category_distribution"]
    # Check no raw records or PII keys in returned dict
    assert "users" not in admin_stats
    assert "patient_name" not in admin_stats
    assert "lifestyle_text" not in admin_stats
