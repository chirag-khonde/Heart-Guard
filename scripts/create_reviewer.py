"""Reviewer account creation script for HeartGuard (Phase 11).

Reads credentials from environment variables ONLY — never from command-line
arguments (which would expose them in shell history and process lists).

Usage:
    Set environment variables in .env or export them:
        REVIEWER_EMAIL=reviewer@heartguard.local
        REVIEWER_PASSWORD=<strong-password>
        REVIEWER_NAME=Dr. Jane Smith   (optional, defaults to 'HeartGuard Reviewer')

    Then run:
        python scripts/create_reviewer.py

SECURITY:
    - Never pass credentials as command-line arguments.
    - Never hard-code credentials in this script.
    - Set a strong password (minimum 8 characters).
    - Rotate the password after first use in production.
    - REVIEWER role accounts can view AI assessments and submit professional
      observations; they cannot modify AI-generated risk scores or SHAP values.
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv()

from src.auth.auth_service import create_reviewer_user  # noqa: E402


def main() -> None:
    """Read reviewer credentials from env and create the REVIEWER account."""
    reviewer_email = os.getenv("REVIEWER_EMAIL", "").strip()
    reviewer_password = os.getenv("REVIEWER_PASSWORD", "").strip()
    reviewer_name = os.getenv("REVIEWER_NAME", "HeartGuard Reviewer").strip()

    if not reviewer_email:
        print("ERROR: REVIEWER_EMAIL environment variable is not set.")
        print("Set it in your .env file or export it before running this script.")
        sys.exit(1)

    if not reviewer_password:
        print("ERROR: REVIEWER_PASSWORD environment variable is not set.")
        print("Set it in your .env file or export it before running this script.")
        sys.exit(1)

    try:
        user = create_reviewer_user(
            name=reviewer_name,
            email=reviewer_email,
            password=reviewer_password,
        )
        print("Reviewer account created successfully.")
        print(f"  ID:    {user['id']}")
        print(f"  Name:  {user['name']}")
        print(f"  Email: {user['email']}")
        print(f"  Role:  {user['role']}")
        print()
        print("IMPORTANT: Clear REVIEWER_PASSWORD from your environment after setup.")
        print("NOTE: This account has read-only access to AI assessment results.")
        print("      It cannot modify clinical risk scores or AI-generated data.")
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: Reviewer creation failed — {type(exc).__name__}")
        sys.exit(1)


if __name__ == "__main__":
    main()
