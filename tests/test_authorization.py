"""Authorization tests for HeartGuard Phase 9.

Tests RBAC enforcement: patient/admin separation, unauthenticated access
prevention, and data isolation guarantees.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.auth.auth_service import create_admin_user, register_user
from src.auth.authorization import is_admin, is_patient
from src.auth.models import init_auth_db
from src.auth.user_repository import find_by_email


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Path:
    db = tmp_path / "test_auth.db"
    init_auth_db(db)
    return db


# ---------------------------------------------------------------------------
# is_admin / is_patient helpers (using mocked session state)
# ---------------------------------------------------------------------------


def _mock_session(authenticated: bool = True, role: str = "PATIENT"):
    """Return a fake st.session_state mapping for authorization tests."""
    if not authenticated:
        return {}
    return {
        "_hg_authenticated": True,
        "_hg_user_id": 1,
        "_hg_name": "Test User",
        "_hg_role": role,
    }


def test_is_admin_returns_true_for_admin():
    fake_state = _mock_session(role="ADMIN")
    with patch("src.auth.session_manager.st") as mock_st:
        mock_st.session_state = fake_state
        with patch("src.auth.authorization.st") as mock_auth_st:
            mock_auth_st.session_state = fake_state
            assert is_admin() is True


def test_is_admin_returns_false_for_patient():
    fake_state = _mock_session(role="PATIENT")
    with patch("src.auth.session_manager.st") as mock_st:
        mock_st.session_state = fake_state
        with patch("src.auth.authorization.st") as mock_auth_st:
            mock_auth_st.session_state = fake_state
            assert is_admin() is False


def test_is_patient_returns_true_for_patient():
    fake_state = _mock_session(role="PATIENT")
    with patch("src.auth.session_manager.st") as mock_st:
        mock_st.session_state = fake_state
        with patch("src.auth.authorization.st") as mock_auth_st:
            mock_auth_st.session_state = fake_state
            assert is_patient() is True


def test_is_patient_returns_false_for_admin():
    fake_state = _mock_session(role="ADMIN")
    with patch("src.auth.session_manager.st") as mock_st:
        mock_st.session_state = fake_state
        with patch("src.auth.authorization.st") as mock_auth_st:
            mock_auth_st.session_state = fake_state
            assert is_patient() is False


def test_unauthenticated_is_not_admin():
    fake_state = _mock_session(authenticated=False)
    with patch("src.auth.session_manager.st") as mock_st:
        mock_st.session_state = fake_state
        with patch("src.auth.authorization.st") as mock_auth_st:
            mock_auth_st.session_state = fake_state
            assert is_admin() is False


def test_unauthenticated_is_not_patient():
    fake_state = _mock_session(authenticated=False)
    with patch("src.auth.session_manager.st") as mock_st:
        mock_st.session_state = fake_state
        with patch("src.auth.authorization.st") as mock_auth_st:
            mock_auth_st.session_state = fake_state
            assert is_patient() is False


# ---------------------------------------------------------------------------
# require_authentication stops unauthenticated access
# ---------------------------------------------------------------------------


def test_require_authentication_calls_stop_when_not_authenticated():
    fake_state = {}  # unauthenticated
    with patch("src.auth.session_manager.st") as mock_sm_st, \
         patch("src.auth.authorization.st") as mock_auth_st:
        mock_sm_st.session_state = fake_state
        mock_auth_st.session_state = fake_state
        mock_auth_st.stop.side_effect = SystemExit("st.stop called")
        mock_auth_st.warning = lambda *a, **k: None
        mock_auth_st.page_link = lambda *a, **k: None

        from src.auth.authorization import require_authentication
        with pytest.raises(SystemExit):
            require_authentication()


def test_require_authentication_passes_when_authenticated():
    fake_state = _mock_session(role="PATIENT")
    with patch("src.auth.session_manager.st") as mock_sm_st, \
         patch("src.auth.authorization.st") as mock_auth_st:
        mock_sm_st.session_state = fake_state
        mock_auth_st.session_state = fake_state
        mock_auth_st.stop.side_effect = SystemExit("st.stop called")

        from src.auth.authorization import require_authentication
        # Should not raise
        require_authentication()


# ---------------------------------------------------------------------------
# require_role blocks wrong role
# ---------------------------------------------------------------------------


def test_require_role_blocks_patient_from_admin():
    fake_state = _mock_session(role="PATIENT")
    with patch("src.auth.session_manager.st") as mock_sm_st, \
         patch("src.auth.authorization.st") as mock_auth_st:
        mock_sm_st.session_state = fake_state
        mock_auth_st.session_state = fake_state
        mock_auth_st.stop.side_effect = SystemExit("st.stop called")
        mock_auth_st.error = lambda *a, **k: None

        from src.auth.authorization import require_role
        with pytest.raises(SystemExit):
            require_role("ADMIN")


def test_require_role_allows_admin_to_admin():
    fake_state = _mock_session(role="ADMIN")
    with patch("src.auth.session_manager.st") as mock_sm_st, \
         patch("src.auth.authorization.st") as mock_auth_st:
        mock_sm_st.session_state = fake_state
        mock_auth_st.session_state = fake_state

        from src.auth.authorization import require_role
        # Should not raise
        require_role("ADMIN")


# ---------------------------------------------------------------------------
# Data isolation: patient cannot access another user's data via repository
# ---------------------------------------------------------------------------


def test_find_by_email_isolates_by_email(tmp_db: Path):
    """Confirm that user look-up is email-scoped; wrong email returns None."""
    register_user("User A", "usera@example.com", "Password8!", "Password8!", db_path=tmp_db)
    register_user("User B", "userb@example.com", "Password8!", "Password8!", db_path=tmp_db)

    user_a = find_by_email("usera@example.com", db_path=tmp_db)
    user_b = find_by_email("userb@example.com", db_path=tmp_db)

    assert user_a is not None
    assert user_b is not None
    assert user_a.id != user_b.id
    assert user_a.email != user_b.email


def test_find_by_email_unknown_returns_none(tmp_db: Path):
    result = find_by_email("nobody@example.com", db_path=tmp_db)
    assert result is None
