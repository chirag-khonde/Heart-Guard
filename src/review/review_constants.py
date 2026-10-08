"""Review constants for HeartGuard Professional Review module (Phase 11).

Centralises the controlled vocabulary for review statuses, display labels,
and urgency flags.  No logic lives here — pure data.

IMPORTANT: These constants define the ONLY valid review statuses.
           Do NOT add clinical diagnosis, prescription, or treatment
           plan values.  This module is review-only, NOT diagnostic.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Review statuses — the only valid values for ProfessionalReview.review_status
# ---------------------------------------------------------------------------

STATUS_PENDING = "PENDING"
STATUS_IN_REVIEW = "IN_REVIEW"
STATUS_REVIEWED = "REVIEWED"
STATUS_FOLLOW_UP_RECOMMENDED = "FOLLOW_UP_RECOMMENDED"
STATUS_CLOSED = "CLOSED"

REVIEW_STATUSES: list[str] = [
    STATUS_PENDING,
    STATUS_IN_REVIEW,
    STATUS_REVIEWED,
    STATUS_FOLLOW_UP_RECOMMENDED,
    STATUS_CLOSED,
]

REVIEW_STATUS_LABELS: dict[str, str] = {
    STATUS_PENDING:               "⏳ Pending",
    STATUS_IN_REVIEW:             "🔍 In Review",
    STATUS_REVIEWED:              "✅ Reviewed",
    STATUS_FOLLOW_UP_RECOMMENDED: "🔄 Follow-up Recommended",
    STATUS_CLOSED:                "🔒 Closed",
}

# ---------------------------------------------------------------------------
# Ordered status progression for UI display
# ---------------------------------------------------------------------------

STATUS_ORDER: dict[str, int] = {s: i for i, s in enumerate(REVIEW_STATUSES)}

# ---------------------------------------------------------------------------
# Urgency display
# ---------------------------------------------------------------------------

URGENCY_LABELS: dict[bool, str] = {
    True:  "🚨 Flagged for Urgent Attention",
    False: "—",
}

# ---------------------------------------------------------------------------
# Notes limits
# ---------------------------------------------------------------------------

PROFESSIONAL_NOTES_MAX_LENGTH = 4000   # characters
PROFESSIONAL_NOTES_MIN_LENGTH = 0      # notes are optional at creation time
