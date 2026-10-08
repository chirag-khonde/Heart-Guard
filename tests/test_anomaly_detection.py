"""Tests for Phase 17 Anomaly Detection."""

from __future__ import annotations

import pytest

from src.analytics.anomaly_detection import AnomalyDetector


class TestAnomalyDetector:
    def test_detect_volume_anomaly_normal(self):
        history = [10, 12, 11, 10, 13, 12, 11, 10, 12, 11]
        result = AnomalyDetector.detect_volume_anomaly(history, 12)
        assert result["status"] == "HEALTHY"

    def test_detect_volume_anomaly_spike(self):
        history = [10, 12, 11, 10, 13, 12, 11, 10, 12, 11]
        result = AnomalyDetector.detect_volume_anomaly(history, 50)
        assert result["status"] == "WARNING"

    def test_detect_volume_anomaly_insufficient(self):
        history = [10, 12]
        result = AnomalyDetector.detect_volume_anomaly(history, 12)
        assert result["status"] == "INSUFFICIENT_DATA"

    def test_detect_distribution_anomaly_normal(self):
        ref = {"A": 50, "B": 50}
        cur = {"A": 50, "B": 50}
        result = AnomalyDetector.detect_distribution_anomaly(ref, cur, "test")
        assert result["status"] == "HEALTHY"

    def test_detect_distribution_anomaly_shifted(self):
        ref = {"A": 90, "B": 10}
        cur = {"A": 10, "B": 90}
        result = AnomalyDetector.detect_distribution_anomaly(ref, cur, "test")
        assert result["status"] == "WARNING"

    def test_detect_error_rate_anomaly_normal(self):
        result = AnomalyDetector.detect_error_rate_anomaly(1000, 10)
        assert result["status"] == "HEALTHY"
        assert result["error_rate"] == 0.01

    def test_detect_error_rate_anomaly_high(self):
        result = AnomalyDetector.detect_error_rate_anomaly(100, 10)
        assert result["status"] == "WARNING"

    def test_detect_error_rate_anomaly_no_events(self):
        result = AnomalyDetector.detect_error_rate_anomaly(0, 0)
        assert result["status"] == "INSUFFICIENT_DATA"

    def test_run_comprehensive_anomaly_detection(self):
        result = AnomalyDetector.run_comprehensive_anomaly_detection()
        assert "checks" in result
        assert "overall_status" in result
        assert "assessment_volume" in result["checks"]
        assert "prediction_distribution" in result["checks"]
