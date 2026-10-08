"""Alert Manager for HeartGuard Emergency Alert & Notification System (Phase 8).

Orchestrates risk threshold triage, message templating, recipient validation,
idempotent Twilio dispatch, and alert audit logging.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from src.alerts.alert_history import (
    is_alert_already_sent,
    record_alert,
)
from src.alerts.alert_templates import (
    build_critical_doctor_message,
    build_critical_emergency_message,
    build_test_message,
)
from src.alerts.alert_validation import (
    mask_phone_number,
    validate_alert_config,
    validate_phone_number,
)
from src.alerts.twilio_service import TwilioSMSService
from src.risk_engine.risk_categories import (
    CATEGORY_APPOINTMENT,
    CATEGORY_CRITICAL,
    CATEGORY_MONITORING,
    CRITICAL_THRESHOLD,
    get_alert_level,
    get_overall_risk_category,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AlertManager:
    """Central orchestrator for HeartGuard emergency alerts."""

    def __init__(
        self,
        twilio_service: TwilioSMSService | None = None,
        alerts_enabled: bool | None = None,
        doctor_phone: str | None = None,
        emergency_phone: str | None = None,
    ) -> None:
        """Initialise the AlertManager.

        Args:
            twilio_service: Optional TwilioSMSService instance (injectable for unit tests).
            alerts_enabled: Optional boolean override for ALERTS_ENABLED.
            doctor_phone: Optional override for registered doctor phone number.
            emergency_phone: Optional override for emergency contact phone number.
        """
        config = validate_alert_config()

        self._alerts_enabled = (
            alerts_enabled if alerts_enabled is not None else config["alerts_enabled"]
        )
        self._doctor_phone = doctor_phone or config["doctor_phone"]
        self._emergency_phone = emergency_phone or config["emergency_phone"]
        self._twilio_service = twilio_service or TwilioSMSService()

    @property
    def alerts_enabled(self) -> bool:
        """Whether live SMS alerts are enabled in configuration."""
        return self._alerts_enabled

    @property
    def doctor_phone_masked(self) -> str:
        """Privacy-masked registered doctor phone number."""
        return mask_phone_number(self._doctor_phone)

    @property
    def emergency_phone_masked(self) -> str:
        """Privacy-masked emergency contact phone number."""
        return mask_phone_number(self._emergency_phone)

    def process_risk_result(
        self,
        risk_result: dict[str, Any],
        patient_context: dict[str, Any] | None = None,
        assessment_id: str | None = None,
        force_send: bool = False,
    ) -> dict[str, Any]:
        """Process Phase 7 Multimodal Risk Engine result and handle notification flow.

        Args:
            risk_result: Structured result dictionary from MultimodalRiskEngine.
            patient_context: Optional dict with patient_name, age, etc.
            assessment_id: Optional unique assessment identifier.
            force_send: Whether to bypass confirmation and send immediately if critical.

        Returns:
            dict[str, Any]: Complete alert execution and delivery summary.
        """
        # Extract risk metrics from Phase 7 result
        if "combined" in risk_result:
            overall_risk = float(risk_result["combined"].get("risk", 0.0))
            risk_level = risk_result["combined"].get("alert_level") or get_alert_level(overall_risk)
        else:
            overall_risk = float(risk_result.get("overall_risk", 0.0))
            risk_level = get_alert_level(overall_risk)

        # Generate or retain assessment ID
        ass_id = assessment_id or str(uuid.uuid4())[:8]

        # Extract patient demographics if explicitly provided
        p_ctx = patient_context or {}
        if not p_ctx and "clinical" in risk_result and "clinical_data" in risk_result["clinical"]:
            p_ctx = risk_result["clinical"]["clinical_data"]

        patient_name = p_ctx.get("patient_name")
        patient_age = p_ctx.get("age")
        if patient_age is not None:
            try:
                patient_age = int(patient_age)
            except (ValueError, TypeError):
                patient_age = None

        # Build message bodies
        doctor_msg = build_critical_doctor_message(overall_risk, patient_name, patient_age)
        emergency_msg = build_critical_emergency_message(overall_risk, patient_name, patient_age)

        # Check threshold (strictly > 85% for Critical alert)
        alert_triggered = overall_risk > CRITICAL_THRESHOLD

        if not alert_triggered:
            logger.info("Risk score %.2f <= 85.0%%; emergency alert not triggered", overall_risk)
            return {
                "assessment_id": ass_id,
                "overall_risk": round(overall_risk, 2),
                "risk_level": risk_level,
                "alert_triggered": False,
                "notification_status": "NOT_TRIGGERED",
                "sms_attempted": False,
                "demo_mode": not self._alerts_enabled,
                "recipients": {
                    "doctor": "NOT_TRIGGERED",
                    "emergency_contact": "NOT_TRIGGERED",
                },
                "doctor_sms": {"success": False, "status": "not_triggered"},
                "emergency_contact_sms": {"success": False, "status": "not_triggered"},
                "sms_preview": {
                    "doctor_message": doctor_msg,
                    "emergency_contact_message": emergency_msg,
                },
                "doctor_phone_masked": self.doctor_phone_masked,
                "emergency_contact_phone_masked": self.emergency_phone_masked,
            }

        # --- Critical Alert Workflow (>85%) ---
        logger.warning("CRITICAL RISK DETECTED (%.2f%%); processing emergency alert flow", overall_risk)

        # Check if SMS sending is disabled (Demo Mode)
        if not self._alerts_enabled:
            logger.info("Alerts disabled (ALERTS_ENABLED=false); simulating alert flow")
            record_alert(
                assessment_id=ass_id,
                risk_score=overall_risk,
                risk_level=risk_level,
                recipient_type="doctor",
                recipient_phone=self._doctor_phone or "Unconfigured",
                status="DISABLED",
                error_message="Alerts disabled in configuration (Demo Mode).",
            )
            record_alert(
                assessment_id=ass_id,
                risk_score=overall_risk,
                risk_level=risk_level,
                recipient_type="emergency_contact",
                recipient_phone=self._emergency_phone or "Unconfigured",
                status="DISABLED",
                error_message="Alerts disabled in configuration (Demo Mode).",
            )

            return {
                "assessment_id": ass_id,
                "overall_risk": round(overall_risk, 2),
                "risk_level": risk_level,
                "alert_triggered": True,
                "notification_status": "DISABLED",
                "sms_attempted": False,
                "demo_mode": True,
                "recipients": {
                    "doctor": "DISABLED",
                    "emergency_contact": "DISABLED",
                },
                "doctor_sms": {
                    "success": False,
                    "status": "disabled",
                    "reason": "Alerts are disabled in configuration (Demo Mode).",
                },
                "emergency_contact_sms": {
                    "success": False,
                    "status": "disabled",
                    "reason": "Alerts are disabled in configuration (Demo Mode).",
                },
                "sms_preview": {
                    "doctor_message": doctor_msg,
                    "emergency_contact_message": emergency_msg,
                },
                "doctor_phone_masked": self.doctor_phone_masked,
                "emergency_contact_phone_masked": self.emergency_phone_masked,
            }

        # --- Live Mode Transmission ---
        doctor_res: dict[str, Any]
        emergency_res: dict[str, Any]

        # 1. Doctor SMS dispatch
        if not self._doctor_phone:
            doctor_res = {
                "success": False,
                "status": "failed",
                "error": "Doctor phone number is not configured.",
            }
            record_alert(
                assessment_id=ass_id,
                risk_score=overall_risk,
                risk_level=risk_level,
                recipient_type="doctor",
                recipient_phone="None",
                status="FAILED",
                error_message=doctor_res["error"],
            )
        elif is_alert_already_sent(ass_id, "doctor"):
            doctor_res = {
                "success": True,
                "status": "already_sent",
                "message": "Alert already sent for this assessment.",
            }
        else:
            doctor_res = self._twilio_service.send_sms(self._doctor_phone, doctor_msg)
            doc_status = "SUCCESS" if doctor_res["success"] else "FAILED"
            record_alert(
                assessment_id=ass_id,
                risk_score=overall_risk,
                risk_level=risk_level,
                recipient_type="doctor",
                recipient_phone=self._doctor_phone,
                status=doc_status,
                message_sid=doctor_res.get("message_sid"),
                error_message=doctor_res.get("error"),
            )

        # 2. Emergency Contact SMS dispatch
        if not self._emergency_phone:
            emergency_res = {
                "success": False,
                "status": "failed",
                "error": "Emergency contact phone number is not configured.",
            }
            record_alert(
                assessment_id=ass_id,
                risk_score=overall_risk,
                risk_level=risk_level,
                recipient_type="emergency_contact",
                recipient_phone="None",
                status="FAILED",
                error_message=emergency_res["error"],
            )
        elif is_alert_already_sent(ass_id, "emergency_contact"):
            emergency_res = {
                "success": True,
                "status": "already_sent",
                "message": "Alert already sent for this assessment.",
            }
        else:
            emergency_res = self._twilio_service.send_sms(self._emergency_phone, emergency_msg)
            em_status = "SUCCESS" if emergency_res["success"] else "FAILED"
            record_alert(
                assessment_id=ass_id,
                risk_score=overall_risk,
                risk_level=risk_level,
                recipient_type="emergency_contact",
                recipient_phone=self._emergency_phone,
                status=em_status,
                message_sid=emergency_res.get("message_sid"),
                error_message=emergency_res.get("error"),
            )

        # Overall delivery status
        doc_ok = doctor_res.get("success", False)
        em_ok = emergency_res.get("success", False)

        if doc_ok and em_ok:
            overall_notification = "SUCCESS"
        elif doc_ok or em_ok:
            overall_notification = "PARTIAL_SUCCESS"
        else:
            overall_notification = "FAILED"

        return {
            "assessment_id": ass_id,
            "overall_risk": round(overall_risk, 2),
            "risk_level": risk_level,
            "alert_triggered": True,
            "notification_status": overall_notification,
            "sms_attempted": True,
            "demo_mode": False,
            "recipients": {
                "doctor": "SUCCESS" if doc_ok else "FAILED",
                "emergency_contact": "SUCCESS" if em_ok else "FAILED",
            },
            "doctor_sms": doctor_res,
            "emergency_contact_sms": emergency_res,
            "sms_preview": {
                "doctor_message": doctor_msg,
                "emergency_contact_message": emergency_msg,
            },
            "doctor_phone_masked": self.doctor_phone_masked,
            "emergency_contact_phone_masked": self.emergency_phone_masked,
        }

    def send_test_sms(self, recipient_phone: str | None = None) -> dict[str, Any]:
        """Send an explicitly labeled test configuration SMS.

        Args:
            recipient_phone: Optional phone to send test message to (defaults to doctor phone).

        Returns:
            dict: Structured delivery result.
        """
        if not self._alerts_enabled:
            return {
                "success": False,
                "status": "disabled",
                "error": "Alerts are disabled in configuration (ALERTS_ENABLED=false). Test SMS not sent.",
            }

        target_phone = recipient_phone or self._doctor_phone
        if not target_phone:
            return {
                "success": False,
                "status": "failed",
                "error": "No recipient phone number configured for test SMS.",
            }

        test_body = build_test_message()
        res = self._twilio_service.send_sms(target_phone, test_body)

        status_str = "SUCCESS" if res["success"] else "FAILED"
        record_alert(
            assessment_id="test-config",
            risk_score=0.0,
            risk_level="TEST",
            recipient_type="test",
            recipient_phone=target_phone,
            status=status_str,
            message_sid=res.get("message_sid"),
            error_message=res.get("error"),
        )
        return res
