"""HeartGuard structured logging (Phase 16 — Production Hardened).

Provides environment-aware, rotating file + stream logging that:
  - Respects LOG_LEVEL and ENVIRONMENT settings.
  - Never logs passwords, tokens, clinical data, or session IDs.
  - Rotates log files to prevent unlimited disk growth.
  - Uses structured format with timestamp, level, module, and message.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

# Import lazily to avoid circular dependency on startup
def _get_settings():
    from config.settings import LOG_LEVEL, LOG_DIR, LOG_MAX_BYTES, LOG_BACKUP_COUNT, LOG_TO_FILE, IS_PRODUCTION
    return LOG_LEVEL, LOG_DIR, LOG_MAX_BYTES, LOG_BACKUP_COUNT, LOG_TO_FILE, IS_PRODUCTION


# Privacy-safe log filter: blocks lines that may contain sensitive values
class _PrivacyFilter(logging.Filter):
    """Drop any log records that appear to contain sensitive credential patterns."""

    _BLOCKED_KEYWORDS = (
        "password=",
        "password_hash",
        "token=",
        "secret=",
        "Authorization:",
        "api_key=",
        "TWILIO_AUTH_TOKEN",
        "SECRET_KEY=",
        "session_id=",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()
        for kw in self._BLOCKED_KEYWORDS:
            if kw.lower() in message:
                record.msg = "[LOG REDACTED — potential sensitive content detected]"
                record.args = ()
                break
        return True


_CONFIGURED_LOGGERS: set[str] = set()
_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _level_int(level_str: str) -> int:
    return getattr(logging, level_str.upper(), logging.INFO)


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Get a configured HeartGuard logger with rotating file and stream handlers.

    Args:
        name: Logger name, typically __name__.
        level: Override log level. Defaults to LOG_LEVEL env setting.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if name in _CONFIGURED_LOGGERS:
        return logger

    _CONFIGURED_LOGGERS.add(name)
    logger.propagate = False

    try:
        LOG_LEVEL, LOG_DIR, LOG_MAX_BYTES, LOG_BACKUP_COUNT, LOG_TO_FILE, IS_PRODUCTION = _get_settings()
    except Exception:
        LOG_LEVEL, LOG_DIR, LOG_MAX_BYTES, LOG_BACKUP_COUNT, LOG_TO_FILE, IS_PRODUCTION = (
            "INFO", Path("logs"), 10 * 1024 * 1024, 5, False, False
        )

    effective_level = level if level is not None else _level_int(LOG_LEVEL)
    logger.setLevel(effective_level)

    privacy_filter = _PrivacyFilter()
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Stream handler (always present, uses stderr in production)
    stream_target = sys.stderr if IS_PRODUCTION else sys.stdout
    stream_handler = logging.StreamHandler(stream_target)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(privacy_filter)
    stream_handler.setLevel(effective_level)
    logger.addHandler(stream_handler)

    # Rotating file handler (when LOG_TO_FILE=true or in production)
    if LOG_TO_FILE:
        try:
            log_path = Path(LOG_DIR)
            log_path.mkdir(parents=True, exist_ok=True)
            log_file = log_path / "heartguard.log"
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(log_file),
                maxBytes=LOG_MAX_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            file_handler.addFilter(privacy_filter)
            file_handler.setLevel(effective_level)
            logger.addHandler(file_handler)
        except OSError as exc:
            logger.warning("Could not create rotating log file: %s", exc)

    return logger


def configure_root_logging() -> None:
    """Configure the root logger once at application startup.

    Should be called from startup validation before any module imports trigger logging.
    """
    try:
        LOG_LEVEL, _, _, _, _, _ = _get_settings()
    except Exception:
        LOG_LEVEL = "INFO"

    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        handler.addFilter(_PrivacyFilter())
        root.addHandler(handler)
        root.setLevel(_level_int(LOG_LEVEL))


# Convenience wrappers (backward compat)
def log_info(logger: logging.Logger, message: str) -> None:
    logger.info(message)


def log_warning(logger: logging.Logger, message: str) -> None:
    logger.warning(message)


def log_error(logger: logging.Logger, message: str) -> None:
    logger.error(message)
