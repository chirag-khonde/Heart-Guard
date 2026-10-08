"""Tests for Phase 17 Performance Metrics."""

from __future__ import annotations

import gc
import shutil
import tempfile
from pathlib import Path

import pytest

from src.analytics.performance_monitoring import PerformanceMonitor


@pytest.fixture
def temp_perf_db():
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = Path(tmpdir) / "test_perf.db"
        gc.collect()
        yield db_path
    finally:
        gc.collect()
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestPerformanceMonitor:
    def test_record_metric(self, temp_perf_db):
        PerformanceMonitor.record_metric(
            "inference", "random_forest_latency", 150.5, "ms", db_path=temp_perf_db
        )

    def test_record_inference_latency(self, temp_perf_db):
        PerformanceMonitor.record_inference_latency(
            "random_forest", 150.5, db_path=temp_perf_db
        )

    def test_record_request(self, temp_perf_db):
        PerformanceMonitor.record_request("/predict", 200, 100.0, db_path=temp_perf_db)

    def test_record_error(self, temp_perf_db):
        PerformanceMonitor.record_error("ml", "prediction_error", db_path=temp_perf_db)

    def test_get_metric_summary(self, temp_perf_db):
        for i in range(5):
            PerformanceMonitor.record_metric(
                "inference", "test_latency", 100.0 + i * 10, "ms", db_path=temp_perf_db
            )
        result = PerformanceMonitor.get_metric_summary(
            "inference", "test_latency", hours=1, db_path=temp_perf_db
        )
        assert result["count"] == 5
        assert result["avg_value"] > 0

    def test_get_error_summary(self, temp_perf_db):
        PerformanceMonitor.record_request("/test", 200, 50.0, db_path=temp_perf_db)
        PerformanceMonitor.record_error("test", "error", db_path=temp_perf_db)
        result = PerformanceMonitor.get_error_summary(hours=1, db_path=temp_perf_db)
        assert result["total_errors"] == 1
        assert result["total_requests"] == 1

    def test_get_system_performance_summary(self, temp_perf_db):
        result = PerformanceMonitor.get_system_performance_summary(hours=1, db_path=temp_perf_db)
        assert "inference_latency" in result
        assert "errors" in result
        assert "overall_status" in result

    def test_get_latency_trend(self, temp_perf_db):
        result = PerformanceMonitor.get_latency_trend(hours=1, db_path=temp_perf_db)
        assert isinstance(result, list)
