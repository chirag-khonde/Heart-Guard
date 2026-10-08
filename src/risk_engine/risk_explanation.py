"""Explanation Generator for HeartGuard Multimodal Risk Engine.

Generates transparent clinical narratives explaining the 70/30 weighted
multimodal calculation, primary contributing risk signals, and guidance.
"""

from __future__ import annotations

from typing import Any

DISCLAIMER_TEXT: str = (
    "HeartGuard is an academic/research prototype and is not a medical diagnostic "
    "system. The overall score is an experimental model-based risk assessment and "
    "should not replace evaluation by a qualified healthcare professional."
)


def generate_overall_explanation(result: dict[str, Any]) -> str:
    """Generate a clear, human-readable narrative explaining the multimodal assessment.

    Args:
        result: Structured multimodal risk assessment result dictionary.

    Returns:
        str: Multi-line plain-text explanation narrative.
    """
    clinical_risk = result.get("clinical", {}).get("risk", 0.0)
    lifestyle_risk = result.get("lifestyle", {}).get("risk", 0.0)
    overall_risk = result.get("combined", {}).get("risk", 0.0)
    category = result.get("combined", {}).get("category", "UNKNOWN")
    action = result.get("combined", {}).get("recommended_action", "")
    detected_factors = result.get("lifestyle", {}).get("detected_factors", [])

    lines = [
        f"HeartGuard estimated a clinical model risk of {clinical_risk:.1f}% and a "
        f"lifestyle risk score of {lifestyle_risk:.0f}/100.",
        f"Using the configured 70/30 multimodal weighting (70% clinical ML + 30% lifestyle NLP), "
        f"the resulting overall risk is {overall_risk:.1f}%.",
        f"Assessment Classification: {category}.",
        "",
    ]

    # Lifestyle signals narrative
    if detected_factors:
        factor_names = [f.get("display_name", "").lower() for f in detected_factors]
        if len(factor_names) == 1:
            factor_str = factor_names[0]
        elif len(factor_names) == 2:
            factor_str = f"{factor_names[0]} and {factor_names[1]}"
        else:
            factor_str = f"{', '.join(factor_names[:-1])}, and {factor_names[-1]}"
        lines.append(f"Primary lifestyle signals detected: {factor_str.capitalize()}.")
    else:
        lines.append("Primary lifestyle signals detected: None (no predefined risk factors identified).")

    # Recommended action
    lines.append(f"Recommended action: {action}")
    lines.append("")
    lines.append(f"Disclaimer: {DISCLAIMER_TEXT}")

    return "\n".join(lines)


def format_multimodal_breakdown(result: dict[str, Any]) -> str:
    """Format the numerical breakdown of the 70/30 weighted contributions as text.

    Args:
        result: Assessment result dictionary.

    Returns:
        str: Formatted breakdown string.
    """
    c_risk = result.get("clinical", {}).get("risk", 0.0)
    c_contrib = result.get("contributions", {}).get("clinical", 0.0)
    l_risk = result.get("lifestyle", {}).get("risk", 0.0)
    l_contrib = result.get("contributions", {}).get("lifestyle", 0.0)
    o_risk = result.get("combined", {}).get("risk", 0.0)

    return (
        f"Clinical Risk: {c_risk:.1f}% × 70% = {c_contrib:.2f} pts\n"
        f"Lifestyle Risk: {l_risk:.1f}% × 30% = {l_contrib:.2f} pts\n"
        f"-----------------------------------------\n"
        f"Overall Risk: {o_risk:.2f}%"
    )
