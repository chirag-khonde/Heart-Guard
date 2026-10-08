"""Alert security and dispatch hardening tests for HeartGuard Phase 9.

Verifies:
- AlertManager respects risk threshold (triggers strictly > 85%).
- Twilio integration is isolated with mocks; no external network calls.
- Duplicate alerts for the same assessment are suppressed (idempotency).
- Phone numbers are masked in all audit logs and outputs.
- Demo mode safely prevents dispatch without throwing exceptions.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.alerts.alert_history import init_alert_db, is_alert_already_sent, record_alert
from src.alerts.alert_manager import AlertManager
from src.alerts.twilio_service import TwilioSMSService


@pytest.fixture()
def tmp_alerts_db(tmp_path: Path, monkeypatch) -> Path:
    """Fixture to ensure all alert persistence uses an isolated temp SQLite DB."""
    db_file = tmp_path / "test_alerts.db"
    init_alert_db(db_file)
    import src.alerts.alert_history
    import src.alerts.alert_manager

    monkeypatch.setattr(src.alerts.alert_history, "DB_PATH", db_file)
    return db_file


@pytest.fixture()
def mock_twilio_service() -> MagicMock:
    """Mock TwilioSMSService that records calls without sending SMS."""
    service = MagicMock(spec=TwilioSMSService)
    service.send_sms.return_value = {
        "success": True,
        "message_sid": "SMmock1234567890abcdef",
        "status": "queued",
        "error": None,
    }
    return service


# ---------------------------------------------------------------------------
# 1. Threshold Triage Security
# ---------------------------------------------------------------------------


def test_alert_not_triggered_for_non_critical_risk(tmp_alerts_db, mock_twilio_service):
    """Risk scores at or below 85% must never trigger an emergency SMS dispatch."""
    manager = AlertManager(
        twilio_service=mock_twilio_service,
        alerts_enabled=True,
        doctor_phone="+15551234567",
        emergency_phone="+15559876543",
    )

    # Moderate / high risk score (84.9%)
    phase7_output = {
        "combined": {
            "risk": 84.9,
            "category": "HIGH",
            "alert_level": "MONITORING",
        }
    }

    result = manager.process_risk_result(phase7_output, assessment_id="ASSESS_001")

    assert result["alert_triggered"] is False
    assert result["notification_status"] == "NOT_TRIGGERED"
    assert result["sms_attempted"] is False
    mock_twilio_service.send_sms.assert_not_called()


def test_alert_triggered_for_critical_risk(tmp_alerts_db, mock_twilio_service):
    """Risk score strictly > 85% triggers dispatch to configured numbers."""
    manager = AlertManager(
        twilio_service=mock_twilio_service,
        alerts_enabled=True,
        doctor_phone="+15551234567",
        emergency_phone="+15559876543",
    )

    phase7_output = {
        "combined": {
            "risk": 91.5,
            "category": "CRITICAL",
            "alert_level": "CRITICAL",
        }
    }

    result = manager.process_risk_result(phase7_output, assessment_id="ASSESS_002")

    assert result["alert_triggered"] is True
    assert mock_twilio_service.send_sms.call_count == 2
    assert result["doctor_sms"]["success"] is True
    assert result["emergency_contact_sms"]["success"] is True


# ---------------------------------------------------------------------------
# 2. Demo Mode Safety
# ---------------------------------------------------------------------------


def test_demo_mode_does_not_dispatch_sms(tmp_alerts_db, mock_twilio_service):
    """When alerts_enabled is False, no SMS is sent even for critical risk."""
    manager = AlertManager(
        twilio_service=mock_twilio_service,
        alerts_enabled=False,
        doctor_phone="+15551234567",
        emergency_phone="+15559876543",
    )

    critical_output = {
        "combined": {
            "risk": 98.0,
            "category": "CRITICAL",
            "alert_level": "CRITICAL",
        }
    }

    result = manager.process_risk_result(critical_output, assessment_id="ASSESS_DEMO")

    assert result["alert_triggered"] is True
    assert result["demo_mode"] is True
    assert result["sms_attempted"] is False
    mock_twilio_service.send_sms.assert_not_called()


# ---------------------------------------------------------------------------
# 3. Deduplication & Idempotency
# ---------------------------------------------------------------------------


def test_duplicate_alert_suppression(tmp_alerts_db, mock_twilio_service):
    """Subsequent attempts with the same assessment_id are prevented from double-sending."""
    manager = AlertManager(
        twilio_service=mock_twilio_service,
        alerts_enabled=True,
        doctor_phone="+15551234567",
        emergency_phone="+15559876543",
    )

    critical_output = {
        "combined": {
            "risk": 89.0,
            "category": "CRITICAL",
            "alert_level": "CRITICAL",
        }
    }

    # First run sends
    res1 = manager.process_risk_result(critical_output, assessment_id="ASSESS_DEDUP")
    assert mock_twilio_service.send_sms.call_count == 2
    assert res1["doctor_sms"]["status"] != "already_sent"

    # Second run with same assessment_id must detect already_sent
    res2 = manager.process_risk_result(critical_output, assessment_id="ASSESS_DEDUP")
    # Call count should NOT increase
    assert mock_twilio_service.send_sms.call_count == 2
    assert res2["doctor_sms"]["status"] == "already_sent"
    assert res2["emergency_contact_sms"]["status"] == "already_sent"


# ---------------------------------------------------------------------------
# 4. Patient & Clinician Privacy (Phone Masking)
# ---------------------------------------------------------------------------


def test_phone_numbers_masked_in_output_and_properties(tmp_alerts_db):
    """Phone numbers exposed in UI results must be masked."""
    manager = AlertManager(
        alerts_enabled=False,
        doctor_phone="+15551234567",
        emergency_phone="+15559876543",
    )

    assert "+15551234567" not in manager.doctor_phone_masked
    assert "+15559876543" not in manager.emergency_phone_masked
    assert manager.doctor_phone_masked.startswith("+1")
    assert manager.doctor_phone_masked.endswith("4567")

    result = manager.process_risk_result(
        {"overall_risk": 50.0},
        assessment_id="ASSESS_MASK",
    )
    assert result["doctor_phone_masked"] == manager.doctor_phone_masked
    assert result["emergency_contact_phone_masked"] == manager.emergency_phone_masked


def test_alert_records_store_masked_phone(tmp_alerts_db):
    """Database records must persist only masked phone numbers."""
    record = record_alert(
        assessment_id="ASSESS_PRIVACY",
        risk_score=92.0,
        risk_level="CRITICAL",
        recipient_type="doctor",
        recipient_phone="+15551234567",
        status="SUCCESS",
        db_path=tmp_alerts_db,
    )
    assert "+15551234567" not in record["recipient_masked"]
    assert record["recipient_masked"].endswith("4567")
