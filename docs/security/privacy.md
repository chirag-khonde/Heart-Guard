# HeartGuard — Data Privacy & Governance Charter

**Document Version:** 1.0.0  
**Phase:** 15 (Security, Privacy, Audit Logging & Compliance)  
**System Status:** Academic & Research Healthcare Demonstration Prototype  

---

## 1. Compliance Baseline & Scope

HeartGuard processes physiological and lifestyle self-reported metrics to calculate risk likelihoods for cardiovascular conditions. 

> [!NOTE]
> **Formal Prototype Disclaimer:** HeartGuard is an academic and research prototype designed for demonstration, validation, and educational evaluation. It is **not** a certified medical diagnostic device under FDA, CE-MDR, or clinical software regulations. The privacy and security controls documented here represent best-practice engineering standards for research systems.

---

## 2. Core Privacy Principles

### 2.1 Principle of Data Minimization
HeartGuard strictly restricts data ingestion to parameters necessary for computing cardiovascular risk and generating behavioral guidance:
- **Clinical Data:** 13 UCI Cleveland features (age, sex, resting blood pressure, cholesterol, fasting blood sugar, resting ECG, max heart rate, exercise angina, ST depression, ST slope, fluoroscopy vessels, thalassemia).
- **Lifestyle Data:** Free-text narrative processed into categorical behavioral indicators (smoking, physical activity, sleep, diet).
- **Audit Logs:** Metadata only. **No raw clinical vectors, lifestyle narrative, or password hashes are ever logged.**

### 2.2 Pseudonymization and Masking
- Network IP addresses are hashed using SHA-256 with a salt before persisting in audit logs.
- Direct identifiers (user names, email addresses, phone numbers) are masked in all administrative screens:
  - Email: `j***e@example.com`
  - Phone: `+1 ***-***-1234`
  - Name: `J*** D***`

### 2.3 User Autonomy & Data Rights (GDPR & CCPA Alignment)
HeartGuard supports core digital data rights:
1. **Right of Access & Portability (GDPR Art. 15 / CCPA § 1798.100):**
   - Patients can download their complete record (profile, assessments, AI recommendations, doctor observations) via `export_user_data()` as a structured JSON file.
2. **Right to Erasure / Account Deactivation (GDPR Art. 17):**
   - Soft-delete account deactivation is available, immediately revoking login capability and disconnecting active sessions.
3. **Transparency & Consent:**
   - Mandatory acknowledgement checkbox displayed before risk evaluation confirming user understanding of the non-diagnostic scope.

### 2.4 LLM & Third-Party Privacy Guardrails
If external LLMs (e.g. OpenAI, Anthropic, Gemini) are configured for lifestyle extraction or recommendation synthesis:
- All Personally Identifiable Information (names, emails, phone numbers, addresses, social security numbers) is sanitized and stripped before sending prompts.
- Only aggregated risk levels and general lifestyle habit categories are passed to the model.

---

## 3. Data Retention & Storage Policy

| Data Category | Storage Location | Encryption at Rest | Retention Window | Purge Trigger |
| :--- | :--- | :--- | :--- | :--- |
| User Credentials | `data/auth/users.db` | Salted Bcrypt (12 rounds) | Active account duration | Account deactivation |
| Risk Assessments | `data/history/history.db` | Parameterized SQLite | Active account duration | User data deletion request |
| Clinician Reviews | `data/reviews/reviews.db` | Parameterized SQLite | Audit lifecycle | Academic evaluation completion |
| Audit Trail | `data/security/audit.db` | Parameterized SQLite | 90 days rolling | Automated archiving script |
| Generated Reports | `data/reports/*.pdf` | Local OS permissions | Transient (cached) | User session termination |
