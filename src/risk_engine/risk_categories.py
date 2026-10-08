"""Risk Categories and Operational Thresholds for HeartGuard Multimodal Risk Engine.

Defines the centralized 70/30 multimodal weights, threshold boundaries,
risk categories, alert levels, and recommended clinical actions based on the
HeartGuard specification.
"""

from __future__ import annotations

# ===========================================================================
# Multimodal Weighting Constants
# ===========================================================================

CLINICAL_WEIGHT: float = 0.70
LIFESTYLE_WEIGHT: float = 0.30

# ===========================================================================
# Operational Thresholds (0 - 100 scale)
# ===========================================================================

# Critical: Risk > 85%
CRITICAL_THRESHOLD: float = 85.0

# Appointment Recommendation: Risk 60% - 85% (inclusive)
APPOINTMENT_THRESHOLD: float = 60.0

# Monitoring: Risk < 60%

# ===========================================================================
# Category Names
# ===========================================================================

CATEGORY_CRITICAL: str = "CRITICAL"
CATEGORY_APPOINTMENT: str = "APPOINTMENT_RECOMMENDED"
CATEGORY_MONITORING: str = "MONITORING"

# Display labels for UI presentation
CATEGORY_DISPLAY_LABELS: dict[str, str] = {
    CATEGORY_CRITICAL: "Critical Risk",
    CATEGORY_APPOINTMENT: "Elevated Risk (Appointment Recommended)",
    CATEGORY_MONITORING: "Low / Moderate Risk (Regular Monitoring)",
}

# Recommended Actions
ACTION_CRITICAL: str = "Immediate medical consultation recommended."
ACTION_APPOINTMENT: str = "Medical appointment recommendation."
ACTION_MONITORING: str = "Regular monitoring recommended."


def get_overall_risk_category(overall_risk: float) -> str:
    """Determine the qualitative risk category from the overall multimodal risk score.

    Rules based on project specification:
        - overall_risk > 85.0:  CRITICAL
        - 60.0 <= overall_risk <= 85.0: APPOINTMENT_RECOMMENDED
        - overall_risk < 60.0:  MONITORING

    Args:
        overall_risk: Overall multimodal risk percentage (0 - 100).

    Returns:
        str: Category constant (CRITICAL, APPOINTMENT_RECOMMENDED, or MONITORING).
    """
    if overall_risk > CRITICAL_THRESHOLD:
        return CATEGORY_CRITICAL
    elif overall_risk >= APPOINTMENT_THRESHOLD:
        return CATEGORY_APPOINTMENT
    else:
        return CATEGORY_MONITORING


def get_recommended_action(overall_risk: float) -> str:
    """Retrieve the non-diagnostic clinical guidance action based on risk score.

    Args:
        overall_risk: Overall multimodal risk percentage (0 - 100).

    Returns:
        str: Guidance recommendation string.
    """
    if overall_risk > CRITICAL_THRESHOLD:
        return ACTION_CRITICAL
    elif overall_risk >= APPOINTMENT_THRESHOLD:
        return ACTION_APPOINTMENT
    else:
        return ACTION_MONITORING


def get_alert_level(overall_risk: float) -> str:
    """Determine the alert escalation level for future notification modules (Phase 8).

    Args:
        overall_risk: Overall multimodal risk percentage (0 - 100).

    Returns:
        str: Alert level string (CRITICAL, APPOINTMENT_RECOMMENDED, or MONITORING).
    """
    return get_overall_risk_category(overall_risk)
