"""Lifestyle NLP evaluation for HeartGuard (Phase 14).

The Lifestyle NLP module (LifestyleAnalyzer) is a RULE-BASED system — not a
trained ML model. It uses lexicon matching and scoring.

Since no external labelled test set exists for NLP outputs, evaluation covers:
  1. Text coverage: empty / short text handling
  2. Output range validity: score in [0, 100]
  3. Known-phrase detection accuracy: given text with known risk phrases, verify flags
  4. Negation handling: negated phrases should not be flagged
  5. Consistency: same input always produces same output
"""

from __future__ import annotations

from src.nlp.lifestyle_analyzer import LifestyleAnalyzer

NLP_EVAL_DISCLAIMER = (
    "The HeartGuard lifestyle NLP module is a deterministic rule-based system, not a trained "
    "machine learning model. It has no learned parameters and no external validated labelled "
    "test set. Evaluation covers coverage, output range validity, known-phrase detection, "
    "and consistency — not generalizable classification accuracy."
)


def evaluate_nlp_coverage(
    test_texts: list[str] | None = None,
) -> dict[str, object]:
    """Evaluate NLP coverage on a set of test texts.

    Args:
        test_texts: List of patient narrative strings to test. Uses defaults if None.

    Returns:
        Dict with coverage statistics.
    """
    if test_texts is None:
        test_texts = _default_coverage_texts()

    analyzer = LifestyleAnalyzer()
    results = []
    for text in test_texts:
        try:
            result = analyzer.analyze(text)
            results.append({
                "text_length": len(text),
                "is_empty": len(text.strip()) == 0,
                "is_short": len(text.strip().split()) < 5,
                "score": result.get("lifestyle_risk_score", 0),
                "factors_detected": len(result.get("risk_factors", [])),
                "success": True,
            })
        except Exception as e:
            results.append({"error": str(e), "success": False, "text_length": len(text)})

    empty_count = sum(1 for r in results if r.get("is_empty", False))
    short_count = sum(1 for r in results if r.get("is_short", False) and not r.get("is_empty", False))
    success_count = sum(1 for r in results if r.get("success", False))

    return {
        "total_texts": len(test_texts),
        "success_rate": round(success_count / len(test_texts), 4) if test_texts else 0.0,
        "empty_text_count": empty_count,
        "short_text_count": short_count,
        "results_summary": results,
        "disclaimer": NLP_EVAL_DISCLAIMER,
    }


def evaluate_nlp_range_validity(
    test_texts: list[str] | None = None,
) -> dict[str, object]:
    """Verify NLP output scores are within [0, 100] for all test texts.

    Args:
        test_texts: List of texts to evaluate. Uses defaults if None.

    Returns:
        Dict with range validation results.
    """
    if test_texts is None:
        test_texts = _default_coverage_texts()

    analyzer = LifestyleAnalyzer()
    out_of_range = []
    scores = []

    for i, text in enumerate(test_texts):
        try:
            result = analyzer.analyze(text)
            score = float(result.get("lifestyle_risk_score", 0))
            scores.append(score)
            if not (0.0 <= score <= 100.0):
                out_of_range.append({"index": i, "score": score})
        except Exception as e:
            out_of_range.append({"index": i, "error": str(e)})

    return {
        "total_texts": len(test_texts),
        "out_of_range_count": len(out_of_range),
        "out_of_range_items": out_of_range,
        "range_valid": len(out_of_range) == 0,
        "score_min": round(min(scores), 4) if scores else None,
        "score_max": round(max(scores), 4) if scores else None,
        "score_mean": round(sum(scores) / len(scores), 4) if scores else None,
    }


def evaluate_nlp_known_phrases(
    phrase_test_cases: list[dict] | None = None,
) -> dict[str, object]:
    """Test that known risk phrases are correctly detected.

    Args:
        phrase_test_cases: List of dicts with 'text', 'expected_flags' (category names),
                           and optionally 'should_be_absent' (negated).

    Returns:
        Dict with per-case detection accuracy.
    """
    if phrase_test_cases is None:
        phrase_test_cases = _default_phrase_tests()

    analyzer = LifestyleAnalyzer()
    results = []

    for case in phrase_test_cases:
        text = case["text"]
        expected_present = case.get("expected_flags", [])
        expected_absent = case.get("should_be_absent", [])

        try:
            result = analyzer.analyze(text)
            detected_categories = {f.get("category", "") for f in result.get("risk_factors", [])}

            detected_expected = [c for c in expected_present if c in detected_categories]
            missed_expected = [c for c in expected_present if c not in detected_categories]
            false_present = [c for c in expected_absent if c in detected_categories]

            results.append({
                "text_snippet": text[:80] + "..." if len(text) > 80 else text,
                "expected_present": expected_present,
                "detected": list(detected_categories),
                "correctly_detected": detected_expected,
                "missed": missed_expected,
                "false_present": false_present,
                "pass": len(missed_expected) == 0 and len(false_present) == 0,
            })
        except Exception as e:
            results.append({"error": str(e), "text_snippet": text[:50], "pass": False})

    passed = sum(1 for r in results if r.get("pass", False))
    return {
        "total_cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "accuracy": round(passed / len(results), 4) if results else 0.0,
        "cases": results,
    }


def evaluate_nlp_consistency(
    test_text: str | None = None,
    n_runs: int = 5,
) -> dict[str, object]:
    """Verify that the rule-based NLP produces identical output on repeated runs.

    Args:
        test_text: Input text to test. Defaults to a standard test string.
        n_runs: Number of repeated evaluations.

    Returns:
        Dict with consistency result.
    """
    if test_text is None:
        test_text = "I smoke about 10 cigarettes per day and rarely exercise. I sleep around 5 hours a night."

    analyzer = LifestyleAnalyzer()
    scores = []
    for _ in range(n_runs):
        result = analyzer.analyze(test_text)
        scores.append(float(result.get("lifestyle_risk_score", 0)))

    is_consistent = len(set(scores)) == 1
    return {
        "is_consistent": is_consistent,
        "n_runs": n_runs,
        "scores": scores,
        "message": "Rule-based NLP is deterministic — all runs produced identical output." if is_consistent
                   else f"Inconsistent output detected: {set(scores)}",
    }


def _default_coverage_texts() -> list[str]:
    return [
        "",
        "Hi",
        "I have a healthy lifestyle.",
        "I smoke about 20 cigarettes per day and drink beer every night. I never exercise.",
        "I don't smoke and I jog 3 times a week. I eat balanced meals and sleep 8 hours.",
        "I occasionally have a drink with friends but I mostly avoid alcohol. I walk daily.",
        "Family history of heart disease. I try to sleep well but often only get 5 hours.",
    ]


def _default_phrase_tests() -> list[dict]:
    return [
        {
            "text": "I smoke a pack of cigarettes every day.",
            "expected_flags": ["smoking"],
            "should_be_absent": [],
        },
        {
            "text": "I do not smoke and have never smoked.",
            "expected_flags": [],
            "should_be_absent": ["smoking"],
        },
        {
            "text": "I am completely sedentary and never exercise.",
            "expected_flags": ["physical_inactivity"],
            "should_be_absent": [],
        },
        {
            "text": "I drink alcohol every day, sometimes heavily.",
            "expected_flags": ["alcohol_use"],
            "should_be_absent": [],
        },
    ]
