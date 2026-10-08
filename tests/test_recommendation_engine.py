"""Tests for the Recommendation Engine core logic, prioritization, and deduplication (Phase 13)."""

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
    lifestyle_factors: list | None = None,
    top_clinical_factors: list | None = None,
    clinical_data: dict | None = None,
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
        clinical_data_json=json.dumps(clinical_data or {}),
        lifestyle_factors_json=json.dumps(lifestyle_factors or []),
        top_clinical_factors_json=json.dumps(top_clinical_factors or []),
        narrative_summary="Assessment summary.",
        model_version="1.0.0",
        created_at="2026-09-08T00:00:00",
    )


def test_deduplication_removes_duplicate_rules():
    """Duplicate recommendation rule IDs generated from multiple sources must be collapsed."""
    engine = RecommendationEngine()
    asmt = _make_assessment(
        "asmt-dup",
        lifestyle_factors=[
            {"category": "smoking", "display_name": "Smoking", "severity": "HIGH", "risk_points": 25},
            {"category": "smoking", "display_name": "Secondhand Smoke", "severity": "MODERATE", "risk_points": 10},
        ],
    )
    insights = engine.generate_insights(asmt)
    rule_ids = [r.rule_id for r in insights.recommendations]
    assert rule_ids.count("SMOKING_CESSATION_SUPPORT") == 1


def test_priority_sorting_order():
    """Recommendations must be sorted with HIGH before MEDIUM before LOW before INFO."""
    engine = RecommendationEngine()
    asmt = _make_assessment(
        "asmt-pri",
        overall_risk=86.0,
        risk_category="Critical Risk",
        lifestyle_factors=[
            {"category": "smoking", "display_name": "Smoking", "severity": "HIGH", "risk_points": 25},
            {"category": "physical_inactivity", "display_name": "Inactive", "severity": "MODERATE", "risk_points": 15},
        ],
        clinical_data={"trestbps": 120, "chol": 180, "fbs": 0},
    )
    insights = engine.generate_insights(asmt)
    priorities = [r.priority for r in insights.recommendations]
    
    # Verify priority ordering
    rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    for i in range(len(priorities) - 1):
        assert rank[priorities[i]] <= rank[priorities[i + 1]]


def test_personalization_different_assessments_yield_different_recommendations():
    """Two different patient assessments must yield different personalized recommendations."""
    engine = RecommendationEngine()
    
    # Patient 1: Active smoker with elevated BP
    asmt1 = _make_assessment(
        "asmt-1",
        lifestyle_factors=[{"category": "smoking", "display_name": "Smoking", "severity": "HIGH", "risk_points": 25}],
        clinical_data={"trestbps": 155, "chol": 190, "fbs": 0},
    )
    
    # Patient 2: Non-smoker, poor sleep, high cholesterol
    asmt2 = _make_assessment(
        "asmt-2",
        lifestyle_factors=[{"category": "poor_sleep", "display_name": "Insomnia", "severity": "MODERATE", "risk_points": 15}],
        clinical_data={"trestbps": 115, "chol": 260, "fbs": 0},
    )
    
    insights1 = engine.generate_insights(asmt1)
    insights2 = engine.generate_insights(asmt2)
    
    rules1 = {r.rule_id for r in insights1.recommendations}
    rules2 = {r.rule_id for r in insights2.recommendations}
    
    assert "SMOKING_CESSATION_SUPPORT" in rules1
    assert "CLINICAL_BP_MONITORING" in rules1
    assert "SMOKING_CESSATION_SUPPORT" not in rules2
    assert "SLEEP_CONSISTENCY" in rules2
    assert "CLINICAL_CHOL_CHECK" in rules2
