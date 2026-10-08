"""Unit Tests for HeartGuard Multimodal Risk Engine (Phase 7).

Tests 70/30 weighting formula, threshold boundary behavior (60, 85, 85.01),
input validation, category mapping, weighted contributions, and JSON serialization.
"""

from __future__ import annotations

import json
import pytest

from src.risk_engine.multimodal_risk import (
    MultimodalRiskEngine,
    calculate_multimodal_risk,
)
from src.risk_engine.risk_categories import (
    ACTION_APPOINTMENT,
    ACTION_CRITICAL,
    ACTION_MONITORING,
    APPOINTMENT_THRESHOLD,
    CATEGORY_APPOINTMENT,
    CATEGORY_CRITICAL,
    CATEGORY_MONITORING,
    CLINICAL_WEIGHT,
    CRITICAL_THRESHOLD,
    LIFESTYLE_WEIGHT,
    get_alert_level,
    get_overall_risk_category,
    get_recommended_action,
)
from src.risk_engine.risk_explanation import (
    format_multimodal_breakdown,
    generate_overall_explanation,
)
from src.risk_engine.risk_validation import (
    validate_clinical_input,
    validate_clinical_risk,
    validate_lifestyle_input,
    validate_lifestyle_risk,
    validate_overall_risk,
    validate_weights,
)


# ===========================================================================
# 1. 70/30 Multimodal Formula Tests
# ===========================================================================


def test_required_formula_case():
    """TEST 60: clinical = 80, lifestyle = 60 -> (80 * 0.70) + (60 * 0.30) = 74.0."""
    result = calculate_multimodal_risk(80.0, 60.0)
    assert result == 74.0


def test_lifestyle_integration_case():
    """TEST 67: clinical = 80, lifestyle = 70 -> (80 * 0.70) + (70 * 0.30) = 77.0."""
    result = calculate_multimodal_risk(80.0, 70.0)
    assert result == 77.0


def test_zero_risk():
    """Verify 0 clinical + 0 lifestyle = 0 overall."""
    assert calculate_multimodal_risk(0.0, 0.0) == 0.0


def test_max_risk():
    """Verify 100 clinical + 100 lifestyle = 100 overall."""
    assert calculate_multimodal_risk(100.0, 100.0) == 100.0


# ===========================================================================
# 2. Operational Thresholds & Boundary Tests
# ===========================================================================


def test_critical_test_case():
    """TEST 61: clinical = 100, lifestyle = 100 -> overall = 100 -> CRITICAL."""
    overall = calculate_multimodal_risk(100.0, 100.0)
    assert overall == 100.0
    assert get_overall_risk_category(overall) == CATEGORY_CRITICAL
    assert get_alert_level(overall) == CATEGORY_CRITICAL
    assert get_recommended_action(overall) == ACTION_CRITICAL


def test_appointment_test_case():
    """TEST 63: clinical = 80, lifestyle = 60 -> overall = 74 -> APPOINTMENT_RECOMMENDED."""
    overall = calculate_multimodal_risk(80.0, 60.0)
    assert overall == 74.0
    assert get_overall_risk_category(overall) == CATEGORY_APPOINTMENT
    assert get_alert_level(overall) == CATEGORY_APPOINTMENT
    assert get_recommended_action(overall) == ACTION_APPOINTMENT


def test_monitoring_test_case():
    """TEST 62: clinical = 40, lifestyle = 20 -> overall = 34 -> MONITORING."""
    overall = calculate_multimodal_risk(40.0, 20.0)
    assert overall == 34.0
    assert get_overall_risk_category(overall) == CATEGORY_MONITORING
    assert get_alert_level(overall) == CATEGORY_MONITORING
    assert get_recommended_action(overall) == ACTION_MONITORING


def test_boundary_exact_60():
    """TEST 64: overall = 60.0 must belong to APPOINTMENT_RECOMMENDED (60-85 range)."""
    assert get_overall_risk_category(60.0) == CATEGORY_APPOINTMENT
    assert get_recommended_action(60.0) == ACTION_APPOINTMENT


def test_boundary_just_below_60():
    """overall = 59.99 must belong to MONITORING."""
    assert get_overall_risk_category(59.99) == CATEGORY_MONITORING
    assert get_recommended_action(59.99) == ACTION_MONITORING


def test_boundary_exact_85():
    """TEST 65: overall = 85.0 must NOT be Critical (rule is strictly > 85%)."""
    assert get_overall_risk_category(85.0) == CATEGORY_APPOINTMENT
    assert get_overall_risk_category(85.0) != CATEGORY_CRITICAL
    assert get_recommended_action(85.0) == ACTION_APPOINTMENT


def test_boundary_above_85():
    """TEST 66: overall = 85.01 becomes CRITICAL."""
    assert get_overall_risk_category(85.01) == CATEGORY_CRITICAL
    assert get_recommended_action(85.01) == ACTION_CRITICAL


# ===========================================================================
# 3. Input Validation Tests
# ===========================================================================


def test_weight_validation_valid():
    """Ensure standard 0.70 / 0.30 passes validation."""
    validate_weights(0.70, 0.30)
    validate_weights(0.50, 0.50)


def test_weight_validation_invalid_sum():
    """Ensure weights that do not sum to 1.0 raise ValueError."""
    with pytest.raises(ValueError, match="must sum to 1.0"):
        validate_weights(0.80, 0.30)


def test_weight_validation_negative():
    """Ensure negative weights raise ValueError."""
    with pytest.raises(ValueError, match="must be between 0 and 1"):
        validate_weights(-0.10, 1.10)


