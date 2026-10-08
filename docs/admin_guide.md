# HeartGuard Admin Guide

## Admin Dashboard Overview

The Admin Dashboard is accessible only to users with the **ADMIN** role. It provides a system-wide view of HeartGuard's operational status, user statistics, assessment analytics, and security audit log.

### Accessing the Dashboard
Log in with an admin account. The admin dashboard loads automatically or can be accessed from the sidebar. All admin page accesses are logged in the audit trail.

### System Status
The top section shows four status indicators:
- **ML Model** — Whether the trained model and preprocessor are loaded and ready.
- **SHAP Explainability** — Whether the SHAP explainer (TreeExplainer or LinearExplainer) is available.
- **Lifestyle NLP** — The rule-based lexicon engine (always ready).
- **Multimodal Engine** — Whether the combined 70/30 clinical-lifestyle engine is operational.

### Alert / Twilio Configuration
Shows the status of the SMS alert service:
- **Alert Mode** — Live Mode (SMS enabled) or Demo Mode (SMS simulated locally).
- **Twilio Account SID** — Configured or Not Configured (only first 6 characters shown).
- **Twilio Auth Token** — Hidden for security; shows Configured or Not Configured.
- **Twilio Phone Number** — Masked; only last 4 digits visible.

### User Statistics
- Patient Accounts, Reviewer Accounts, Admin Accounts, and Total Active Users.

### System Assessment & Review Analytics
Aggregated platform metrics (individual patient data is never exposed):
- Total Assessments, Assessed Patients, System Mean Risk, Total Reviews, Pending Reviews.
- **Risk Category Distribution** — bar chart of all assessments by category.
- **Review Distribution** — bar chart of review statuses.
- **Alert Dispatch Statistics** — bar chart of alert outcomes.
- **Model Version Usage** — table showing which model versions are in use.

### User Accounts (Admin View)
Expandable section showing all registered users with Name, Email, Role, Active status, and Created date. Password hashes are never displayed.

### Recent Security Events
The last 50 audit log entries showing Timestamp, Event type, User ID, Role, Status, and Detail. Sensitive values (passwords, tokens, clinical data) are never stored in the audit log.

---

## User Management

### Creating Admin Accounts
Admin accounts cannot be self-registered. They must be created via the command-line script:

1. Set environment variables in your `.env` file:
   ```
   ADMIN_EMAIL=admin@heartguard.local
   ADMIN_PASSWORD=<strong-password>
   ADMIN_NAME=HeartGuard Admin
   ```
2. Run the script:
   ```
   python scripts/create_admin.py
   ```
3. The script will confirm the account creation with ID, email, and role.
4. **Important:** Clear `ADMIN_PASSWORD` from your environment after setup.

Security notes:
- Credentials are read from environment variables only, never from command-line arguments.
- Never hard-code credentials in the script.
- Use a strong password (minimum 8 characters).
- Rotate the password after first use in production.

### Creating Reviewer Accounts
Reviewer accounts are also created via a command-line script (only admins should run this):

1. Set environment variables:
   ```
   REVIEWER_EMAIL=reviewer@heartguard.local
   REVIEWER_PASSWORD=<strong-password>
   REVIEWER_NAME=Dr. Jane Smith
   ```
2. Run the script:
   ```
   python scripts/create_reviewer.py
   ```
3. The script confirms creation and notes that the account has read-only access to AI assessment results. It cannot modify clinical risk scores or AI-generated data.

### User Role Summary
| Role | Self-Register | Can Create Assessments | Can Review | Can Access Admin |
|---|---|---|---|---|
| PATIENT | Yes | Yes | No | No |
| REVIEWER | No (script) | No | Yes | No |
| ADMIN | No (script) | No | Yes (read-only) | Yes |

---

## Analytics Dashboard

Navigate to **"System Analytics Dashboard"** from the sidebar (Admin only).

### Time Range Filter
Filter all analytics by: All Time, Last 7 Days, Last 30 Days, or Last 90 Days.

### Assessment Overview
- Total Predictions, Unique Patients, Mean Risk, Total Alerts, Model Versions.

