"""Tests for lifestyle analyzer module integration."""

import pytest


def test_lifestyle_module_importable():
    """Test that lifestyle analyzer module can be imported."""
    from src.nlp import lifestyle_analyzer

    assert hasattr(lifestyle_analyzer, "analyze_lifestyle_text")
    assert hasattr(lifestyle_analyzer, "detect_risk_factors")
    assert hasattr(lifestyle_analyzer, "LifestyleAnalyzer")


def test_analyze_lifestyle_text_works():
    """Test that analyze_lifestyle_text returns analysis dict."""
    from src.nlp.lifestyle_analyzer import analyze_lifestyle_text

    res = analyze_lifestyle_text("I smoke 10 cigarettes a day.")
    assert res["lifestyle_score"] == 25
    assert res["risk_category"] == "LOW"
    assert len(res["detected_risk_factors"]) == 1


def test_detect_risk_factors_works():
    """Test that detect_risk_factors returns risk factor names."""
    from src.nlp.lifestyle_analyzer import detect_risk_factors

    factors = detect_risk_factors("I eat oily food and smoke.")
    assert "smoking" in factors
    assert "unhealthy_diet" in factors
