"""Tests for Recommendation Engine safety, non-diagnostic phrasing, and medical boundary enforcement (Phase 13)."""

import pytest

from src.recommendations.recommendation_models import Recommendation
from src.recommendations.recommendation_validator import (
    DIAGNOSTIC_TERMS,
    PRESCRIPTION_TERMS,
    validate_recommendation,
)


def test_validate_safe_recommendation():
    """A normal, non-diagnostic guidance recommendation must validate cleanly."""
    rec = Recommendation(
        assessment_id="asmt-001",
        category="Physical Activity",
        title="Consider increasing daily movement",
        description="Gradually introducing 20-30 minutes of moderate activity may support cardiovascular wellness.",
        priority="MEDIUM",
        source="Lifestyle Data",
        rule_id="PHYSICAL_ACTIVITY_BOOST",
    )
    is_valid, reason = validate_recommendation(rec)
    assert is_valid is True
    assert reason == ""


@pytest.mark.parametrize(
    "diagnostic_phrase",
    [
        "You have heart disease.",
        "You have had a heart attack recently.",
        "You are diagnosed with cardiac arrest.",
        "You definitely have hypertension.",
        "We diagnose you with coronary artery disease.",
    ],
)
def test_validate_rejects_diagnostic_claims(diagnostic_phrase):
    """Safety validator must strictly reject any diagnostic statements."""
    rec = Recommendation(
        assessment_id="asmt-001",
        category="Clinical Follow-up",
        title="Diagnostic Alert",
        description=diagnostic_phrase,
        priority="HIGH",
        source="Rule Engine",
        rule_id="BAD_DIAGNOSTIC_RULE",
    )
    is_valid, reason = validate_recommendation(rec)
    assert is_valid is False
    assert "diagnostic claim" in reason.lower()


@pytest.mark.parametrize(
    "prescription_phrase",
    [
        "Take aspirin 81mg daily.",
        "Start atorvastatin 20mg immediately.",
        "We prescribe lisinopril 10 mg for your blood pressure.",
        "Take 500mg metformin with meals.",
        "Take 25mg hydrochlorothiazide as prescribed.",
    ],
)
def test_validate_rejects_prescriptions_and_medications(prescription_phrase):
    """Safety validator must strictly reject medication names, prescriptions, and dosages."""
    rec = Recommendation(
        assessment_id="asmt-001",
        category="Nutrition",
        title="Prescription Recommendation",
        description=prescription_phrase,
        priority="HIGH",
        source="Rule Engine",
        rule_id="BAD_PRESCRIPTION_RULE",
    )
    is_valid, reason = validate_recommendation(rec)
    assert is_valid is False
    assert "medication" in reason.lower() or "prescription" in reason.lower() or "dosage" in reason.lower()


@pytest.mark.parametrize(
    "absolute_phrase",
    [
        "This will cure your cardiovascular issues permanently.",
        "Following this will prevent all heart problems.",
        "You must stop everything immediately.",
    ],
)
def test_validate_rejects_unsupported_or_imperative_claims(absolute_phrase):
    """Safety validator must reject cure/prevention guarantees and imperative commands."""
    rec = Recommendation(
        assessment_id="asmt-001",
        category="Lifestyle",
        title="Overstated Claim",
        description=absolute_phrase,
        priority="MEDIUM",
        source="Rule Engine",
        rule_id="BAD_CLAIM_RULE",
    )
    is_valid, reason = validate_recommendation(rec)
    assert is_valid is False
