# HeartGuard Privacy Documentation

**Document Version:** 1.0.0  
**Phase:** 15 (Security, Privacy, Audit Logging & Compliance)  
**System Status:** Academic & Research Healthcare Demonstration Prototype

---

## 1. Overview

HeartGuard processes physiological and lifestyle self-reported metrics to calculate cardiovascular risk likelihoods. This document describes the privacy principles, data collection practices, and privacy controls implemented in the platform.

---

## 2. Data Minimization Principles

HeartGuard adheres to strict data minimization — only collecting data necessary for cardiovascular risk assessment:

### What Data IS Collected

| Data Type | Purpose | Storage Location |
|-----------|---------|------------------|
| **User Identity** | Account management, authentication | `data/auth/heartguard_auth.db` |
| **Clinical Metrics** (13 parameters) | Risk calculation | `data/assessments/assessments.db` |
| **Lifestyle Narrative** | NLP behavioral analysis | Processed in memory; categorical indicators stored |
| **Assessment Results** | Risk scores, categories, SHAP explanations | `data/assessments/assessments.db` |
| **AI Recommendations** | Behavioral guidance | `data/assessments/recommendations.db` |
| **Clinician Reviews** | Professional observations | `data/assessments/reviews.db` |
| **Audit Metadata** | Security event tracking | `data/security/audit.db` |

### Clinical Parameters Collected
13 UCI Cleveland features:
- Age, sex, chest pain type
- Resting blood pressure, serum cholesterol
- Fasting blood sugar > 120 mg/dl
- Resting electrocardiographic results
- Maximum heart rate achieved
- Exercise-induced angina
- ST depression induced by exercise
- Slope of peak exercise ST segment
- Number of major fluoroscopy-colored vessels
- Thalassemia type

---

## 3. What Data is NOT Collected

| Data Type | Reason for Exclusion |
|-----------|---------------------|
| **Passwords** | Hashed immediately; plaintext never stored |
| **Password Hashes in Logs** | Stripped from all user dictionaries and logs |
| **Raw Clinical Vectors in Audit Logs** | Only metadata logged; no health values |
| **Lifestyle Narrative in Persistent Logs** | Processed in memory; never written to audit trail |
| **Raw Lifestyle Text in SMS** | Only categorical indicators sent |
| **Internal Auth Tokens** | Session tokens never persisted to database |
| **Third-Party PII** | Only user's own data collected |
| **Biometric Data** | Not collected |
| **Location Data** | Not collected |
| **Device Fingerprints** | Not collected |

---

## 4. Access Control

### Patient Data Isolation
- Assessment queries scoped to authenticated `user_id`
- Patients can ONLY access their own assessments, recommendations, and reports
- IDOR attempts detected, blocked, and logged via `SecurityLogger.log_idor_attempt()`

### Role-Based Access

| Role | Access Scope |
|------|-------------|
| `PATIENT` | Own data only |
| `REVIEWER` | All patient data (clinical oversight) |
| `ADMIN` | Full system access (user management, audit logs) |

### Server-Side Enforcement
- `AuthorizationService.verify_assessment_access()` checks ownership before data retrieval
- `verify_report_access()` verifies user ownership or reviewer/admin role
- All enforcement is server-side — UI hiding alone is NOT relied upon

---

## 5. Data Storage

### Database Architecture
Separate isolated SQLite databases prevent cross-domain data leakage:

| Database | Purpose | Location |
|----------|---------|----------|
| `heartguard_auth.db` | User accounts, credentials | `data/auth/` |
| `assessments.db` | Risk assessments, clinical data | `data/assessments/` |
| `recommendations.db` | AI-generated guidance | `data/assessments/` |
| `reviews.db` | Clinician observations | `data/assessments/` |
| `audit.db` | Security event log | `data/security/` |
| `alerts.db` | Emergency notification history | `data/alerts/` |

### Storage Security
- **Parameterized queries** — 100% SQL injection prevention
- **No encryption at rest** — relies on OS file permissions
- **SQLite timeouts** — 10-second timeout on all connections
- **Busy timeout** — 5-second busy timeout for concurrent access

---

## 6. Data Retention

| Data Category | Retention Window | Purge Trigger |
|---------------|------------------|---------------|
| User Credentials | Active account duration | Account deactivation |
| Risk Assessments | Active account duration | User data deletion request |
| AI Recommendations | Active account duration | User data deletion request |
| Clinician Reviews | Audit lifecycle | Academic evaluation completion |
| Audit Trail | 90 days rolling | Automated archiving |
| Generated Reports | 30 days (configurable) | Automated cleanup |
| Temporary Files | 24 hours | Automated cleanup |

