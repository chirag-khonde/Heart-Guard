"""Tests for alert service module."""

import pytest


def test_alert_module_importable():
    """Test that alert service module can be imported."""
    from src.alerts import alert_service

    assert hasattr(alert_service, "send_sms_alert")
    assert hasattr(alert_service, "check_alert_threshold")
    assert hasattr(alert_service, "log_alert")


def test_send_sms_alert():
    """Test that send_sms_alert returns delivery status dictionary."""
    from src.alerts.alert_service import send_sms_alert

    res = send_sms_alert("1234567890", "test")
    assert isinstance(res, dict)
    assert "success" in res


def test_check_alert_threshold():
    """Test check_alert_threshold returns correct boolean."""
    from src.alerts.alert_service import check_alert_threshold

    assert check_alert_threshold(90.0) is True
    assert check_alert_threshold(50.0) is False
    assert check_alert_threshold(85.0) is True


def test_log_alert():
    """Test log_alert returns correct dictionary."""
    from src.alerts.alert_service import log_alert

    result = log_alert("P001", 90.0, "critical")
    assert result["patient_id"] == "P001"
    assert result["risk_score"] == 90.0
    assert result["alert_type"] == "critical"
    assert result["status"] == "pending"
    assert "timestamp" in result
