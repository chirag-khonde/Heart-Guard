"""Password hashing and verification service for HeartGuard (Phase 9).

Uses bcrypt for all password operations. Plaintext passwords NEVER leave
this module — they are hashed immediately and the hash is what is stored.

Security guarantees:
  - Passwords are never logged, printed, or returned to callers.
  - Work factor is bcrypt default (12 rounds).
  - Verification uses constant-time comparison (bcrypt.checkpw).
"""

from __future__ import annotations

import bcrypt

from src.utils.logger import get_logger

logger = get_logger(__name__)

# bcrypt work factor (cost parameter). Do not lower below 10.
_BCRYPT_ROUNDS = 12


def hash_password(plaintext_password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        plaintext_password: The user's plaintext password.

    Returns:
        bcrypt hash string (safe to store in the database).

    Raises:
        ValueError: If the password is empty.
    """
    if not plaintext_password:
        raise ValueError("Password must not be empty.")

    encoded = plaintext_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed: bytes = bcrypt.hashpw(encoded, salt)
    # Do NOT log the hash or the plaintext
    return hashed.decode("utf-8")


def verify_password(plaintext_password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against its stored bcrypt hash.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        plaintext_password: Password provided at login.
        stored_hash: bcrypt hash retrieved from the database.

    Returns:
        True if the password matches, False otherwise.
    """
    if not plaintext_password or not stored_hash:
        return False

    try:
        encoded_plain = plaintext_password.encode("utf-8")
        encoded_hash = stored_hash.encode("utf-8")
        return bcrypt.checkpw(encoded_plain, encoded_hash)
    except Exception:
        # Log the failure without revealing any credential information
        logger.warning("Password verification encountered an unexpected error.")
        return False
