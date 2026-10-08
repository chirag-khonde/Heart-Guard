"""Comprehensive Phase 15 Security, Privacy & Audit Logging Tests.

Tests:
  - Password complexity and blacklist rules
  - Rate limiting with sliding window
  - Inactivity session timeout and token rotation
  - Server-side IDOR defense and ownership verification
  - Path traversal and file upload security
  - Privacy data masking and GDPR-style data export
  - Audit logging taxonomy, filtering, stats, and IP hashing
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import pytest

from config.security import MAX_UPLOAD_SIZE_BYTES, SESSION_INACTIVITY_LIMIT_SECONDS
from src.auth.models import init_auth_db
from src.auth.session_manager import (
    check_session_timeout,
    clear_session,
    create_session,
    get_current_user,
    get_session_token,
    is_authenticated,
    touch_session,
)
from src.auth.user_repository import create_user, UserRepository
from src.security.audit_logger import (
    _hash_ip,
    get_audit_statistics,
    get_filtered_events,
    get_recent_events,
    init_audit_db,
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
    sanitize_text_for_display,
    validate_password_strength,
)
from src.security.privacy import (
    export_user_data,
    mask_email,
    mask_name,
    mask_phone,
    scan_repo_secrets,
)
from src.security.rate_limiter import InMemoryRateLimiter
from src.security.security_logger import SecurityLogger


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_audit_db(tmp_path: Path) -> Path:
    db = tmp_path / "test_audit.db"
    init_audit_db(db)
    return db


@pytest.fixture
def tmp_auth_db(tmp_path: Path) -> Path:
    db = tmp_path / "test_auth.db"
    init_auth_db(db)
    return db


# ── Password Policy Tests ──────────────────────────────────────────────────

def test_password_policy_valid():
    validate_password_strength("CardioSecure99!")
    validate_password_strength("P@ssw0rdStrength")


def test_password_policy_too_short():
    with pytest.raises(ValueError, match="at least 8"):
        validate_password_strength("Sh0rt!")


def test_password_policy_no_digits():
    with pytest.raises(ValueError, match="at least one digit"):
        validate_password_strength("AllLettersOnly")


def test_password_policy_no_letters():
    with pytest.raises(ValueError, match="at least one letter"):
        validate_password_strength("1234567890")


def test_password_policy_common_blacklist():
    with pytest.raises(ValueError, match="too common"):
        validate_password_strength("password123")


# ── Rate Limiter Tests ─────────────────────────────────────────────────────

def test_rate_limiter_sliding_window():
    limiter = InMemoryRateLimiter()
    key = "user_test_1"

    # Allow 3 requests in 10 seconds
    for _ in range(3):
        allowed, _ = limiter.is_allowed(key, max_requests=3, window_seconds=10)
        assert allowed is True

    # 4th request must be blocked
    allowed, retry_after = limiter.is_allowed(key, max_requests=3, window_seconds=10)
    assert allowed is False
    assert retry_after > 0

    # Reset
    limiter.reset(key)
    allowed, _ = limiter.is_allowed(key, max_requests=3, window_seconds=10)
    assert allowed is True


# ── Session Security Tests ─────────────────────────────────────────────────

def test_session_lifecycle_and_rotation():
    clear_session()
    user = {"id": 101, "name": "Alice Patient", "role": "PATIENT"}

    token1 = create_session(user)
    assert is_authenticated() is True
    assert get_current_user()["id"] == 101
    assert get_session_token() == token1

    # Rotation on second login
    user2 = {"id": 102, "name": "Bob Patient", "role": "PATIENT"}
    token2 = create_session(user2)
    assert token2 != token1
    assert get_current_user()["id"] == 102

    clear_session()
    assert is_authenticated() is False


def test_session_inactivity_timeout():
    clear_session()
    user = {"id": 200, "name": "Timeout User", "role": "PATIENT"}
    create_session(user)
    assert is_authenticated() is True

    # Manually simulate expired last activity
    from src.auth.session_manager import _get_storage, _KEY_LAST_ACTIVITY
    storage = _get_storage()
    storage[_KEY_LAST_ACTIVITY] = datetime.now(timezone.utc).timestamp() - (SESSION_INACTIVITY_LIMIT_SECONDS + 5)

    # Calling check_session_timeout should trigger expiration
    assert check_session_timeout() is True
    assert is_authenticated() is False


# ── Privacy Masking Tests ──────────────────────────────────────────────────

def test_privacy_data_masking():
    assert mask_email("doctor.watson@hospital.org") == "d***n@hospital.org"
    assert mask_email("a@b.com") == "a***@b.com"
    assert mask_email(None) == "******"

    assert mask_phone("+1 555-867-5309") == "+1*********5309"
    assert mask_phone("123") == "****"

    assert mask_name("Sherlock Holmes") == "S*** H***"
    assert mask_name("Admin") == "A***"


# ── Path Traversal and File Security Tests ──────────────────────────────────

def test_safe_path_validation(tmp_path: Path):
    base_dir = tmp_path / "sandbox"
    base_dir.mkdir()

    safe_file = base_dir / "report.pdf"
    safe_file.touch()

    assert is_safe_path(base_dir, safe_file) is True

    # Escaping base directory
    traversal_path = base_dir / ".." / "secret.txt"
    assert is_safe_path(base_dir, traversal_path) is False

    with pytest.raises(PermissionError):
        resolve_safe_path(base_dir, "../../../windows/win.ini")


def test_validate_uploaded_file():
    # Empty
    valid, msg = validate_uploaded_file("doc.pdf", b"")
    assert valid is False

    # Too big
    valid, msg = validate_uploaded_file("big.pdf", b"X" * (MAX_UPLOAD_SIZE_BYTES + 10))
    assert valid is False

    # Disallowed extension
    valid, msg = validate_uploaded_file("malicious.exe", b"MZexecutable")
    assert valid is False

    # Valid PDF with correct magic bytes
    pdf_bytes = b"%PDF-1.4 header contents..."
    valid, msg = validate_uploaded_file("scan.pdf", pdf_bytes)
    assert valid is True

    # Spoofed extension with wrong magic bytes
    spoofed = b"NOT_A_PDF_CONTENT"
    valid, msg = validate_uploaded_file("fake.pdf", spoofed)
    assert valid is False


# ── IDOR & Authorization Tests ─────────────────────────────────────────────

def test_authorization_role_hierarchy():
    assert AuthorizationService.has_role("ADMIN", "PATIENT") is True
    assert AuthorizationService.has_role("ADMIN", "REVIEWER") is True
    assert AuthorizationService.has_role("REVIEWER", "PATIENT") is True
    assert AuthorizationService.has_role("PATIENT", "ADMIN") is False
    assert AuthorizationService.has_role("PATIENT", "REVIEWER") is False


def test_authorization_assessment_access_idor(tmp_path: Path):
    from src.analytics.history_service import HistoryService
    from src.analytics.models import init_assessment_db

    db_path = tmp_path / "test_history.db"
    init_assessment_db(db_path)

    # Save assessment for User 10 using dict format matching MultimodalRiskEngine output
    dummy_result = {
        "combined": {"risk": 45.0, "category": "MONITORING", "recommended_action": "Regular monitoring recommended."},
        "clinical": {"risk": 40.0, "model": "HeartGuard-ML"},
        "lifestyle": {"risk": 50.0, "detected_factors": []},
        "overall_explanation": "Test assessment for IDOR verification.",
    }
    rec = HistoryService.save_assessment(
        user_id=10,
        multimodal_result=dummy_result,
        alert_status="NOT_TRIGGERED",
        assessment_id="TEST_ASSESS_001",
        db_path=db_path,
    )

    # User 10 can access own assessment
    assert AuthorizationService.verify_assessment_access(
        user_id=10, role="PATIENT", assessment_id="TEST_ASSESS_001", db_path=db_path
    ) is True

    # Admin and Reviewer can access
    assert AuthorizationService.verify_assessment_access(
        user_id=999, role="ADMIN", assessment_id="TEST_ASSESS_001", db_path=db_path
    ) is True
    assert AuthorizationService.verify_assessment_access(
        user_id=888, role="REVIEWER", assessment_id="TEST_ASSESS_001", db_path=db_path
    ) is True

    # User 20 (attacker) cannot access User 10's assessment (IDOR blocked)
    assert AuthorizationService.verify_assessment_access(
        user_id=20, role="PATIENT", assessment_id="TEST_ASSESS_001", db_path=db_path
    ) is False


# ── Audit Logging & Privacy Export Tests ───────────────────────────────────

def test_audit_logging_and_filtering(tmp_audit_db: Path):
    log_event(
        event_type="login_success",
        status="SUCCESS",
        user_id=42,
        role="PATIENT",
        detail="User logged in",
        category="AUTHENTICATION",
        severity="INFO",
        ip_hash=_hash_ip("192.168.1.50"),
        db_path=tmp_audit_db,
    )
    log_event(
        event_type="idor_attempt",
        status="BLOCKED",
        user_id=43,
        role="PATIENT",
        detail="Attempted unauthorized access to assessment 999",
        category="AUTHORIZATION",
        severity="HIGH",
        db_path=tmp_audit_db,
    )

    # Retrieve all
    events = get_recent_events(limit=10, db_path=tmp_audit_db)
    assert len(events) == 2

    # Filter by category
    auth_events, count = get_filtered_events(category="AUTHENTICATION", db_path=tmp_audit_db)
    assert count == 1
    assert auth_events[0]["event_type"] == "login_success"

    # Filter by severity
    high_events, count = get_filtered_events(severity="HIGH", db_path=tmp_audit_db)
    assert count == 1
    assert high_events[0]["event_type"] == "idor_attempt"

    # Statistics
    stats = get_audit_statistics(db_path=tmp_audit_db)
    assert stats["total_events"] == 2
    assert stats["high_severity_events"] == 1
    assert stats["access_denied_events"] == 1


def test_user_data_export_omits_secrets(tmp_auth_db: Path):
    user = create_user(
        name="Charlie Test",
        email="charlie@example.com",
        password_hash="$2b$12$fakepasswordhashforexporttesting",
        role="PATIENT",
        db_path=tmp_auth_db,
    )

    export_pkg = export_user_data(user_id=user.id, auth_db_path=tmp_auth_db)
    assert export_pkg["user_id"] == user.id
    assert "password_hash" not in str(export_pkg)
    assert "password" not in str(export_pkg)
    assert "token" not in str(export_pkg)
    assert export_pkg["prototype_notice"] != ""


def test_scan_repo_secrets_finds_zero_live_keys():
    findings = scan_repo_secrets()
    # Expect 0 live hardcoded keys committed in the codebase
    assert len(findings) == 0
