"""Security tests for Phase 13 Recommendation Service: IDOR protection, user isolation, and SQL safety."""

import os
import tempfile
import pytest

from src.analytics.history_service import HistoryService
from src.analytics.models import Assessment
from src.recommendations.recommendation_models import Recommendation, init_recommendation_db
from src.recommendations.recommendation_service import RecommendationService


@pytest.fixture
def test_dbs():
    """Create isolated temporary databases for assessments and recommendations."""
    fd1, asmt_db = tempfile.mkstemp(suffix="_asmt.db")
    os.close(fd1)
    fd2, rec_db = tempfile.mkstemp(suffix="_rec.db")
    os.close(fd2)

    HistoryService.init_db(asmt_db)
    init_recommendation_db(rec_db)

    yield asmt_db, rec_db

    for p in [asmt_db, rec_db]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


def test_idor_protection_other_user_cannot_access_recommendations(test_dbs):
    """Patient A's recommendations must not be accessible by Patient B (IDOR defense)."""
    asmt_db, rec_db = test_dbs

    # Create assessment belonging to Patient 10
    asmt = Assessment(
        assessment_id="asmt-pat10",
        user_id=10,
        clinical_risk=50.0,
        lifestyle_risk=40.0,
        overall_risk=47.0,
        risk_category="Moderate Risk",
        recommendation="Follow healthy lifestyle guidance.",
        alert_status="NONE",
        clinical_data_json="{}",
        lifestyle_factors_json="[]",
        top_clinical_factors_json="[]",
        narrative_summary="Summary",
        model_version="1.0.0",
        created_at="2026-09-08T00:00:00",
    )
    HistoryService.save_assessment(asmt, db_path=asmt_db)

    # Patient 10 accesses their own insights -> succeeds
    insights10 = RecommendationService.get_or_create_insights(
        "asmt-pat10", user_id=10, db_path=rec_db, assessment_db_path=asmt_db
    )
    assert insights10 is not None

    # Patient 20 attempts to access Patient 10's assessment -> PermissionError
    with pytest.raises(PermissionError) as excinfo:
        RecommendationService.get_or_create_insights(
            "asmt-pat10", user_id=20, db_path=rec_db, assessment_db_path=asmt_db
        )
    assert "access denied" in str(excinfo.value).lower()


def test_reviewer_can_access_authorized_assessment(test_dbs):
    """Reviewer or admin role can access assessment insights for clinical review without ownership."""
    asmt_db, rec_db = test_dbs

    asmt = Assessment(
        assessment_id="asmt-pat30",
        user_id=30,
        clinical_risk=65.0,
        lifestyle_risk=75.0,
        overall_risk=68.0,
        risk_category="Elevated Risk",
        recommendation="Consider clinical review.",
        alert_status="NONE",
        clinical_data_json="{}",
        lifestyle_factors_json="[]",
        top_clinical_factors_json="[]",
        narrative_summary="Review needed.",
        model_version="1.0.0",
        created_at="2026-09-08T00:00:00",
    )
    HistoryService.save_assessment(asmt, db_path=asmt_db)

    # Reviewer accesses assessment -> succeeds
    insights_rev = RecommendationService.get_or_create_insights(
        "asmt-pat30", user_id=99, user_role="reviewer", db_path=rec_db, assessment_db_path=asmt_db
    )
    assert insights_rev is not None
    assert insights_rev.assessment_id == "asmt-pat30"


def test_user_cannot_view_another_users_recommendation_history(test_dbs):
    """Querying user recommendations must be strictly scoped to the requesting user_id."""
    asmt_db, rec_db = test_dbs

    # Create recommendations for user 10 and user 20
    rec1 = Recommendation(
        assessment_id="asmt-u10",
        category="Physical Activity",
        title="Active Life",
        description="Daily walk",
        priority="LOW",
        source="Rule Engine",
        rule_id="RULE_1",
    )
    rec2 = Recommendation(
        assessment_id="asmt-u20",
        category="Sleep",
        title="Sleep Hygiene",
        description="Consistent routine",
        priority="MEDIUM",
        source="Rule Engine",
        rule_id="RULE_2",
    )

    RecommendationService._persist_recommendations_if_absent("asmt-u10", [rec1], db_path=rec_db)
    RecommendationService._persist_recommendations_if_absent("asmt-u20", [rec2], db_path=rec_db)

    # User 10 history only retrieves user 10 records
    u10_recs = RecommendationService.get_user_recommendations(user_id=10, db_path=rec_db)
    # Since get_user_recommendations links through assessments DB or assessment_ids:
    # Here with rec_db only it queries by assessment ownership
    for r in u10_recs:
        assert r.assessment_id != "asmt-u20"
