"""Security and privacy tests for HeartGuard Dashboards (Phase 12).

Tests:
  - Cross-user data isolation: Patient A cannot retrieve Patient B dashboard data
  - Admin privacy: Aggregated statistics do NOT expose raw patient lifestyle text or PII
  - Non-reviewer cannot update review records
  - User-scoped queries prevent cross-user data leakage
"""

from __future__ import annotations

from pathlib import Path
import pytest

from src.analytics.analytics_service import AnalyticsService
from src.analytics.history_service import HistoryService
from src.analytics.models import init_assessment_db
from src.review.models import init_review_db
from src.review.review_service import ReviewService


@pytest.fixture()
def isolated_dbs(tmp_path: Path):
    """Provide isolated assessment and review databases."""
    assess_db = tmp_path / "assessments.db"
    review_db = tmp_path / "reviews.db"
    init_assessment_db(assess_db)
    init_review_db(review_db)
    return assess_db, review_db


def _make_dummy_result(patient_secret_text: str = "Private patient details"):
    return {
        "combined": {
            "risk": 65.0,
            "category": "HIGH",
            "alert_level": "MONITORING",
            "recommended_action": "Consult clinician.",
        },
        "clinical": {
            "risk": 70.0,
            "probability": 0.7,
            "prediction": 1,
            "model_version": "1.0.0",
            "top_drivers": [{"clinical_label": "RestingBP", "shap_value": 0.2}],
        },
        "lifestyle": {
            "score": 50.0,
            "risk_tier": "Moderate",
            "narrative_summary": patient_secret_text,
            "structured_factors": [{"category": "stress", "level": "High"}],
        },
        "alert": {"status": "NOT_TRIGGERED", "mode": "DEMO"},
        "clinical_features": {"trestbps": 150, "chol": 240},
    }


def test_cross_user_dashboard_isolation(isolated_dbs):
    assess_db, review_db = isolated_dbs

    # Patient A (id=10)
    HistoryService.save_assessment(
        user_id=10,
        multimodal_result=_make_dummy_result("Patient A secret narrative"),
        db_path=assess_db,
    )

    # Patient B (id=20)
    HistoryService.save_assessment(
        user_id=20,
        multimodal_result=_make_dummy_result("Patient B secret narrative"),
        db_path=assess_db,
    )

    # Query Patient A dashboard data
    user_a_recent = AnalyticsService.get_user_recent_assessments(
        user_id=10, db_path=assess_db, review_db_path=review_db
    )
    user_a_stats = AnalyticsService.calculate_user_statistics(
        user_id=10, db_path=assess_db
    )

    # Verify Patient A only sees 1 assessment
    assert len(user_a_recent) == 1
    assert user_a_recent[0]["user_id"] == 10
    assert user_a_stats["total_assessments"] == 1

    # Verify Patient A cannot see Patient B's data
    for a in user_a_recent:
        assert a["user_id"] != 20
        assert "Patient B" not in str(a.get("narrative_summary", ""))


def test_admin_privacy_preservation(isolated_dbs):
    assess_db, review_db = isolated_dbs

    secret_text_1 = "Patient 1 sensitive lifestyle habits with smoking history"
    secret_text_2 = "Patient 2 sensitive stress factors and anxiety"

    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(secret_text_1), db_path=assess_db)
    HistoryService.save_assessment(user_id=2, multimodal_result=_make_dummy_result(secret_text_2), db_path=assess_db)

    # Admin analytics query
    admin_data = AnalyticsService.get_admin_aggregated_analytics(
        db_path=assess_db, review_db_path=review_db
    )

    # Convert entire admin summary output to string
    admin_str = str(admin_data)

    # Ensure aggregate counts are correct
    assert admin_data["total_assessments"] == 2
    assert admin_data["active_patients"] == 2

    # PRIVACY GUARANTEE: Sensitive patient text must NEVER leak into admin analytics
    assert secret_text_1 not in admin_str
    assert secret_text_2 not in admin_str
    assert "narrative_summary" not in admin_str
    assert "clinical_features" not in admin_str


def test_reviewer_ownership_enforcement(isolated_dbs):
    assess_db, review_db = isolated_dbs

    rec = HistoryService.save_assessment(
        user_id=1, multimodal_result=_make_dummy_result(), db_path=assess_db
    )

    # Reviewer 1 claims the review
    rev = ReviewService.create_review(
        reviewer_id=101,
        assessment_id=rec.assessment_id,
        review_db_path=review_db,
        assessment_db_path=assess_db,
    )

    # Reviewer 2 tries to update Reviewer 1's review -> Must raise PermissionError
    with pytest.raises(PermissionError):
        ReviewService.update_review(
            review_id=rev.review_id,
            reviewer_id=202,
            review_status="ACCEPTED",
            review_db_path=review_db,
        )
