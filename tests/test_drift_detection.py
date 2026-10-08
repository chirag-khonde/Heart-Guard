"""Tests for Phase 17 Drift Detection."""

from __future__ import annotations

import numpy as np
import pytest

from src.analytics.drift_detection import (
    DriftDetector,
    _psi,
    _jensen_shannon_divergence,
    _categorical_psi,
)


class TestDriftDetection:
    """Test suite for drift detection functions."""

    def test_psi_no_drift(self):
        np.random.seed(42)
        ref = np.random.normal(50, 10, 100)
        cur = np.random.normal(50, 10, 100)
        psi = _psi(ref, cur)
        assert psi < 0.10

    def test_psi_with_drift(self):
        np.random.seed(42)
        ref = np.random.normal(50, 10, 100)
        cur = np.random.normal(70, 10, 100)
        psi = _psi(ref, cur)
        assert psi > 0.10

    def test_jensen_shannon_identical(self):
        p = np.array([0.25, 0.25, 0.25, 0.25])
        q = np.array([0.25, 0.25, 0.25, 0.25])
        js = _jensen_shannon_divergence(p, q)
        assert js < 0.01

    def test_jensen_shannon_different(self):
        p = np.array([0.9, 0.05, 0.03, 0.02])
        q = np.array([0.02, 0.03, 0.05, 0.9])
        js = _jensen_shannon_divergence(p, q)
        assert js > 0.1

    def test_categorical_psi_no_drift(self):
        ref = {"A": 50, "B": 50}
        cur = {"A": 50, "B": 50}
        psi = _categorical_psi(ref, cur)
        assert psi < 0.01

    def test_categorical_psi_with_drift(self):
        ref = {"A": 90, "B": 10}
        cur = {"A": 10, "B": 90}
        psi = _categorical_psi(ref, cur)
        assert psi > 0.5

    def test_detect_numerical_drift_no_drift(self):
        np.random.seed(42)
        ref = np.random.normal(50, 10, 100)
        cur = np.random.normal(50, 10, 100)
        result = DriftDetector.detect_numerical_drift(ref, cur, "age")
        assert result["status"] == "HEALTHY"
        assert result["feature"] == "age"

    def test_detect_numerical_drift_with_drift(self):
        np.random.seed(42)
        ref = np.random.normal(50, 10, 100)
        cur = np.random.normal(80, 10, 100)
        result = DriftDetector.detect_numerical_drift(ref, cur, "age")
        assert result["status"] in ("WARNING", "DRIFT_DETECTED")

    def test_detect_numerical_drift_insufficient_data(self):
        ref = np.array([1.0, 2.0, 3.0])
        cur = np.array([4.0, 5.0, 6.0])
        result = DriftDetector.detect_numerical_drift(ref, cur, "age")
        assert result["status"] == "INSUFFICIENT_DATA"

    def test_detect_categorical_drift_no_drift(self):
        ref = {"0": 50, "1": 50}
        cur = {"0": 50, "1": 50}
        result = DriftDetector.detect_categorical_drift(ref, cur, "sex")
        assert result["status"] == "HEALTHY"

    def test_detect_categorical_drift_with_drift(self):
        ref = {"0": 90, "1": 10}
        cur = {"0": 10, "1": 90}
        result = DriftDetector.detect_categorical_drift(ref, cur, "sex")
        assert result["status"] in ("WARNING", "DRIFT_DETECTED")

    def test_detect_categorical_drift_insufficient_data(self):
        ref = {"0": 5, "1": 5}
        cur = {"0": 3, "1": 3}
        result = DriftDetector.detect_categorical_drift(ref, cur, "sex")
        assert result["status"] == "INSUFFICIENT_DATA"

    def test_detect_prediction_drift(self):
        ref = ["Low"] * 50 + ["High"] * 50
        cur = ["Low"] * 50 + ["High"] * 50
        result = DriftDetector.detect_prediction_drift(ref, cur)
        assert result["status"] == "HEALTHY"

    def test_detect_prediction_drift_shifted(self):
        ref = ["Low"] * 80 + ["High"] * 20
        cur = ["Low"] * 20 + ["High"] * 80
        result = DriftDetector.detect_prediction_drift(ref, cur)
        assert result["status"] in ("WARNING", "DRIFT_DETECTED")

    def test_detect_prediction_drift_insufficient(self):
        ref = ["Low"] * 5
        cur = ["High"] * 5
        result = DriftDetector.detect_prediction_drift(ref, cur)
        assert result["status"] == "INSUFFICIENT_DATA"

    def test_run_full_drift_analysis(self):
        reference = {
            "numerical": {"age": list(np.random.normal(50, 10, 100))},
            "categorical": {"sex": {"0": 50, "1": 50}},
        }
        current = {
            "numerical": {"age": list(np.random.normal(50, 10, 100))},
            "categorical": {"sex": {"0": 50, "1": 50}},
        }
        result = DriftDetector.run_full_drift_analysis(reference, current)
        assert "overall_status" in result
        assert "numerical_features" in result
        assert "categorical_features" in result

    def test_run_full_drift_analysis_with_drift(self):
        reference = {
            "numerical": {"age": list(np.random.normal(50, 10, 100))},
            "categorical": {"sex": {"0": 90, "1": 10}},
        }
        current = {
            "numerical": {"age": list(np.random.normal(80, 10, 100))},
            "categorical": {"sex": {"0": 10, "1": 90}},
        }
        result = DriftDetector.run_full_drift_analysis(reference, current)
        assert result["overall_status"] in ("WARNING", "DRIFT_DETECTED")
