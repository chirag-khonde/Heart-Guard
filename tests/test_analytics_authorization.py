"""Tests for Phase 17 Analytics Authorization."""

from __future__ import annotations

import gc
import json
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.analytics.analytics_service import AnalyticsService
from src.analytics.history_service import HistoryService
from src.analytics.models import Assessment, init_assessment_db


@pytest.fixture
def temp_db():
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = Path(tmpdir) / "test_auth.db"
        init_assessment_db(db_path)
        now = datetime.now(timezone.utc).isoformat()
        for i in range(3):
            asmt = Assessment(
                assessment_id=f"u1-{i:04d}",
                user_id=1,
                created_at=now,
                clinical_risk=50.0 + i * 5,
                lifestyle_risk=30.0 + i * 3,
                overall_risk=44.0 + i * 4,
                risk_category="Low",
                recommendation="Monitor",
                model_version="v1",
                narrative_summary="Test",
                alert_status="NOT_TRIGGERED",
            )
            HistoryService.save_assessment(asmt, db_path=db_path)
        for i in range(2):
            asmt = Assessment(
                assessment_id=f"u2-{i:04d}",
                user_id=2,
                created_at=now,
                clinical_risk=60.0 + i * 5,
                lifestyle_risk=35.0 + i * 3,
                overall_risk=52.0 + i * 4,
                risk_category="Elevated",
                recommendation="Review",
                model_version="v1",
                narrative_summary="Test",
                alert_status="NOT_TRIGGERED",
            )
            HistoryService.save_assessment(asmt, db_path=db_path)
        gc.collect()
        yield db_path
    finally:
        gc.collect()
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestAnalyticsAuthorization:
    """Test patient data isolation in analytics."""

    def test_user_only_sees_own_assessments(self, temp_db):
        user1_stats = AnalyticsService.calculate_user_statistics(user_id=1, db_path=temp_db)
        user2_stats = AnalyticsService.calculate_user_statistics(user_id=2, db_path=temp_db)
        assert user1_stats["total_assessments"] == 3
        assert user2_stats["total_assessments"] == 2

    def test_user_category_distribution_isolation(self, temp_db):
        user1_dist = AnalyticsService.get_category_distribution(user_id=1, db_path=temp_db)
        user2_dist = AnalyticsService.get_category_distribution(user_id=2, db_path=temp_db)
        assert "Low" in user1_dist
        assert "Elevated" in user2_dist

    def test_user_assessments_are_isolated(self, temp_db):
        user1_assessments = HistoryService.get_user_assessments(user_id=1, db_path=temp_db)
        user2_assessments = HistoryService.get_user_assessments(user_id=2, db_path=temp_db)
        for a in user1_assessments:
            assert a.user_id == 1
        for a in user2_assessments:
            assert a.user_id == 2

    def test_admin_aggregated_analytics_no_pii(self, temp_db):
        result = AnalyticsService.get_admin_aggregated_analytics(db_path=temp_db)
        assert "total_assessments" in result
        assert "active_patients" in result
        assert "category_distribution" in result
        for key in result:
            if isinstance(result[key], str):
                assert "@" not in result[key]

    def test_user_owns_assessment(self, temp_db):
        assert HistoryService.user_owns_assessment(1, "u1-0000", db_path=temp_db)
        assert not HistoryService.user_owns_assessment(2, "u1-0000", db_path=temp_db)

    def test_assessment_by_id_with_user_filter(self, temp_db):
        result = HistoryService.get_assessment_by_id("u1-0000", user_id=1, db_path=temp_db)
        assert result is not None
        result = HistoryService.get_assessment_by_id("u1-0000", user_id=2, db_path=temp_db)
        assert result is None
