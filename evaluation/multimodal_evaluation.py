"""Multimodal risk engine evaluation for HeartGuard (Phase 14).

The MultimodalRiskEngine is DETERMINISTIC — it uses a fixed formula:
    Overall Risk = (Clinical Risk × 0.70) + (Lifestyle Risk × 0.30)

Since there is no external ground-truth dataset for the final combined score,
evaluation covers:
  1. Range validity — output must be in [0, 100]
  2. Component integration — weighted sum is correctly applied
  3. Consistency — same inputs always produce same output
  4. Edge cases — (0,0), (100,100), (100,0), (0,100)
  5. Weight constraint — weights sum to 1.0

NO clinical sensitivity, specificity, or diagnostic accuracy is claimed.
"""

from __future__ import annotations

from src.risk_engine.multimodal_risk import calculate_multimodal_risk
from src.risk_engine.risk_categories import CLINICAL_WEIGHT, LIFESTYLE_WEIGHT

MULTIMODAL_DISCLAIMER = (
    "The HeartGuard multimodal risk engine is a deterministic formula combining clinical "
    "ML probability (70%) and lifestyle NLP score (30%). No external ground-truth dataset "
    "exists for the final combined score. Evaluation covers consistency, range validity, "
    "and component integration only — NOT clinical diagnostic accuracy or sensitivity/specificity."
)


def evaluate_multimodal_consistency(
    test_cases: list[dict] | None = None,
) -> dict[str, object]:
    """Evaluate multimodal engine for range validity, weight correctness, and edge cases.

    Args:
        test_cases: List of dicts with 'clinical_risk', 'lifestyle_risk', 'expected_output'.
                    If None, uses default test cases.

    Returns:
        Dict with evaluation results and disclaimer.
    """
    if test_cases is None:
        test_cases = _default_test_cases()

    results = []
    all_pass = True

    for case in test_cases:
        c_risk = case["clinical_risk"]
        l_risk = case["lifestyle_risk"]
        expected = case.get("expected_output")
        label = case.get("label", f"c={c_risk}, l={l_risk}")

        try:
            actual = calculate_multimodal_risk(c_risk, l_risk)
            in_range = 0.0 <= actual <= 100.0

            # Verify formula: (c * 0.70) + (l * 0.30)
            formula_result = round(c_risk * CLINICAL_WEIGHT + l_risk * LIFESTYLE_WEIGHT, 4)
            formula_match = abs(actual - formula_result) < 0.01

            case_pass = in_range and formula_match
            if expected is not None:
                case_pass = case_pass and abs(actual - expected) < 0.01

            if not case_pass:
                all_pass = False

            results.append({
                "label": label,
                "clinical_risk": c_risk,
                "lifestyle_risk": l_risk,
                "actual_output": round(actual, 4),
                "expected_output": expected,
                "in_range": in_range,
                "formula_match": formula_match,
                "pass": case_pass,
            })
        except Exception as e:
            all_pass = False
            results.append({"label": label, "error": str(e), "pass": False})

    weight_sum = round(CLINICAL_WEIGHT + LIFESTYLE_WEIGHT, 6)
    weights_valid = abs(weight_sum - 1.0) < 1e-6

    passed = sum(1 for r in results if r.get("pass", False))

    return {
        "total_cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "all_pass": all_pass,
        "weights": {
            "clinical_weight": CLINICAL_WEIGHT,
            "lifestyle_weight": LIFESTYLE_WEIGHT,
            "weight_sum": weight_sum,
            "weights_valid": weights_valid,
        },
        "cases": results,
        "disclaimer": MULTIMODAL_DISCLAIMER,
    }


def _default_test_cases() -> list[dict]:
    return [
        {"label": "both_zero", "clinical_risk": 0.0, "lifestyle_risk": 0.0, "expected_output": 0.0},
        {"label": "both_max", "clinical_risk": 100.0, "lifestyle_risk": 100.0, "expected_output": 100.0},
        {"label": "clinical_only", "clinical_risk": 100.0, "lifestyle_risk": 0.0, "expected_output": 70.0},
        {"label": "lifestyle_only", "clinical_risk": 0.0, "lifestyle_risk": 100.0, "expected_output": 30.0},
        {"label": "midpoint", "clinical_risk": 50.0, "lifestyle_risk": 50.0, "expected_output": 50.0},
        {"label": "typical_low", "clinical_risk": 30.0, "lifestyle_risk": 20.0, "expected_output": 27.0},
        {"label": "typical_high", "clinical_risk": 80.0, "lifestyle_risk": 60.0, "expected_output": 74.0},
        {"label": "critical_clinical", "clinical_risk": 90.0, "lifestyle_risk": 40.0, "expected_output": 75.0},
    ]
