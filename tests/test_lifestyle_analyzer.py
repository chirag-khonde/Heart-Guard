"""Unit Tests for Lifestyle Text Analyzer (Phase 6).

Comprehensive test coverage verifying keyword detection, phrase matching,
negation handling, disambiguation, scoring, risk categories, and JSON output.
"""

from __future__ import annotations

import json
import pytest

from src.nlp.explanation import (
    generate_lifestyle_summary,
    generate_risk_factor_explanation,
    get_top_lifestyle_risk_factors,
)
from src.nlp.lifestyle_analyzer import (
    MAX_INPUT_CHARACTERS,
    LifestyleAnalyzer,
    analyze_lifestyle_text,
    calculate_lifestyle_score_from_results,
    detect_risk_factors,
)
from src.nlp.risk_lexicon import (
    MAX_LIFESTYLE_SCORE,
    RISK_LEXICON,
)
from src.nlp.scoring import (
    calculate_category_contribution,
    calculate_lifestyle_score,
    get_risk_category,
    get_score_breakdown,
)
from src.nlp.text_preprocessor import (
    ensure_nltk_resources,
    normalize_text,
    normalize_whitespace,
    remove_unnecessary_punctuation,
    tokenize_text,
)


@pytest.fixture
def analyzer() -> LifestyleAnalyzer:
    """Fixture returning a fresh LifestyleAnalyzer instance."""
    return LifestyleAnalyzer()


# ===========================================================================
# 1. Individual Risk Factor Detection
# ===========================================================================


def test_smoking_detection(analyzer: LifestyleAnalyzer):
    """Test detection of smoking and variations."""
    res1 = analyzer.analyze("I smoke about 10 cigarettes a day.")
    cats1 = [f["category"] for f in res1["detected_risk_factors"]]
    assert "smoking" in cats1
    assert res1["lifestyle_score"] == 25

    res2 = analyzer.analyze("Using tobacco and cigars frequently.")
    cats2 = [f["category"] for f in res2["detected_risk_factors"]]
    assert "smoking" in cats2


def test_physical_inactivity_detection(analyzer: LifestyleAnalyzer):
    """Test detection of sedentary habits and physical inactivity."""
    res1 = analyzer.analyze("I work a desk job and have a sedentary lifestyle.")
    cats1 = [f["category"] for f in res1["detected_risk_factors"]]
    assert "physical_inactivity" in cats1
    assert res1["lifestyle_score"] == 15

    res2 = analyzer.analyze("I have no regular exercise.")
    cats2 = [f["category"] for f in res2["detected_risk_factors"]]
    assert "physical_inactivity" in cats2


def test_unhealthy_diet_detection(analyzer: LifestyleAnalyzer):
    """Test detection of unhealthy diet indicators."""
    res1 = analyzer.analyze("I eat a lot of oily food and fast food.")
    cats1 = [f["category"] for f in res1["detected_risk_factors"]]
    assert "unhealthy_diet" in cats1
    assert res1["lifestyle_score"] == 18

    res2 = analyzer.analyze("Eating fried chicken and junk snacks daily.")
    cats2 = [f["category"] for f in res2["detected_risk_factors"]]
    assert "unhealthy_diet" in cats2


def test_poor_sleep_detection(analyzer: LifestyleAnalyzer):
    """Test detection of poor sleep and insomnia."""
    res1 = analyzer.analyze("I suffer from severe insomnia.")
    cats1 = [f["category"] for f in res1["detected_risk_factors"]]
    assert "poor_sleep" in cats1
    assert res1["lifestyle_score"] == 12

    res2 = analyzer.analyze("Getting poor sleep most nights.")
    cats2 = [f["category"] for f in res2["detected_risk_factors"]]
    assert "poor_sleep" in cats2


