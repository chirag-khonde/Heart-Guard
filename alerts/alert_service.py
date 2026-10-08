"""Emergency alert service module for HeartGuard (Phase 8).

Provides convenience functional entry points and backward compatibility
for the HeartGuard alert subsystem.
"""

from __future__ import annotations

from typing import Any

from src.alerts.alert_history import record_alert
from src.alerts.alert_manager import AlertManager
from src.alerts.alert_validation import validate_alert_config
from src.alerts.twilio_service import TwilioSMSService
from src.risk_engine.risk_categories import CRITICAL_THRESHOLD
from src.utils.logger import get_logger

logger = get_logger(__name__)


def send_sms_alert(
    phone_number: str,
    message: str,
) -> dict[str, Any]:
    """Send an SMS alert via Twilio service.

    Args:
        phone_number: Recipient phone number.
        message: Alert message text.

    Returns:
        dict: Delivery status and message metadata.
    """
    service = TwilioSMSService()
    return service.send_sms(phone_number, message)


def check_alert_threshold(risk_score: float, threshold: float = CRITICAL_THRESHOLD) -> bool:
    """Check if risk score meets or exceeds the emergency alert threshold (>= 85%).

    Args:
        risk_score: Patient risk score (0 - 100).
        threshold: Alert threshold value (default: 85.0).

    Returns:
        bool: True if alert threshold is reached.
    """
    return risk_score >= threshold


def log_alert(
    patient_id: str,
    risk_score: float,
    alert_type: str,
    status: str = "pending",
) -> dict[str, Any]:
    """Log an alert event to the persistent audit repository.

    Args:
        patient_id: Patient identifier.
        risk_score: Risk score that triggered alert.
        alert_type: Type of alert (e.g. 'critical').
        status: Alert delivery status.

    Returns:
        dict: Recorded alert dictionary.
    """
    res = record_alert(
        assessment_id=patient_id,
        risk_score=risk_score,
        risk_level=alert_type.upper(),
        recipient_type="general",
        recipient_phone="Unspecified",
        status=status.upper(),
    )
    # Backward-compatible alias keys
    res["patient_id"] = patient_id
    res["alert_type"] = alert_type
    res["status"] = status
    return res
