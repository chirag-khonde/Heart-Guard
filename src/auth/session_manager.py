"""Session manager for HeartGuard (Phase 9 & Phase 15).

Manages authenticated session state, enforces session rotation, and checks
inactivity timeouts.

Only stores: user_id (int), name (str), role (str), session_token (str), last_active (float).
NEVER stores: password, password_hash, raw clinical data vectors.
"""

from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any, Optional
import uuid

try:
    import streamlit as st
except ImportError:
    st = None

from config.security import SESSION_INACTIVITY_LIMIT_SECONDS
from src.security.audit_logger import log_event
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Session state keys
_KEY_USER_ID = "_hg_user_id"
_KEY_ROLE = "_hg_role"
_KEY_NAME = "_hg_name"
_KEY_IS_AUTH = "_hg_authenticated"
_KEY_SESSION_TOKEN = "_hg_session_token"
_KEY_LAST_ACTIVITY = "_hg_last_activity"

# Keys to purge on logout or timeout
_SENSITIVE_KEYS = [
    _KEY_USER_ID,
    _KEY_ROLE,
    _KEY_NAME,
    _KEY_IS_AUTH,
    _KEY_SESSION_TOKEN,
    _KEY_LAST_ACTIVITY,
    # Assessment / patient data
    "assessment_result",
    "lifestyle_result",
    "alert_result",
    "current_patient_data",
    "pdf_report_bytes",
]

# In-memory dictionary fallback for testing outside Streamlit runtime
_FALLBACK_SESSION: dict[str, Any] = {}


def _get_storage() -> dict[str, Any]:
    if st is not None:
        try:
            return st.session_state
        except Exception:
            pass
    return _FALLBACK_SESSION


def create_session(user: dict[str, Any]) -> str:
    """Create a new authenticated session with rotated session token.

    Args:
        user: Safe user dict from auth_service (must contain id, name, role).

    Returns:
        New session token string.
    """
    storage = _get_storage()
    # Invalidate any prior session state to prevent session fixation
    clear_session()

    session_token = secrets.token_hex(24)
    storage[_KEY_IS_AUTH] = True
    storage[_KEY_USER_ID] = user["id"]
    storage[_KEY_ROLE] = user["role"]
    storage[_KEY_NAME] = user["name"]
    storage[_KEY_SESSION_TOKEN] = session_token
    storage[_KEY_LAST_ACTIVITY] = datetime.now(timezone.utc).timestamp()

    return session_token


def is_authenticated() -> bool:
    """Return True if there is an active authenticated session and not expired."""
    storage = _get_storage()
    if not bool(storage.get(_KEY_IS_AUTH, False)):
        return False

    # Enforce session inactivity timeout
    if check_session_timeout():
        return False

    return True


def check_session_timeout() -> bool:
    """Check if the session has exceeded the inactivity limit.

    If timed out, clears session and returns True. Otherwise updates activity and returns False.
    """
    storage = _get_storage()
    if not storage.get(_KEY_IS_AUTH):
        return False

    last_active = storage.get(_KEY_LAST_ACTIVITY)
    if last_active is None:
        return False

    now = datetime.now(timezone.utc).timestamp()
    elapsed = now - float(last_active)

    if elapsed > SESSION_INACTIVITY_LIMIT_SECONDS:
        user_id = storage.get(_KEY_USER_ID)
        role = storage.get(_KEY_ROLE)
        logger.info("Session timed out for user_id=%s after %s seconds of inactivity", user_id, int(elapsed))
        log_event(
            event_type="session_expired",
            status="SUCCESS",
            user_id=user_id,
            role=role,
            detail=f"Session expired after {int(elapsed)}s of inactivity.",
            category="AUTHENTICATION",
            severity="INFO",
        )
        clear_session()
        return True

    # Touch session to record recent activity
    storage[_KEY_LAST_ACTIVITY] = now
    return False


def touch_session() -> None:
    """Update last activity timestamp."""
    storage = _get_storage()
    if storage.get(_KEY_IS_AUTH):
        storage[_KEY_LAST_ACTIVITY] = datetime.now(timezone.utc).timestamp()


def get_current_user() -> Optional[dict[str, Any]]:
    """Return safe user info for the authenticated session."""
    if not is_authenticated():
        return None
    storage = _get_storage()
    return {
        "id": storage.get(_KEY_USER_ID),
        "name": storage.get(_KEY_NAME, ""),
        "role": storage.get(_KEY_ROLE, ""),
    }


def get_current_user_id() -> Optional[int]:
    """Return the current user's internal ID, or None."""
    return get_current_user()["id"] if is_authenticated() else None


def get_current_role() -> Optional[str]:
    """Return the current user's role string, or None."""
    user = get_current_user()
    return user["role"] if user else None


def get_session_token() -> Optional[str]:
    """Return the current session token."""
    storage = _get_storage()
    return storage.get(_KEY_SESSION_TOKEN) if is_authenticated() else None


def clear_session() -> None:
    """Clear all authentication and sensitive session state on logout or timeout."""
    storage = _get_storage()
    for key in _SENSITIVE_KEYS:
        storage.pop(key, None)
