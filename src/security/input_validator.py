"""Input validation and sanitisation for HeartGuard (Phase 9 & Phase 15).

All user-facing inputs pass through these validators before use.
These are distinct from the clinical validators in src/utils/validators.py,
which operate on medical domain values.

Security rules:
  - Reject HTML/script fragments in free-text fields (XSS defense).
  - Enforce length and character limits everywhere.
  - Enforce robust password policy (min 8 chars, letters + numbers, common blacklist).
  - Enforce strict identifier formats (IDOR / injection defense).
  - Prevent path traversal in filenames.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
import re
from typing import Any, Optional

from config.security import (
    COMMON_PASSWORDS,
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    REQUIRE_LETTERS,
    REQUIRE_NUMBERS,
)
from config.settings import (
    EMAIL_MAX_LENGTH,
    LIFESTYLE_TEXT_MAX_LENGTH,
    NAME_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
)

# Patterns for dangerous input and identifiers
_SCRIPT_PATTERN = re.compile(r"<\s*script", re.IGNORECASE)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")
_SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9_.\-]+$")


# ---------------------------------------------------------------------------
# Email & Identity
# ---------------------------------------------------------------------------


def validate_email(email: Any) -> str:
    """Validate and normalise an email address."""
    if not email:
        raise ValueError("Email address is required.")
    email_str = str(email).strip().lower()
    if len(email_str) > EMAIL_MAX_LENGTH:
        raise ValueError("Email address is too long.")
    if not _EMAIL_RE.match(email_str):
        raise ValueError("Email address format is invalid.")
    return email_str


def validate_name(name: Any) -> str:
    """Validate a display name."""
    if not name:
        raise ValueError("Name is required.")
    name_str = str(name).strip()
    if not name_str:
        raise ValueError("Name cannot be blank.")
    if len(name_str) > NAME_MAX_LENGTH:
        raise ValueError(f"Name must be {NAME_MAX_LENGTH} characters or fewer.")
    return name_str


def validate_identifier(value: Any, field_name: str = "id") -> str:
    """Validate that an ID string consists strictly of alphanumeric chars, dashes, or underscores."""
    if value is None:
        raise ValueError(f"Field '{field_name}' cannot be None.")
    id_str = str(value).strip()
    if not id_str:
        raise ValueError(f"Field '{field_name}' cannot be empty.")
    if len(id_str) > 64:
        raise ValueError(f"Field '{field_name}' is too long (max 64 characters).")
    if not _SAFE_ID_RE.match(id_str):
        raise ValueError(f"Field '{field_name}' contains invalid characters.")
    return id_str


def validate_integer_id(value: Any, field_name: str = "id") -> int:
    """Validate that an ID is a valid positive integer."""
    if value is None:
        raise ValueError(f"Field '{field_name}' cannot be None.")
    try:
        val_int = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"Field '{field_name}' must be a valid integer.")
    if val_int <= 0:
        raise ValueError(f"Field '{field_name}' must be positive.")
    return val_int


# ---------------------------------------------------------------------------
# Password Policy (Phase 15 Hardened)
# ---------------------------------------------------------------------------


def validate_password_strength(password: str) -> None:
    """Validate password meets security complexity and blacklist requirements.

    Raises:
        ValueError: If requirements are not met.
    """
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must be {MAX_PASSWORD_LENGTH} characters or fewer.")

    if password.lower() in COMMON_PASSWORDS:
        raise ValueError("Password is too common and easily guessable. Please choose a stronger password.")

    if REQUIRE_LETTERS and not any(c.isalpha() for c in password):
        raise ValueError("Password must contain at least one letter.")

    if REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one digit or number.")


# ---------------------------------------------------------------------------
# Lifestyle Text & General Free Text
# ---------------------------------------------------------------------------


def validate_lifestyle_text_length(text: Any) -> str:
    """Validate that lifestyle text is within the allowed length."""
    if not text:
        raise ValueError("Lifestyle description is required.")
    text_str = str(text).strip()
    if not text_str:
        raise ValueError("Lifestyle description cannot be blank.")
    if len(text_str) > LIFESTYLE_TEXT_MAX_LENGTH:
        raise ValueError(
            f"Lifestyle description is too long. "
            f"Maximum {LIFESTYLE_TEXT_MAX_LENGTH:,} characters allowed."
        )
    return text_str


# ---------------------------------------------------------------------------
# Sanitisation & XSS Defense
# ---------------------------------------------------------------------------


def sanitize_text_for_display(text: str) -> str:
    """HTML-escape user-controlled text before rendering in the UI.

    Strips any detected script/HTML fragments and escapes remaining content.
    """
    if not text:
        return ""
    # Remove script tags and contents
    cleaned = _SCRIPT_PATTERN.sub("", text)
    # Remove remaining HTML tags
    cleaned = _HTML_TAG_PATTERN.sub("", cleaned)
    # HTML-escape any residual special characters
    return html.escape(cleaned)


def sanitize_sms_content(value: str) -> str:
    """Sanitise a dynamic value before inclusion in an SMS message."""
    if not value:
        return ""
    return re.sub(r"[\r\n|]", " ", str(value)).strip()


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent directory traversal and illegal characters."""
    if not filename:
        raise ValueError("Filename cannot be empty.")
    # Extract only the base name (strip any directory prefixes)
    base = Path(filename).name
    # Strip null bytes and traversal sequences
    cleaned = base.replace("\0", "").replace("..", "")
    # Remove any character that is not alphanumeric, underscore, hyphen, or dot
    cleaned = re.sub(r"[^a-zA-Z0-9_.\-]", "_", cleaned)
    if not cleaned or cleaned.startswith("."):
        raise ValueError(f"Invalid filename '{filename}'.")
    return cleaned


# ---------------------------------------------------------------------------
# Payload & Range Validations
# ---------------------------------------------------------------------------


def validate_json_payload(raw_json: str, allowed_keys: Optional[set[str]] = None) -> dict[str, Any]:
    """Parse and validate JSON payload, preventing mass assignment."""
    try:
        data = json.loads(raw_json)
    except Exception as exc:
        raise ValueError(f"Malformed JSON payload: {exc}")

    if not isinstance(data, dict):
        raise ValueError("JSON payload must be an object.")

    if allowed_keys is not None:
        extra_keys = set(data.keys()) - allowed_keys
        if extra_keys:
            raise ValueError(f"Unexpected keys in payload: {sorted(extra_keys)}")

    return data


def validate_physiological_metric(
    metric_name: str,
    value: Any,
    min_val: float,
    max_val: float,
) -> float:
    """Validate that a physiological measurement falls within biologically possible bounds."""
    try:
        num = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Metric '{metric_name}' must be numeric.")
    if num < min_val or num > max_val:
        raise ValueError(
            f"Metric '{metric_name}' value {num} is outside acceptable bounds ({min_val} to {max_val})."
        )
    return num
