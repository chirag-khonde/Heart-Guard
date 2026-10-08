"""Dashboard router for HeartGuard API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.deps import CurrentUser, get_current_user
from src.analytics.analytics_service import AnalyticsService
from src.analytics.history_service import HistoryService
from src.analytics.trend_service import TrendService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardResponse(BaseModel):
    statistics: dict[str, Any]
    latest_assessment: dict[str, Any] | None
    recent_assessments: list[dict[str, Any]]
    trends: list[dict[str, Any]]
    # Top-level analytics fields expected by frontend
    risk_trend: list[dict[str, Any]] = []
    risk_distribution: dict[str, int] = {}
    total_assessments: int = 0
    avg_risk: float = 0.0
    low_risk_count: int = 0
    critical_alerts: int = 0


@router.get("", response_model=DashboardResponse)
async def get_dashboard(current_user: CurrentUser = Depends(get_current_user)):
    stats = AnalyticsService.calculate_user_statistics(user_id=current_user.user_id)

    latest = HistoryService.get_latest_assessment(user_id=current_user.user_id)
    latest_dict = latest.to_dict() if latest else None

    recent = AnalyticsService.get_user_recent_assessments(
        user_id=current_user.user_id,
        limit=5,
    )

    raw_trends = TrendService.get_risk_trends(user_id=current_user.user_id)
    cat_dist = AnalyticsService.get_category_distribution(user_id=current_user.user_id)

    formatted_trends = []
    for t in raw_trends:
        item = dict(t)
        score = item.get("overall_risk", 0.0)
        item["risk_score"] = score
        item["date"] = str(item.get("date", ""))
        formatted_trends.append(item)

    total_assessments = int(stats.get("total_assessments", 0))
    avg_risk = float(stats.get("average_overall_risk") or 0.0)
    critical_count = int(stats.get("critical_count", 0))
    low_risk_count = int(cat_dist.get("LOW", 0) + cat_dist.get("Low", 0))

    return DashboardResponse(
        statistics=stats,
        latest_assessment=latest_dict,
        recent_assessments=recent,
        trends=formatted_trends,
        risk_trend=formatted_trends,
        risk_distribution=cat_dist,
        total_assessments=total_assessments,
        avg_risk=round(avg_risk, 1),
        low_risk_count=low_risk_count,
        critical_alerts=critical_count,
    )
