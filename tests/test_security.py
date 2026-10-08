"""Security and hardening tests for HeartGuard Phase 9.

Validates input sanitisation, validation bounds, SQL injection resistance,
password security, credential sanitisation, audit logging, and rate limiting.
Uses isolated temporary SQLite databases for all database interactions.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
import pytest

from config import settings
from src.auth.models import User, init_auth_db
from src.auth.password_service import hash_password, verify_password
from src.auth.user_repository import create_user, find_by_email
from src.security.audit_logger import get_recent_events, log_event
from src.security.input_validator import (
    sanitize_sms_content,
    sanitize_text_for_display,
    validate_email,
    validate_lifestyle_text_length,
    validate_name,
    validate_password_strength,
)
from src.security.rate_limiter import (
    is_rate_limited,
    record_failed_attempt,
    reset_attempts,
    seconds_remaining,
)


@pytest.fixture()
def tmp_auth_db(tmp_path: Path) -> Path:
    """Provide a clean temporary auth SQLite database."""
    db_file = tmp_path / "test_auth.db"
    init_auth_db(db_file)
    return db_file


@pytest.fixture()
def tmp_audit_db(tmp_path: Path) -> Path:
    """Provide a clean temporary audit SQLite database."""
    return tmp_path / "test_audit.db"


# ---------------------------------------------------------------------------
# 1. No hardcoded production secrets in configuration
# ---------------------------------------------------------------------------


def test_no_hardcoded_live_secrets_in_settings():
    """Ensure defaults are placeholders and do not contain real API keys or tokens."""
    # Twilio token should be empty or a clearly safe placeholder
    token = settings.TWILIO_AUTH_TOKEN
    assert "AC" not in token or len(token) <= 4 or token == ""
    # Doctor and emergency phones should not be real private numbers
    doc_phone = settings.DOCTOR_PHONE_NUMBER
    assert doc_phone in ("", "+15550000000", "+1234567890", "+15551234567") or doc_phone.startswith("+1555")
    # Secret key should have a fallback or env-based value, never a live prod secret
    assert isinstance(settings.SECRET_KEY, str)


# ---------------------------------------------------------------------------
# 2. Password Security and Safe Serialization
# ---------------------------------------------------------------------------


def test_passwords_never_stored_plaintext(tmp_auth_db: Path):
    """Ensure stored user row contains bcrypt hash, not plaintext password."""
    from src.auth.auth_service import register_user

    raw_pass = "SuperSecret123!"
    user = register_user(
        name="Security Patient",
        email="patient_sec@example.com",
        password=raw_pass,
        confirm_password=raw_pass,
        db_path=tmp_auth_db,
    )
    # Service returns safe dict which must never include password_hash
    assert "password_hash" not in user
    assert "password" not in user

    # Verify directly in SQLite table that stored hash is bcrypt and not plaintext
    with sqlite3.connect(str(tmp_auth_db)) as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],)).fetchone()
        assert row is not None
        stored_hash = row[0]
        assert stored_hash != raw_pass
        assert raw_pass not in stored_hash
        assert stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$")


def test_user_safe_dict_omits_password_hash():
    """Ensure User.to_safe_dict() strips password_hash completely."""
    user = User(
        id=1,
        name="Alice Safe",
        email="alice@example.com",
        password_hash="$2b$12$eXamp1eHashNotReal...",
        role="PATIENT",
        is_active=True,
    )
    safe = user.to_safe_dict()
    assert "password_hash" not in safe
    assert "password" not in safe
    assert safe["email"] == "alice@example.com"
    assert safe["id"] == 1


# ---------------------------------------------------------------------------
# 3. Input Validation Bounds and Formats
# ---------------------------------------------------------------------------


def test_validate_email_valid():
    assert validate_email("Patient.One@example.com") == "patient.one@example.com"
    assert validate_email("user+tag@domain.co.uk") == "user+tag@domain.co.uk"


def test_validate_email_invalid():
    with pytest.raises(ValueError, match="required"):
        validate_email("")
    with pytest.raises(ValueError, match="format is invalid"):
        validate_email("not-an-email")
    with pytest.raises(ValueError, match="format is invalid"):
        validate_email("user@domain")
    with pytest.raises(ValueError, match="too long"):
        validate_email("a" * 250 + "@example.com")


def test_validate_name_bounds():
    assert validate_name("Dr. Smith") == "Dr. Smith"
    with pytest.raises(ValueError, match="required"):
        validate_name("")
    with pytest.raises(ValueError, match="blank"):
        validate_name("   ")
    with pytest.raises(ValueError, match="characters or fewer"):
        validate_name("X" * (settings.NAME_MAX_LENGTH + 1))


def test_validate_password_strength():
    validate_password_strength("ValidPass123")
    with pytest.raises(ValueError, match="at least"):
        validate_password_strength("short")
    with pytest.raises(ValueError, match="at least"):
        validate_password_strength("")


def test_validate_lifestyle_text_length():
    valid_text = "I exercise 3 days a week and eat balanced meals."
    assert validate_lifestyle_text_length(valid_text) == valid_text

    with pytest.raises(ValueError, match="required"):
        validate_lifestyle_text_length("")
    with pytest.raises(ValueError, match="blank"):
        validate_lifestyle_text_length("   ")

    # Exceed maximum allowed length (5000 characters)
    too_long = "a" * (settings.LIFESTYLE_TEXT_MAX_LENGTH + 1)
    with pytest.raises(ValueError, match="too long"):
        validate_lifestyle_text_length(too_long)


# ---------------------------------------------------------------------------
# 4. Content Sanitisation (XSS & SMS Injection)
# ---------------------------------------------------------------------------


def test_sanitize_text_for_display_strips_scripts_and_escapes():
    xss_input = "<script>alert('xss')</script>Hello <b>World</b> & goodbye"
    sanitized = sanitize_text_for_display(xss_input)
    assert "<script>" not in sanitized.lower()
    assert "<b>" not in sanitized
    assert "&amp;" in sanitized or "&" in sanitized
    assert "Hello" in sanitized
    assert "goodbye" in sanitized


def test_sanitize_sms_content_strips_control_characters():
    sms_payload = "High Risk Patient\r\nSTATUS: EMERGENCY\n|DO_NOT_DISPATCH|"
    sanitized = sanitize_sms_content(sms_payload)
    assert "\r" not in sanitized
    assert "\n" not in sanitized
    assert "|" not in sanitized
    assert "High Risk Patient" in sanitized


# ---------------------------------------------------------------------------
# 5. SQL Injection Resistance
# ---------------------------------------------------------------------------


def test_sql_injection_resistance(tmp_auth_db: Path):
    """Verify parameterized queries resist standard SQL injection vectors."""
    # Attempt SQL injection in find_by_email
    sqli_email = "' OR '1'='1' --"
    res = find_by_email(sqli_email, db_path=tmp_auth_db)
    assert res is None

    # Attempt SQL injection during account creation
    sqli_name = "Admin'); DROP TABLE users; --"
    user = create_user(
        name=sqli_name,
        email="sqli_test@example.com",
        password_hash=hash_password("ValidPassword123!"),
        role="PATIENT",
        db_path=tmp_auth_db,
    )
    assert user.name == sqli_name

    # Check that users table still exists and contains the user
    found = find_by_email("sqli_test@example.com", db_path=tmp_auth_db)
    assert found is not None
    assert found.name == sqli_name


# ---------------------------------------------------------------------------
# 6. Audit Logging and Data Privacy
# ---------------------------------------------------------------------------


def test_audit_log_records_valid_events(tmp_audit_db: Path):
    """Test that audit log writes valid event records."""
    log_event(
        event_type="login_success",
        status="SUCCESS",
        user_id=42,
        role="ADMIN",
        detail="Successful admin portal login",
        db_path=tmp_audit_db,
    )

    events = get_recent_events(limit=10, db_path=tmp_audit_db)
    assert len(events) == 1
    assert events[0]["event_type"] == "login_success"
    assert events[0]["user_id"] == 42
    assert events[0]["role"] == "ADMIN"
    assert events[0]["status"] == "SUCCESS"


def test_audit_log_ignores_invalid_event_types(tmp_audit_db: Path):
    """Events outside the whitelist are discarded."""
    log_event(
        event_type="unregistered_custom_event",
        status="FAILURE",
        db_path=tmp_audit_db,
    )
    events = get_recent_events(limit=10, db_path=tmp_audit_db)
    assert len(events) == 0


def test_audit_log_truncates_long_details(tmp_audit_db: Path):
    """Details longer than 500 characters must be truncated to prevent log flooding."""
    long_detail = "A" * 1000
    log_event(
        event_type="access_denied",
        status="BLOCKED",
        detail=long_detail,
        db_path=tmp_audit_db,
    )
    events = get_recent_events(limit=10, db_path=tmp_audit_db)
    assert len(events) == 1
    assert len(events[0]["detail"]) == 500


# ---------------------------------------------------------------------------
# 7. Rate Limiting Logic
# ---------------------------------------------------------------------------


from unittest.mock import patch


def test_rate_limiter_blocks_after_threshold(monkeypatch):
    """Rate limiter blocks after configured max failed attempts."""
    monkeypatch.setattr("src.security.rate_limiter.LOGIN_MAX_ATTEMPTS", 3)
    monkeypatch.setattr("src.security.rate_limiter.LOGIN_COOLDOWN_SECONDS", 60)

    fake_state: dict = {}
    with patch("src.security.rate_limiter.st") as mock_st:
        mock_st.session_state = fake_state

        assert is_rate_limited() is False
        assert seconds_remaining() == 0

        # 1st failure
        cnt1 = record_failed_attempt()
        assert cnt1 == 1
        assert is_rate_limited() is False

        # 2nd failure
        cnt2 = record_failed_attempt()
        assert cnt2 == 2
        assert is_rate_limited() is False

        # 3rd failure -> reaches threshold 3, blocks
        cnt3 = record_failed_attempt()
        assert cnt3 == 3
        assert is_rate_limited() is True
        assert seconds_remaining() > 0

        # Reset on success
        reset_attempts()
        assert is_rate_limited() is False
        assert seconds_remaining() == 0
