"""HeartGuard centralized configuration (Phase 16 — Production Hardened).

Loads all environment variables and provides a single source of truth
for application settings. Sensitive values are never hard-coded here.

Environment Support:
    ENVIRONMENT=development  (default)
    ENVIRONMENT=testing
    ENVIRONMENT=production
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if present (development only; production uses real env vars)
load_dotenv()

# ---------------------------------------------------------------------------
# Application Identity & Versioning (Phase 16)
# ---------------------------------------------------------------------------
PROJECT_NAME = "HeartGuard"
PROJECT_VERSION = "1.0.0"
HEARTGUARD_VERSION = "1.0.0"
PHASE_STATUS = "Phase 20 — Final Release"

# ---------------------------------------------------------------------------
# Environment (Phase 16)
# ---------------------------------------------------------------------------
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower().strip()
IS_PRODUCTION: bool = ENVIRONMENT == "production"
IS_TESTING: bool = ENVIRONMENT == "testing"
IS_DEVELOPMENT: bool = ENVIRONMENT == "development"

# ---------------------------------------------------------------------------
# Application URLs (Phase 16)
# ---------------------------------------------------------------------------
APP_URL: str = os.getenv("APP_URL", "http://localhost:8501")
ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501")

# ---------------------------------------------------------------------------
# Risk scoring weights (Phase 7 — must not change)
# ---------------------------------------------------------------------------
CLINICAL_WEIGHT = 0.70
LIFESTYLE_WEIGHT = 0.30

# Risk thresholds (percentage)
RISK_THRESHOLD_LOW = 60
RISK_THRESHOLD_MODERATE = 75
RISK_THRESHOLD_HIGH = 85
RISK_THRESHOLD_CRITICAL = 85

# ---------------------------------------------------------------------------
# Base directory (project root)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------
MODEL_DIRECTORY: Path = Path(os.getenv("MODEL_DIR", str(BASE_DIR / "models")))
DATA_DIRECTORY: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
RAW_DATA_DIRECTORY: Path = DATA_DIRECTORY / "raw"
PROCESSED_DATA_DIRECTORY: Path = DATA_DIRECTORY / "processed"
ALERT_DIRECTORY: Path = DATA_DIRECTORY / "alerts"
AUTH_DATA_DIRECTORY: Path = DATA_DIRECTORY / "auth"
SECURITY_DATA_DIRECTORY: Path = DATA_DIRECTORY / "security"
ASSESSMENT_DATA_DIRECTORY: Path = DATA_DIRECTORY / "assessments"
REPORT_DIRECTORY: Path = Path(os.getenv("REPORT_DIR", str(BASE_DIR / "reports")))
TEMP_DIRECTORY: Path = Path(os.getenv("TEMP_DIR", str(BASE_DIR / "data" / "tmp")))

# ---------------------------------------------------------------------------
# Logging (Phase 16)
# ---------------------------------------------------------------------------
_DEFAULT_LOG_LEVEL = "WARNING" if IS_PRODUCTION else "INFO"
LOG_LEVEL: str = os.getenv("LOG_LEVEL", _DEFAULT_LOG_LEVEL).upper()
LOG_DIR: Path = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs")))
LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))   # 10 MB
LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "true" if IS_PRODUCTION else "false").lower() == "true"

# ---------------------------------------------------------------------------
# Database paths (Phase 9 + Phase 10 + Phase 16)
# ---------------------------------------------------------------------------
AUTH_DB_PATH: Path = Path(os.getenv("AUTH_DB_PATH", str(AUTH_DATA_DIRECTORY / "heartguard_auth.db")))
AUDIT_DB_PATH: Path = Path(os.getenv("AUDIT_DB_PATH", str(SECURITY_DATA_DIRECTORY / "audit.db")))
ALERTS_DB_PATH: Path = Path(os.getenv("ALERTS_DB_PATH", str(ALERT_DIRECTORY / "alerts.db")))
ASSESSMENTS_DB_PATH: Path = Path(os.getenv("ASSESSMENTS_DB_PATH", str(ASSESSMENT_DATA_DIRECTORY / "assessments.db")))
REVIEWS_DB_PATH: Path = Path(os.getenv("REVIEWS_DB_PATH", str(ASSESSMENT_DATA_DIRECTORY / "reviews.db")))
RECOMMENDATIONS_DB_PATH: Path = Path(os.getenv("RECOMMENDATIONS_DB_PATH", str(ASSESSMENT_DATA_DIRECTORY / "recommendations.db")))
RECOMMENDATION_ENGINE_VERSION = "1.0.0"

# Database timeouts (Phase 16)
DB_TIMEOUT_SECONDS: float = float(os.getenv("DB_TIMEOUT_SECONDS", "10.0"))
DB_BUSY_TIMEOUT_MS: int = int(os.getenv("DB_BUSY_TIMEOUT_MS", "5000"))

# ---------------------------------------------------------------------------
# Evaluation configuration (Phase 14)
# ---------------------------------------------------------------------------
EVALUATION_DATA_DIRECTORY: Path = DATA_DIRECTORY / "evaluations"
EVALUATION_DB_PATH: Path = EVALUATION_DATA_DIRECTORY / "evaluation.db"
EVALUATION_ARTIFACTS_DIR: Path = BASE_DIR / "artifacts" / "evaluation"
EVALUATION_RANDOM_STATE: int = 42
EVALUATION_TEST_SIZE: float = 0.20
EVALUATION_CV_FOLDS: int = 5
EVALUATION_ENGINE_VERSION: str = "1.0.0"

# ---------------------------------------------------------------------------
# External API Timeouts (Phase 16)
# ---------------------------------------------------------------------------
TWILIO_TIMEOUT_SECONDS: int = int(os.getenv("TWILIO_TIMEOUT_SECONDS", "10"))
LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
REPORT_GENERATION_TIMEOUT_SECONDS: int = int(os.getenv("REPORT_GENERATION_TIMEOUT_SECONDS", "30"))

# ---------------------------------------------------------------------------
# File storage and retention (Phase 16)
# ---------------------------------------------------------------------------
REPORT_RETENTION_DAYS: int = int(os.getenv("REPORT_RETENTION_DAYS", "30"))
TEMP_FILE_RETENTION_HOURS: int = int(os.getenv("TEMP_FILE_RETENTION_HOURS", "24"))
MAX_REPORTS_PER_USER: int = int(os.getenv("MAX_REPORTS_PER_USER", "100"))

# ---------------------------------------------------------------------------
# Ensure required directories exist (Phase 16: also creates LOG_DIR, TEMP_DIR)
# ---------------------------------------------------------------------------
for _dir in [
    MODEL_DIRECTORY,
    PROCESSED_DATA_DIRECTORY,
    ALERT_DIRECTORY,
    AUTH_DATA_DIRECTORY,
    SECURITY_DATA_DIRECTORY,
    ASSESSMENT_DATA_DIRECTORY,
    REPORT_DIRECTORY,
    EVALUATION_DATA_DIRECTORY,
    EVALUATION_ARTIFACTS_DIR,
    TEMP_DIRECTORY,
    LOG_DIR,
]:
    _dir.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Twilio / Alert configuration (Phase 8)
# ---------------------------------------------------------------------------
TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
DOCTOR_PHONE_NUMBER: str = os.getenv("DOCTOR_PHONE_NUMBER", "")
EMERGENCY_CONTACT_PHONE_NUMBER: str = os.getenv("EMERGENCY_CONTACT_PHONE_NUMBER", "")
ALERTS_ENABLED: bool = os.getenv("ALERTS_ENABLED", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Application mode
# ---------------------------------------------------------------------------
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# Demo mode: active when alerts are disabled (default safe state)
DEMO_MODE: bool = not ALERTS_ENABLED

# Secret key — used for signed-token needs; never displayed
SECRET_KEY: str = os.getenv("SECRET_KEY", "heartguard-change-in-production")

# Default insecure secret detection (Phase 16)
SECRET_KEY_IS_DEFAULT: bool = SECRET_KEY in (
    "heartguard-change-in-production",
    "heartguard-change-this-in-production",
    "",
)

# ---------------------------------------------------------------------------
# Input limits (Phase 9)
# ---------------------------------------------------------------------------
LIFESTYLE_TEXT_MAX_LENGTH: int = 2000
PASSWORD_MIN_LENGTH: int = 8
NAME_MAX_LENGTH: int = 100
EMAIL_MAX_LENGTH: int = 254

# ---------------------------------------------------------------------------
# Rate limiting (Phase 9)
# ---------------------------------------------------------------------------
LOGIN_MAX_ATTEMPTS: int = 5
LOGIN_COOLDOWN_SECONDS: int = 60

# ---------------------------------------------------------------------------
# User roles (Phase 9 / Phase 11)
# ---------------------------------------------------------------------------
ROLE_PATIENT = "PATIENT"
ROLE_ADMIN = "ADMIN"
ROLE_REVIEWER = "REVIEWER"
VALID_ROLES = {ROLE_PATIENT, ROLE_ADMIN, ROLE_REVIEWER}