def test_family_history_detection(analyzer: LifestyleAnalyzer):
    """Test detection of cardiac family history."""
    res1 = analyzer.analyze("Strong family history of heart attack.")
    cats1 = [f["category"] for f in res1["detected_risk_factors"]]
    assert "family_history" in cats1
    assert res1["lifestyle_score"] == 20

    res2 = analyzer.analyze("My father had a heart attack at age 50.")
    cats2 = [f["category"] for f in res2["detected_risk_factors"]]
    assert "family_history" in cats2


def test_alcohol_detection(analyzer: LifestyleAnalyzer):
    """Test detection of alcohol consumption."""
    res1 = analyzer.analyze("I drink beer every weekend.")
    cats1 = [f["category"] for f in res1["detected_risk_factors"]]
    assert "alcohol_use" in cats1
    assert res1["lifestyle_score"] == 10

    res2 = analyzer.analyze("I drink occasionally with friends.")
    cats2 = [f["category"] for f in res2["detected_risk_factors"]]
    assert "alcohol_use" in cats2


# ===========================================================================
# 2. Section 46 Required Test Cases (TEST 1 to TEST 7)
# ===========================================================================


def test_required_case_1(analyzer: LifestyleAnalyzer):
    """TEST 1: 'I smoke about 10 cigarettes a day.' -> Smoking, score 25."""
    res = analyzer.analyze("I smoke about 10 cigarettes a day.")
    cats = [f["category"] for f in res["detected_risk_factors"]]
    assert "smoking" in cats
    assert res["lifestyle_score"] == 25


def test_required_case_2(analyzer: LifestyleAnalyzer):
    """TEST 2: 'I eat oily food and junk food.' -> Unhealthy diet once, score 18."""
    res = analyzer.analyze("I eat oily food and junk food.")
    cats = [f["category"] for f in res["detected_risk_factors"]]
    assert cats == ["unhealthy_diet"]
    assert res["lifestyle_score"] == 18


def test_required_case_3(analyzer: LifestyleAnalyzer):
    """TEST 3: 'I smoke, eat oily food, sleep 5 hours, and do not exercise.' -> 70."""
    res = analyzer.analyze("I smoke, eat oily food, sleep 5 hours, and do not exercise.")
    cats = {f["category"] for f in res["detected_risk_factors"]}
    assert cats == {"smoking", "unhealthy_diet", "poor_sleep", "physical_inactivity"}
    assert res["lifestyle_score"] == 25 + 18 + 12 + 15  # 70


def test_required_case_4(analyzer: LifestyleAnalyzer):
    """TEST 4: 'I do not smoke and I don't drink alcohol.' -> Neither detected."""
    res = analyzer.analyze("I do not smoke and I don't drink alcohol.")
    cats = [f["category"] for f in res["detected_risk_factors"]]
    assert "smoking" not in cats
    assert "alcohol_use" not in cats
    assert res["lifestyle_score"] == 0


def test_required_case_5(analyzer: LifestyleAnalyzer):
    """TEST 5: 'I sleep 8 hours and exercise every morning.' -> Neither detected."""
    res = analyzer.analyze("I sleep 8 hours and exercise every morning.")
    cats = [f["category"] for f in res["detected_risk_factors"]]
    assert "poor_sleep" not in cats
    assert "physical_inactivity" not in cats
    assert res["lifestyle_score"] == 0


def test_required_case_6(analyzer: LifestyleAnalyzer):
    """TEST 6: 'I drink water throughout the day.' -> Alcohol NOT detected."""
    res = analyzer.analyze("I drink water throughout the day.")
    cats = [f["category"] for f in res["detected_risk_factors"]]
    assert "alcohol_use" not in cats
    assert res["lifestyle_score"] == 0


def test_required_case_7(analyzer: LifestyleAnalyzer):
    """TEST 7: 'My father had a heart attack and I smoke.' -> Family History + Smoking = 45."""
    res = analyzer.analyze("My father had a heart attack and I smoke.")
    cats = {f["category"] for f in res["detected_risk_factors"]}
    assert cats == {"family_history", "smoking"}
    assert res["lifestyle_score"] == 20 + 25  # 45


