"""Tests for Phase 11 reviewer authorization helpers.

Covers:
  - is_reviewer() returns True only for REVIEWER role
  - is_reviewer() returns False for PATIENT, ADMIN, unauthenticated
  - require_reviewer() calls st.stop() for non-REVIEWER roles
  - require_reviewer() passes through for REVIEWER role
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_session(role: str | None, authenticated: bool = True):
    """Return patch kwargs for session_manager references inside authorization module."""
    return {
        "is_authenticated": MagicMock(return_value=authenticated),
        "get_current_role": MagicMock(return_value=role),
    }


# ---------------------------------------------------------------------------
# is_reviewer()
# ---------------------------------------------------------------------------


class TestIsReviewer:
    def test_returns_true_for_reviewer_role(self) -> None:
        patches = _mock_session("REVIEWER")
        with patch.multiple("src.auth.authorization", **patches):
            from src.auth.authorization import is_reviewer
            assert is_reviewer() is True

    def test_returns_false_for_patient(self) -> None:
        patches = _mock_session("PATIENT")
        with patch.multiple("src.auth.authorization", **patches):
            from src.auth.authorization import is_reviewer
            assert is_reviewer() is False

    def test_returns_false_for_admin(self) -> None:
        patches = _mock_session("ADMIN")
        with patch.multiple("src.auth.authorization", **patches):
            from src.auth.authorization import is_reviewer
            assert is_reviewer() is False

    def test_returns_false_when_unauthenticated(self) -> None:
        patches = _mock_session(None, authenticated=False)
        with patch.multiple("src.auth.authorization", **patches):
            from src.auth.authorization import is_reviewer
            assert is_reviewer() is False


# ---------------------------------------------------------------------------
# require_reviewer()
# ---------------------------------------------------------------------------


class TestRequireReviewer:
    def _run_require_reviewer(self, role: str | None, authenticated: bool = True):
        """Call require_reviewer() with mocked session and capture st calls."""
        patches = _mock_session(role, authenticated)
        with patch.multiple("src.auth.authorization", **patches):
            import streamlit as st
            with patch.object(st, "stop", side_effect=SystemExit(0)) as mock_stop, \
                 patch.object(st, "error") as mock_error, \
                 patch.object(st, "warning") as mock_warning, \
                 patch.object(st, "page_link"):
                from src.auth.authorization import require_reviewer
                try:
                    require_reviewer()
                    return mock_stop, mock_error, mock_warning, False  # did not stop
                except SystemExit:
                    return mock_stop, mock_error, mock_warning, True   # st.stop() called

    def test_passes_for_reviewer(self) -> None:
        mock_stop, _, _, stopped = self._run_require_reviewer("REVIEWER")
        assert not stopped, "require_reviewer() should NOT stop for REVIEWER role"

    def test_stops_for_patient(self) -> None:
        mock_stop, _, _, stopped = self._run_require_reviewer("PATIENT")
        assert stopped, "require_reviewer() should call st.stop() for PATIENT role"

    def test_stops_for_admin(self) -> None:
        mock_stop, _, _, stopped = self._run_require_reviewer("ADMIN")
        assert stopped, "require_reviewer() should call st.stop() for ADMIN role"

    def test_stops_when_unauthenticated(self) -> None:
        mock_stop, _, _, stopped = self._run_require_reviewer(None, authenticated=False)
        assert stopped, "require_reviewer() should call st.stop() for unauthenticated users"

    def test_shows_error_for_wrong_role(self) -> None:
        _, mock_error, _, stopped = self._run_require_reviewer("PATIENT")
        assert stopped
        mock_error.assert_called_once()
        # The error message should NOT contain diagnosis/clinical terminology
        error_text = mock_error.call_args[0][0]
        forbidden_terms = ["diagnos", "prescri", "treat", "medic"]
        for term in forbidden_terms:
            assert term.lower() not in error_text.lower(), (
                f"Authorization error message must not contain clinical term '{term}'"
            )


# ---------------------------------------------------------------------------
# Role constant
# ---------------------------------------------------------------------------


class TestRoleReviewerConstant:
    def test_role_reviewer_defined(self) -> None:
        from config.settings import ROLE_REVIEWER
        assert ROLE_REVIEWER == "REVIEWER"

    def test_role_reviewer_in_valid_roles(self) -> None:
        from config.settings import VALID_ROLES, ROLE_REVIEWER
        assert ROLE_REVIEWER in VALID_ROLES

    def test_valid_roles_contains_all_three(self) -> None:
        from config.settings import VALID_ROLES
        assert "PATIENT" in VALID_ROLES
        assert "ADMIN" in VALID_ROLES
        assert "REVIEWER" in VALID_ROLES


# ---------------------------------------------------------------------------
# Review constants sanity checks
# ---------------------------------------------------------------------------


class TestReviewConstants:
    def test_review_statuses_complete(self) -> None:
        from src.review.review_constants import REVIEW_STATUSES
        expected = {"PENDING", "IN_REVIEW", "REVIEWED", "FOLLOW_UP_RECOMMENDED", "CLOSED"}
        assert set(REVIEW_STATUSES) == expected

    def test_all_statuses_have_labels(self) -> None:
        from src.review.review_constants import REVIEW_STATUSES, REVIEW_STATUS_LABELS
        for status in REVIEW_STATUSES:
            assert status in REVIEW_STATUS_LABELS, f"Missing label for status '{status}'"

    def test_notes_max_length_positive(self) -> None:
        from src.review.review_constants import PROFESSIONAL_NOTES_MAX_LENGTH
        assert PROFESSIONAL_NOTES_MAX_LENGTH > 0

    def test_reviews_db_path_configured(self) -> None:
        from config.settings import REVIEWS_DB_PATH
        assert REVIEWS_DB_PATH is not None
        assert "reviews" in str(REVIEWS_DB_PATH).lower()
