"""Tests for ReviewService (Phase 11).

Covers:
  - Database initialization
  - Review creation (new, idempotent)
  - Review retrieval by assessment / by reviewer / by ID
  - Review update with ownership enforcement
  - Status validation
  - Notes length validation
  - Pending assessments query
  - All-assessments-with-review-status query
  - SAFETY: original assessment fields are never mutated
"""

from __future__ import annotations

import sqlite3
import tempfile
import uuid
from pathlib import Path

import pytest

from src.analytics.models import init_assessment_db
from src.review.models import ProfessionalReview, init_review_db
from src.review.review_constants import (
    PROFESSIONAL_NOTES_MAX_LENGTH,
    REVIEW_STATUSES,
    STATUS_CLOSED,
    STATUS_FOLLOW_UP_RECOMMENDED,
    STATUS_IN_REVIEW,
    STATUS_PENDING,
    STATUS_REVIEWED,
)
from src.review.review_service import ReviewService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db_pair(tmp_path: Path):
    """Return (assessment_db_path, review_db_path) pointing to temp files."""
    assessment_db = tmp_path / "assessments.db"
    review_db = tmp_path / "reviews.db"
    init_assessment_db(assessment_db)
    init_review_db(review_db)
    return assessment_db, review_db


def _insert_assessment(db_path: Path, assessment_id: str | None = None, user_id: int = 1) -> str:
    """Insert a minimal test assessment record and return its assessment_id."""
    aid = assessment_id or uuid.uuid4().hex[:8]
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO assessments (
                assessment_id, user_id, created_at, clinical_risk, lifestyle_risk,
                overall_risk, risk_category, recommendation, model_version,
                narrative_summary, alert_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                aid, user_id, "2024-01-01T12:00:00+00:00",
                65.0, 40.0, 57.5,
                "MODERATE_RISK", "Schedule a check-up.", "HeartGuard-ML (v0.1.0)",
                "AI narrative.", "NOT_TRIGGERED",
            ),
        )
        conn.commit()
    return aid


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------


class TestReviewDBInit:
    def test_creates_table(self, tmp_path: Path) -> None:
        db = tmp_path / "reviews.db"
        init_review_db(db)
        with sqlite3.connect(str(db)) as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='professional_reviews'"
            ).fetchone()
        assert row is not None, "professional_reviews table should be created"

    def test_idempotent(self, tmp_path: Path) -> None:
        db = tmp_path / "reviews.db"
        init_review_db(db)
        init_review_db(db)  # second call should not raise


# ---------------------------------------------------------------------------
# ProfessionalReview dataclass validation
# ---------------------------------------------------------------------------


class TestProfessionalReviewModel:
    def _make_review(self, **kwargs) -> ProfessionalReview:
        defaults = dict(
            id=None,
            review_id="abc123",
            assessment_id="assess001",
            reviewer_id=99,
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T00:00:00+00:00",
            review_status=STATUS_PENDING,
            professional_notes="",
            follow_up_required=False,
            urgency_flag=False,
        )
        defaults.update(kwargs)
        return ProfessionalReview(**defaults)

    def test_valid_construction(self) -> None:
        r = self._make_review()
        assert r.review_status == STATUS_PENDING

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid review_status"):
            self._make_review(review_status="DIAGNOSE")

    def test_notes_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="professional_notes exceeds"):
            self._make_review(professional_notes="x" * (PROFESSIONAL_NOTES_MAX_LENGTH + 1))

    def test_to_dict_has_no_extra_fields(self) -> None:
        r = self._make_review(professional_notes="test note")
        d = r.to_dict()
        assert "professional_notes" in d
        # Must NOT contain any AI-generated fields
        ai_fields = {"clinical_risk", "lifestyle_risk", "overall_risk", "risk_category",
                     "recommendation", "model_version", "narrative_summary"}
        for field in ai_fields:
            assert field not in d, f"AI field '{field}' must not appear in review dict"


# ---------------------------------------------------------------------------
# ReviewService.create_review
# ---------------------------------------------------------------------------


