"""Data Minimization, Privacy, and Redaction Utilities (Phase 15).

Provides masking, data sanitization, privacy-safe export, LLM prompt redaction,
and secret scanning for the HeartGuard platform.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Any, Optional

from config.security import COMPLIANCE_STATEMENT, PROTOTYPE_NOTICE
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Masking & Redaction Functions
# ---------------------------------------------------------------------------


def mask_email(email: Optional[str]) -> str:
    """Mask email for privacy display. Example: john.doe@example.com -> j***e@example.com."""
    if not email or "@" not in email:
        return "******"
    local_part, domain = email.split("@", 1)
    if len(local_part) <= 2:
        masked_local = local_part[0] + "***"
    else:
        masked_local = local_part[0] + "***" + local_part[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: Optional[str]) -> str:
    """Mask phone number. Example: +1234567890 -> +1*****7890."""
    if not phone:
        return "******"
    clean = str(phone).strip()
    if len(clean) <= 4:
        return "****"
    return clean[:2] + ("*" * (len(clean) - 6)) + clean[-4:]


def mask_name(name: Optional[str]) -> str:
    """Mask personal name for logs and privacy view. Example: Alice Smith -> A*** S***."""
    if not name:
        return "Anonymous"
    parts = name.strip().split()
    masked_parts = []
    for part in parts:
        if len(part) <= 1:
            masked_parts.append(part + "***")
        else:
            masked_parts.append(part[0] + "***")
    return " ".join(masked_parts)


# ---------------------------------------------------------------------------
# LLM Sanitizer
# ---------------------------------------------------------------------------

_LLM_REDACTION_PATTERNS = [
    # Email
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL_REDACTED]"),
    # Phone numbers
    (re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[PHONE_REDACTED]"),
    # Social security / National ID patterns
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[GOV_ID_REDACTED]"),
    # Credit Card numbers
    (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "[CARD_REDACTED]"),
]


def sanitize_for_llm_processing(prompt_text: str) -> str:
    """Strip direct patient identifiers and sensitive contact details before AI processing."""
    if not prompt_text:
        return ""
    sanitized = prompt_text
    for pattern, replacement in _LLM_REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


# ---------------------------------------------------------------------------
# Privacy-Safe User Data Export (GDPR Art. 15 / CCPA Compliant Export)
# ---------------------------------------------------------------------------


def export_user_data(
    user_id: int,
    include_assessments: bool = True,
    include_recommendations: bool = True,
    auth_db_path: Optional[Path | str] = None,
    assessment_db_path: Optional[Path | str] = None,
    rec_db_path: Optional[Path | str] = None,
) -> dict[str, Any]:
    """Compile an exportable privacy package containing only the user's personal data.

    Invariants:
      - NEVER includes password_hash, session tokens, or internal credentials.
      - NEVER includes other patients' records.
      - STRICTLY personal data only.
    """
    from src.analytics.history_service import HistoryService
    from src.auth.user_repository import UserRepository
    from src.recommendations.recommendation_service import RecommendationService

    user = UserRepository.get_by_id(user_id, db_path=auth_db_path)
    if user is None:
        raise ValueError(f"User {user_id} not found for export.")

    export_package: dict[str, Any] = {
        "user_id": user.user_id,
        "prototype_notice": PROTOTYPE_NOTICE,
        "export_metadata": {
            "user_id": user.user_id,
            "username": user.username,
            "export_notice": PROTOTYPE_NOTICE,
            "compliance_statement": COMPLIANCE_STATEMENT,
        },
        "profile": {
            "user_id": user.user_id,
            "username": user.username,
            "email_masked": mask_email(user.email) if hasattr(user, "email") and user.email else None,
            "full_name": getattr(user, "full_name", user.username),
            "role": user.role,
            "created_at": getattr(user, "created_at", None),
        },
        "assessments": [],
        "recommendations": [],
    }

    if include_assessments:
        assessments = HistoryService.get_user_assessments(
            user_id=user_id, sort_order="desc", limit=100, db_path=assessment_db_path
        )
        for a in assessments:
            export_package["assessments"].append(
                {
                    "assessment_id": a.assessment_id,
                    "created_at": a.created_at,
                    "overall_risk": a.overall_risk,
                    "clinical_risk": a.clinical_risk,
                    "lifestyle_risk": a.lifestyle_risk,
                    "risk_category": a.risk_category,
                    "summary": a.narrative_summary,
                }
            )

    if include_recommendations:
        recs = RecommendationService.get_user_recommendations(
            user_id=user_id, limit=100, rec_db_path=rec_db_path
        )
        for r in recs:
            export_package["recommendations"].append(
                {
                    "recommendation_id": r.recommendation_id,
                    "assessment_id": r.assessment_id,
                    "category": r.category,
                    "title": r.title,
                    "description": r.description,
                    "priority": r.priority,
                    "created_at": r.created_at,
                }
            )

    return export_package


# ---------------------------------------------------------------------------
# Repository Secret Scanner
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    ("AWS Access Key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Private Key Header", re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")),
    ("Generic Secret Token", re.compile(r'(?:secret|api_key|access_token)\s*=\s*["\'][A-Za-z0-9_\-\.]{24,}["\']', re.IGNORECASE)),
    ("Hardcoded Password", re.compile(r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE)),
]


def scan_repo_secrets(repo_root: Optional[Path] = None) -> list[dict[str, Any]]:
    """Scan source files for accidental committed secrets or API tokens."""
    root = repo_root or Path(__file__).resolve().parent.parent.parent
    findings: list[dict[str, Any]] = []

    # Files and folders to skip
    skip_dirs = {".git", ".pytest_cache", "__pycache__", "venv", ".venv", "tests", "frontend", "node_modules"}
    skip_exts = {".pyc", ".db", ".png", ".jpg", ".pkl", ".joblib", ".pt", ".onnx"}
    skip_files = {"logger.py"}  # Contains privacy filter keywords, not actual secrets

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in skip_exts:
                continue
            if fname in skip_files:
                continue
            fpath = Path(dirpath) / fname
            # Skip test files and settings (settings reads env vars)
            if "test" in fname.lower() or fname.lower() == "settings.py":
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for name, pattern in _SECRET_PATTERNS:
                matches = pattern.findall(content)
                if matches:
                    findings.append(
                        {
                            "file": str(fpath.relative_to(root)),
                            "secret_type": name,
                            "count": len(matches),
                        }
                    )

    return findings
