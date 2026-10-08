"""Safety validator for HeartGuard AI Recommendations (Phase 13).

Ensures that all generated recommendations adhere to strict clinical safety constraints:
  - Strictly NON-DIAGNOSTIC: Never asserts confirmed medical conditions or diagnoses.
  - Strictly NON-PRESCRIPTIVE: Never references medication names, dosages, or drug schedules.
  - Tentative phrasing: Enforces advisory guidance language ("Consider...", "Discuss with...").
"""

from __future__ import annotations

import re
from typing import Any
from src.recommendations.recommendation_models import PRIORITIES

# Disallowed diagnostic assertions
DIAGNOSTIC_TERMS = [
    r"\byou have heart disease\b",
    r"\byou have had a heart attack\b",
    r"\byou are diagnosed with\b",
    r"\bdiagnosed with\b",
    r"\bwe diagnose\b",
    r"\bheart attack detected\b",
    r"\bdefinitely have\b",
    r"\bconfirmed diagnosis\b",
    r"\bproven heart disease\b",
    r"\bguaranteed cure\b",
    r"\bwill cure\b",
    r"\bwill prevent all\b",
]

# Disallowed pharmaceutical / medication terms
MEDICATION_TERMS = [
    r"\bstatin\b",
    r"\batorvastatin\b",
    r"\brosuvastatin\b",
    r"\baspirin\b",
    r"\blisinopril\b",
    r"\bamlodipine\b",
    r"\bmetoprolol\b",
    r"\bbeta blocker\b",
    r"\bace inhibitor\b",
    r"\bnitroglycerin\b",
    r"\bwarfarin\b",
    r"\bclopidogrel\b",
    r"\bmetformin\b",
    r"\bhydrochlorothiazide\b",
    r"\bprescription\b",
    r"\bprescribe\b",
    r"\bdosage\b",
    r"\b\d+\s*mg\b",
    r"\btablet\b",
    r"\bpill\b",
    r"\bcapsule\b",
    r"\btake daily\b",
]

PRESCRIPTION_TERMS = MEDICATION_TERMS

# Unsupported claims and imperative guarantees
UNSUPPORTED_CLAIMS = [
    r"\bwill cure\b",
    r"\bwill prevent all\b",
    r"\bguaranteed cure\b",
    r"\bstop everything immediately\b",
]


class SafetyValidationError(ValueError):
    """Raised when a recommendation violates safety or non-diagnostic policies."""


def validate_recommendation(
    recommendation: Any,
    raise_on_error: bool = False,
) -> tuple[bool, str]:
    """Validate that a recommendation strictly complies with medical safety standards.

    Args:
        recommendation: Dict or Recommendation object to validate.
        raise_on_error: If True, raises SafetyValidationError instead of returning False.

    Returns:
        tuple[bool, str]: (is_valid, failure_reason)
    """
    if isinstance(recommendation, dict):
        title = str(recommendation.get("title", ""))
        desc = str(recommendation.get("description", ""))
        priority = str(recommendation.get("priority", ""))
    else:
        title = str(getattr(recommendation, "title", ""))
        desc = str(getattr(recommendation, "description", ""))
        priority = str(getattr(recommendation, "priority", ""))

    if not title.strip():
        reason = "Recommendation title cannot be empty."
        if raise_on_error:
            raise SafetyValidationError(reason)
        return False, reason

    if not desc.strip():
        reason = "Recommendation description cannot be empty."
        if raise_on_error:
            raise SafetyValidationError(reason)
        return False, reason

    if priority and priority not in PRIORITIES:
        reason = f"Invalid priority '{priority}'. Must be one of {PRIORITIES}."
        if raise_on_error:
            raise SafetyValidationError(reason)
        return False, reason

    full_text = f"{title} {desc}".lower()

    # 1. Check for diagnostic claims
    for pattern in DIAGNOSTIC_TERMS:
        if re.search(pattern, full_text, re.IGNORECASE):
            reason = f"Prohibited diagnostic claim detected matching '{pattern}'."
            if raise_on_error:
                raise SafetyValidationError(reason)
            return False, reason

    # 2. Check for pharmaceutical / prescription terms
    for pattern in MEDICATION_TERMS:
        if re.search(pattern, full_text, re.IGNORECASE):
            reason = f"Prohibited medication or prescription terms detected matching '{pattern}'."
            if raise_on_error:
                raise SafetyValidationError(reason)
            return False, reason

    # 3. Check for imperative / unsupported claims
    for pattern in UNSUPPORTED_CLAIMS:
        if re.search(pattern, full_text, re.IGNORECASE):
            reason = f"Prohibited absolute or imperative claim detected matching '{pattern}'."
            if raise_on_error:
                raise SafetyValidationError(reason)
            return False, reason

    return True, ""