### Configuration
- `REPORT_RETENTION_DAYS`: Default 30 days (`config/settings.py:124`)
- `TEMP_FILE_RETENTION_HOURS`: Default 24 hours (`config/settings.py:125`)
- `MAX_REPORTS_PER_USER`: Default 100 reports (`config/settings.py:126`)

---

## 7. Logging Privacy

### Privacy Filter (`src/security/audit_logger.py:119-126`)
Before writing to audit log, detail text is sanitized:
- Passwords: `password:***` → `password:[REDACTED]`
- Tokens: `token:***` → `token:[REDACTED]`
- API Keys: `api_key:***` → `api_key:[REDACTED]`
- Bearer tokens: `bearer ***` → `bearer:[REDACTED]`
- Detail text truncated to 500 characters

### IP Address Pseudonymization (`src/security/audit_logger.py:29-34`)
- IP addresses hashed with SHA-256 and static salt
- Only 16-character hash prefix stored
- Original IP never written to audit log

### What is Never Logged
- Plaintext passwords or password hashes
- Auth tokens or session tokens
- Raw clinical input vectors
- Detailed patient health answers
- Private clinician notes
- Lifestyle narrative text
- API keys or secret tokens

---

## 8. Patient Data Isolation (IDOR Prevention)

### Assessment Access Control (`src/security/authorization_service.py:37-76`)
1. Patient requests assessment → server verifies `assessment.user_id == request.user_id`
2. If mismatch → IDOR attempt logged via `SecurityLogger.log_idor_attempt()`
3. Access denied with `BLOCKED` status

### Report Access Control (`src/security/file_security.py:97-133`)
1. Patient requests report → server checks filename contains `user_{user_id}`
2. Fallback: checks if report matches any of user's assessment IDs
3. If no match → IDOR attempt logged and access denied

### Logging of IDOR Attempts
- Actor ID, actor role, resource type, resource ID, owner ID all recorded
- Severity: HIGH
- Category: AUTHORIZATION

---

## 9. Export Capabilities (GDPR Art. 15)

### Personal Data Export (`src/security/privacy.py:92-170`)
Patients can download their complete record via `export_user_data()`:

**Exported Data:**
- User profile (user_id, username, masked email, name, role, created_at)
- All risk assessments (up to 100 most recent)
- All AI recommendations (up to 100 most recent)

**Export Invariants:**
- NEVER includes password_hash, session tokens, or internal credentials
- NEVER includes other patients' records
- STRICTLY personal data only

**Export Format:**
- Structured JSON package
- Includes prototype notice and compliance statement
- Email masked in export (`j***e@example.com`)

### Right to Erasure (GDPR Art. 17)
- Account deactivation available
- Immediately revokes login capability
- Disconnects active sessions

---

## 10. Audit Trail

### Security Events Tracked
- Authentication: login success/failure, logout, registration, session expiration
- Authorization: access denied, IDOR attempts, privilege escalation attempts
- Data access: assessment created/viewed/deleted, recommendations generated
- Reports: generated, downloaded, file upload rejected
- System: rate limit exceeded, input validation failures

### Audit Log Structure
| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 UTC timestamp |
| `event_type` | Specific event identifier |
| `user_id` | Authenticated user (None for unauthenticated) |
| `role` | User role at time of event |
| `status` | SUCCESS, FAILURE, BLOCKED, DENIED |
| `detail` | Sanitized description (max 500 chars) |
| `resource_type` | Target resource type |
| `resource_id` | Target resource identifier |
| `category` | Broad event category |
| `severity` | INFO, WARNING, HIGH, CRITICAL |
| `ip_hash` | Privacy-safe hashed IP address |

### Audit Log Integrity
- Append-only SQLite database
- Indexed on timestamp, user_id, event_type, category, severity
- Failed writes logged but do not expose database errors to users

---

## 11. LLM & Third-Party Privacy

### PII Redaction Before AI Processing (`src/security/privacy.py:77-84`)
Before sending text to external LLMs:
- Emails → `[EMAIL_REDACTED]`
- Phone numbers → `[PHONE_REDACTED]`
- Government IDs → `[GOV_ID_REDACTED]`
- Credit card numbers → `[CARD_REDACTED]`

### Data Sent to LLMs
- Only aggregated risk levels
- General lifestyle habit categories
- No names, emails, phone numbers, addresses

---

## 12. Compliance Statement

> HeartGuard is an academic and research prototype developed for educational, demonstration, and evaluation purposes. Security and privacy controls (RBAC, IDOR protection, audit logging, data minimization, session protection) are implemented as best-practice engineering standards for research systems. It is NOT a certified medical device and does not provide clinical diagnosis or prescribe medical treatments.
