"""HeartGuard Health Service (Phase 16).

Provides lightweight, safe health, readiness, and liveness checks for:
  - Database connectivity (all SQLite databases)
  - ML model artifact availability and integrity
  - File storage accessibility
  - Application configuration validity

Rules:
  - NEVER expose database paths, error tracebacks, or env vars in status output.
  - All checks are fast; do NOT run ML inference on health requests.
  - Designed for Docker HEALTHCHECK, monitoring, and admin status displays.
"""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import (
    APP_URL,
    ASSESSMENTS_DB_PATH,
    AUDIT_DB_PATH,
    AUTH_DB_PATH,
    HEARTGUARD_VERSION,
    MODEL_DIRECTORY,
    REPORT_DIRECTORY,
    REVIEWS_DB_PATH,
    TEMP_DIRECTORY,
    IS_PRODUCTION,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Individual Checks
# ---------------------------------------------------------------------------

def check_database(db_path: Path, db_name: str) -> dict[str, Any]:
    """Check that an SQLite database is reachable and readable.

    Never exposes the file path in the returned dict.
    """
    start = time.monotonic()
    try:
        conn = sqlite3.connect(str(db_path), timeout=3.0)
        conn.execute("SELECT 1")
        conn.close()
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        return {"name": db_name, "status": "ok", "latency_ms": latency_ms}
    except Exception as exc:
        logger.warning("Health check — DB '%s' failed: %s", db_name, type(exc).__name__)
        return {"name": db_name, "status": "error", "error": "database unavailable"}


def check_model_artifacts() -> dict[str, Any]:
    """Check that required ML model files exist on disk."""
    required_files = [
        "random_forest.pkl",
        "preprocessor.pkl",
        "feature_names.json",
        "model_manifest.json",
    ]
    optional_files = [
        "xgboost.pkl",
        "neural_network.pkl",
        "logistic_regression.pkl",
    ]
    missing_required = [f for f in required_files if not (MODEL_DIRECTORY / f).exists()]
    missing_optional = [f for f in optional_files if not (MODEL_DIRECTORY / f).exists()]

    status = "ok" if not missing_required else "error"
    return {
        "status": status,
        "required_files_ok": len(missing_required) == 0,
        "missing_required": missing_required if missing_required else None,
        "missing_optional_count": len(missing_optional),
    }


def check_file_storage() -> dict[str, Any]:
    """Check that report and temp directories are writable."""
    results = {}
    for label, directory in [("reports", REPORT_DIRECTORY), ("temp", TEMP_DIRECTORY)]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            test_file = directory / ".health_check_probe"
            test_file.touch()
            test_file.unlink()
            results[label] = "ok"
        except Exception as exc:
            logger.warning("Storage check '%s' failed: %s", label, type(exc).__name__)
            results[label] = "error"
    overall = "ok" if all(v == "ok" for v in results.values()) else "degraded"
    return {"status": overall, "storage": results}


def check_configuration() -> dict[str, Any]:
    """Check that critical configuration is present and valid."""
    from config.settings import SECRET_KEY_IS_DEFAULT, DEBUG
    issues = []
    if SECRET_KEY_IS_DEFAULT and IS_PRODUCTION:
        issues.append("SECRET_KEY is using default value in production")
    if DEBUG and IS_PRODUCTION:
        issues.append("DEBUG is enabled in production")
    return {
        "status": "ok" if not issues else "warning",
        "issues": issues if issues else None,
    }


# ---------------------------------------------------------------------------
# Aggregate Status
# ---------------------------------------------------------------------------

def get_health_status() -> dict[str, Any]:
    """Run all health checks and return an aggregate status dict.

    Safe for public use — no secrets or paths exposed.
    """
    db_checks = [
        check_database(AUTH_DB_PATH, "auth_db"),
        check_database(AUDIT_DB_PATH, "audit_db"),
        check_database(ASSESSMENTS_DB_PATH, "assessments_db"),
        check_database(REVIEWS_DB_PATH, "reviews_db"),
    ]

    models_check = check_model_artifacts()
    storage_check = check_file_storage()
    config_check = check_configuration()

    db_ok = all(c["status"] == "ok" for c in db_checks)
    models_ok = models_check["status"] == "ok"
    storage_ok = storage_check["status"] == "ok"

    # Overall: healthy only when databases and required models are up
    overall = "healthy" if (db_ok and models_ok) else "degraded"
    if not db_ok or not models_ok:
        overall = "unhealthy"

    return {
        "status": overall,
        "version": HEARTGUARD_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "databases": db_checks,
        "models": models_check,
        "storage": storage_check,
        "configuration": config_check,
    }


def get_system_info() -> dict[str, Any]:
    """Return authorized admin system information.

    Safe for admin display — no secrets or credentials exposed.
    Includes: version, environment, model versions, evaluation version.
    """
    from config.settings import (
        ENVIRONMENT,
        HEARTGUARD_VERSION,
        RECOMMENDATION_ENGINE_VERSION,
        EVALUATION_ENGINE_VERSION,
    )
    from src.ml.model_registry import ModelRegistry

    try:
        registry = ModelRegistry.get()
        model_versions = registry.get_versions()
        models_health = registry.get_health_status()
    except Exception:
        model_versions = {}
        models_health = {"overall": "error", "loaded_count": 0}

    return {
        "application_version": HEARTGUARD_VERSION,
        "environment": ENVIRONMENT,
        "model_versions": model_versions,
        "model_health": models_health["overall"],
        "models_loaded": models_health.get("loaded_count", 0),
        "recommendation_engine_version": RECOMMENDATION_ENGINE_VERSION,
        "evaluation_engine_version": EVALUATION_ENGINE_VERSION,
    }


def get_liveness_status() -> dict[str, str]:
    """Lightweight liveness check — just confirms the process is alive.

    Safe to expose publicly. No secrets, no database queries.
    """
    return {"status": "alive", "version": HEARTGUARD_VERSION}


def get_readiness_status() -> dict[str, Any]:
    """Readiness check — verifies required dependencies are available.

    Returns 'ready' only when all critical dependencies pass.
    """
    db_auth = check_database(AUTH_DB_PATH, "auth_db")
    models = check_model_artifacts()

    ready = db_auth["status"] == "ok" and models["status"] == "ok"
    return {
        "status": "ready" if ready else "not_ready",
        "auth_db": db_auth["status"],
        "models": models["status"],
        "version": HEARTGUARD_VERSION,
    }
