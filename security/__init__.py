"""HeartGuard Security Package (Phase 9 & Phase 15).

Provides comprehensive security controls:
  - Audit logging with structured taxonomy, pagination, filtering, and stats.
  - Input validation, XSS sanitization, identifier checks, and mass assignment defenses.
  - Thread-safe sliding-window rate limiting.
  - Server-side IDOR defense and ownership verification.
  - File security and path traversal protection.
  - Privacy data minimization, masking, and export.
  - Security event logging and IP hashing.
"""

from src.security.audit_logger import (
    get_audit_statistics,
    get_filtered_events,
    get_recent_events,
    log_event,
)
from src.security.authorization_service import AuthorizationService
from src.security.file_security import (
    is_safe_path,
    resolve_safe_path,
    validate_uploaded_file,
    verify_report_access,
)
from src.security.input_validator import (
    sanitize_filename,
    sanitize_sms_content,
    sanitize_text_for_display,
    validate_email,
    validate_identifier,
    validate_integer_id,
    validate_json_payload,
    validate_lifestyle_text_length,
    validate_name,
    validate_password_strength,
    validate_physiological_metric,
)
from src.security.privacy import (
    export_user_data,
    mask_email,
    mask_name,
    mask_phone,
    sanitize_for_llm_processing,
    scan_repo_secrets,
)
from src.security.rate_limiter import (
    InMemoryRateLimiter,
    check_rate_limit,
    is_rate_limited,
    record_failed_attempt,
    reset_attempts,
    seconds_remaining,
)
from src.security.security_logger import SecurityLogger

__all__ = [
    "log_event",
    "get_recent_events",
    "get_filtered_events",
    "get_audit_statistics",
    "SecurityLogger",
    "AuthorizationService",
    "validate_email",
    "validate_name",
    "validate_password_strength",
    "validate_lifestyle_text_length",
    "sanitize_text_for_display",
    "sanitize_sms_content",
    "sanitize_filename",
    "validate_identifier",
    "validate_integer_id",
    "validate_json_payload",
    "validate_physiological_metric",
    "is_safe_path",
    "resolve_safe_path",
    "validate_uploaded_file",
    "verify_report_access",
    "InMemoryRateLimiter",
    "check_rate_limit",
    "is_rate_limited",
    "record_failed_attempt",
    "reset_attempts",
    "seconds_remaining",
    "mask_email",
    "mask_phone",
    "mask_name",
    "export_user_data",
    "sanitize_for_llm_processing",
    "scan_repo_secrets",
]
