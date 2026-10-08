"""Explanation Module for HeartGuard Lifestyle Text Analyzer.

Generates patient-friendly, human-readable explanations and identifies top
detected lifestyle risk factors with appropriate research disclaimers.
"""

from __future__ import annotations

from typing import Any

DISCLAIMER_TEXT: str = (
    "HeartGuard is an academic/research prototype and is not a medical diagnostic "
    "system. The Lifestyle Risk Score is a rule-based project indicator and should "
    "not be interpreted as a clinically validated cardiovascular risk score."
)


def get_top_lifestyle_risk_factors(
    detected_factors: list[dict[str, Any]],
    top_n: int = 3,
) -> list[dict[str, Any]]:
    """Sort detected factors by risk points descending and return the top N.

    Args:
        detected_factors: List of detected risk factor dictionaries.
        top_n: Number of top factors to return (default: 3).

    Returns:
        List of top factor dictionaries.
    """
    if not detected_factors:
        return []

    # Sort primarily by risk_points descending, secondarily by display_name
    sorted_factors = sorted(
        detected_factors,
        key=lambda f: (f.get("risk_points", 0), f.get("display_name", "")),
        reverse=True,
    )
    return sorted_factors[:top_n]


def generate_risk_factor_explanation(factor: dict[str, Any]) -> str:
    """Generate a single descriptive explanation sentence for a detected factor.

    Args:
        factor: Factor dictionary containing display_name, risk_points,
            severity, and evidence/matched_terms.

    Returns:
        str: Descriptive sentence.
    """
    display_name = factor.get("display_name", "Unknown Factor")
    pts = factor.get("risk_points", 0)
    severity = factor.get("severity", "Unspecified")
    evidence = factor.get("evidence", "")

    if evidence:
        return f"{display_name} (+{pts} pts, {severity} severity): Evidence found '{evidence}'."
    return f"{display_name} (+{pts} pts, {severity} severity)."


def generate_lifestyle_summary(
    detected_factors: list[dict[str, Any]],
    score: int,
    category: str,
) -> str:
    """Generate a comprehensive, human-readable summary of the lifestyle analysis.

    Args:
        detected_factors: List of detected factor dictionaries.
        score: Aggregated lifestyle score (0-100).
        category: Qualitative risk category (LOW, MODERATE, HIGH, CRITICAL).

    Returns:
        str: Plain English multi-line narrative.
    """
    if not detected_factors:
        return (
            "No predefined lifestyle risk factors were detected in the provided description.\n"
            f"Lifestyle risk score: 0/100 ({category}).\n\n"
            f"Disclaimer: {DISCLAIMER_TEXT}"
        )

    names = [f.get("display_name", "").lower() for f in detected_factors]
    if len(names) == 1:
        factor_list_str = names[0]
    elif len(names) == 2:
        factor_list_str = f"{names[0]} and {names[1]}"
    else:
        factor_list_str = f"{', '.join(names[:-1])}, and {names[-1]}"

    lines = [
        f"HeartGuard detected {factor_list_str} in the provided lifestyle description.",
        f"These findings produced a lifestyle risk score of {score}/100 ({category}).",
        "",
        "Detected factor details:",
    ]

    for factor in detected_factors:
        d_name = factor.get("display_name", "")
        pts = factor.get("risk_points", 0)
        sev = factor.get("severity", "")
        terms = ", ".join(factor.get("matched_terms", []))
        lines.append(f"  - {d_name} (+{pts} pts, {sev} severity) [matched: '{terms}']")

    lines.append("")
    lines.append(f"Disclaimer: {DISCLAIMER_TEXT}")

    return "\n".join(lines)
