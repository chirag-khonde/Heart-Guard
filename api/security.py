"""Security router for HeartGuard API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from api.deps import CurrentUser, get_current_user
from src.security.audit_logger import get_audit_statistics, get_filtered_events

router = APIRouter(prefix="/api/security", tags=["security"])


@router.get("/audit")
async def get_my_audit_log(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    events, total = get_filtered_events(
        limit=limit,
        offset=offset,
        event_type=event_type,
        status=status,
        category=category,
        severity=severity,
        search_query=search,
        user_id=current_user.user_id,
    )
    return {
        "events": events,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
