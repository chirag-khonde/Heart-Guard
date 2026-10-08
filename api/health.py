"""Health router for HeartGuard API."""

from __future__ import annotations

from fastapi import APIRouter

from src.health.health_service import (
    get_health_status,
    get_liveness_status,
    get_readiness_status,
)

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health_check():
    return get_health_status()


@router.get("/ready")
async def readiness_check():
    status = get_readiness_status()
    if status["status"] != "ready":
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=status)
    return status


@router.get("/live")
async def liveness_check():
    return get_liveness_status()
