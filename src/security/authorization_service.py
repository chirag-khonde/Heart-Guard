"""Server-Side Authorization & IDOR Defense Service (Phase 15).

Enforces mandatory access control and ownership verification across all domain
entities: assessments, recommendations, clinician reviews, and exported files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.analytics.history_service import HistoryService
from src.security.file_security import verify_report_access as _check_report_access
from src.security.security_logger import SecurityLogger
from src.utils.logger import get_logger

logger = get_logger(__name__)

ROLE_HIERARCHY: dict[str, int] = {
    "PATIENT": 10,
    "REVIEWER": 20,
    "ADMIN": 30,
}


class AuthorizationService:
    """Centralized server-side authorization and IDOR verification engine."""

    @staticmethod
    def has_role(user_role: str, required_role: str) -> bool:
        """Check if user_role satisfies required_role in the hierarchy."""
        user_level = ROLE_HIERARCHY.get(user_role.upper().strip(), 0)
        req_level = ROLE_HIERARCHY.get(required_role.upper().strip(), 0)
        return user_level >= req_level

    @classmethod
    def verify_assessment_access(
        cls,
        user_id: int,
        role: str,
        assessment_id: str,
        db_path: Optional[Path | str] = None,
    ) -> bool:
        """Verify whether actor can view/modify an assessment.

        Rules:
          - ADMIN and REVIEWER have clinical oversight access to all assessments.
          - PATIENT can ONLY access assessments where assessment.user_id == actor.user_id.
        """
        clean_role = role.upper().strip()
        if clean_role in ("ADMIN", "REVIEWER"):
            return True

        assessment = HistoryService.get_assessment_by_id(assessment_id, db_path=db_path)
        if assessment is None:
            SecurityLogger.log_access_denied(
                actor_id=user_id,
                actor_role=role,
                action="get_assessment",
                resource_id=assessment_id,
                reason="Assessment not found",
            )
            return False

        if assessment.user_id == user_id:
            return True

        # IDOR violation detected
        SecurityLogger.log_idor_attempt(
            actor_id=user_id,
            actor_role=role,
            resource_type="assessment",
            resource_id=assessment_id,
            owner_id=assessment.user_id,
        )
        return False

    @classmethod
    def verify_recommendation_access(
        cls,
        user_id: int,
        role: str,
        assessment_id: str,
        assessment_db_path: Optional[Path | str] = None,
    ) -> bool:
        """Verify whether actor can access recommendations for an assessment."""
        clean_role = role.upper().strip()
        if clean_role in ("ADMIN", "REVIEWER"):
            return True

        return cls.verify_assessment_access(
            user_id=user_id,
            role=role,
            assessment_id=assessment_id,
            db_path=assessment_db_path,
        )

    @classmethod
    def verify_report_access(
        cls,
        user_id: int,
        role: str,
        report_path_or_id: str | Path,
    ) -> bool:
        """Verify whether actor can download or view a report file."""
        return _check_report_access(user_id=user_id, role=role, report_identifier=report_path_or_id)

    @classmethod
    def verify_admin_privilege(cls, user_id: int, role: str, action: str) -> bool:
        """Verify actor has administrator rights."""
        if role.upper().strip() == "ADMIN":
            return True
        SecurityLogger.log_access_denied(
            actor_id=user_id,
            actor_role=role,
            action=action,
            reason="Requires ADMIN role",
        )
        return False

    @classmethod
    def verify_reviewer_privilege(cls, user_id: int, role: str, action: str) -> bool:
        """Verify actor has clinical reviewer or admin rights."""
        if role.upper().strip() in ("REVIEWER", "ADMIN"):
            return True
        SecurityLogger.log_access_denied(
            actor_id=user_id,
            actor_role=role,
            action=action,
            reason="Requires REVIEWER or ADMIN role",
        )
        return False
