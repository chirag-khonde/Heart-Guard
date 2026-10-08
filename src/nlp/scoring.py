"""Scoring Module for HeartGuard Lifestyle Text Analyzer.

Implements rule-based lifestyle risk point aggregation, capping at 100,
and mapping into transparent risk categories (LOW, MODERATE, HIGH, CRITICAL).
"""

from __future__ import annotations

from typing import Any

from src.nlp.risk_lexicon import MAX_LIFESTYLE_SCORE, RISK_LEXICON


def calculate_lifestyle_score(detected_factors: list[dict[str, Any]]) -> int:
    """Calculate the aggregated lifestyle risk score from detected factors.

    The score is the sum of unique detected risk category points, capped at 100.

    Args:
        detected_factors: List of detected factor dictionaries, each containing
            at least 'category' and 'risk_points'.

    Returns:
        int: Capped integer score between 0 and 100.
    """
    if not detected_factors:
        return 0

    # Ensure each category is counted at most once
    seen_categories: set[str] = set()
    total_score: int = 0

    for factor in detected_factors:
        cat = factor.get("category", "")
        if cat and cat not in seen_categories:
            seen_categories.add(cat)
            pts = factor.get("risk_points", 0)
            total_score += int(pts)

    # Cap score strictly at 100
    capped_score = min(total_score, MAX_LIFESTYLE_SCORE)
    return capped_score


def get_risk_category(score: int | float) -> str:
    """Map a numerical lifestyle risk score (0-100) to its qualitative category.

    Thresholds:
        0 - 29:   LOW
        30 - 59:  MODERATE
        60 - 84:  HIGH
        85 - 100: CRITICAL

    Args:
        score: Numerical score.

    Returns:
        str: Category name ("LOW", "MODERATE", "HIGH", or "CRITICAL").
    """
    val = max(0, min(int(round(score)), 100))

    if val <= 29:
        return "LOW"
    elif val <= 59:
        return "MODERATE"
    elif val <= 84:
        return "HIGH"
    else:
        return "CRITICAL"


def calculate_category_contribution(
    category: str,
    detected_factors: list[dict[str, Any]],
) -> int:
    """Retrieve the points contributed by a specific category.

    Args:
        category: Lexicon category key (e.g., 'smoking').
        detected_factors: List of detected factor dicts.

    Returns:
        int: Risk points (0 if not detected).
    """
    for factor in detected_factors:
        if factor.get("category") == category:
            return int(factor.get("risk_points", 0))
    return 0


def get_score_breakdown(
    detected_factors: list[dict[str, Any]],
) -> dict[str, Any]:
    """Provide a full category-by-category score breakdown.

    Args:
        detected_factors: List of detected factor dictionaries.

    Returns:
        dict containing total_score, category, and per-category details.
    """
    total = calculate_lifestyle_score(detected_factors)
    category = get_risk_category(total)

    breakdown_by_category: dict[str, int] = {}
    for cat_key in RISK_LEXICON:
        breakdown_by_category[cat_key] = calculate_category_contribution(
            cat_key, detected_factors
        )

    return {
        "lifestyle_score": total,
        "risk_category": category,
        "max_score": MAX_LIFESTYLE_SCORE,
        "category_scores": breakdown_by_category,
        "total_detected_factors": len(detected_factors),
    }
