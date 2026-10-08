"""Validation and Phone Masking Utilities for HeartGuard Emergency Alert System.

Provides international phone number validation, privacy-preserving phone masking,
and Twilio credential configuration checks.
"""

from __future__ import annotations

import os
import re
from typing import Any


def validate_phone_number(phone: str | None) -> str:
    """Validate an international or standard phone number.

    Args:
        phone: Raw phone number string (e.g., '+919876543210', '+12025550123').

    Returns:
        str: Normalized stripped phone string.

    Raises:
        ValueError: If phone number is empty, too short, or has invalid characters.
    """
    if phone is None or not str(phone).strip():
        raise ValueError("Phone number cannot be empty.")

    cleaned = re.sub(r"[\s\-\(\)\.]", "", str(phone).strip())

    # Check for valid international E.164-like pattern (+ followed by 7 to 15 digits, or 7 to 15 digits)
    pattern = re.compile(r"^\+?[1-9]\d{6,14}$")
    if not pattern.match(cleaned):
        raise ValueError(
            f"Invalid phone number format: '{phone}'. Expected standard international format (e.g. +919876543210)."
        )

    return cleaned


def mask_phone_number(phone: str | None) -> str:
    """Mask a phone number for privacy-compliant UI display.

    Example:
        '+919876543210' -> '+91******3210'
        '1234567890'    -> '12******7890'

    Args:
        phone: Phone number string.

    Returns:
        str: Masked phone number string.
    """
    if not phone or not str(phone).strip():
        return "Not configured"

    raw = str(phone).strip()
    if len(raw) <= 4:
        return "****"

    prefix = raw[:3] if raw.startswith("+") else raw[:2]
    suffix = raw[-4:]
    masked_count = max(3, len(raw) - len(prefix) - len(suffix))

    return f"{prefix}{'*' * masked_count}{suffix}"


def validate_twilio_config(
    account_sid: str | None,
    auth_token: str | None,
    from_number: str | None,
) -> tuple[bool, str]:
    """Validate the presence of required Twilio API credentials.

    Args:
        account_sid: Twilio Account SID.
        auth_token: Twilio Auth Token.
        from_number: Twilio sending phone number.

    Returns:
        tuple[bool, str]: (is_valid, message)
    """
    if not account_sid or not str(account_sid).strip():
        return False, "TWILIO_ACCOUNT_SID is missing or empty."
    if not auth_token or not str(auth_token).strip():
        return False, "TWILIO_AUTH_TOKEN is missing or empty."
    if not from_number or not str(from_number).strip():
        return False, "TWILIO_PHONE_NUMBER is missing or empty."

    # Basic format check for SID (typically starts with AC)
    if not str(account_sid).strip().startswith("AC"):
        return False, "TWILIO_ACCOUNT_SID must start with 'AC'."

    return True, "Twilio configuration valid."


def validate_alert_config() -> dict[str, Any]:
    """Read and validate alert configuration from environment variables.

    Returns:
        dict: Configuration dictionary with credentials, numbers, and flags.
    """
    alerts_enabled_raw = os.getenv("ALERTS_ENABLED", "false").strip().lower()
    alerts_enabled = alerts_enabled_raw in ("true", "1", "yes")

    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.getenv("TWILIO_PHONE_NUMBER", "").strip()

    doctor_phone = os.getenv("DOCTOR_PHONE_NUMBER") or os.getenv("DOCTOR_PHONE", "")
    emergency_phone = os.getenv("EMERGENCY_CONTACT_PHONE_NUMBER") or os.getenv("EMERGENCY_CONTACT_PHONE", "")

    is_twilio_valid, twilio_msg = validate_twilio_config(account_sid, auth_token, from_number)

    return {
        "alerts_enabled": alerts_enabled,
        "is_twilio_valid": is_twilio_valid,
        "twilio_status_message": twilio_msg,
        "account_sid": account_sid,
        "auth_token": auth_token,
        "from_number": from_number,
        "doctor_phone": doctor_phone.strip(),
        "emergency_phone": emergency_phone.strip(),
        "doctor_phone_masked": mask_phone_number(doctor_phone),
        "emergency_phone_masked": mask_phone_number(emergency_phone),
    }