# ===========================================================================
# 3. Score Cap and Real Project Example
# ===========================================================================


def test_score_capped_at_100(analyzer: LifestyleAnalyzer):
    """Verify that score never exceeds 100 when all categories are triggered."""
    text = (
        "I smoke cigarettes, eat lots of oily food, sleep 5 hours, "
        "have a sedentary desk job, drink wine, and have a family history of heart attack."
    )
    res = analyzer.analyze(text)
    assert len(res["detected_risk_factors"]) == 6
    assert res["lifestyle_score"] == 100
    assert res["lifestyle_score"] <= MAX_LIFESTYLE_SCORE


def test_real_project_example(analyzer: LifestyleAnalyzer):
    """Test exact text from specification section 48."""
    text = (
        "I smoke about 10 cigarettes a day, eat a lot of oily food, "
        "work desk job, sleep 5 hours, drink occasionally, no regular "
        "exercise, family history of heart attack."
    )
    res = analyzer.analyze(text)
    cats = {f["category"] for f in res["detected_risk_factors"]}
    expected = {
        "smoking",
        "physical_inactivity",
        "unhealthy_diet",
        "poor_sleep",
        "family_history",
        "alcohol_use",
    }
    assert cats == expected
    assert res["lifestyle_score"] == 100
    assert res["risk_category"] == "CRITICAL"


# ===========================================================================
# 4. Negation Handling & Disambiguation
# ===========================================================================


def test_negation_variations(analyzer: LifestyleAnalyzer):
    """Test various negation forms across categories."""
    assert "smoking" not in [
        f["category"] for f in analyzer.analyze("I never smoke cigarettes.")["detected_risk_factors"]
    ]
    assert "smoking" not in [
        f["category"] for f in analyzer.analyze("I quit smoking last year.")["detected_risk_factors"]
    ]
    assert "unhealthy_diet" not in [
        f["category"] for f in analyzer.analyze("I avoid fast food and junk food.")["detected_risk_factors"]
    ]
    assert "physical_inactivity" not in [
        f["category"] for f in analyzer.analyze("I do not have a sedentary job.")["detected_risk_factors"]
    ]


def test_alcohol_disambiguation_other_drinks(analyzer: LifestyleAnalyzer):
    """Ensure milk, tea, coffee, juice are not classified as alcohol."""
    assert "alcohol_use" not in [
        f["category"] for f in analyzer.analyze("I drink green tea and milk.")["detected_risk_factors"]
    ]
    assert "alcohol_use" not in [
        f["category"] for f in analyzer.analyze("I drink orange juice in the morning.")["detected_risk_factors"]
    ]
    assert "alcohol_use" not in [
        f["category"] for f in analyzer.analyze("I drink 2 cups of coffee.")["detected_risk_factors"]
    ]


def test_sleep_hour_thresholds(analyzer: LifestyleAnalyzer):
    """Verify numeric hour parsing: < 6h is poor sleep; >= 6h is not."""
    res_4h = analyzer.analyze("I only sleep 4 hours a night.")
    assert "poor_sleep" in [f["category"] for f in res_4h["detected_risk_factors"]]

    res_5h = analyzer.analyze("I sleep 5.5 hours daily.")
    assert "poor_sleep" in [f["category"] for f in res_5h["detected_risk_factors"]]

    res_7h = analyzer.analyze("I sleep 7 hours every night.")
    assert "poor_sleep" not in [f["category"] for f in res_7h["detected_risk_factors"]]

    res_9h = analyzer.analyze("I get 9 hours of sleep.")
    assert "poor_sleep" not in [f["category"] for f in res_9h["detected_risk_factors"]]


# ===========================================================================
# 5. Risk Category Mapping Thresholds
# ===========================================================================


