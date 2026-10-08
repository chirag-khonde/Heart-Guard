"""Twilio SMS Service for HeartGuard Emergency Alert System.

Wraps the Twilio Python SDK for sending emergency notifications with error
isolation, input validation, and credential security.
"""

from __future__ import annotations

import os
from typing import Any

from src.alerts.alert_validation import validate_phone_number, validate_twilio_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TwilioSMSService:
    """Wrapper service for Twilio SMS operations."""

    def __init__(
        self,
        account_sid: str | None = None,
        auth_token: str | None = None,
        from_number: str | None = None,
        client: Any = None,
    ) -> None:
        """Initialise the Twilio SMS service.

        Args:
            account_sid: Optional Twilio Account SID (defaults to env var).
            auth_token: Optional Twilio Auth Token (defaults to env var).
            from_number: Optional Twilio phone number (defaults to env var).
            client: Optional injected Twilio client (useful for unit tests).
        """
        self._account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        self._auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        self._from_number = from_number or os.getenv("TWILIO_PHONE_NUMBER", "").strip()
        self._client = client

    def is_configured(self) -> bool:
        """Check if all required Twilio credentials are provided.

        Returns:
            bool: True if configuration credentials are valid.
        """
        valid, _ = validate_twilio_config(self._account_sid, self._auth_token, self._from_number)
        return valid

    def validate_configuration(self) -> tuple[bool, str]:
        """Validate credentials and return configuration status message."""
        return validate_twilio_config(self._account_sid, self._auth_token, self._from_number)

    def _get_client(self) -> Any:
        """Retrieve or lazily instantiate the Twilio REST Client."""
        if self._client is not None:
            return self._client

        from twilio.rest import Client

        self._client = Client(self._account_sid, self._auth_token)
        return self._client

    def send_sms(self, to: str, body: str) -> dict[str, Any]:
        """Send an SMS notification to the designated recipient.

        Args:
            to: Recipient phone number (international format).
            body: Text message content.

        Returns:
            dict: Structured result containing success, message_sid, status, and optional error.
        """
        if not self.is_configured():
            _, reason = self.validate_configuration()
            logger.warning("Twilio SMS transmission aborted: %s", reason)
            return {
                "success": False,
                "message_sid": None,
                "status": "failed",
                "error": f"Twilio is not properly configured: {reason}",
            }

        try:
            valid_to = validate_phone_number(to)
            client = self._get_client()

            message = client.messages.create(
                body=body,
                from_=self._from_number,
                to=valid_to,
            )

            msg_sid = getattr(message, "sid", "mock_sid")
            msg_status = getattr(message, "status", "queued")

            logger.info("Twilio SMS sent successfully (SID: %s, Status: %s)", msg_sid, msg_status)
            return {
                "success": True,
                "message_sid": msg_sid,
                "status": msg_status or "queued",
                "error": None,
            }

        except Exception as exc:
            # Safe sanitization to never leak credentials or secrets
            clean_err = str(exc)
            if self._auth_token and self._auth_token in clean_err:
                clean_err = clean_err.replace(self._auth_token, "[REDACTED]")
            if self._account_sid and self._account_sid in clean_err:
                clean_err = clean_err.replace(self._account_sid, "[REDACTED]")

            logger.error("Twilio SMS delivery failed: %s", clean_err)
            return {
                "success": False,
                "message_sid": None,
                "status": "failed",
                "error": f"SMS transmission error: {clean_err}",
            }
