# HeartGuard — STRIDE Threat Model

**Document Version:** 1.0.0  
**Phase:** 15 (Security, Privacy, Audit Logging & Compliance)  
**System Classification:** Academic & Research Healthcare Demonstration Prototype  

---

## 1. System Scope & Boundary

HeartGuard is a multimodal AI system for early heart disease risk assessment. It ingests:
1. Tabular clinical measurements (13 UCI Cleveland parameters)
2. Free-text lifestyle descriptions processed by an NLP lexicon
3. Historical assessment records and SHAP local explanations

The system evaluates risk through a dual-channel weighting engine (70% Clinical ML, 30% Lifestyle NLP) and generates deterministic, non-diagnostic behavioral recommendations and emergency notifications.

```
                    [ External Browser Client ]
                               │ (HTTPS / TLS 1.3)
                    ┌──────────▼──────────┐
                    │   Reverse Proxy /   │
                    │  Security Headers   │
                    └──────────┬──────────┘
                               │
               ┌───────────────┴───────────────┐
               │    Streamlit Web Gateway       │
               │  - Session Inactivity Timeout │
               │  - Sliding Window Rate Limit  │
               └───────────────┬───────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ Auth & RBAC  │       │ Multimodal   │       │  Audit &     │
│ Service      │       │ Risk Engine  │       │  Security    │
│ (Bcrypt)     │       │ (Frozen ML)  │       │  Dispatcher  │
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       │                      │                      │
       ▼                      ▼                      ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  Auth DB     │       │ Assessment   │       │  Audit DB    │
│  (users.db)  │       │ History DB   │       │  (audit.db)  │
└──────────────┘       └──────────────┘       └──────────────┘
```

---

## 2. STRIDE Threat Analysis Matrix

| Threat Category | Threat Description | Attacker Objective | System Vulnerability Addressed | Applied Countermeasures | Residual Risk & Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **S** - Spoofing | Identity spoofing via stolen or guessed credentials | Gain unauthorized access to patient health reports | Weak password rules or absence of brute-force limits | Bcrypt salt hashing, minimum 8 characters with letter & number requirements, common password blacklist, 5 attempts/min rate limiter | LOW — Addressed |
| **S** - Spoofing | Session fixation or hijacked token | Impersonate an active doctor or patient session | Reusing previous session token across state transitions | Unique cryptographic token generation (`secrets.token_hex`), complete state wipe on logout/rotation, 30-min inactivity timeout | LOW — Addressed |
| **T** - Tampering | Client manipulation of risk scores | Artificially reduce or escalate calculated cardiac risk | Accepting risk scores from frontend HTTP parameters | Risk scores strictly calculated server-side in `MultimodalRiskEngine`. Zero client inputs accepted for scores. Parameterized SQLite queries | MINIMAL — Verified |
| **T** - Tampering | Local File Inclusion / Path Traversal | Overwrite application files or read system configs | Unvalidated filenames in PDF report generator | `resolve_safe_path()` directory containment checks; strict alphanumeric sanitation; rejection of `..` / null bytes | LOW — Addressed |
| **R** - Repudiation | Denying clinical action or data export | Disclaim having changed user role or downloaded reports | Absence of structured audit trails | Append-only SQLite `audit_log` with indexed timestamps, actor roles, resource IDs, and hashed IP addresses | LOW — Addressed |
| **I** - Information Disclosure | Insecure Direct Object Reference (IDOR) | Access another patient's medical records or recommendations | Guessing sequential or UUID assessment IDs | Strict server-side ownership checks (`AuthorizationService.verify_assessment_access`). Non-owners rejected and logged | LOW — Addressed |
| **I** - Information Disclosure | Sensitive data leakage in audit records | Harvest clinical vectors or credentials from log files | Excessive logging of raw requests | Dedicated data sanitizers redact passwords, tokens, API keys, and clinical values before `INSERT` | MINIMAL — Verified |
| **I** - Information Disclosure | Diagnostic claim or liability risk | System falsely claims to diagnose heart attack or prescribes drug | AI generating unregulated medical assertions | Rule engine safety invariant (`validate_recommendation`) blocking prescription terms, medical diagnoses, and cures | LOW — Addressed |
| **D** - Denial of Service | Pipeline exhaustion via heavy SHAP computations | Exhaust server CPU/memory with concurrent assessments | Unbounded model execution requests | Thread-safe sliding-window rate limiters per IP/session; max 10 assessments/minute; bounded upload sizes (5MB) | MEDIUM — Addressed |
| **E** - Elevation of Privilege | Patient accessing Doctor or Admin portals | Approve assessments, change user roles, view all patients | Frontend-only route masking | Mandatory server-side authorization check `require_role()` on every page; server-side role check on repository writes | LOW — Addressed |

---

## 3. Threat Mitigation Summary & Defense-in-Depth

1. **Layer 1: Edge & Network**
   - Security headers enforced: CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff.
   - Sliding window rate limiting on all sensitive endpoints.
2. **Layer 2: Identity & Session**
   - Role hierarchy (`PATIENT` < `REVIEWER` < `ADMIN`).
   - Inactivity session invalidation after 30 minutes.
   - Bcrypt hashing with timing attack mitigation on user lookup.
3. **Layer 3: Data & Object Access (IDOR)**
   - Ownership validation at repository and service layer.
   - Separate isolated databases for authentication, assessment history, reviews, and audit logs.
4. **Layer 4: AI & Recommendation Safety**
   - Static non-diagnostic blocklist (`MEDICATION_TERMS`, `UNSUPPORTED_CLAIMS`).
   - Mandatory informational acknowledgement checkbox before assessment calculation.
