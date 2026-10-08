"""Admin router for HeartGuard API."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import CurrentUser, require_role
from src.analytics.analytics_service import AnalyticsService
from src.analytics.data_quality_monitoring import DataQualityMonitor
from src.analytics.drift_detection import DriftDetector
from src.analytics.model_monitoring import ModelMonitoringService
from src.analytics.performance_monitoring import PerformanceMonitor
from src.auth.user_repository import UserRepository
from src.health.health_service import get_health_status, get_system_info
from src.security.audit_logger import get_audit_statistics, get_filtered_events

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/analytics")
async def get_analytics(
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    return AnalyticsService.get_admin_aggregated_analytics()


@router.get("/monitoring/model-status")
async def get_model_status(
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    return ModelMonitoringService.get_model_status_summary()


@router.get("/monitoring/model-comparison")
async def get_model_comparison(
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    return ModelMonitoringService.get_model_comparison()


@router.get("/monitoring/drift")
async def get_drift(
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    return DriftDetector.get_drift_summary_from_assessments()


@router.get("/monitoring/data-quality")
async def get_data_quality(
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    return DataQualityMonitor.assess_data_quality()


@router.get("/monitoring/performance")
async def get_performance(
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    return PerformanceMonitor.get_system_performance_summary()


@router.get("/health")
async def get_health(
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    return get_health_status()


@router.get("/audit")
async def get_audit_log(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    events, total = get_filtered_events(
        limit=limit,
        offset=offset,
        event_type=event_type,
        role=role,
        status=status,
        category=category,
        severity=severity,
        search_query=search,
    )
    return {
        "events": events,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/audit/stats")
async def get_audit_stats(
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    return get_audit_statistics()


@router.get("/users")
async def list_users(
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    users = UserRepository.list_users()
    return [u.to_safe_dict() for u in users]
