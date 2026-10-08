"""Authentication tests for HeartGuard Phase 9.

Tests registration, password hashing, login, logout, and account state.
Uses a temporary SQLite database so tests never touch the real auth DB.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.auth.auth_service import authenticate_user, create_admin_user, register_user
from src.auth.models import init_auth_db
from src.auth.password_service import hash_password, verify_password
from src.auth.user_repository import find_by_email, find_by_id


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Path:
    """Return a path to a fresh temporary auth database."""
    db = tmp_path / "test_auth.db"
    init_auth_db(db)
    return db


# ---------------------------------------------------------------------------
# Password service
# ---------------------------------------------------------------------------


def test_hash_password_returns_string():
    hashed = hash_password("SecurePass1")
    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_hash_password_not_plaintext():
    pw = "MyPassword99"
    hashed = hash_password(pw)
    assert pw not in hashed


def test_verify_password_correct():
    pw = "CorrectHorse!"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("RightPassword")
    assert verify_password("WrongPassword", hashed) is False


def test_verify_password_empty_inputs():
    assert verify_password("", "somehash") is False
    assert verify_password("password", "") is False


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_patient_success(tmp_db: Path):
    user = register_user("Alice Smith", "alice@example.com", "Password8!", "Password8!", db_path=tmp_db)
    assert user["name"] == "Alice Smith"
    assert user["email"] == "alice@example.com"
    assert user["role"] == "PATIENT"
    assert user["is_active"] is True
    # password_hash must NOT be in the returned dict
    assert "password_hash" not in user
    assert "password" not in user


def test_register_normalises_email(tmp_db: Path):
    register_user("Bob", "Bob@EXAMPLE.COM", "Password8!", "Password8!", db_path=tmp_db)
    user = find_by_email("bob@example.com", db_path=tmp_db)
    assert user is not None
    assert user.email == "bob@example.com"


def test_register_duplicate_email_raises(tmp_db: Path):
    register_user("Alice", "dup@example.com", "Password8!", "Password8!", db_path=tmp_db)
    with pytest.raises(ValueError):
        register_user("Alice2", "dup@example.com", "Password8!", "Password8!", db_path=tmp_db)


def test_register_duplicate_email_case_insensitive(tmp_db: Path):
    register_user("Alice", "Case@Example.com", "Password8!", "Password8!", db_path=tmp_db)
    with pytest.raises(ValueError):
        register_user("Alice2", "CASE@EXAMPLE.COM", "Password8!", "Password8!", db_path=tmp_db)


def test_register_password_mismatch_raises(tmp_db: Path):
    with pytest.raises(ValueError, match="Passwords do not match"):
        register_user("Carol", "carol@example.com", "Password8!", "Different8!", db_path=tmp_db)


def test_register_short_password_raises(tmp_db: Path):
    with pytest.raises(ValueError):
        register_user("Dave", "dave@example.com", "Short", "Short", db_path=tmp_db)


def test_register_invalid_email_raises(tmp_db: Path):
    with pytest.raises(ValueError):
        register_user("Eve", "not-an-email", "Password8!", "Password8!", db_path=tmp_db)


def test_register_empty_name_raises(tmp_db: Path):
    with pytest.raises(ValueError):
        register_user("", "frank@example.com", "Password8!", "Password8!", db_path=tmp_db)


def test_register_sets_patient_role(tmp_db: Path):
    """Self-registration must always produce PATIENT role, never ADMIN."""
    user = register_user("Grace", "grace@example.com", "Password8!", "Password8!", db_path=tmp_db)
    assert user["role"] == "PATIENT"


# ---------------------------------------------------------------------------
# Login / Authentication
# ---------------------------------------------------------------------------


def test_authenticate_correct_credentials(tmp_db: Path):
    register_user("Heidi", "heidi@example.com", "Password8!", "Password8!", db_path=tmp_db)
    result = authenticate_user("heidi@example.com", "Password8!", db_path=tmp_db)
    assert result is not None
    assert result["email"] == "heidi@example.com"
    assert "password_hash" not in result


def test_authenticate_wrong_password_returns_none(tmp_db: Path):
    register_user("Ivan", "ivan@example.com", "Password8!", "Password8!", db_path=tmp_db)
    result = authenticate_user("ivan@example.com", "WrongPass!", db_path=tmp_db)
    assert result is None


def test_authenticate_unknown_email_returns_none(tmp_db: Path):
    result = authenticate_user("nobody@example.com", "Password8!", db_path=tmp_db)
    assert result is None


def test_authenticate_normalises_email(tmp_db: Path):
    register_user("Judy", "judy@example.com", "Password8!", "Password8!", db_path=tmp_db)
    result = authenticate_user("JUDY@EXAMPLE.COM", "Password8!", db_path=tmp_db)
    assert result is not None


def test_authenticate_empty_inputs_return_none(tmp_db: Path):
    assert authenticate_user("", "password", db_path=tmp_db) is None
    assert authenticate_user("user@example.com", "", db_path=tmp_db) is None


# ---------------------------------------------------------------------------
# Admin creation (controlled path only)
# ---------------------------------------------------------------------------


def test_create_admin_sets_admin_role(tmp_db: Path):
    user = create_admin_user("Admin User", "admin@example.com", "AdminPass1!", db_path=tmp_db)
    assert user["role"] == "ADMIN"
    assert "password_hash" not in user


def test_patient_auth_has_patient_role(tmp_db: Path):
    register_user("PatUser", "pat@example.com", "Password8!", "Password8!", db_path=tmp_db)
    result = authenticate_user("pat@example.com", "Password8!", db_path=tmp_db)
    assert result["role"] == "PATIENT"


def test_admin_auth_has_admin_role(tmp_db: Path):
    create_admin_user("AdminUser", "adm@example.com", "AdminPass1!", db_path=tmp_db)
    result = authenticate_user("adm@example.com", "AdminPass1!", db_path=tmp_db)
    assert result["role"] == "ADMIN"
