"""User repository for HeartGuard authentication (Phase 9 & Phase 15).

Data-access layer for the users table. All queries use parameterized
statements — no string concatenation with user input is ever performed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import List, Optional

from config.settings import AUTH_DB_PATH
from src.auth.models import User, init_auth_db
from src.security.audit_logger import log_event
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _get_connection(db_path: Path | str = AUTH_DB_PATH) -> sqlite3.Connection:
    """Return a thread-safe SQLite connection with row factory set."""
    target = Path(db_path or AUTH_DB_PATH)
    init_auth_db(target)
    conn = sqlite3.connect(str(target), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_user(row: sqlite3.Row) -> User:
    """Convert a sqlite3.Row to a User dataclass."""
    return User(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        password_hash=row["password_hash"],
        role=row["role"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------------------------------------------------------------------------
# Module-level functions (Backward Compatibility)
# ---------------------------------------------------------------------------


def create_user(
    name: str,
    email: str,
    password_hash: str,
    role: str = "PATIENT",
    db_path: Path | str = AUTH_DB_PATH,
) -> User:
    """Insert a new user record."""
    target = Path(db_path or AUTH_DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    sql = (
        "INSERT INTO users (name, email, password_hash, role, is_active, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 1, ?, ?)"
    )
    try:
        with _get_connection(target) as conn:
            cursor = conn.execute(sql, (name, email.lower().strip(), password_hash, role.upper().strip(), now, now))
            conn.commit()
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Email address is already registered.")

    logger.info("User created: id=%s role=%s", user_id, role)
    return User(
        id=user_id,
        name=name,
        email=email.lower().strip(),
        password_hash=password_hash,
        role=role.upper().strip(),
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def deactivate_user(user_id: int, db_path: Path | str = AUTH_DB_PATH) -> bool:
    """Deactivate a user account (soft delete)."""
    target = Path(db_path or AUTH_DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    sql = "UPDATE users SET is_active=0, updated_at=? WHERE id=?"
    with _get_connection(target) as conn:
        cursor = conn.execute(sql, (now, user_id))
        conn.commit()
    updated = cursor.rowcount > 0
    if updated:
        logger.info("User deactivated: id=%s", user_id)
    return updated


def find_by_email(email: str, db_path: Path | str = AUTH_DB_PATH) -> Optional[User]:
    """Find an active user by normalised lowercase email."""
    target = Path(db_path or AUTH_DB_PATH)
    sql = "SELECT * FROM users WHERE email=? AND is_active=1 LIMIT 1"
    with _get_connection(target) as conn:
        row = conn.execute(sql, (email.lower().strip(),)).fetchone()
    return _row_to_user(row) if row else None


def find_by_id(user_id: int, db_path: Path | str = AUTH_DB_PATH) -> Optional[User]:
    """Find a user by primary key."""
    target = Path(db_path or AUTH_DB_PATH)
    sql = "SELECT * FROM users WHERE id=? LIMIT 1"
    with _get_connection(target) as conn:
        row = conn.execute(sql, (user_id,)).fetchone()
    return _row_to_user(row) if row else None


def list_users(db_path: Path | str = AUTH_DB_PATH) -> List[User]:
    """List all user accounts."""
    target = Path(db_path or AUTH_DB_PATH)
    sql = "SELECT * FROM users ORDER BY created_at DESC"
    with _get_connection(target) as conn:
        rows = conn.execute(sql).fetchall()
    return [_row_to_user(r) for r in rows]


def count_users_by_role(db_path: Path | str = AUTH_DB_PATH) -> dict:
    """Return user counts grouped by role."""
    target = Path(db_path or AUTH_DB_PATH)
    sql = "SELECT role, COUNT(*) as cnt FROM users WHERE is_active=1 GROUP BY role"
    with _get_connection(target) as conn:
        rows = conn.execute(sql).fetchall()
    return {row["role"]: row["cnt"] for row in rows}


# ---------------------------------------------------------------------------
# UserRepository Class Interface
# ---------------------------------------------------------------------------


class UserRepository:
    """Class interface for user account queries and modifications."""

    create_user = staticmethod(create_user)
    find_by_id = staticmethod(find_by_id)
    get_by_id = staticmethod(find_by_id)
    find_by_email = staticmethod(find_by_email)
    get_by_email = staticmethod(find_by_email)
    list_users = staticmethod(list_users)
    deactivate_user = staticmethod(deactivate_user)
    count_users_by_role = staticmethod(count_users_by_role)

    @classmethod
    def update_user_role(
        cls,
        user_id: int,
        new_role: str,
        actor_id: Optional[int] = None,
        db_path: Path | str = AUTH_DB_PATH,
    ) -> bool:
        """Update a user's role (ADMIN action only)."""
        valid_roles = {"PATIENT", "REVIEWER", "ADMIN"}
        role_clean = new_role.upper().strip()
        if role_clean not in valid_roles:
            raise ValueError(f"Invalid role '{new_role}'. Allowed: {valid_roles}")

        target = Path(db_path)
        now = datetime.now(timezone.utc).isoformat()
        sql = "UPDATE users SET role=?, updated_at=? WHERE id=?"
        with _get_connection(target) as conn:
            cursor = conn.execute(sql, (role_clean, now, user_id))
            conn.commit()

        success = cursor.rowcount > 0
        if success:
            logger.info("User role updated: user_id=%s new_role=%s by actor=%s", user_id, role_clean, actor_id)
            log_event(
                event_type="role_changed",
                status="SUCCESS",
                user_id=actor_id,
                role="ADMIN",
                detail=f"Changed user {user_id} role to {role_clean}",
                resource_type="user",
                resource_id=str(user_id),
                category="ADMIN_ACTION",
                severity="INFO",
            )
        return success

    @classmethod
    def toggle_user_active(
        cls,
        user_id: int,
        is_active: bool,
        actor_id: Optional[int] = None,
        db_path: Path | str = AUTH_DB_PATH,
    ) -> bool:
        """Activate or deactivate a user account."""
        target = Path(db_path)
        now = datetime.now(timezone.utc).isoformat()
        sql = "UPDATE users SET is_active=?, updated_at=? WHERE id=?"
        with _get_connection(target) as conn:
            cursor = conn.execute(sql, (1 if is_active else 0, now, user_id))
            conn.commit()

        success = cursor.rowcount > 0
        if success:
            action_desc = "activated" if is_active else "deactivated"
            logger.info("User %s: user_id=%s by actor=%s", action_desc, user_id, actor_id)
            log_event(
                event_type="user_status_changed",
                status="SUCCESS",
                user_id=actor_id,
                role="ADMIN",
                detail=f"User {user_id} was {action_desc}",
                resource_type="user",
                resource_id=str(user_id),
                category="ADMIN_ACTION",
                severity="INFO",
            )
        return success

    @classmethod
    def update_profile(
        cls,
        user_id: int,
        name: str,
        db_path: Path | str = AUTH_DB_PATH,
    ) -> bool:
        """Update permitted profile fields (display name only). Prevents mass-assignment."""
        from src.security.input_validator import validate_name
        clean_name = validate_name(name)

        target = Path(db_path)
        now = datetime.now(timezone.utc).isoformat()
        sql = "UPDATE users SET name=?, updated_at=? WHERE id=?"
        with _get_connection(target) as conn:
            cursor = conn.execute(sql, (clean_name, now, user_id))
            conn.commit()

        return cursor.rowcount > 0
