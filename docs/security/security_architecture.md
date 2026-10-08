# HeartGuard — Security Architecture

**Document Version:** 1.0.0  
**Phase:** 15 (Security, Privacy, Audit Logging & Compliance)  
**Classification:** Academic & Research Healthcare Demonstration Prototype  

---

## 1. Architectural Philosophy

HeartGuard implements **Defense-in-Depth** and the **Principle of Least Privilege**. Recognizing that cardiovascular data and AI risk predictions carry significant privacy and ethical considerations, the platform enforces strict boundaries across identity, authorization, transport, data storage, and model execution.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION TIER                               │
│  - Streamlit Web Interface                                             │
│  - Mandatory Informational Acknowledgement Checkbox                    │
│  - Output HTML Sanitization & Sensitive Metric Masking                 │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                    SECURITY & ENFORCEMENT TIER                         │
│  - AuthorizationService (Server-Side IDOR & Role Enforcement)          │
│  - InMemoryRateLimiter (Thread-Safe Sliding Window Token Bucket)       │
│  - InputValidator (Path Traversal, Type Coercion, Format Verification) │
│  - SessionManager (30-minute Timeout, Session Token Rotation)          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                      APPLICATION & DOMAIN SERVICES                     │
│  - AuthService & PasswordService (Bcrypt Salted Hashing)               │
│  - MultimodalRiskEngine (Dual-channel 70/30 Risk Computation)          │
│  - RecommendationEngine & Safe Validator (No Prescription Rule)        │
│  - AlertManager (Idempotent Notification Pipeline)                     │
│  - HistoryService (Assessment Persistence & Trend Analytics)           │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                       PERSISTENCE & AUDIT TIER                         │
│  - Parameterized SQLite Isolation (users.db, history.db, audit.db)     │
│  - SecurityLogger & AuditLogger (Append-Only, Redacted, Indexed)       │
│  - Safe File Resolution (Sandboxed Report Export Directory)            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Security Subsystems

### 2.1 Identity and Access Management (IAM)
- **Role-Based Access Control (RBAC):** Three distinct roles:
  - `PATIENT`: Can initiate personal assessments, view own trends, and download own PDF reports.
  - `REVIEWER`: Clinical oversight privilege to review patient assessments and record clinician observations; cannot alter AI-calculated risk scores.
  - `ADMIN`: Full oversight over system health, role assignments, user status, and the immutable audit log viewer.
- **Password Security:**
  - Salted Bcrypt hashing with standard 12 rounds.
  - Policy enforcement: 8 to 128 characters, required mix of letters and digits, rejection of common weak passwords.
  - Zero plaintext passwords in memory logs, databases, or UI state.
- **Timing Attack Defense:**
  - Constant-time password verification using dummy hash evaluation when an unknown email is supplied.

### 2.2 Server-Side Authorization & IDOR Defense
- Every request to access an assessment (`/history`, `/review`, or `/dashboard`) is verified server-side through `AuthorizationService.verify_assessment_access(user_id, role, assessment_id)`.
- Client-supplied identifier spoofing is detected immediately, rejected, and dispatched to `SecurityLogger.log_idor_attempt()` with actor ID and owner ID recorded.

### 2.3 Session Hardening & Lifecycle
- Every login generates a high-entropy session token (`secrets.token_hex(24)`).
- Session fixation is thwarted by purging all previous session tokens and sensitive data on authentication state transitions.
- Automatic inactivity expiration invalidates the session after **30 minutes** of idle time.

### 2.4 Rate Limiting & Denial of Service Protection
- Sliding-window thread-safe in-memory rate limiting (`InMemoryRateLimiter`).
- Protected actions:
  - Login endpoint: 5 attempts / 60 seconds
  - Registration: 3 attempts / 300 seconds
  - Assessment calculation: 10 requests / 60 seconds
  - Report export: 10 requests / 60 seconds
  - Password reset: 3 attempts / 300 seconds

### 2.5 Input Validation & Output Encoding
- Strict boundary validation on all 13 clinical features.
- Lifestyle text length limits (10 to 1,000 characters) to prevent memory allocation attacks.
- Display text sanitization via `html.escape` and script-tag stripping.
- Path traversal defense via `resolve_safe_path()` ensuring all file operations remain strictly inside designated sandboxes (`data/reports/`).

### 2.6 Data Minimization & Privacy
- Zero clinical input vectors stored in audit logs.
- Sensitive identifiers (email, phone, name) are masked in administrative and public interfaces (`j***e@domain.com`).
- GDPR Art. 15 compliant self-service personal data package export (`export_user_data()`).
- Automated repository scanner detecting committed API tokens or private keys (`scan_repo_secrets()`).

### 2.7 AI Recommendation Guardrails
- AI recommendations undergo static safety verification via `validate_recommendation()`.
- Explicit blocklist rejects any text containing prescription advice, diagnostic affirmations ("You have heart disease"), or unsupported cure claims.
- The model weights and inference pipelines are frozen and verified through cryptographic checksums.
