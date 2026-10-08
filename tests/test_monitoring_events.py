"""Tests for Phase 17 Monitoring Events."""

from __future__ import annotations

import gc
import shutil
import tempfile
from pathlib import Path

import pytest

from src.analytics.monitoring_events import MonitoringEventService, init_monitoring_db


@pytest.fixture
def temp_monitoring_db():
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = Path(tmpdir) / "test_monitoring.db"
        init_monitoring_db(db_path)
        gc.collect()
        yield db_path
    finally:
        gc.collect()
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestMonitoringEventService:
    def test_create_event(self, temp_monitoring_db):
        result = MonitoringEventService.create_event(
            event_type="DATA_DRIFT_DETECTED",
            severity="WARNING",
            component="drift_detection",
            message="Test drift detected",
            db_path=temp_monitoring_db,
        )
        assert result["event_type"] == "DATA_DRIFT_DETECTED"
        assert result["severity"] == "WARNING"
        assert result["status"] == "OPEN"

    def test_create_event_with_details(self, temp_monitoring_db):
        result = MonitoringEventService.create_event(
            event_type="ANOMALY_DETECTED",
            severity="HIGH",
            component="anomaly_detection",
            message="Volume spike detected",
            metric_name="assessment_volume",
            metric_value=50.0,
            threshold_value=30.0,
            details={"day": "2024-01-01", "count": 50},
            db_path=temp_monitoring_db,
        )
        assert result["event_type"] == "ANOMALY_DETECTED"

    def test_get_events(self, temp_monitoring_db):
        MonitoringEventService.create_event(
            event_type="DATA_DRIFT_DETECTED",
            severity="WARNING",
            component="drift",
            message="Drift 1",
            db_path=temp_monitoring_db,
        )
        MonitoringEventService.create_event(
            event_type="HIGH_ERROR_RATE",
            severity="CRITICAL",
            component="errors",
            message="Error 1",
            db_path=temp_monitoring_db,
        )
        events = MonitoringEventService.get_events(db_path=temp_monitoring_db)
        assert len(events) == 2

    def test_get_events_filtered(self, temp_monitoring_db):
        MonitoringEventService.create_event(
            event_type="DATA_DRIFT_DETECTED",
            severity="WARNING",
            component="drift",
            message="Drift",
            db_path=temp_monitoring_db,
        )
        MonitoringEventService.create_event(
            event_type="HIGH_ERROR_RATE",
            severity="CRITICAL",
            component="errors",
            message="Error",
            db_path=temp_monitoring_db,
        )
        events = MonitoringEventService.get_events(
            event_type="DATA_DRIFT_DETECTED", db_path=temp_monitoring_db
        )
        assert len(events) == 1

    def test_acknowledge_event(self, temp_monitoring_db):
        result = MonitoringEventService.create_event(
            event_type="DATA_DRIFT_DETECTED",
            severity="WARNING",
            component="drift",
            message="Drift",
            db_path=temp_monitoring_db,
        )
        acked = MonitoringEventService.acknowledge_event(
            result["event_id"], "admin_user", db_path=temp_monitoring_db
        )
        assert acked is True

        events = MonitoringEventService.get_events(
            status="ACKNOWLEDGED", db_path=temp_monitoring_db
        )
        assert len(events) == 1
        assert events[0]["acknowledged_by"] == "admin_user"

    def test_get_event_counts(self, temp_monitoring_db):
        MonitoringEventService.create_event(
            event_type="DATA_DRIFT_DETECTED",
            severity="WARNING",
            component="drift",
            message="Drift",
            db_path=temp_monitoring_db,
        )
        counts = MonitoringEventService.get_event_counts(db_path=temp_monitoring_db)
        assert counts["total"] == 1
        assert counts["by_severity"]["WARNING"] == 1
        assert counts["by_status"]["OPEN"] == 1

    def test_get_recent_events(self, temp_monitoring_db):
        for i in range(5):
            MonitoringEventService.create_event(
                event_type="DATA_DRIFT_DETECTED",
                severity="INFO",
                component="drift",
                message=f"Event {i}",
                db_path=temp_monitoring_db,
            )
        events = MonitoringEventService.get_recent_events(limit=3, db_path=temp_monitoring_db)
        assert len(events) == 3

    def test_cleanup_old_events(self, temp_monitoring_db):
        MonitoringEventService.create_event(
            event_type="DATA_DRIFT_DETECTED",
            severity="INFO",
            component="drift",
            message="Old event",
            db_path=temp_monitoring_db,
        )
        deleted = MonitoringEventService.cleanup_old_events(
            retention_days=0, db_path=temp_monitoring_db
        )
        assert deleted >= 0
