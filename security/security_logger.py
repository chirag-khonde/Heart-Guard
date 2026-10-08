"""High-level security event dispatcher (Phase 15).

Provides centralized, convenience routines for recording critical security events
such as IDOR attempts, authentication outcomes, administrative modifications,
and rate-limit violations across HeartGuard.
"""

from __future__ import annotations

import hashlib
from typing import Optional

from src.security.audit_logger import log_event
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _hash_ip(ip_address: Optional[str]) -> Optional[str]:
    """Return a non-reversible salt-hashed representation of an IP address."""
    if not ip_address:
        return None
    # Use SHA-256 with static prefix for pseudonymization
    salt = "hg_ip_sec_2026_"
    return hashlib.sha256((salt + ip_address.strip()).encode("utf-8")).hexdigest()[:16]


class SecurityLogger:
    """Convenience dispatcher for structured HeartGuard security logging."""

    @staticmethod
    def log_authentication(
        username: str,
        success: bool,
        user_id: Optional[int] = None,
        role: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Log a login or registration authentication event."""
        event_type = "login_success" if success else "login_failure"
        status = "SUCCESS" if success else "FAILURE"
        severity = "INFO" if success else "WARNING"
        detail = f"User: {username}" + (f" - Reason: {reason}" if reason else "")

        logger.info("Authentication %s for '%s' (id=%s, role=%s)", status, username, user_id, role)
        log_event(
            event_type=event_type,
            status=status,
            user_id=user_id,
            role=role,
            detail=detail,
            category="AUTHENTICATION",
            severity=severity,
            ip_hash=_hash_ip(ip_address),
        )

    @staticmethod
    def log_idor_attempt(
        actor_id: int,
        actor_role: str,
        resource_type: str,
        resource_id: str,
        owner_id: Optional[int] = None,
    ) -> None:
        """Log an unauthorized direct object reference (IDOR) attempt."""
        detail = (
            f"User {actor_id} ({actor_role}) attempted unauthorized access to {resource_type} "
            f"'{resource_id}' owned by user {owner_id}."
        )
        logger.warning("SECURITY ALERT: IDOR attempt - %s", detail)
        log_event(
            event_type="idor_attempt",
            status="BLOCKED",
            user_id=actor_id,
            role=actor_role,
            detail=detail,
            resource_type=resource_type,
            resource_id=resource_id,
            category="AUTHORIZATION",
            severity="HIGH",
        )

    @staticmethod
    def log_access_denied(
        actor_id: Optional[int],
        actor_role: Optional[str],
        action: str,
        resource_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Log general access control denial."""
        detail = f"Access denied for action '{action}'" + (f": {reason}" if reason else "")
        logger.warning("Access denied: actor=%s role=%s action=%s", actor_id, actor_role, action)
        log_event(
            event_type="access_denied",
            status="DENIED",
            user_id=actor_id,
            role=actor_role,
            detail=detail,
            resource_id=resource_id,
            category="AUTHORIZATION",
            severity="WARNING",
        )

    @staticmethod
    def log_admin_action(
        actor_id: int,
        actor_role: str,
        action: str,
        target_user_id: Optional[int] = None,
        detail: Optional[str] = None,
    ) -> None:
        """Log an administrative action (e.g. role modification, account status change)."""
        full_detail = f"Admin {actor_id} performed '{action}'"
        if target_user_id is not None:
            full_detail += f" on target user {target_user_id}"
        if detail:
            full_detail += f": {detail}"

        logger.info("Admin action executed: %s", full_detail)
        log_event(
            event_type="admin_access",
            status="SUCCESS",
            user_id=actor_id,
            role=actor_role,
            detail=full_detail,
            resource_type="user" if target_user_id else None,
            resource_id=str(target_user_id) if target_user_id else None,
            category="ADMIN_ACTION",
            severity="INFO",
        )

    @staticmethod
    def log_rate_limit(
        endpoint: str,
        identifier: str,
        limit: int,
    ) -> None:
        """Log when a client exceeds rate limits."""
        detail = f"Rate limit exceeded on '{endpoint}' (limit: {limit}) for identifier '{identifier}'"
        logger.warning(detail)
        log_event(
            event_type="rate_limit_exceeded",
            status="BLOCKED",
            detail=detail,
            category="SYSTEM_SECURITY",
            severity="WARNING",
        )

    @staticmethod
    def log_file_access(
        actor_id: Optional[int],
        actor_role: Optional[str],
        filename: str,
        action: str,
        status: str = "SUCCESS",
    ) -> None:
        """Log report and file access/download events."""
        detail = f"File {action} for '{filename}'"
        log_event(
            event_type="report_downloaded" if action == "download" else "report_generated",
            status=status,
            user_id=actor_id,
            role=actor_role,
            detail=detail,
            resource_type="report",
            resource_id=filename,
            category="FILE_ACCESS",
            severity="INFO" if status == "SUCCESS" else "WARNING",
        )
