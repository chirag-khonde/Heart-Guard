"""Role-based authorization for HeartGuard (Phase 9).

Provides guard functions that enforce authentication and role checks.
All enforcement is server-side — UI hiding alone is NOT relied upon.

Usage (at the top of every protected page):
    from src.auth.authorization import require_authentication, require_role
    require_authentication()                  # any logged-in user
    require_role("ADMIN")                     # admin only

These functions call st.stop() on violation, halting page rendering.
"""

from __future__ import annotations

import streamlit as st

from config.settings import ROLE_ADMIN, ROLE_PATIENT, ROLE_REVIEWER
from src.auth.session_manager import get_current_role, is_authenticated


# ---------------------------------------------------------------------------
# Core guards
# ---------------------------------------------------------------------------


def require_authentication() -> None:
    """Stop page rendering if the user is not authenticated.

    Displays a safe prompt to log in and calls st.stop().
    """
    if not is_authenticated():
        st.warning("🔒 Please log in to access this page.")
        st.page_link("pages/login.py", label="Go to Login")
        st.stop()


def require_role(role: str) -> None:
    """Stop page rendering if the current user does not have the required role.

    Also enforces authentication (calls require_authentication first).

    Args:
        role: Required role string, e.g. 'ADMIN' or 'PATIENT'.
    """
    require_authentication()
    current_role = get_current_role()
    if current_role != role:
        st.error("⛔ You do not have permission to access this page.")
        st.stop()


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------


def is_admin() -> bool:
    """Return True if the current authenticated user has the ADMIN role.

    Returns:
        bool: True for admin users.
    """
    if not is_authenticated():
        return False
    return get_current_role() == ROLE_ADMIN


def is_patient() -> bool:
    """Return True if the current authenticated user has the PATIENT role.

    Returns:
        bool: True for patient users.
    """
    if not is_authenticated():
        return False
    return get_current_role() == ROLE_PATIENT


def is_reviewer() -> bool:
    """Return True if the current authenticated user has the REVIEWER role.

    Returns:
        bool: True for authorized professional reviewer users.
    """
    if not is_authenticated():
        return False
    return get_current_role() == ROLE_REVIEWER


def require_reviewer() -> None:
    """Stop page rendering if the current user does not have the REVIEWER role.

    Also enforces authentication (calls require_authentication first).
    This guard must be called at the top of every reviewer-only page.
    """
    require_authentication()
    current_role = get_current_role()
    if current_role != ROLE_REVIEWER:
        st.error(
            "⛔ This page is restricted to authorized professional reviewers. "
            "Please contact your system administrator if you require access."
        )
        st.stop()
