"""Tests for deterministic recommendation rules based on lifestyle, clinical metrics, risk tiers, and trends (Phase 13)."""

import pytest

from src.recommendations.recommendation_models import Recommendation
from src.recommendations.recommendation_rules import (
    evaluate_clinical_rules,
    evaluate_lifestyle_rules,
    evaluate_risk_tier_rules,
    evaluate_trend_rules,
)


def test_smoking_rule_trigger():
    """Presence of smoking risk factor must trigger smoking cessation support."""
    lifestyle_factors = [
        {"category": "smoking", "display_name": "Active Smoking Habit", "severity": "HIGH", "risk_points": 25}
    ]
    recs = evaluate_lifestyle_rules("asmt-01", lifestyle_factors)
    rule_ids = [r.rule_id for r in recs]
    assert "SMOKING_CESSATION_SUPPORT" in rule_ids
    match = next(r for r in recs if r.rule_id == "SMOKING_CESSATION_SUPPORT")
    assert match.priority == "HIGH"
    assert match.category == "Smoking"
    assert "smoking" in match.description.lower()


def test_physical_inactivity_rule_trigger():
    """Inactivity factor must trigger physical activity boost."""
    lifestyle_factors = [
        {"category": "physical_inactivity", "display_name": "Sedentary Routine", "severity": "MODERATE", "risk_points": 15}
    ]
    recs = evaluate_lifestyle_rules("asmt-01", lifestyle_factors)
    rule_ids = [r.rule_id for r in recs]
    assert "PHYSICAL_ACTIVITY_BOOST" in rule_ids
    match = next(r for r in recs if r.rule_id == "PHYSICAL_ACTIVITY_BOOST")
    assert match.priority == "MEDIUM"
    assert match.category == "Physical Activity"


def test_poor_sleep_rule_trigger():
    """Poor sleep must trigger sleep consistency recommendation."""
    lifestyle_factors = [
        {"category": "poor_sleep", "display_name": "Frequent Insomnia", "severity": "MODERATE", "risk_points": 10}
    ]
    recs = evaluate_lifestyle_rules("asmt-01", lifestyle_factors)
    rule_ids = [r.rule_id for r in recs]
    assert "SLEEP_CONSISTENCY" in rule_ids
    match = next(r for r in recs if r.rule_id == "SLEEP_CONSISTENCY")
    assert match.priority == "MEDIUM"
    assert match.category == "Sleep"


def test_clinical_rules_hypertension_and_glucose():
    """Resting BP >= 140 or glucose >= 126 must trigger clinical follow-up recommendations."""
    clinical_data = {
        "trestbps": 150,
        "chol": 210,
        "fbs": 1,
    }
    recs = evaluate_clinical_rules("asmt-01", clinical_data)
    rule_ids = [r.rule_id for r in recs]
    assert "CLINICAL_BP_MONITORING" in rule_ids
    assert "CLINICAL_GLUCOSE_MONITORING" in rule_ids
    assert "CLINICAL_CHOL_CHECK" not in rule_ids  # Chol is under 240


def test_clinical_cholesterol_trigger():
    """Cholesterol >= 240 mg/dL triggers lipid profile discussion recommendation."""
    clinical_data = {
        "trestbps": 120,
        "chol": 265,
        "fbs": 0,
    }
    recs = evaluate_clinical_rules("asmt-01", clinical_data)
    rule_ids = [r.rule_id for r in recs]
    assert "CLINICAL_CHOL_CHECK" in rule_ids


def test_risk_tier_critical_evaluation():
    """Critical risk category generates HIGH priority consultation recommendation."""
    recs = evaluate_risk_tier_rules("asmt-01", risk_category="Critical Risk", overall_risk=88.5)
    rule_ids = [r.rule_id for r in recs]
    assert "RISK_TIER_CRITICAL_FOLLOWUP" in rule_ids
    rec = recs[0]
    assert rec.priority == "HIGH"
    assert "qualified healthcare professional" in rec.description.lower()
    # Non-diagnostic check
    assert "you have heart disease" not in rec.description.lower()


def test_risk_tier_low_risk_evaluation():
    """Low risk category generates routine maintenance recommendation."""
    recs = evaluate_risk_tier_rules("asmt-01", risk_category="Low Risk", overall_risk=15.0)
    rule_ids = [r.rule_id for r in recs]
    assert "ROUTINE_PREVENTION_MAINTENANCE" in rule_ids
    rec = recs[0]
    assert rec.priority == "LOW"


def test_trend_rules_increased_and_decreased():
    """Increasing or decreasing trends must produce supportive trend insights."""
    recs_inc = evaluate_trend_rules("asmt-01", trend_direction="INCREASED", delta=7.5)
    assert len(recs_inc) == 1
    assert recs_inc[0].rule_id == "TREND_INCREASED_ATTENTION"
    assert recs_inc[0].priority == "MEDIUM"

    recs_dec = evaluate_trend_rules("asmt-01", trend_direction="DECREASED", delta=-5.2)
    assert len(recs_dec) == 1
    assert recs_dec[0].rule_id == "TREND_DECREASING_REINFORCE"
    assert recs_dec[0].priority == "LOW"
