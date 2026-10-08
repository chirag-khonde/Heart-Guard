# HeartGuard Security Documentation

**Document Version:** 2.0.0  
**Phase:** 15 (Security, Privacy, Audit Logging & Compliance)  
**System Status:** Academic & Research Healthcare Demonstration Prototype

---

## 1. Overview

HeartGuard implements defense-in-depth security across authentication, authorization, session management, input validation, audit logging, and file security. This document describes the security controls implemented in the codebase.

---

## 2. Authentication

### Password Hashing
- **Algorithm:** Bcrypt with 12 salt rounds (`src/auth/password_service.py:21`)
- **Plaintext passwords never stored** — hashed immediately upon receipt
- **Constant-time verification** via `bcrypt.checkpw()` prevents timing attacks
- **Dummy hash evaluation** when email not found to prevent user enumeration (`src/auth/auth_service.py:144`)

### Password Policy (`config/security.py:55-71`)
- Minimum 8 characters, maximum 128 characters
- Requires at least one letter and one digit
- Blacklist of common weak passwords (e.g., "password", "12345678", "heartguard")
- Enforced via `validate_password_strength()` in `src/security/input_validator.py:106-125`

### Registration
- Only `PATIENT` accounts can self-register via web UI
- Admin accounts created via CLI script reading environment variables
- Reviewer accounts created programmatically

### Login
- Generic error messages ("Invalid email or password") — never reveals whether email exists
- Rate limiting: 5 attempts per 60 seconds (`config/security.py:21`)
- Failed attempt tracking with cooldown lockout

---

## 3. Authorization

### Role-Based Access Control (RBAC)
Three roles with hierarchical permissions:

| Role | Permissions |
|------|-------------|
| `PATIENT` | Own assessments, own reports, own recommendations |
| `REVIEWER` | Clinical oversight — view all assessments, record clinician notes (cannot alter AI risk scores) |
| `ADMIN` | Full system access — user management, audit logs, role assignments |

### Server-Side Enforcement (`src/auth/authorization.py`)
- `require_authentication()` — stops page rendering if not logged in
- `require_role("ADMIN")` — stops page rendering if wrong role
- `require_reviewer()` — stops page rendering for non-reviewer users
- **All enforcement is server-side** — UI hiding alone is NOT relied upon

### IDOR Prevention (`src/security/authorization_service.py`)
- Assessment access verified via `verify_assessment_access(user_id, role, assessment_id)`
- Patients can only access their own assessments
- Report access verified via `verify_report_access()` in `src/security/file_security.py:97-133`
- IDOR attempts logged via `SecurityLogger.log_idor_attempt()`

---

## 4. Session Security

### Session Management (`src/auth/session_manager.py`)
- **Token generation:** `secrets.token_hex(24)` — 48-character hex token
- **Session fixation prevention:** All previous session state wiped on login
- **Inactivity timeout:** 30 minutes (`config/security.py:12`)
- **Complete state wipe** on logout or timeout
- **Session state keys:** Only stores `user_id`, `name`, `role`, `session_token`, `last_active`

### Cookie Security (`config/security.py:14-16`)
- `SESSION_COOKIE_SECURE = True`
- `SESSION_COOKIE_HTTPONLY = True`
- `SESSION_COOKIE_SAMESITE = "Lax"`

### Sensitive Keys Purged on Logout
- Assessment results, lifestyle results, alert results, patient data, PDF report bytes

---

## 5. Rate Limiting

### Endpoint Rate Limits (`config/security.py:21-29`)

| Action | Limit | Window |
|--------|-------|--------|
| Login | 5 attempts | 60 seconds |
| Registration | 5 attempts | 60 seconds |
| Assessment creation | 10 requests | 60 seconds |
| Report generation | 10 requests | 60 seconds |
| Report download | 15 requests | 60 seconds |
| AI insights | 20 requests | 60 seconds |
| Model evaluation | 3 requests | 60 seconds |

### Implementation
- Thread-safe sliding window algorithm (`src/security/rate_limiter.py:42-84`)
- In-memory storage with fallback for testing
- Rate limit violations logged via `SecurityLogger.log_rate_limit()`

---

## 6. Input Validation

### XSS Prevention (`src/security/input_validator.py`)
- `sanitize_text_for_display()` — removes `<script>` tags, strips HTML, applies `html.escape()`
- `sanitize_sms_content()` — strips control characters and pipe symbols
- Pattern-based detection for script injection and HTML tags

### SQL Injection Prevention
- **100% parameterized queries** across all SQLite operations
- No string concatenation in SQL statements
- Separate isolated databases for auth, history, reviews, and audit

