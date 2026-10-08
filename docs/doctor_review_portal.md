# HeartGuard — Doctor Review Portal (Phase 11)

## Overview

Phase 11 introduces the **Doctor Review Portal** — a secure, role-gated module
that allows an authorized `REVIEWER`-role user to inspect AI-generated assessment
results and record structured professional observations.

---

## ⚠️ Clinical Safety Notice

> **This module is NOT a diagnostic system.**
>
> - Professional review notes are **observations only**, not clinical diagnoses.
> - Reviewers must NOT enter diagnoses, medication recommendations, treatment plans,
>   or any clinical decisions into the notes field.
> - AI-generated risk scores, SHAP values, and recommendations are **read-only**
>   and can NEVER be modified through the review portal.
> - HeartGuard is an academic/research prototype and is NOT a certified medical device.

---

## Architecture

### Data Separation

Phase 11 stores review data in a **completely separate database** from assessments:

| Database | Path | Contents |
|---|---|---|
| `assessments.db` | `data/assessments/assessments.db` | AI-generated assessment records (immutable after creation) |
| `reviews.db`     | `data/assessments/reviews.db`     | Professional review entries (created/updated by reviewers) |

This ensures that no review operation can ever corrupt or modify the original AI output.

### Review Record Fields

| Field | Type | Description |
|---|---|---|
| `review_id` | str | Unique identifier for this review |
| `assessment_id` | str | Links to the assessment being reviewed (FK — never modified) |
| `reviewer_id` | int | User ID of the REVIEWER who created this record |
| `created_at` | str | UTC ISO-8601 timestamp (immutable after creation) |
| `updated_at` | str | UTC ISO-8601 last-update timestamp |
| `review_status` | str | One of the controlled review statuses below |
| `professional_notes` | str | Free-text observations (max 4,000 chars) |
| `follow_up_required` | bool | Whether the reviewer recommends follow-up scheduling |
| `urgency_flag` | bool | Whether the reviewer flags the case for urgent attention |

### Controlled Review Statuses

| Status | Label |
|---|---|
| `PENDING` | ⏳ Pending |
| `IN_REVIEW` | 🔍 In Review |
| `REVIEWED` | ✅ Reviewed |
| `FOLLOW_UP_RECOMMENDED` | 🔄 Follow-up Recommended |
| `CLOSED` | 🔒 Closed |

---

## Module Structure

```
src/review/
    __init__.py          # Public API exports
    models.py            # ProfessionalReview dataclass + SQLite schema
    review_service.py    # CRUD service with ownership enforcement
    review_constants.py  # Controlled vocabulary (statuses, labels, limits)

pages/
    review.py            # Streamlit Doctor Review Portal page

scripts/
    create_reviewer.py   # Provisioning script for REVIEWER accounts

tests/
    test_review_service.py       # 27 service tests
    test_review_authorization.py # 16 authorization tests
```

---

## Provisioning a REVIEWER Account

Reviewer accounts must be created by a system administrator using the
provisioning script. Never create reviewer accounts through the public UI.

```bash
# Set credentials as environment variables (never as CLI arguments)
export REVIEWER_EMAIL=reviewer@heartguard.local
export REVIEWER_PASSWORD=<strong-password>
export REVIEWER_NAME="Dr. Jane Smith"

python scripts/create_reviewer.py

# Clear credentials from environment after setup
unset REVIEWER_PASSWORD
```

---

## Authorization

Phase 11 adds the following to `src/auth/authorization.py`:

```python
def is_reviewer() -> bool: ...       # Returns True for REVIEWER role
def require_reviewer() -> None: ...  # Calls st.stop() if role != REVIEWER
```

The `pages/review.py` page calls `require_reviewer()` at the top before any
rendering, enforcing server-side role checks.

---

## Ownership Rules

- A reviewer may only **update** review records that they created (`reviewer_id` match).
- Any authenticated REVIEWER may **read** all pending assessments.
- If another reviewer has already created a review for an assessment, the review
  detail panel shows a read-only view of that review to the second reviewer.

---

## Test Coverage

```bash
# Run Phase 11 tests only
pytest tests/test_review_service.py tests/test_review_authorization.py -v

# Run full regression suite
pytest -q --ignore=tests/test_auth.py --ignore=tests/test_authorization.py --ignore=tests/test_security.py
```

Phase 11 adds **43 new tests** (27 service + 16 authorization). All 310 runnable
regression tests pass after Phase 11.
