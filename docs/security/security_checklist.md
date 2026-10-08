# HeartGuard — Security Verification Checklist & Compliance Matrix

**Document Version:** 1.0.0  
**Phase:** 15 (Security, Privacy, Audit Logging & Compliance)  
**Verification Date:** September 2026  
**Status:** ALL VERIFIED (Production-Ready Architecture for Academic Prototype)  

---

## 1. Compliance Statement

> [!IMPORTANT]
> **Academic & Research Healthcare Prototype Status:**  
> HeartGuard is developed as an academic and research prototype demonstrating advanced early heart disease risk prediction with explainable AI. The platform enforces defense-in-depth engineering standards including role-based access control, cryptographic password hashing, IDOR prevention, and tamper-evident audit logging. It is **not** certified as a clinical medical device under FDA/CE-MDR regulations and is not intended for primary clinical diagnosis or emergency triage.

---

## 2. Security Control Verification Matrix

### 2.1 Authentication & Credential Protection
| Control ID | Description | Implementation File | Verification Status |
| :--- | :--- | :--- | :--- |
| **AUTH-01** | Password hashing with Bcrypt (12 rounds) & salt | `src/auth/password_service.py:34-45` | ✅ VERIFIED |
| **AUTH-02** | Zero plaintext passwords stored in DB or logs | `src/auth/user_repository.py:63-75` | ✅ VERIFIED |
| **AUTH-03** | Password complexity: 8-128 chars, mixed letters/digits | `src/security/input_validator.py:108-132` | ✅ VERIFIED |
| **AUTH-04** | Blacklist rejection of common weak passwords | `src/security/input_validator.py:27-46` | ✅ VERIFIED |
| **AUTH-05** | Timing-attack mitigation during email authentication | `src/auth/auth_service.py:140-165` | ✅ VERIFIED |
| **AUTH-06** | Brute-force rate limiting (5 attempts/min cooldown) | `src/security/rate_limiter.py:48-65` | ✅ VERIFIED |

### 2.2 Authorization & Role-Based Access Control (RBAC)
| Control ID | Description | Implementation File | Verification Status |
| :--- | :--- | :--- | :--- |
| **RBAC-01** | Three roles: `PATIENT`, `REVIEWER`, `ADMIN` | `config/settings.py:82-84` | ✅ VERIFIED |
| **RBAC-02** | Mandatory server-side page authorization | `src/auth/authorization.py:42-80` | ✅ VERIFIED |
| **RBAC-03** | Reviewer restriction (cannot alter ML risk scores) | `src/reviews/review_service.py:110-145` | ✅ VERIFIED |
| **RBAC-04** | Admin restriction (only admins can change roles) | `src/auth/user_repository.py:140-165` | ✅ VERIFIED |

### 2.3 IDOR Defense & User Isolation
| Control ID | Description | Implementation File | Verification Status |
| :--- | :--- | :--- | :--- |
| **IDOR-01** | Assessment ownership verification | `src/security/authorization_service.py:35-65` | ✅ VERIFIED |
| **IDOR-02** | Insecure direct object reference attack logging | `src/security/security_logger.py:45-68` | ✅ VERIFIED |
| **IDOR-03** | History database queries scoped to authenticated `user_id` | `src/analytics/history_service.py:90-115` | ✅ VERIFIED |
| **IDOR-04** | Report export downloads restricted to owner/clinician | `src/security/file_security.py:65-95` | ✅ VERIFIED |

### 2.4 Session Security
| Control ID | Description | Implementation File | Verification Status |
| :--- | :--- | :--- | :--- |
| **SESS-01** | Cryptographic session token generation | `src/auth/session_manager.py:48-62` | ✅ VERIFIED |
| **SESS-02** | Session fixation prevention (state wipe on login) | `src/auth/session_manager.py:53-56` | ✅ VERIFIED |
| **SESS-03** | Inactivity timeout after 30 minutes | `src/auth/session_manager.py:75-102` | ✅ VERIFIED |
| **SESS-04** | Complete state wipe on user logout | `src/auth/session_manager.py:120-135` | ✅ VERIFIED |

### 2.5 Input Validation & Output Encoding
| Control ID | Description | Implementation File | Verification Status |
| :--- | :--- | :--- | :--- |
| **VAL-01** | RFC-5322 email regex and normalization | `src/security/input_validator.py:49-75` | ✅ VERIFIED |
| **VAL-02** | Lifestyle text length bounds (10 to 1,000 chars) | `src/security/input_validator.py:135-155` | ✅ VERIFIED |
| **VAL-03** | Display text sanitization (`html.escape` & script strip) | `src/security/input_validator.py:160-185` | ✅ VERIFIED |
| **VAL-04** | SMS content sanitization (control characters stripped) | `src/security/input_validator.py:190-210` | ✅ VERIFIED |
| **VAL-05** | Path traversal prevention (`resolve_safe_path`) | `src/security/file_security.py:28-48` | ✅ VERIFIED |
| **VAL-06** | File upload size limits (5 MB) and magic byte check | `src/security/file_security.py:50-75` | ✅ VERIFIED |

### 2.6 Database & Secret Security
| Control ID | Description | Implementation File | Verification Status |
| :--- | :--- | :--- | :--- |
| **DB-01** | 100% Parameterized queries (SQLi protection) | `src/auth/user_repository.py`, `src/analytics/history_service.py` | ✅ VERIFIED |
| **DB-02** | Isolated databases for auth, history, and audit | `config/settings.py:65-72` | ✅ VERIFIED |
| **SEC-01** | Zero committed live secrets (`scan_repo_secrets()`) | `src/security/privacy.py:150-180` | ✅ VERIFIED |
| **SEC-02** | Environment variable fallback for all keys | `config/settings.py:110-140` | ✅ VERIFIED |

### 2.7 Audit Logging & Privacy
| Control ID | Description | Implementation File | Verification Status |
| :--- | :--- | :--- | :--- |
| **AUD-01** | Structured event taxonomy and severity levels | `config/security.py:15-35` | ✅ VERIFIED |
| **AUD-02** | Redaction of passwords, tokens, and clinical data | `src/security/audit_logger.py:120-145` | ✅ VERIFIED |
| **AUD-03** | Privacy-preserving IP address hashing (SHA-256) | `src/security/audit_logger.py:65-80` | ✅ VERIFIED |
| **AUD-04** | Database indexing on timestamps, events, and users | `src/security/audit_logger.py:90-115` | ✅ VERIFIED |
| **PRIV-01** | PII field masking (email, phone, name) | `src/security/privacy.py:30-65` | ✅ VERIFIED |
| **PRIV-02** | GDPR Art. 15 personal data package export | `src/security/privacy.py:80-140` | ✅ VERIFIED |

### 2.8 Clinical & AI Model Safety Guardrails
| Control ID | Description | Implementation File | Verification Status |
| :--- | :--- | :--- | :--- |
| **SAFE-01** | Prohibition of prescription and diagnostic claims | `src/recommendations/recommendation_validation.py:25-65` | ✅ VERIFIED |
| **SAFE-02** | Immutable clinical weights (70% ML / 30% NLP) | `src/risk_engine/risk_categories.py:30-35` | ✅ VERIFIED |
| **SAFE-03** | Mandatory informational acknowledgement checkbox | `pages/risk_assessment.py:218-230` | ✅ VERIFIED |
| **SAFE-04** | Prominent non-diagnostic prototype notices | `config/security.py:9-12`, `pages/security.py:40-45` | ✅ VERIFIED |
