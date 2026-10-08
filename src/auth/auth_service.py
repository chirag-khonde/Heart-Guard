"""Authentication service for HeartGuard (Phase 9 & Phase 15).

Orchestrates user registration and login. Applies input validation,
password hashing, timing attack mitigation, and audit logging.
Never reveals whether a specific email exists on failed login.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Optional

from config.settings import (
    AUTH_DB_PATH,
    EMAIL_MAX_LENGTH,
    NAME_MAX_LENGTH,
    ROLE_PATIENT,
)
from src.auth.models import init_auth_db
from src.auth.password_service import hash_password, verify_password
from src.auth.user_repository import create_user, find_by_email
from src.security.input_validator import validate_password_strength
from src.security.security_logger import SecurityLogger
from src.utils.logger import get_logger

logger = get_logger(__name__)

# RFC-5322 regex for registration email format validation
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


def _normalise_email(email: str) -> str:
    """Lowercase and strip whitespace from email for consistent storage."""
    return email.strip().lower()


def _validate_email_format(email: str) -> None:
    """Raise ValueError if email format is invalid."""
    if not email or len(email) > EMAIL_MAX_LENGTH:
        raise ValueError("Email address is invalid.")
    if not _EMAIL_RE.match(email):
        raise ValueError("Email address is invalid.")


def _validate_name(name: str) -> None:
    """Raise ValueError if name is empty or too long."""
    if not name or not name.strip():
        raise ValueError("Name is required.")
    if len(name.strip()) > NAME_MAX_LENGTH:
        raise ValueError(f"Name must be {NAME_MAX_LENGTH} characters or fewer.")


# ---------------------------------------------------------------------------
# Public Functions
# ---------------------------------------------------------------------------


def register_user(
    name: str,
    email: str,
    password: str,
    confirm_password: str,
    db_path: Path | str = AUTH_DB_PATH,
) -> dict:
    """Register a new PATIENT user account.

    Role is always set to PATIENT on self-registration.
    Admin accounts must be created via scripts/create_admin.py.
    """
    target_path = Path(db_path)
    # Validate name
    _validate_name(name)
    clean_name = name.strip()

    # Validate and normalise email
    _validate_email_format(email)
    clean_email = _normalise_email(email)

    # Validate password against security policy (Phase 15)
    validate_password_strength(password)

    # Confirm passwords match (never log either value)
    if password != confirm_password:
        raise ValueError("Passwords do not match.")

    # Ensure DB is ready
    init_auth_db(target_path)

    # Hash immediately — plaintext never persisted
    pw_hash = hash_password(password)

    # create_user raises ValueError on duplicate email
    user = create_user(
        name=clean_name,
        email=clean_email,
        password_hash=pw_hash,
        role=ROLE_PATIENT,
        db_path=target_path,
    )

    logger.info("Registration successful: user_id=%s role=%s", user.id, user.role)
    SecurityLogger.log_authentication(
        username=clean_email,
        success=True,
        user_id=user.id,
        role=user.role,
        reason="Account registration",
    )
    return user.to_safe_dict()


def authenticate_user(
    email: str,
    password: str,
    db_path: Path | str = AUTH_DB_PATH,
    ip_address: Optional[str] = None,
) -> Optional[dict]:
    """Authenticate a user by email and password.

    Intentionally generic error path — does NOT reveal whether an email
    exists in the database.
    """
    target_path = Path(db_path)
    if not email or not password:
        SecurityLogger.log_authentication(
            username=email or "unknown",
            success=False,
            ip_address=ip_address,
            reason="Missing credentials",
        )
        return None

    clean_email = _normalise_email(email)

    # Retrieve user — even if not found, we run verify_password against a
    # dummy hash to prevent timing-based email enumeration.
    user = find_by_email(clean_email, db_path=target_path)

    if user is None:
        # Run a dummy verification to normalise timing
        verify_password(password, "$2b$12$invalidhashplaceholder00000000000000000000000000000000")
        logger.warning("Login attempt for unknown email")
        SecurityLogger.log_authentication(
            username=clean_email,
            success=False,
            ip_address=ip_address,
            reason="Account not found",
        )
        return None

    if not user.is_active:
        verify_password(password, "$2b$12$invalidhashplaceholder00000000000000000000000000000000")
        logger.warning("Login attempt for deactivated account: user_id=%s", user.id)
        SecurityLogger.log_authentication(
            username=clean_email,
            success=False,
            user_id=user.id,
            role=user.role,
            ip_address=ip_address,
            reason="Account deactivated",
        )
        return None

    if not verify_password(password, user.password_hash):
        logger.warning("Failed login: user_id=%s", user.id)
        SecurityLogger.log_authentication(
            username=clean_email,
            success=False,
            user_id=user.id,
            role=user.role,
            ip_address=ip_address,
            reason="Invalid credentials",
        )
        return None

    logger.info("Login successful: user_id=%s role=%s", user.id, user.role)
    SecurityLogger.log_authentication(
        username=clean_email,
        success=True,
        user_id=user.id,
        role=user.role,
        ip_address=ip_address,
        reason="Login successful",
    )
    return user.to_safe_dict()


def create_admin_user(
    name: str,
    email: str,
    password: str,
    db_path: Path | str = AUTH_DB_PATH,
) -> dict:
    """Create an ADMIN user account."""
    target_path = Path(db_path)
    _validate_name(name)
    _validate_email_format(email)
    validate_password_strength(password)

    clean_email = _normalise_email(email)
    pw_hash = hash_password(password)

    init_auth_db(target_path)
    user = create_user(
        name=name.strip(),
        email=clean_email,
        password_hash=pw_hash,
        role="ADMIN",
        db_path=target_path,
    )
    logger.info("Admin account created: user_id=%s", user.id)
    SecurityLogger.log_admin_action(
        actor_id=user.id or 0,
        actor_role="ADMIN",
        action="create_admin_user",
        target_user_id=user.id,
        detail=f"Created admin account {clean_email}",
    )
    return user.to_safe_dict()


def create_reviewer_user(
    name: str,
    email: str,
    password: str,
    db_path: Path | str = AUTH_DB_PATH,
) -> dict:
    """Create a REVIEWER user account (Phase 11)."""
    target_path = Path(db_path)
    _validate_name(name)
    _validate_email_format(email)
    validate_password_strength(password)

    clean_email = _normalise_email(email)
    pw_hash = hash_password(password)

    init_auth_db(target_path)
    user = create_user(
        name=name.strip(),
        email=clean_email,
        password_hash=pw_hash,
        role="REVIEWER",
        db_path=target_path,
    )
    logger.info("Reviewer account created: user_id=%s", user.id)
    return user.to_safe_dict()


class AuthService:
    """Authentication and identity lifecycle service."""

    register_user = staticmethod(register_user)
    authenticate_user = staticmethod(authenticate_user)
    create_admin_user = staticmethod(create_admin_user)
    create_reviewer_user = staticmethod(create_reviewer_user)
