"""Tests for HeartGuard Dashboard Analytics & Summaries (Phase 12).

Verifies the 10 required criteria:
  1. Empty history handling
  2. One assessment handling
  3. Multiple assessments handling
  4. Chronological trend ordering (oldest to newest)
  5. Category distribution
  6. Review distribution
  7. Alert distribution
  8. Average risk calculation
  9. Critical count calculation
  10. User-specific filtering (User A vs User B)
Plus performance validation with 100+ stored assessments.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
import pytest

from src.analytics.analytics_service import AnalyticsService
from src.analytics.history_service import HistoryService
from src.analytics.models import init_assessment_db
from src.analytics.trend_service import TrendService
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


def _make_dummy_result(
    overall: float = 40.0,
    clinical: float = 45.0,
    lifestyle: float = 30.0,
    category: str = "LOW",
    alert_status: str = "NOT_TRIGGERED",
) -> dict:
    return {
        "combined": {
            "risk": overall,
            "category": category,
            "alert_level": "MONITORING",
            "recommended_action": "Maintain healthy habits.",
        },
        "clinical": {
            "risk": clinical,
            "probability": clinical / 100.0,
            "prediction": 0,
            "model_version": "1.0.0",
            "top_drivers": [{"clinical_label": "Age", "shap_value": 0.12}],
        },
        "lifestyle": {
            "score": lifestyle,
            "risk_tier": "Low Risk",
            "narrative_summary": "Active lifestyle.",
            "structured_factors": [{"category": "exercise", "level": "High"}],
        },
        "alert": {"status": alert_status, "mode": "DEMO"},
        "clinical_features": {"age": 45, "chol": 190},
    }


def test_1_empty_history(isolated_dbs):
    assess_db, review_db = isolated_dbs
    stats = AnalyticsService.calculate_user_statistics(user_id=99, db_path=assess_db)
    assert stats["total_assessments"] == 0
    assert stats["latest_risk"] is None
    assert stats["latest_category"] is None
    assert stats["latest_review_status"] == "NOT_REVIEWED"
    assert stats["latest_alert_status"] is None
    assert stats["average_overall_risk"] is None
    assert stats["critical_count"] == 0

    recent = AnalyticsService.get_user_recent_assessments(user_id=99, db_path=assess_db, review_db_path=review_db)
    assert recent == []


def test_2_one_assessment(isolated_dbs):
    assess_db, review_db = isolated_dbs
    res = _make_dummy_result(overall=55.4, category="ELEVATED", alert_status="NOT_TRIGGERED")
    rec = HistoryService.save_assessment(user_id=1, multimodal_result=res, db_path=assess_db)

    stats = AnalyticsService.calculate_user_statistics(user_id=1, db_path=assess_db)
    assert stats["total_assessments"] == 1
    assert stats["latest_risk"] == 55.4
    assert stats["latest_category"] == "ELEVATED"
    assert stats["average_overall_risk"] == 55.4
    assert stats["critical_count"] == 0

    recent = AnalyticsService.get_user_recent_assessments(user_id=1, db_path=assess_db, review_db_path=review_db)
    assert len(recent) == 1
    assert recent[0]["assessment_id"] == rec.assessment_id


def test_3_multiple_assessments(isolated_dbs):
    assess_db, review_db = isolated_dbs
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=30.0, category="LOW"), db_path=assess_db)
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=50.0, category="ELEVATED"), db_path=assess_db)
    rec3 = HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=85.0, category="CRITICAL"), db_path=assess_db)

    stats = AnalyticsService.calculate_user_statistics(user_id=1, db_path=assess_db)
    assert stats["total_assessments"] == 3
    assert stats["latest_risk"] == 85.0
    assert stats["latest_category"] == "CRITICAL"


def test_4_trend_ordering(isolated_dbs):
    assess_db, review_db = isolated_dbs
    r1 = HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=35.0), db_path=assess_db)
    r2 = HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=55.0), db_path=assess_db)
    r3 = HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=75.0), db_path=assess_db)

    trends = TrendService.get_risk_trends(user_id=1, db_path=assess_db)
    assert len(trends) == 3
    # Chronological: oldest first
    assert trends[0]["assessment_id"] == r1.assessment_id
    assert trends[1]["assessment_id"] == r2.assessment_id
    assert trends[2]["assessment_id"] == r3.assessment_id


def test_5_category_distribution(isolated_dbs):
    assess_db, _ = isolated_dbs
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=20.0, category="LOW"), db_path=assess_db)
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=25.0, category="LOW"), db_path=assess_db)
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=60.0, category="ELEVATED"), db_path=assess_db)

    dist = AnalyticsService.get_category_distribution(user_id=1, db_path=assess_db)
    assert dist.get("LOW") == 2
    assert dist.get("ELEVATED") == 1


def test_6_review_distribution(isolated_dbs):
    assess_db, review_db = isolated_dbs
    r1 = HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(), db_path=assess_db)
    r2 = HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(), db_path=assess_db)

    rev1 = ReviewService.create_review(reviewer_id=10, assessment_id=r1.assessment_id, review_db_path=review_db, assessment_db_path=assess_db)
    rev2 = ReviewService.create_review(reviewer_id=10, assessment_id=r2.assessment_id, review_db_path=review_db, assessment_db_path=assess_db)

    ReviewService.update_review(review_id=rev1.review_id, reviewer_id=10, review_status="REVIEWED", review_db_path=review_db)
    ReviewService.update_review(review_id=rev2.review_id, reviewer_id=10, review_status="IN_REVIEW", review_db_path=review_db)

    dist = AnalyticsService.get_review_distribution(review_db_path=review_db)
    assert dist.get("REVIEWED") == 1
    assert dist.get("IN_REVIEW") == 1
    assert dist.get("PENDING") is None or dist.get("PENDING") == 0


def test_7_alert_distribution(isolated_dbs):
    assess_db, _ = isolated_dbs
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(), alert_status="NOT_TRIGGERED", db_path=assess_db)
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(), alert_status="TRIGGERED", db_path=assess_db)
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(), alert_status="SENT", db_path=assess_db)

    admin_analytics = AnalyticsService.get_admin_aggregated_analytics(db_path=assess_db)
    alert_dist = admin_analytics["alert_status_distribution"]
    assert alert_dist.get("NOT_TRIGGERED") == 1
    assert alert_dist.get("TRIGGERED") == 1
    assert alert_dist.get("SENT") == 1


def test_8_average_risk_computation(isolated_dbs):
    assess_db, _ = isolated_dbs
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=40.0), db_path=assess_db)
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=60.0), db_path=assess_db)

    stats = AnalyticsService.calculate_user_statistics(user_id=1, db_path=assess_db)
    assert stats["average_overall_risk"] == 50.0


def test_9_critical_count_computation(isolated_dbs):
    assess_db, _ = isolated_dbs
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=30.0, category="LOW"), db_path=assess_db)
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=85.0, category="CRITICAL"), db_path=assess_db)
    HistoryService.save_assessment(user_id=1, multimodal_result=_make_dummy_result(overall=90.0, category="CRITICAL"), db_path=assess_db)

    stats = AnalyticsService.calculate_user_statistics(user_id=1, db_path=assess_db)
    assert stats["critical_count"] == 2


def test_10_user_specific_filtering(isolated_dbs):
    assess_db, _ = isolated_dbs
    HistoryService.save_assessment(user_id=101, multimodal_result=_make_dummy_result(overall=20.0, category="LOW"), db_path=assess_db)
    HistoryService.save_assessment(user_id=202, multimodal_result=_make_dummy_result(overall=80.0, category="CRITICAL"), db_path=assess_db)

    user101_stats = AnalyticsService.calculate_user_statistics(user_id=101, db_path=assess_db)
    user202_stats = AnalyticsService.calculate_user_statistics(user_id=202, db_path=assess_db)

    assert user101_stats["total_assessments"] == 1
    assert user101_stats["latest_risk"] == 20.0
    assert user101_stats["critical_count"] == 0

    assert user202_stats["total_assessments"] == 1
    assert user202_stats["latest_risk"] == 80.0
    assert user202_stats["critical_count"] == 1


def test_performance_with_many_assessments(isolated_dbs):
    assess_db, review_db = isolated_dbs
    # Insert 100 assessments for user 1
    for i in range(100):
        HistoryService.save_assessment(
            user_id=1,
            multimodal_result=_make_dummy_result(overall=float(20 + (i % 60))),
            db_path=assess_db,
        )

    start = time.perf_counter()
    stats = AnalyticsService.calculate_user_statistics(user_id=1, db_path=assess_db)
    recent = AnalyticsService.get_user_recent_assessments(user_id=1, limit=5, db_path=assess_db, review_db_path=review_db)
    elapsed = time.perf_counter() - start

    assert stats["total_assessments"] == 100
    assert len(recent) == 5
    assert elapsed < 1.0  # Must query and return in under 1 second without retraining models