class TestCreateReview:
    def test_creates_review_for_valid_assessment(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        aid = _insert_assessment(assess_db)

        review = ReviewService.create_review(
            reviewer_id=1, assessment_id=aid,
            review_db_path=review_db, assessment_db_path=assess_db,
        )
        assert review.review_id is not None
        assert review.assessment_id == aid
        assert review.reviewer_id == 1
        assert review.review_status == STATUS_PENDING

    def test_raises_for_nonexistent_assessment(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        with pytest.raises(ValueError, match="not found"):
            ReviewService.create_review(
                reviewer_id=1, assessment_id="ghost_id",
                review_db_path=review_db, assessment_db_path=assess_db,
            )

    def test_idempotent_on_duplicate_assessment(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        aid = _insert_assessment(assess_db)

        r1 = ReviewService.create_review(1, aid, review_db, assess_db)
        r2 = ReviewService.create_review(1, aid, review_db, assess_db)
        assert r1.review_id == r2.review_id, "Second create should return existing review"


# ---------------------------------------------------------------------------
# ReviewService.update_review
# ---------------------------------------------------------------------------


class TestUpdateReview:
    def _create_fresh(self, tmp_db_pair):
        assess_db, review_db = tmp_db_pair
        aid = _insert_assessment(assess_db, user_id=5)
        review = ReviewService.create_review(5, aid, review_db, assess_db)
        return review, assess_db, review_db

    def test_updates_status(self, tmp_db_pair) -> None:
        review, _, review_db = self._create_fresh(tmp_db_pair)
        updated = ReviewService.update_review(
            review_id=review.review_id,
            reviewer_id=review.reviewer_id,
            review_status=STATUS_IN_REVIEW,
            review_db_path=review_db,
        )
        assert updated.review_status == STATUS_IN_REVIEW

    def test_updates_notes(self, tmp_db_pair) -> None:
        review, _, review_db = self._create_fresh(tmp_db_pair)
        notes = "Patient appears stable based on AI scores."
        updated = ReviewService.update_review(
            review_id=review.review_id,
            reviewer_id=review.reviewer_id,
            professional_notes=notes,
            review_db_path=review_db,
        )
        assert updated.professional_notes == notes

    def test_updates_flags(self, tmp_db_pair) -> None:
        review, _, review_db = self._create_fresh(tmp_db_pair)
        updated = ReviewService.update_review(
            review_id=review.review_id,
            reviewer_id=review.reviewer_id,
            follow_up_required=True,
            urgency_flag=True,
            review_db_path=review_db,
        )
        assert updated.follow_up_required is True
        assert updated.urgency_flag is True

    def test_ownership_enforced(self, tmp_db_pair) -> None:
        """A different reviewer must not be able to update another reviewer's record."""
        review, _, review_db = self._create_fresh(tmp_db_pair)
        with pytest.raises(PermissionError):
            ReviewService.update_review(
                review_id=review.review_id,
                reviewer_id=9999,  # wrong reviewer
                review_status=STATUS_CLOSED,
                review_db_path=review_db,
            )

    def test_invalid_status_raises(self, tmp_db_pair) -> None:
        review, _, review_db = self._create_fresh(tmp_db_pair)
        with pytest.raises(ValueError, match="Invalid review_status"):
            ReviewService.update_review(
                review_id=review.review_id,
                reviewer_id=review.reviewer_id,
                review_status="PRESCRIBE",
                review_db_path=review_db,
            )

    def test_notes_max_length_enforced(self, tmp_db_pair) -> None:
        review, _, review_db = self._create_fresh(tmp_db_pair)
        with pytest.raises(ValueError, match="professional_notes exceeds"):
            ReviewService.update_review(
                review_id=review.review_id,
                reviewer_id=review.reviewer_id,
                professional_notes="x" * (PROFESSIONAL_NOTES_MAX_LENGTH + 1),
                review_db_path=review_db,
            )

    def test_nonexistent_review_raises(self, tmp_db_pair) -> None:
        _, review_db = tmp_db_pair
        with pytest.raises(ValueError, match="not found"):
            ReviewService.update_review(
                review_id="does_not_exist",
                reviewer_id=1,
                review_db_path=review_db,
            )


# ---------------------------------------------------------------------------
# ReviewService — read helpers
# ---------------------------------------------------------------------------


class TestReviewReads:
    def test_get_review_for_assessment_returns_none_when_absent(self, tmp_db_pair) -> None:
        _, review_db = tmp_db_pair
        result = ReviewService.get_review_for_assessment("no_such_id", review_db)
        assert result is None

    def test_get_review_for_assessment_returns_record(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        aid = _insert_assessment(assess_db)
        ReviewService.create_review(1, aid, review_db, assess_db)
        result = ReviewService.get_review_for_assessment(aid, review_db)
        assert result is not None
        assert result.assessment_id == aid

    def test_get_reviews_by_reviewer_returns_correct_reviews(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        aid1 = _insert_assessment(assess_db, user_id=1)
        aid2 = _insert_assessment(assess_db, user_id=1)
        ReviewService.create_review(42, aid1, review_db, assess_db)
        ReviewService.create_review(42, aid2, review_db, assess_db)
        # reviewer 99 creates a different review
        aid3 = _insert_assessment(assess_db, user_id=2)
        ReviewService.create_review(99, aid3, review_db, assess_db)

        reviews_42 = ReviewService.get_reviews_by_reviewer(42, review_db)
        assert len(reviews_42) == 2
        assert all(r.reviewer_id == 42 for r in reviews_42)

    def test_get_review_by_id(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        aid = _insert_assessment(assess_db)
        created = ReviewService.create_review(7, aid, review_db, assess_db)
        fetched = ReviewService.get_review_by_id(created.review_id, review_db)
        assert fetched is not None
        assert fetched.review_id == created.review_id

    def test_get_all_reviews(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        for i in range(3):
            aid = _insert_assessment(assess_db, user_id=i + 1)
            ReviewService.create_review(10 + i, aid, review_db, assess_db)
        all_reviews = ReviewService.get_all_reviews(review_db)
        assert len(all_reviews) == 3


# ---------------------------------------------------------------------------
# Pending assessments
# ---------------------------------------------------------------------------


class TestPendingAssessments:
    def test_returns_only_unreviewed(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        aid_reviewed = _insert_assessment(assess_db)
        aid_pending = _insert_assessment(assess_db)

        ReviewService.create_review(1, aid_reviewed, review_db, assess_db)

        pending = ReviewService.get_pending_assessments(assess_db, review_db)
        pending_ids = [a.assessment_id for a in pending]
        assert aid_pending in pending_ids
        assert aid_reviewed not in pending_ids

    def test_empty_when_all_reviewed(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        aid = _insert_assessment(assess_db)
        ReviewService.create_review(1, aid, review_db, assess_db)

        pending = ReviewService.get_pending_assessments(assess_db, review_db)
        assert len(pending) == 0


# ---------------------------------------------------------------------------
# All assessments with review status
# ---------------------------------------------------------------------------


class TestAllAssessmentsWithReviewStatus:
    def test_includes_review_status(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        aid = _insert_assessment(assess_db)
        ReviewService.create_review(1, aid, review_db, assess_db)
        ReviewService.update_review(
            ReviewService.get_review_for_assessment(aid, review_db).review_id,
            reviewer_id=1,
            review_status=STATUS_REVIEWED,
            review_db_path=review_db,
        )

        rows = ReviewService.get_all_assessments_with_review_status(assess_db, review_db)
        matched = [r for r in rows if r["assessment_id"] == aid]
        assert matched
        assert matched[0]["review_status"] == STATUS_REVIEWED

    def test_unreviewed_shows_pending(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        aid = _insert_assessment(assess_db)

        rows = ReviewService.get_all_assessments_with_review_status(assess_db, review_db)
        matched = [r for r in rows if r["assessment_id"] == aid]
        assert matched
        assert matched[0]["review_status"] == STATUS_PENDING


# ---------------------------------------------------------------------------
# Safety: AI fields must not exist in any review payload
# ---------------------------------------------------------------------------


class TestAISafety:
    """Verify that no AI-generated field is ever returned by the review service."""

    AI_FIELDS = {
        "clinical_risk", "lifestyle_risk", "overall_risk",
        "risk_category", "recommendation", "model_version",
        "narrative_summary", "top_clinical_factors_json",
        "lifestyle_factors_json", "clinical_data_json",
    }

    def test_review_dict_has_no_ai_fields(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        aid = _insert_assessment(assess_db)
        review = ReviewService.create_review(1, aid, review_db, assess_db)
        d = review.to_dict()
        for field in self.AI_FIELDS:
            assert field not in d, f"AI field '{field}' must NOT appear in a review dict"

    def test_get_reviews_by_reviewer_no_ai_fields(self, tmp_db_pair) -> None:
        assess_db, review_db = tmp_db_pair
        aid = _insert_assessment(assess_db)
        ReviewService.create_review(1, aid, review_db, assess_db)
        reviews = ReviewService.get_reviews_by_reviewer(1, review_db)
        for r in reviews:
            d = r.to_dict()
            for field in self.AI_FIELDS:
                assert field not in d
