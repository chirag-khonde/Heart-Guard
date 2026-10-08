"""Tests for SHAP feature explanations, trend comparison phrasing, and personalized summary generation (Phase 13)."""

import pytest

from src.analytics.models import Assessment
from src.recommendations.recommendation_engine import RecommendationEngine


def _make_assessment(
    assessment_id: str,
    user_id: int = 1,
    overall_risk: float = 60.0,
    clinical_risk: float = 55.0,
    lifestyle_risk: float = 70.0,
    risk_category: str = "Elevated Risk",
    top_clinical_factors: list | None = None,
) -> Assessment:
    import json
    return Assessment(
        assessment_id=assessment_id,
        user_id=user_id,
        clinical_risk=clinical_risk,
        lifestyle_risk=lifestyle_risk,
        overall_risk=overall_risk,
        risk_category=risk_category,
        recommendation="Consider scheduling an appointment with a physician.",
        alert_status="NONE",
        clinical_data_json="{}",
        lifestyle_factors_json="[]",
        top_clinical_factors_json=json.dumps(top_clinical_factors or []),
        narrative_summary="Assessment summary.",
        model_version="1.0.0",
        created_at="2026-09-08T00:00:00",
    )


def test_shap_factors_explanation():
    """SHAP contributors should be formatted into non-diagnostic model contribution descriptions."""
    engine = RecommendationEngine()
    asmt = _make_assessment(
        "asmt-shap",
        top_clinical_factors=[
            {"feature": "trestbps", "importance": 0.42, "direction": "increases_risk"},
            {"feature": "chol", "importance": 0.28, "direction": "increases_risk"},
        ],
    )
    insights = engine.generate_insights(asmt)
    assert len(insights.top_factors) == 2
    f1 = insights.top_factors[0]
    assert "Resting Blood Pressure" in f1["feature"]
    assert "contributed" in f1["description"].lower()
    # Must not claim diagnosis or causation
    assert "caused" not in f1["description"].lower()


def test_first_assessment_trend_summary():
    """If no previous assessment exists, comparison must indicate first assessment."""
    engine = RecommendationEngine()
    asmt = _make_assessment("asmt-first")
    insights = engine.generate_insights(asmt, previous_assessment=None)
    assert "first HeartGuard assessment" in insights.trend_summary
    assert insights.comparison is None


def test_trend_comparison_increasing_and_decreasing():
    """Trend summary reflects model-based score increase and decrease without clinical disease progression labels."""
    engine = RecommendationEngine()
    
    prev = _make_assessment("asmt-prev", overall_risk=45.0, clinical_risk=40.0, lifestyle_risk=50.0)
    curr_higher = _make_assessment("asmt-curr", overall_risk=60.0, clinical_risk=55.0, lifestyle_risk=70.0)
    
    insights_inc = engine.generate_insights(curr_higher, previous_assessment=prev)
    assert "increased" in insights_inc.trend_summary.lower()
    assert "deterioration" not in insights_inc.trend_summary.lower()
    assert "disease progression" not in insights_inc.trend_summary.lower()

    curr_lower = _make_assessment("asmt-curr2", overall_risk=35.0, clinical_risk=30.0, lifestyle_risk=40.0)
    insights_dec = engine.generate_insights(curr_lower, previous_assessment=prev)
    assert "decreased" in insights_dec.trend_summary.lower()
    assert "cured" not in insights_dec.trend_summary.lower()


def test_summary_text_generation():
    """Personalized summary text must accurately reflect overall risk score and category."""
    engine = RecommendationEngine()
    asmt = _make_assessment(
        "asmt-sum",
        overall_risk=68.4,
        risk_category="Elevated Risk",
        top_clinical_factors=[{"feature": "thalach", "importance": 0.35, "direction": "increases_risk"}],
    )
    insights = engine.generate_insights(asmt)
    assert "68.4%" in insights.summary_text
    assert "Elevated Risk" in insights.summary_text
    assert "Max Heart Rate" in insights.summary_text
