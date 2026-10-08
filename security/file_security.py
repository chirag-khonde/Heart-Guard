"""File and report access security layer (Phase 15).

Protects against:
  - Path Traversal (LFI / Directory traversal)
  - Malicious file uploads (magic byte checks, extension restrictions, size caps)
  - Unauthorized report access (IDOR on report exports)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from config.security import (
    ALLOWED_MIME_TYPES,
    ALLOWED_UPLOAD_EXTENSIONS,
    FILE_SIGNATURES,
    MAX_UPLOAD_SIZE_BYTES,
)
from config.settings import DATA_DIRECTORY, REPORT_DIRECTORY
from src.security.input_validator import sanitize_filename
from src.security.security_logger import SecurityLogger
from src.utils.logger import get_logger

logger = get_logger(__name__)


def is_safe_path(base_dir: Path | str, target_path: Path | str) -> bool:
    """Verify that target_path strictly resolves within base_dir.

    Prevents directory traversal attacks such as `../../etc/passwd`.
    """
    try:
        resolved_base = Path(base_dir).resolve()
        resolved_target = Path(target_path).resolve()
        # On Python 3.9+, is_relative_to is standard
        return resolved_target.is_relative_to(resolved_base)
    except Exception:
        return False


def resolve_safe_path(base_dir: Path | str, requested_filename: str) -> Path:
    """Safely resolve a filename within base_dir.

    Raises:
        ValueError: If filename contains invalid characters or escapes base_dir.
        PermissionError: If traversal is attempted.
    """
    if ".." in requested_filename or requested_filename.startswith(("/", "\\")):
        raise PermissionError(f"Directory traversal detected: '{requested_filename}'")

    safe_name = sanitize_filename(requested_filename)
    base = Path(base_dir).resolve()
    target = (base / safe_name).resolve()

    if not is_safe_path(base, target):
        raise PermissionError(f"Directory traversal detected: '{requested_filename}'")

    return target


def validate_uploaded_file(
    file_name: str,
    file_bytes: bytes,
    max_size: int = MAX_UPLOAD_SIZE_BYTES,
) -> tuple[bool, str]:
    """Validate uploaded file size, extension, and binary signatures.

    Returns:
        tuple[bool, str]: (is_valid, rejection_reason)
    """
    if not file_bytes:
        return False, "Uploaded file is empty."

    if len(file_bytes) > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File exceeds maximum allowed size of {max_mb:.1f} MB."

    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return False, f"File extension '{ext}' is not permitted. Allowed: {sorted(ALLOWED_UPLOAD_EXTENSIONS)}"

    # Check magic byte signatures if registered
    if ext in FILE_SIGNATURES:
        valid_sig = False
        for sig in FILE_SIGNATURES[ext]:
            if file_bytes.startswith(sig):
                valid_sig = True
                break
        if not valid_sig:
            return False, f"File content does not match expected {ext.upper()} format."

    return True, ""


def verify_report_access(
    user_id: int,
    role: str,
    report_identifier: str | Path,
) -> bool:
    """Verify whether a user has permission to view or download a generated report.

    Rules:
      - REVIEWER and ADMIN have clinical oversight access.
      - PATIENT can ONLY access reports belonging to their own user_id or assessment.
    """
    clean_role = role.upper().strip()
    if clean_role in ("ADMIN", "REVIEWER"):
        return True

    rep_name = Path(report_identifier).name

    # Check if report contains user's user_id or username prefix
    expected_user_tag = f"user_{user_id}"
    expected_tag_short = f"u{user_id}_"
    if expected_user_tag in rep_name or expected_tag_short in rep_name:
        return True

    # Check if report matches an assessment owned by this user
    from src.analytics.history_service import HistoryService
    user_assessments = HistoryService.get_user_assessments(user_id=user_id, limit=200)
    for a in user_assessments:
        if a.assessment_id in rep_name:
            return True

    SecurityLogger.log_idor_attempt(
        actor_id=user_id,
        actor_role=role,
        resource_type="report",
        resource_id=rep_name,
    )
    return False
