"""User model definition for HeartGuard (Phase 9).

Defines the User dataclass and the schema used for the auth SQLite database.
Passwords are NEVER stored here as plaintext; only bcrypt hashes are persisted.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import AUTH_DB_PATH


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class User:
    """Represents a HeartGuard user account.

    Attributes:
        id: Auto-incremented primary key (None before first save).
        name: Display name (not used as auth key).
        email: Normalised lowercase email (auth key).
        password_hash: bcrypt hash — never the plaintext password.
        role: Either 'PATIENT' or 'ADMIN'.
        is_active: Whether the account may log in.
        created_at: UTC creation timestamp (ISO-8601 string).
        updated_at: UTC last-update timestamp (ISO-8601 string).
    """

    id: Optional[int]
    name: str
    email: str
    password_hash: str
    role: str
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def user_id(self) -> Optional[int]:
        return self.id

    @property
    def username(self) -> str:
        return self.email

    def to_safe_dict(self) -> dict:
        """Return a safe representation — omits password_hash.

        This is the ONLY dict representation that should ever leave this layer.
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

_CREATE_USERS_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    password_hash TEXT  NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'PATIENT',
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
)
"""


def init_auth_db(db_path: Path | str = AUTH_DB_PATH) -> None:
    """Initialise the authentication database and create tables if needed.

    Args:
        db_path: Path to the SQLite database file. Created automatically.
    """
    target = Path(db_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(target)) as conn:
        conn.execute(_CREATE_USERS_SQL)
        conn.commit()