### Path Traversal Prevention (`src/security/file_security.py`)
- `is_safe_path()` — verifies target resolves within base directory
- `resolve_safe_path()` — rejects `..`, leading `/` or `\`
- `sanitize_filename()` — strips null bytes, traversal sequences, illegal characters

### File Upload Security (`config/security.py:34-50`)
- Maximum size: 5 MB
- Allowed extensions: `.pdf`, `.csv`, `.png`, `.jpg`, `.jpeg`
- Magic byte signature validation for PDF, PNG, JPG formats
- MIME type whitelist

### Identifier Validation
- `validate_identifier()` — alphanumeric, dashes, underscores only (max 64 chars)
- `validate_integer_id()` — positive integers only
- `validate_email()` — RFC-5322 regex, max 254 characters
- `validate_json_payload()` — validates JSON structure, optional key whitelist

---

## 7. Audit Logging

### Audit Event Taxonomy (`config/security.py:76-91`)

**Categories:** AUTHENTICATION, AUTHORIZATION, DATA_ACCESS, ADMIN_ACTION, FILE_ACCESS, MODEL_OPERATION, SYSTEM_SECURITY

**Severities:** INFO, WARNING, HIGH, CRITICAL

### Event Types (`src/security/audit_logger.py:69-107`)
- Authentication: login_success, login_failure, logout, registration, password_change, session_expired
- Authorization: access_denied, idor_attempt, privilege_escalation_attempt
- Data: assessment_created, assessment_viewed, assessment_deleted, recommendations_generated
- Reports: report_generated, report_downloaded, file_upload_rejected
- System: rate_limit_exceeded, input_validation_failed, config_error

### Privacy Controls
- **IP addresses hashed** with SHA-256 and salt before storage (`src/security/audit_logger.py:29-34`)
- **Detail text sanitized** — passwords, tokens, API keys, bearer tokens redacted (`src/security/audit_logger.py:119-126`)
- **Detail truncated** to 500 characters
- **Never logs:** passwords, password hashes, auth tokens, raw clinical vectors, lifestyle text

### Storage
- Append-only SQLite database (`data/security/audit.db`)
- Indexed on timestamp, user_id, event_type, category, severity
- Filtered querying with pagination support

---

## 8. Privacy

### Data Minimization
- Only collects data necessary for cardiovascular risk assessment
- Clinical data: 13 UCI Cleveland parameters
- Lifestyle data: free-text processed into categorical indicators
- Audit logs: metadata only — no raw clinical vectors

### Field Masking (`src/security/privacy.py`)
- Email: `j***e@example.com`
- Phone: `+1*****7890`
- Name: `J*** D***`

### LLM Privacy
- Before AI processing, PII stripped via regex patterns:
  - Emails replaced with `[EMAIL_REDACTED]`
  - Phone numbers replaced with `[PHONE_REDACTED]`
  - Government IDs replaced with `[GOV_ID_REDACTED]`
  - Credit card numbers replaced with `[CARD_REDACTED]`

### Patient Data Isolation
- Assessment queries scoped to authenticated `user_id`
- Separate databases prevent cross-domain data leakage
- Report downloads verified against user ownership

---

## 9. Secret Management

### Environment Variables
All sensitive configuration loaded from environment variables (`config/settings.py`):
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- `ADMIN_EMAIL`, `ADMIN_PASSWORD`
- `SECRET_KEY`
- Database paths

### Startup Validation
- `.env.example` template provided for development
- `.env` excluded from version control via `.gitignore`
- Secret key default detection (`config/settings.py:168-172`)

### Repository Scanning
- `scan_repo_secrets()` in `src/security/privacy.py:185-223` scans for:
  - AWS access keys
  - Private key headers
  - Generic secret tokens
  - Hardcoded passwords

---

## 10. Security Headers

Configured in `config/security.py:96-109`:

| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'` |

---

## 11. File Security

### Path Traversal Prevention
- `is_safe_path()` — verifies resolved path stays within base directory
- `resolve_safe_path()` — raises `PermissionError` on traversal attempts
- `sanitize_filename()` — strips null bytes, traversal sequences, illegal characters

### Upload Restrictions (`config/security.py:34-50`)
- Maximum file size: 5 MB
- Allowed extensions: `.pdf`, `.csv`, `.png`, `.jpg`, `.jpeg`
- Magic byte signature validation
- MIME type whitelist

### Report Access Control
- `verify_report_access()` — checks user ownership or reviewer/admin role
- IDOR attempts logged and blocked

---

## 12. Security Limitations

### Known Limitations
1. **No encryption at rest** — SQLite databases stored unencrypted (relies on OS file permissions)
2. **No TLS termination** — application does not handle TLS; requires reverse proxy
3. **In-memory rate limiting** — state lost on server restart; not distributed
4. **No account lockout** — rate limiting only; accounts not locked after N failures
5. **No MFA** — single-factor authentication only
6. **No CSRF tokens** — Streamlit handles CSRF via SameSite cookies
7. **Session storage** — Streamlit session state is server-side but not persistent across restarts
8. **No webhook validation** — external integrations not signed
9. **Prototype status** — not certified for clinical use; security controls are educational

### Residual Risks
- **DoS via heavy computations** — SHAP explanations are CPU-intensive; rate limiting mitigates but does not eliminate
- **Client-side state** — Streamlit reruns may cause race conditions in session state
- **SQLite concurrency** — single-writer database; may underwrite under high load

---

## 13. Compliance Statement

> HeartGuard is an academic and research prototype developed for educational, demonstration, and evaluation purposes. Security and privacy controls (RBAC, IDOR protection, audit logging, data minimization, session protection) are implemented as best-practice engineering standards for research systems. It is NOT a certified medical device and does not provide clinical diagnosis or prescribe medical treatments.