def test_score_bounds_validation():
    """Ensure risk inputs outside [0, 100] raise ValueError."""
    with pytest.raises(ValueError, match="Clinical risk must be between 0 and 100"):
        validate_clinical_risk(-1.0)

    with pytest.raises(ValueError, match="Clinical risk must be between 0 and 100"):
        validate_clinical_risk(101.0)

    with pytest.raises(ValueError, match="Lifestyle risk must be between 0 and 100"):
        validate_lifestyle_risk(-5.0)

    with pytest.raises(ValueError, match="Lifestyle risk must be between 0 and 100"):
        validate_lifestyle_risk(120.0)

    with pytest.raises(ValueError, match="Overall risk must be between 0 and 100"):
        validate_overall_risk(105.0)


def test_missing_lifestyle_text():
    """TEST 10: Missing lifestyle text must raise ValueError."""
    with pytest.raises(ValueError, match="Lifestyle description is required"):
        validate_lifestyle_input(None)

    with pytest.raises(ValueError, match="Lifestyle description is required"):
        validate_lifestyle_input("")

    with pytest.raises(ValueError, match="Lifestyle description is required"):
        validate_lifestyle_input("   \n\t  ")


def test_excessive_lifestyle_text():
    """Lifestyle text exceeding 5000 characters must raise ValueError."""
    with pytest.raises(ValueError, match="exceeds maximum allowed limit"):
        validate_lifestyle_input("a" * 5001)


def test_missing_clinical_data():
    """TEST 9: Missing clinical fields must raise ValueError."""
    with pytest.raises(ValueError, match="Complete the required clinical information"):
        validate_clinical_input(None)

    with pytest.raises(ValueError, match="Missing fields"):
        # Missing chest_pain_type, resting_bp, etc.
        validate_clinical_input({"age": 55, "sex": 1})


def test_invalid_clinical_bounds():
    """Physiologically impossible values must raise ValueError."""
    bad_data = {
        "age": 200,  # exceeds 150
        "sex": 1,
        "chest_pain_type": 0,
        "resting_bp": 130,
        "cholesterol": 200,
        "fasting_blood_sugar": 0,
        "resting_ecg": 0,
        "max_heart_rate": 150,
        "exercise_angina": 0,
        "st_depression": 1.0,
        "num_major_vessels": 0,
    }
    with pytest.raises(ValueError, match="outside physiological range"):
        validate_clinical_input(bad_data)


# ===========================================================================
# 4. Engine End-to-End & JSON Serialization Tests
# ===========================================================================


@pytest.fixture
def valid_patient() -> dict:
    """Fixture returning valid canonical clinical metrics."""
    return {
        "age": 58,
        "sex": 1,
        "chest_pain_type": 2,
        "resting_bp": 140,
        "cholesterol": 260,
        "fasting_blood_sugar": 0,
        "resting_ecg": 1,
        "max_heart_rate": 145,
        "exercise_angina": 1,
        "st_depression": 2.2,
        "num_major_vessels": 1,
    }


def test_engine_assessment_structure(valid_patient: dict):
    """Verify structured output schema and key values from MultimodalRiskEngine."""
    engine = MultimodalRiskEngine()
    lifestyle_text = "I smoke 10 cigarettes a day, eat oily food, and sleep 5 hours."

    result = engine.assess(valid_patient, lifestyle_text, include_shap=True)

    # Check top-level keys
    assert "clinical" in result
    assert "lifestyle" in result
    assert "weights" in result
    assert "contributions" in result
    assert "combined" in result
    assert "overall_explanation" in result
    assert "disclaimer" in result

    # Check weights
    assert result["weights"]["clinical"] == CLINICAL_WEIGHT
    assert result["weights"]["lifestyle"] == LIFESTYLE_WEIGHT

    # Verify contributions sum to overall risk
    c_contrib = result["contributions"]["clinical"]
    l_contrib = result["contributions"]["lifestyle"]
    overall = result["combined"]["risk"]
    assert pytest.approx(c_contrib + l_contrib, abs=0.05) == overall

    # Check that category and action are populated
    assert result["combined"]["category"] in (CATEGORY_CRITICAL, CATEGORY_APPOINTMENT, CATEGORY_MONITORING)
    assert len(result["combined"]["recommended_action"]) > 0

    # Check explanations
    assert "HeartGuard estimated" in result["overall_explanation"]
    assert "Disclaimer" in result["overall_explanation"]


def test_engine_json_serialization(valid_patient: dict):
    """TEST 15: Ensure complete assessment result is strictly JSON serializable."""
    engine = MultimodalRiskEngine()
    lifestyle_text = "I work a desk job, rarely exercise, and drink wine on weekends."

    result = engine.assess(valid_patient, lifestyle_text, include_shap=False)
    serialized = json.dumps(result, indent=2)
    deserialized = json.loads(serialized)

    assert deserialized["combined"]["risk"] == result["combined"]["risk"]
    assert deserialized["combined"]["category"] == result["combined"]["category"]


def test_explanation_formatting(valid_patient: dict):
    """Verify narrative and breakdown text generation."""
    engine = MultimodalRiskEngine()
    lifestyle_text = "I drink water and sleep 8 hours."
    result = engine.assess(valid_patient, lifestyle_text, include_shap=False)

    narrative = generate_overall_explanation(result)
    assert "HeartGuard estimated" in narrative
    assert "multimodal weighting" in narrative

    breakdown = format_multimodal_breakdown(result)
    assert "Clinical Risk:" in breakdown
    assert "Lifestyle Risk:" in breakdown
    assert "Overall Risk:" in breakdown
