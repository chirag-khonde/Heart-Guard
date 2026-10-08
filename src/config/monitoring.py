"""HeartGuard Monitoring Configuration (Phase 17).

Centralized configuration for all monitoring thresholds, drift detection parameters,
analytics windows, and monitoring event lifecycle. Engineering monitoring thresholds
are clearly distinguished from clinical/medical thresholds.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Monitoring Database
# ---------------------------------------------------------------------------
MONITORING_DB_DIR: Path = Path(os.getenv("MONITORING_DB_DIR", "data/monitoring"))
MONITORING_DB_PATH: Path = MONITORING_DB_DIR / "monitoring.db"

# ---------------------------------------------------------------------------
# Drift Detection — Engineering Thresholds
# These are system monitoring thresholds, NOT clinical thresholds.
# ---------------------------------------------------------------------------
DRIFT_PSI_WARNING: float = float(os.getenv("DRIFT_PSI_WARNING", "0.10"))
DRIFT_PSI_CRITICAL: float = float(os.getenv("DRIFT_PSI_CRITICAL", "0.25"))
DRIFT_KS_ALPHA: float = float(os.getenv("DRIFT_KS_ALPHA", "0.05"))
DRIFT_JS_DIVERGENCE_WARNING: float = float(os.getenv("DRIFT_JS_DIVERGENCE_WARNING", "0.05"))
DRIFT_JS_DIVERGENCE_CRITICAL: float = float(os.getenv("DRIFT_JS_DIVERGENCE_CRITICAL", "0.15"))
DRIFT_PREDICTION_SHIFT_THRESHOLD: float = float(os.getenv("DRIFT_PREDICTION_SHIFT_THRESHOLD", "0.10"))
DRIFT_CONFIDENCE_THRESHOLD: float = float(os.getenv("DRIFT_CONFIDENCE_THRESHOLD", "0.10"))

# Minimum sample size for drift analysis (engineering threshold, not clinical)
DRIFT_MIN_SAMPLE_SIZE: int = int(os.getenv("DRIFT_MIN_SAMPLE_SIZE", "30"))
DRIFT_REFERENCE_WINDOW_DAYS: int = int(os.getenv("DRIFT_REFERENCE_WINDOW_DAYS", "90"))
DRIFT_CURRENT_WINDOW_DAYS: int = int(os.getenv("DRIFT_CURRENT_WINDOW_DAYS", "30"))

# ---------------------------------------------------------------------------
# Data Quality — Engineering Thresholds
# ---------------------------------------------------------------------------
DQ_MISSING_RATE_WARNING: float = float(os.getenv("DQ_MISSING_RATE_WARNING", "0.05"))
DQ_MISSING_RATE_CRITICAL: float = float(os.getenv("DQ_MISSING_RATE_CRITICAL", "0.20"))
DQ_DUPLICATE_RATE_WARNING: float = float(os.getenv("DQ_DUPLICATE_RATE_WARNING", "0.02"))
DQ_DUPLICATE_RATE_CRITICAL: float = float(os.getenv("DQ_DUPLICATE_RATE_CRITICAL", "0.10"))
DQ_OUT_OF_RANGE_WARNING: float = float(os.getenv("DQ_OUT_OF_RANGE_WARNING", "0.03"))
DQ_MIN_RECORDS: int = int(os.getenv("DQ_MIN_RECORDS", "10"))

# ---------------------------------------------------------------------------
# Confidence Monitoring — Engineering Thresholds
# ---------------------------------------------------------------------------
CONFIDENCE_LOW_THRESHOLD: float = float(os.getenv("CONFIDENCE_LOW_THRESHOLD", "0.40"))
CONFIDENCE_HIGH_THRESHOLD: float = float(os.getenv("CONFIDENCE_HIGH_THRESHOLD", "0.80"))
CONFIDENCE_LOW_PERCENT_WARNING: float = float(os.getenv("CONFIDENCE_LOW_PERCENT_WARNING", "0.30"))

# ---------------------------------------------------------------------------
# Anomaly Detection — Engineering Thresholds
# ---------------------------------------------------------------------------
ANOMALY_ZSCORE_THRESHOLD: float = float(os.getenv("ANOMALY_ZSCORE_THRESHOLD", "3.0"))
ANOMALY_MIN_HISTORY: int = int(os.getenv("ANOMALY_MIN_HISTORY", "10"))
ANOMALY_VOLUME_SPIKE_FACTOR: float = float(os.getenv("ANOMALY_VOLUME_SPIKE_FACTOR", "2.0"))
ANOMALY_LATENCY_SPIKE_FACTOR: float = float(os.getenv("ANOMALY_LATENCY_SPIKE_FACTOR", "3.0"))
ANOMALY_ERROR_RATE_THRESHOLD: float = float(os.getenv("ANOMALY_ERROR_RATE_THRESHOLD", "0.05"))

# ---------------------------------------------------------------------------
# Performance Monitoring — Engineering Thresholds
# ---------------------------------------------------------------------------
PERF_LATENCY_WARNING_MS: float = float(os.getenv("PERF_LATENCY_WARNING_MS", "5000.0"))
PERF_LATENCY_CRITICAL_MS: float = float(os.getenv("PERF_LATENCY_CRITICAL_MS", "10000.0"))
PERF_ERROR_RATE_WARNING: float = float(os.getenv("PERF_ERROR_RATE_WARNING", "0.05"))
PERF_ERROR_RATE_CRITICAL: float = float(os.getenv("PERF_ERROR_RATE_CRITICAL", "0.15"))
PERF_CACHE_TTL_SECONDS: int = int(os.getenv("PERF_CACHE_TTL_SECONDS", "300"))

# ---------------------------------------------------------------------------
# Monitoring Events Lifecycle
# ---------------------------------------------------------------------------
EVENT_RETENTION_DAYS: int = int(os.getenv("EVENT_RETENTION_DAYS", "90"))
EVENT_MAX_PER_PAGE: int = int(os.getenv("EVENT_MAX_PER_PAGE", "50"))

# ---------------------------------------------------------------------------
# Monitoring Severity Levels
# ---------------------------------------------------------------------------
SEVERITY_INFO = "INFO"
SEVERITY_WARNING = "WARNING"
SEVERITY_HIGH = "HIGH"
SEVERITY_CRITICAL = "CRITICAL"
VALID_SEVERITIES = {SEVERITY_INFO, SEVERITY_WARNING, SEVERITY_HIGH, SEVERITY_CRITICAL}

# ---------------------------------------------------------------------------
# Monitoring Event Types
# ---------------------------------------------------------------------------
EVENT_DATA_DRIFT_DETECTED = "DATA_DRIFT_DETECTED"
EVENT_PREDICTION_DRIFT_DETECTED = "PREDICTION_DRIFT_DETECTED"
EVENT_DATA_QUALITY_DEGRADED = "DATA_QUALITY_DEGRADED"
EVENT_MODEL_PERFORMANCE_DEGRADED = "MODEL_PERFORMANCE_DEGRADED"
EVENT_ANOMALY_DETECTED = "ANOMALY_DETECTED"
EVENT_SCHEMA_CHANGE_DETECTED = "SCHEMA_CHANGE_DETECTED"
EVENT_HIGH_ERROR_RATE = "HIGH_ERROR_RATE"
EVENT_HIGH_LATENCY = "HIGH_LATENCY"
EVENT_LOW_CONFIDENCE = "LOW_CONFIDENCE"
EVENT_MONITORING_CONFIG_CHANGED = "MONITORING_CONFIG_CHANGED"
EVENT_MODEL_STATUS_CHANGED = "MODEL_STATUS_CHANGED"
EVENT_THRESHOLD_CHANGED = "THRESHOLD_CHANGED"

# ---------------------------------------------------------------------------
# Time Filter Windows
# ---------------------------------------------------------------------------
TIME_FILTERS = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "180d": 180,
    "365d": 365,
    "all": None,
}

# ---------------------------------------------------------------------------
# Monitoring Status Values
# ---------------------------------------------------------------------------
STATUS_HEALTHY = "HEALTHY"
STATUS_DEGRADED = "DEGRADED"
STATUS_UNAVAILABLE = "UNAVAILABLE"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_WARNING = "WARNING"
STATUS_DRIFT_DETECTED = "DRIFT_DETECTED"
STATUS_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

# ---------------------------------------------------------------------------
# Model Status Values
# ---------------------------------------------------------------------------
MODEL_PRODUCTION = "PRODUCTION"
MODEL_VALIDATION = "VALIDATION"
MODEL_RETIRED = "RETIRED"
MODEL_UNKNOWN = "UNKNOWN"
