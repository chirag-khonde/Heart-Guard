"""HeartGuard Centralized Security Configuration (Phase 15).

Defines security policies, rate limits, upload restrictions, password rules,
audit categories, and compliance definitions for the application.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Session Security
# ---------------------------------------------------------------------------
SESSION_TIMEOUT_MINUTES: int = 30
SESSION_INACTIVITY_LIMIT_SECONDS: int = SESSION_TIMEOUT_MINUTES * 60
SESSION_COOKIE_SECURE: bool = True
SESSION_COOKIE_HTTPONLY: bool = True
SESSION_COOKIE_SAMESITE: str = "Lax"

# ---------------------------------------------------------------------------
# Rate Limiting Policies (requests, window_seconds)
# ---------------------------------------------------------------------------
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "login": (5, 60),              # 5 attempts per 60 seconds
    "register": (5, 60),           # 5 registrations per 60 seconds
    "assessment_create": (10, 60),  # 10 assessments per minute
    "report_generate": (10, 60),   # 10 report generations per minute
    "report_download": (15, 60),   # 15 report downloads per minute
    "insights": (20, 60),          # 20 AI insight evaluations per minute
    "model_evaluation": (3, 60),   # 3 heavy model evaluations per minute
}

# ---------------------------------------------------------------------------
# File Upload Security
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
ALLOWED_UPLOAD_EXTENSIONS: set[str] = {".pdf", ".csv", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES: set[str] = {
    "application/pdf",
    "text/csv",
    "image/png",
    "image/jpeg",
    "text/plain",
}

# Magic numbers for file format validation
FILE_SIGNATURES: dict[str, list[bytes]] = {
    ".pdf": [b"%PDF"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
}

# ---------------------------------------------------------------------------
# Password Policy
# ---------------------------------------------------------------------------
MIN_PASSWORD_LENGTH: int = 8
MAX_PASSWORD_LENGTH: int = 128
REQUIRE_NUMBERS: bool = True
REQUIRE_LETTERS: bool = True

COMMON_PASSWORDS: set[str] = {
    "password",
    "password123",
    "12345678",
    "123456789",
    "qwerty123",
    "admin123",
    "heartguard",
    "heartguard123",
    "welcome1",
    "letmein123",
}

# ---------------------------------------------------------------------------
# Audit Logging Taxonomy
# ---------------------------------------------------------------------------
EVENT_CATEGORIES: tuple[str, ...] = (
    "AUTHENTICATION",
    "AUTHORIZATION",
    "DATA_ACCESS",
    "ADMIN_ACTION",
    "FILE_ACCESS",
    "MODEL_OPERATION",
    "SYSTEM_SECURITY",
)

EVENT_SEVERITIES: tuple[str, ...] = (
    "INFO",
    "WARNING",
    "HIGH",
    "CRITICAL",
)

# ---------------------------------------------------------------------------
# HTTP Security Headers
# ---------------------------------------------------------------------------
SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    ),
}

# ---------------------------------------------------------------------------
# Compliance & Legal Disclaimers (Academic / Research Prototype)
# ---------------------------------------------------------------------------
PROTOTYPE_NOTICE: str = (
    "HeartGuard is an academic and research prototype developed for educational, "
    "demonstration, and evaluation purposes. It provides model-based risk estimates "
    "and explainable AI insights. It is NOT a certified medical device and does not "
    "provide clinical diagnosis or prescribe medical treatments."
)

COMPLIANCE_STATEMENT: str = (
    "Security and privacy controls implemented for this research and demonstration prototype "
    "(Role-Based Access Control, IDOR Protection, Audit Logging, Data Minimization, and Session Protection)."
)

INFORMATIONAL_ACKNOWLEDGEMENT_TEXT: str = (
    "I understand that this assessment is informational and does not replace professional medical advice."
)