def test_risk_category_mapping():
    """Verify exact category thresholds: 0-29 Low, 30-59 Mod, 60-84 High, 85-100 Crit."""
    assert get_risk_category(0) == "LOW"
    assert get_risk_category(25) == "LOW"
    assert get_risk_category(29) == "LOW"
    assert get_risk_category(30) == "MODERATE"
    assert get_risk_category(59) == "MODERATE"
    assert get_risk_category(60) == "HIGH"
    assert get_risk_category(84) == "HIGH"
    assert get_risk_category(85) == "CRITICAL"
    assert get_risk_category(100) == "CRITICAL"


# ===========================================================================
# 6. Edge Cases: Empty, Short, Long Input & JSON Serialization
# ===========================================================================


def test_empty_and_whitespace_input(analyzer: LifestyleAnalyzer):
    """Test empty, whitespace, and None text inputs."""
    res_empty = analyzer.analyze("")
    assert res_empty["lifestyle_score"] == 0
    assert res_empty["risk_category"] == "LOW"
    assert len(res_empty["detected_risk_factors"]) == 0

    res_spaces = analyzer.analyze("   \n\t  ")
    assert res_spaces["lifestyle_score"] == 0

    res_none = analyzer.analyze(None)
    assert res_none["lifestyle_score"] == 0


def test_short_input(analyzer: LifestyleAnalyzer):
    """Test very short single-word/phrase inputs."""
    res1 = analyzer.analyze("smoke")
    assert "smoking" in [f["category"] for f in res1["detected_risk_factors"]]

    res2 = analyzer.analyze("junk food")
    assert "unhealthy_diet" in [f["category"] for f in res2["detected_risk_factors"]]


def test_long_input_within_limit(analyzer: LifestyleAnalyzer):
    """Test long input within the 5000 character limit."""
    filler = "I go about my daily routine calmly. " * 50
    text = filler + "I smoke cigarettes."
    assert len(text) < MAX_INPUT_CHARACTERS
    res = analyzer.analyze(text)
    assert "smoking" in [f["category"] for f in res["detected_risk_factors"]]


def test_long_input_exceeding_limit(analyzer: LifestyleAnalyzer):
    """Test that input exceeding 5000 characters raises ValueError."""
    long_text = "a" * (MAX_INPUT_CHARACTERS + 10)
    with pytest.raises(ValueError, match="exceeds maximum allowed limit"):
        analyzer.analyze(long_text)


def test_json_serialization(analyzer: LifestyleAnalyzer):
    """Ensure complete analysis output is strictly JSON serializable."""
    text = "I smoke cigarettes, drink beer, sleep 5 hours."
    result = analyzer.analyze(text)
    serialized = json.dumps(result, indent=2)
    deserialized = json.loads(serialized)
    assert deserialized["lifestyle_score"] == result["lifestyle_score"]
    assert deserialized["risk_category"] == result["risk_category"]


# ===========================================================================
# 7. Functional Standalone API & Explanations
# ===========================================================================


def test_standalone_functions():
    """Verify standalone functions in src.nlp."""
    res = analyze_lifestyle_text("I smoke cigarettes.")
    assert res["lifestyle_score"] == 25

    cats = detect_risk_factors("I smoke cigarettes.")
    assert cats == ["smoking"]

    score = calculate_lifestyle_score_from_results(res)
    assert score == 25.0


def test_explanation_and_top_factors(analyzer: LifestyleAnalyzer):
    """Test summary generation and top risk factor extraction."""
    text = "I smoke, eat oily food, sleep 5 hours, work a desk job, and my father had a heart attack."
    res = analyzer.analyze(text)
    top_3 = res["top_risk_factors"]
    assert len(top_3) == 3
    # Smoking (25), Family History (20), Unhealthy Diet (18) should be top 3
    assert top_3[0]["category"] == "smoking"
    assert top_3[1]["category"] == "family_history"
    assert top_3[2]["category"] == "unhealthy_diet"

    summary = res["summary"]
    assert "HeartGuard detected" in summary
    assert "Disclaimer" in summary
