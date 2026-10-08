"""HeartGuard FastAPI Backend Application.

Thin REST API layer wrapping existing Python services.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth_router
from api.assessments import router as assessments_router
from api.dashboard import router as dashboard_router
from api.reviews import router as reviews_router
from api.admin import router as admin_router
from api.recommendations import router as recommendations_router
from api.reports import router as reports_router
from api.security import router as security_router
from api.health import router as health_router
from api.lifestyle import router as lifestyle_router
from api.deps import rate_limit_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="HeartGuard API",
    description="AI-Based Heart Disease Risk Assessment Backend",
    version="1.0.0",
    lifespan=lifespan,
)

_cors_origins = os.getenv(
    "HEARTGUARD_CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(rate_limit_middleware)

app.include_router(auth_router)
app.include_router(assessments_router)
app.include_router(dashboard_router)
app.include_router(reviews_router)
app.include_router(admin_router)
app.include_router(recommendations_router)
app.include_router(reports_router)
app.include_router(security_router)
app.include_router(health_router)
app.include_router(lifestyle_router)


@app.get("/", tags=["root"])
async def root():
    return {"message": "HeartGuard API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