### Risk Distribution
- Category distribution chart (CRITICAL, ELEVATED, LOWER_RISK) with counts, average risk, and percentages.
- Detailed table of each category's statistics.

### Prediction Trend
A line chart showing daily prediction volume over time.

### Model Version Analytics
Table showing which model versions are in use and their usage counts.

### Alert Analytics
- Total Alerts, Successful alerts, Failed alerts, Success Rate.
- Alert distribution chart by risk level.

### Recommendation Analytics
- Total Recommendations, Unique Users, Average per Assessment.
- Breakdown by recommendation category.

### Explainability Analytics
- Top features ranked by frequency of appearance as a top risk factor across all assessments.
- Mean absolute SHAP values for each feature.
- Privacy note: individual patient data is never exposed.

### Security Analytics
- Total Events, Failed Logins, Authorization Failures, Admin Actions.

### Anomaly Detection
- **Assessment Volume** — Health status of assessment submission rates.
- **Prediction Distribution** — Health status of prediction distribution (checks for distribution shifts).

### Monitoring Events
The 15 most recent monitoring events with timestamp, event type, severity, component, status, and message.

---

## Model Monitoring

Navigate to **"Model Monitoring Dashboard"** from the sidebar (Admin only).

### Model Performance
- **Best Model** name, number of loaded models, integrity verification status, total evaluations.
- **Latest Evaluation Metrics:** Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC.
- **Model Comparison Table:** Side-by-side comparison of all evaluated models.
- **Metric History:** Interactive line chart showing any metric over time for a selected model.

### Data Drift
- **Current Feature Distributions:** For numerical features (mean, std, min, max) and categorical features (category counts, top category).
- **Prediction Distribution Drift:** Compares current prediction distribution against the reference distribution. Shows HEALTHY, WARNING, or DEGRADED status.
- **Reference vs Current Distribution Table:** Side-by-side comparison of category percentages.

### Data Quality
- **Total Records, Valid Records, Duplicate Rate, Quality Status** (HEALTHY, WARNING, or DEGRADED).
- **Issues:** Any data quality issues detected (warnings displayed).
- **Missing Data by Feature:** Table showing missing count and missing rate per feature.
- **Schema Issues:** Unexpected categories in categorical features.

### System Performance
- **Average Inference Latency** (ms), **Error Rate**, **Total Requests** (last 24 hours).
- **Latency Trend:** Line chart of inference latency over the last 24 hours.

### Monitoring Events
- Total Events, Open Events, Warnings, Critical events.
- Table of the 20 most recent monitoring events.

**Disclaimer:** All monitoring thresholds are engineering thresholds, NOT clinical thresholds. Drift warnings indicate data distribution differences, not medical safety issues. Model monitoring supports human review; it does not automatically determine clinical validity.

---

## Data Quality Monitoring

The Data Quality section within Model Monitoring provides:

- **Record counts** — Total and valid records.
- **Duplicate detection** — Percentage of duplicate records.
- **Missing data analysis** — Per-feature breakdown of missing values with counts and rates.
- **Schema validation** — Detection of unexpected categories in categorical features.
- **Overall quality status** — HEALTHY, WARNING, or DEGRADED.

Use this to identify data issues that could affect model predictions.

---

## System Health

System health is visible in two places:

### Admin Dashboard (Top Section)
Shows the status of ML Model, SHAP Explainability, Lifestyle NLP, and Multimodal Engine.

### Patient Dashboard (Collapsible Section)
Visible to all users in an expandable section showing:
- Cleveland Dataset status (Ready or Not Found)
- Data Preprocessor status (Ready or Not Ready)
- Clinical ML Model status (Ready with model name, or Not Trained)
- Multimodal Engine status (Operational 70/30, or ML Required)

---

## Audit Logs

### Accessing Audit Logs
- **Admin Dashboard** — Last 50 events displayed in the "Recent Security Events" section.
- **Security & Audit Center** — Full interactive audit log viewer with filtering (Admin and Reviewer roles).

### Audit Log Viewer (Security Center)
Navigate to the **"Security & Audit Center"** page and select the **"Audit Log Viewer"** tab.

