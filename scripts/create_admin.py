"""Admin user creation script for HeartGuard (Phase 9).

Reads credentials from environment variables ONLY — never from command-line
arguments (which would expose them in shell history and process lists).

Usage:
    Set environment variables in .env or export them:
        ADMIN_EMAIL=admin@heartguard.local
        ADMIN_PASSWORD=<strong-password>

    Then run:
        python scripts/create_admin.py

SECURITY:
    - Never pass credentials as command-line arguments.
    - Never hard-code credentials in this script.
    - Set a strong password (minimum 8 characters).
    - Rotate the password after first use in production.
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv()

from src.auth.auth_service import create_admin_user


def main() -> None:
    """Read admin credentials from env and create the admin account."""
    admin_email = os.getenv("ADMIN_EMAIL", "").strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
    admin_name = os.getenv("ADMIN_NAME", "HeartGuard Admin").strip()

    if not admin_email:
        print("ERROR: ADMIN_EMAIL environment variable is not set.")
        print("Set it in your .env file or export it before running this script.")
        sys.exit(1)

    if not admin_password:
        print("ERROR: ADMIN_PASSWORD environment variable is not set.")
        print("Set it in your .env file or export it before running this script.")
        sys.exit(1)

    try:
        user = create_admin_user(
            name=admin_name,
            email=admin_email,
            password=admin_password,
        )
        # Print only non-sensitive confirmation
        print(f"Admin account created successfully.")
        print(f"  ID:    {user['id']}")
        print(f"  Email: {user['email']}")
        print(f"  Role:  {user['role']}")
        print()
        print("IMPORTANT: Clear ADMIN_PASSWORD from your environment after setup.")
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: Admin creation failed — {type(exc).__name__}")
        sys.exit(1)


if __name__ == "__main__":
    main()
