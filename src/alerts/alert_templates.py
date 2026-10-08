"""Message Templates for HeartGuard Emergency Alert System.

Provides concise, privacy-preserving notification templates for doctors,
emergency family contacts, and test transmissions.
"""

from __future__ import annotations


def build_critical_doctor_message(
    overall_risk: float,
    patient_name: str | None = None,
    age: int | None = None,
) -> str:
    """Build SMS message body for registered physician upon critical risk detection.

    Args:
        overall_risk: Overall multimodal risk score (0 - 100).
        patient_name: Optional patient name if explicitly provided.
        age: Optional patient age if explicitly provided.

    Returns:
        str: Formatted SMS message.
    """
    clean_name = str(patient_name).strip() if patient_name else None

    if clean_name and age is not None:
        return (
            f"HeartGuard ALERT: Patient {clean_name}, Age {age}, has been flagged as "
            f"CRITICAL risk ({overall_risk:.1f}%). Immediate consultation is recommended. "
            f"Please review the HeartGuard assessment."
        )
    elif clean_name:
        return (
            f"HeartGuard ALERT: Patient {clean_name} has been flagged as "
            f"CRITICAL risk ({overall_risk:.1f}%). Immediate consultation is recommended. "
            f"Please review the HeartGuard assessment."
        )
    else:
        return (
            f"HeartGuard ALERT: A patient has been flagged as CRITICAL risk "
            f"({overall_risk:.1f}%). Immediate medical consultation is recommended. "
            f"Please review the HeartGuard assessment."
        )


def build_critical_emergency_message(
    overall_risk: float,
    patient_name: str | None = None,
    age: int | None = None,
) -> str:
    """Build SMS message body for emergency contact / family member upon critical risk.

    Args:
        overall_risk: Overall multimodal risk score (0 - 100).
        patient_name: Optional patient name if explicitly provided.
        age: Optional patient age if explicitly provided.

    Returns:
        str: Formatted SMS message.
    """
    clean_name = str(patient_name).strip() if patient_name else None

    if clean_name:
        return (
            f"HeartGuard ALERT: Patient {clean_name} has been flagged as CRITICAL "
            f"cardiovascular risk ({overall_risk:.1f}%). Immediate medical consultation is "
            f"recommended. Please contact or assist them immediately."
        )
    else:
        return (
            f"HeartGuard ALERT: Your family member has been flagged as CRITICAL "
            f"cardiovascular risk ({overall_risk:.1f}%). Immediate medical consultation is "
            f"recommended. Please contact or assist them immediately."
        )


def build_test_message() -> str:
    """Build clearly-labeled test message for configuration verification.

    Returns:
        str: Test SMS body.
    """
    return (
        "HeartGuard Test Alert: This is a configuration test. "
        "No medical alert is being issued."
    )


def build_appointment_message(overall_risk: float) -> str:
    """Build informational text for elevated risk (non-emergency)."""
    return (
        f"HeartGuard: Elevated risk detected ({overall_risk:.1f}%). "
        f"Medical appointment recommendation."
    )


def build_monitoring_message(overall_risk: float) -> str:
    """Build informational text for lower risk (non-emergency)."""
    return (
        f"HeartGuard: Lower risk ({overall_risk:.1f}%). "
        f"Regular health monitoring recommended."
    )