**KPI Metrics:**
- Total Events, Failed Logins, Blocked Access / IDOR, Admin Actions, High/Critical Events.

**Filters:**
- Category (e.g., AUTHENTICATION, DATA_ACCESS, ADMIN_ACTION)
- Severity (INFO, WARNING, CRITICAL)
- Status (SUCCESS, FAILURE, BLOCKED, DENIED)
- Search by keyword, user ID, or resource

**Table Columns:**
ID, Timestamp (UTC), Severity, Category, Event Type, User ID, Role, Status, Resource, Detail.

### What Is Logged
- Login successes and failures
- Registration attempts
- Assessment creation
- Review creation and updates
- Admin dashboard access
- Access denied / IDOR blocks
- Report generation
- Data exports

### What Is NOT Logged
- Passwords or password hashes
- Twilio auth tokens
- Raw clinical data or lifestyle narratives
- Session tokens

---

## Security Center

Navigate to **"Security & Audit Center"** from the sidebar.

### Security Posture Tab
Shows the complete security controls checklist organized by category:

**Identity, Access & Session Security:**
- Scrypt/Bcrypt salted password hashing
- Strict PATIENT / REVIEWER / ADMIN role segregation
- IDOR defense on all assessments, insights, and PDF reports
- Session rotation on login; 30-minute inactivity timeout
- Sliding-window rate limiting on authentication and prediction endpoints

**Network & Transport Security:**
- HTTP security headers (Nosniff, X-Frame-Options: DENY, Referrer-Policy)
- Content Security Policy (CSP)
- Environment-variable backed configuration (no secrets committed)

**Clinical Data & Model Protection:**
- Immutable clinical weights and ML models at runtime
- Data minimization in audit logs
- Safe validation engine (rejects diagnostic assertions and prescriptions)
- Mandatory user acknowledgement before risk calculation

**Database & File Security:**
- 100% parameterized SQLite queries (SQL injection immunity)
- Path traversal defense on file exports
- 5 MB upload size cap with MIME verification
- Append-only immutable audit trail

### Privacy & Data Rights Tab
- **Privacy Safeguards:** Data minimization, field masking, no training on user data.
- **Self-Service Data Export:** Generate and download a complete personal data package in JSON format (GDPR Article 15 compliant).

### System Security Report Tab (Admin/Reviewer)
Generate a formal, exportable compliance summary:
1. Click **"Generate Formal Security Report"**.
2. Review the report preview containing:
   - Executive summary
   - Security metrics (audit records, failed logins, access denials, hardcoded secrets scan)
   - Verified controls checklist
   - Academic prototype notice
3. Download as Markdown.

---

## Configuration

### Environment Variables
HeartGuard uses environment variables (via `.env` file) for configuration:

| Variable | Purpose |
|---|---|
| `ADMIN_EMAIL` | Admin account email (for create_admin.py) |
| `ADMIN_PASSWORD` | Admin account password (for create_admin.py) |
| `ADMIN_NAME` | Admin display name |
| `REVIEWER_EMAIL` | Reviewer account email (for create_reviewer.py) |
| `REVIEWER_PASSWORD` | Reviewer account password |
| `REVIEWER_NAME` | Reviewer display name |
| `TWILIO_ACCOUNT_SID` | Twilio account SID for SMS alerts |
| `TwILIO_AUTH_TOKEN` | Twilio auth token (never displayed in UI) |
| `TWILIO_PHONE_NUMBER` | Twilio phone number for outgoing SMS |
| `DOCTOR_PHONE_NUMBER` | Doctor's phone for emergency alerts |
| `EMERGENCY_CONTACT_PHONE_NUMBER` | Emergency contact phone |
| `ALERTS_ENABLED` | Enable/disable live SMS alerts |
| `DEMO_MODE` | Run in demo mode (SMS simulated) |
| `DEBUG` | Enable debug mode (disable before public deployment) |

### Mode Indicators
The Security Center shows current mode:
- **Demo Mode** — External SMS alerts simulated locally. Models and security fully active.
- **Live Mode** — Production SMS alerts and transport active.
- **DEBUG=True** — Active development environment. Disable before public deployment.
- **DEBUG=False** — Hardened production configuration.
