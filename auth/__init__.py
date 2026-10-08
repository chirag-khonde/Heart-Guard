"""HeartGuard Authentication Package (Phase 9).

Provides user registration, login, session management, and role-based
authorization for the HeartGuard application.

Public API:
    - auth_service: register_user, authenticate_user, logout_user
    - authorization: require_authentication, require_role, is_admin, is_patient
    - session_manager: create_session, get_current_user, is_authenticated, clear_session
    - password_service: hash_password, verify_password
"""
