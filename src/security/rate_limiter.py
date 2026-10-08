"""Rate limiter for HeartGuard endpoints and session protection (Phase 9 & Phase 15).

Provides:
  1. Generic thread-safe in-memory sliding window rate limiter (`InMemoryRateLimiter`).
  2. Backward-compatible session-state wrappers for Streamlit login forms.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import threading
from typing import Optional

try:
    import streamlit as st
except ImportError:
    st = None

from config.security import RATE_LIMITS
from config.settings import LOGIN_COOLDOWN_SECONDS, LOGIN_MAX_ATTEMPTS
from src.security.security_logger import SecurityLogger
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Fallback in-memory storage if Streamlit session state is not active
_MEMORY_STATE: dict[str, Any] = {}
_LOCK = threading.Lock()


def _now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Generic Thread-Safe Sliding Window Rate Limiter
# ---------------------------------------------------------------------------


class InMemoryRateLimiter:
    """Thread-safe sliding window rate limiter."""

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        endpoint_name: str = "generic",
    ) -> tuple[bool, int]:
        """Check if request under key is allowed.

        Returns:
            tuple[bool, int]: (allowed, retry_after_seconds)
        """
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_seconds

        with self._lock:
            # Purge expired timestamps
            valid = [ts for ts in self._requests[key] if ts > cutoff]
            self._requests[key] = valid

            if len(valid) >= max_requests:
                earliest = valid[0]
                retry_after = max(1, int(earliest + window_seconds - now))
                SecurityLogger.log_rate_limit(endpoint_name, key, max_requests)
                return False, retry_after

            self._requests[key].append(now)
            return True, 0

    def reset(self, key: Optional[str] = None) -> None:
        """Reset rate limit counts."""
        with self._lock:
            if key:
                self._requests.pop(key, None)
            else:
                self._requests.clear()


# Global rate limiter instance
_GLOBAL_LIMITER = InMemoryRateLimiter()


def check_rate_limit(
    action: str,
    identifier: str,
) -> tuple[bool, str]:
    """Check whether an action by identifier is permitted under configured policies.

    Returns:
        tuple[bool, str]: (is_allowed, error_message_if_blocked)
    """
    policy = RATE_LIMITS.get(action, (10, 60))
    max_req, window = policy
    key = f"{action}:{identifier}"
    allowed, retry_after = _GLOBAL_LIMITER.is_allowed(
        key=key,
        max_requests=max_req,
        window_seconds=window,
        endpoint_name=action,
    )
    if not allowed:
        return False, f"Too many requests. Please wait {retry_after} seconds before retrying."
    return True, ""


# ---------------------------------------------------------------------------
# Streamlit Session State Login Rate Limiter (Phase 9 Compatibility)
# ---------------------------------------------------------------------------

_KEY_ATTEMPTS = "_hg_login_attempts"
_KEY_BLOCKED_UNTIL = "_hg_login_blocked_until"


def _get_session_val(key: str, default: Any = None) -> Any:
    if st is not None:
        try:
            return st.session_state.get(key, default)
        except Exception:
            pass
    with _LOCK:
        return _MEMORY_STATE.get(key, default)


def _set_session_val(key: str, val: Any) -> None:
    if st is not None:
        try:
            st.session_state[key] = val
            return
        except Exception:
            pass
    with _LOCK:
        _MEMORY_STATE[key] = val


def _pop_session_val(key: str) -> None:
    if st is not None:
        try:
            st.session_state.pop(key, None)
            return
        except Exception:
            pass
    with _LOCK:
        _MEMORY_STATE.pop(key, None)


def is_rate_limited() -> bool:
    """Check whether the current session is currently rate-limited."""
    blocked_until: datetime | None = _get_session_val(_KEY_BLOCKED_UNTIL)
    if blocked_until is None:
        return False
    if _now() < blocked_until:
        return True
    # Cooldown expired — reset
    _pop_session_val(_KEY_BLOCKED_UNTIL)
    _set_session_val(_KEY_ATTEMPTS, 0)
    return False


def record_failed_attempt() -> int:
    """Increment the failed-login counter and apply a block if threshold reached."""
    current = int(_get_session_val(_KEY_ATTEMPTS, 0)) + 1
    _set_session_val(_KEY_ATTEMPTS, current)

    if current >= LOGIN_MAX_ATTEMPTS:
        blocked_until = _now() + timedelta(seconds=LOGIN_COOLDOWN_SECONDS)
        _set_session_val(_KEY_BLOCKED_UNTIL, blocked_until)

    return current


def reset_attempts() -> None:
    """Reset attempt counter on successful login."""
    _pop_session_val(_KEY_ATTEMPTS)
    _pop_session_val(_KEY_BLOCKED_UNTIL)


def seconds_remaining() -> int:
    """Return seconds until the rate-limit block expires (0 if not blocked)."""
    blocked_until: datetime | None = _get_session_val(_KEY_BLOCKED_UNTIL)
    if blocked_until is None:
        return 0
    delta = (blocked_until - _now()).total_seconds()
    return max(0, int(delta))
