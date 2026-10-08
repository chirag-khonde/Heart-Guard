"""HeartGuard Startup Validator (Phase 16).

Validates critical configuration and dependencies at application startup.

Rules:
  - NEVER print secret values.
  - Block production launch with insecure SECRET_KEY.
  - Log errors without exposing sensitive environment details.
  - Fast execution — only checks, no ML inference.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    passed: bool = True
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    blocked: bool = False  # True if startup should be halted


def validate_environment() -> ValidationResult:
    """Validate environment variables and production configuration."""
    from config.settings import (
        ENVIRONMENT,
        SECRET_KEY_IS_DEFAULT,
        DEBUG,
        IS_PRODUCTION,
    )

    result = ValidationResult()

    if ENVIRONMENT not in ("development", "testing", "production"):
        result.warnings.append(
            f"Unknown ENVIRONMENT value '{ENVIRONMENT}'. Expected: development, testing, production."
        )

    if IS_PRODUCTION and SECRET_KEY_IS_DEFAULT:
        result.errors.append(
            "CRITICAL: SECRET_KEY is set to the insecure default value in production. "
            "Set a strong random SECRET_KEY via environment variable."
        )
        result.passed = False
        result.blocked = True
        logger.critical("Startup blocked — insecure SECRET_KEY in production.")

    if IS_PRODUCTION and DEBUG:
        result.errors.append(
            "CRITICAL: DEBUG=True is not allowed in production. Set DEBUG=false."
        )
        result.passed = False
        result.blocked = True
        logger.critical("Startup blocked — DEBUG enabled in production.")

    return result


def validate_model_artifacts() -> ValidationResult:
    """Validate that required ML model files exist."""
    from config.settings import MODEL_DIRECTORY

    result = ValidationResult()
    required = [
        "random_forest.pkl",
        "preprocessor.pkl",
        "feature_names.json",
    ]
    for fname in required:
        fpath = MODEL_DIRECTORY / fname
        if not fpath.exists():
            result.errors.append(f"Required model artifact missing: {fname}")
            result.passed = False
            logger.error("Missing required model: %s", fname)

    # Manifest is a warning only, not blocking
    manifest = MODEL_DIRECTORY / "model_manifest.json"
    if not manifest.exists():
        result.warnings.append("model_manifest.json not found — integrity verification disabled.")
        logger.warning("Model manifest missing — integrity checks skipped.")

    return result


def validate_database_access() -> ValidationResult:
    """Verify critical databases are accessible."""
    import sqlite3
    from config.settings import AUTH_DB_PATH, AUDIT_DB_PATH

    result = ValidationResult()
    critical_dbs = [("auth", AUTH_DB_PATH), ("audit", AUDIT_DB_PATH)]

    for name, db_path in critical_dbs:
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("SELECT 1")
            conn.close()
        except Exception as exc:
            result.errors.append(f"Cannot access {name} database: {type(exc).__name__}")
            result.passed = False
            logger.error("Database access failure for '%s': %s", name, type(exc).__name__)

    return result


def validate_logging() -> ValidationResult:
    """Verify logging can be initialized."""
    from config.settings import LOG_TO_FILE, LOG_DIR

    result = ValidationResult()
    if LOG_TO_FILE:
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            result.warnings.append(f"Cannot create log directory: {type(exc).__name__}")
            logger.warning("Log directory creation failed: %s", type(exc).__name__)
    return result


def run_startup_validation(block_on_error: bool = True) -> ValidationResult:
    """Run all startup validations and return aggregate result.

    Args:
        block_on_error: If True and production, raise RuntimeError on critical failures.

    Returns:
        Aggregate ValidationResult.
    """
    from config.settings import IS_PRODUCTION

    aggregate = ValidationResult()

    checks = [
        ("environment", validate_environment),
        ("model_artifacts", validate_model_artifacts),
        ("database_access", validate_database_access),
        ("logging", validate_logging),
    ]

    for check_name, check_fn in checks:
        try:
            result = check_fn()
            aggregate.warnings.extend(result.warnings)
            aggregate.errors.extend(result.errors)
            if not result.passed:
                aggregate.passed = False
            if result.blocked:
                aggregate.blocked = True
        except Exception as exc:
            aggregate.warnings.append(f"Check '{check_name}' raised unexpected error: {type(exc).__name__}")
            logger.warning("Startup check '%s' failed unexpectedly: %s", check_name, type(exc).__name__)

    if aggregate.warnings:
        for w in aggregate.warnings:
            logger.warning("[STARTUP] %s", w)

    if aggregate.errors:
        for e in aggregate.errors:
            logger.error("[STARTUP] %s", e)

    if aggregate.blocked and block_on_error:
        raise RuntimeError(
            "HeartGuard startup blocked due to critical configuration errors. "
            "Review application logs for details. Do NOT expose error details to end users."
        )

    return aggregate
