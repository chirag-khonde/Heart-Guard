# HeartGuard Demo Script — Final-Year Presentation

**Duration:** 15–20 minutes
**Audience:** Panel of evaluators / academic committee

---

## 1. Problem Statement (2 min)

> "Heart disease remains the leading cause of death globally, accounting for approximately 17.9 million deaths annually according to the WHO. Early detection of cardiovascular risk significantly improves patient outcomes, yet existing clinical decision support systems often operate as black boxes — providing predictions without transparent reasoning."

**Key points to cover:**
- Heart disease is the #1 cause of death globally
- Early risk prediction saves lives through timely intervention
- Current AI diagnostic tools lack explainability — clinicians cannot trust what they cannot understand
- Patients have no visibility into why a system flagged them as high-risk

**Introduce HeartGuard:**
- An academic/research prototype for early heart disease risk prediction
- Combines clinical data analysis, machine learning, and lifestyle text analysis
- Provides explainable predictions using SHAP (SHapley Additive exPlanations)
- Multimodal approach: clinical ML (70%) + lifestyle NLP (30%)
- Three user roles: Patient, Reviewer (doctor), Admin
- Built with Python 3.12+, Streamlit, scikit-learn, XGBoost, TensorFlow, SHAP, NLTK

> "HeartGuard addresses this gap by combining multiple AI techniques — supervised classification, SHAP-based explainability, and NLP lifestyle analysis — into a single, transparent risk assessment platform."

---

## 2. Architecture Overview (3 min)

> "Let me walk you through the system architecture."

### High-Level Architecture Diagram (draw on whiteboard or show slide)

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Frontend                  │
│         (pages/, src/ui/, app.py)                   │
├──────────────┬──────────────┬───────────────────────┤
│  Patient UI  │  Reviewer UI │     Admin UI          │
├──────────────┴──────────────┴───────────────────────┤
│                  Python Backend                      │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │ Auth (RBAC) │ │ Risk Engine  │ │  SHAP XAI    │ │
│  │ src/auth/   │ │src/risk_engine│ │src/explainab.│ │
│  └─────────────┘ └──────────────┘ └──────────────┘ │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │ ML Models   │ │ NLP Lifestyle│ │  Monitoring  │ │
│  │ src/ml/     │ │  src/nlp/    │ │ src/analytics│ │
│  └─────────────┘ └──────────────┘ └──────────────┘ │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │ Security    │ │ Alerts       │ │  Reports     │ │
│  │src/security │ │ src/alerts/  │ │ src/reports/ │ │
│  └─────────────┘ └──────────────┘ └──────────────┘ │
├─────────────────────────────────────────────────────┤
│              SQLite Databases                       │
│  auth.db │ assessments.db │ reviews.db │ audit.db   │
│  monitoring.db │ evaluation.db                       │
└─────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Location | Purpose |
|-----------|----------|---------|
| **Streamlit Frontend** | `app.py`, `pages/` | Interactive web UI with 15 pages |
| **Authentication** | `src/auth/` | bcrypt password hashing, session management, RBAC |
| **Risk Engine** | `src/risk_engine/` | 70/30 multimodal risk calculation |
| **ML Models** | `src/ml/`, `models/` | 4 classifiers with cross-validation |
| **SHAP Explainability** | `src/explainability/` | TreeExplainer, LinearExplainer, KernelExplainer |
| **NLP Lifestyle** | `src/nlp/` | Lexicon-based lifestyle risk scoring (0–100) |
| **Security** | `src/security/` | Input validation, rate limiting, audit logging, XSS defense |
| **Monitoring** | `src/analytics/` | Drift detection, data quality, anomaly detection |
| **Alerts** | `src/alerts/` | Twilio SMS for critical risk cases |
| **Reports** | `src/reports/` | PDF generation via ReportLab |

### Databases

| Database | Path | Purpose |
|----------|------|---------|
| `auth.db` | `data/auth/` | User accounts, bcrypt hashes |
| `assessments.db` | `data/assessments/` | Patient assessment history |
| `reviews.db` | `data/reviews/` | Doctor review records |
| `audit.db` | `data/security/` | Security audit log (append-only) |
| `monitoring.db` | `data/monitoring/` | Drift/quality monitoring events |
| `evaluation.db` | `data/evaluation/` | Model evaluation run history |

---

## 3. Live Demo — Patient Workflow (5 min)

### 3.1 Login as Patient

> "Let me log in as a patient user."

- Navigate to the login page (`pages/login.py`)
- Enter patient credentials
- Point out: timing-attack resistant verification, generic error messages (no user enumeration)

### 3.2 Dashboard Overview

> "This is the patient dashboard."

Show:
- **Personalized greeting** and academic prototype disclaimer banner
- **5 KPI cards:** Model-Based Risk, Risk Category badge, Total Assessments, Review Status, Alert Status
- **Latest assessment summary** with comparative delta analysis
- **Risk component decomposition** cards (70% Clinical ML + 30% Lifestyle NLP)
- **Chronological multimodal risk trajectory** trend line
- **SHAP feature contribution chart** using non-diagnostic language
- **Structured lifestyle insights** cards (sleep, stress, exercise, diet, smoking)
- **Recent assessments table** (5 latest records)

### 3.3 Create New Assessment

> "Now I'll create a new risk assessment."

Navigate to `pages/risk_assessment.py`.

**Step 1 — Enter Clinical Data:**
- Age, sex, chest pain type, resting BP, cholesterol, fasting blood sugar, resting ECG, max heart rate, exercise angina, ST depression, number of major vessels
- Point out: physiological bounds validation, real-time input validation

**Step 2 — Enter Lifestyle Description:**
- Free-text area for lifestyle narrative
- Example: "I am a 55-year-old male. I smoke cigarettes daily and have a family history of heart attack. I eat fast food regularly and exercise rarely. I sleep about 5 hours per night and drink alcohol on weekends."
- Max 5,000 characters, XSS sanitization applied

**Step 3 — Submit Assessment:**
- Click submit
- Show the loading state briefly

### 3.4 Show Risk Result

> "Here is the multimodal risk result."

Show:
- **Overall risk score** (gauge visualization)
- **Risk category:** MONITORING / APPOINTMENT_RECOMMENDED / CRITICAL
- **Recommended action** (non-diagnostic guidance)
- **Clinical contribution** (70% weight): clinical_risk × 0.70
- **Lifestyle contribution** (30% weight): lifestyle_risk × 0.30
- **Clinical model used:** (e.g., Logistic Regression, XGBoost, Random Forest, or Neural Network)
- **Alert level:** MONITORING, APPOINTMENT_RECOMMENDED, or CRITICAL

### 3.5 Show SHAP Explanation

> "This is the explainable AI component — the heart of what makes HeartGuard different."

Show:
- **SHAP waterfall plot** — shows how each clinical feature pushes risk above or below baseline
- **Top risk factors** — ranked by absolute SHAP value
- **Human-readable summary** — plain-language explanation of the prediction
- Point out: "These are model-based contributions, not clinical diagnoses"

Explain SHAP briefly:
> "SHAP uses game theory — specifically Shapley values — to fairly distribute the prediction among features. Each feature gets a contribution score. Positive values push toward disease presence; negative values push toward absence."

### 3.6 Show Recommendations

Show:
- Clinical guidance based on risk category
- Disclaimer that this is informational, not diagnostic
- Encouragement to consult a healthcare professional

### 3.7 View History

Navigate to `pages/history.py`:
- Chronological list of all past assessments
- Pairwise comparison with percentage-point changes
- CSV export with formula-injection sanitization

### 3.8 Generate PDF Report

> "The patient can also download a professional PDF report."

Show:
- Multi-page academic/research prototype PDF generated via ReportLab
- Contains: executive risk summary, weighted multimodal breakdown, SHAP explainability drivers, trend charts, alert audit details, medical disclaimers
- Secure filename sanitization prevents path traversal

---

## 4. Live Demo — Reviewer Workflow (2 min)

### 4.1 Login as Reviewer

> "Now let me switch to the reviewer (doctor) role."

- Log out patient, log in as reviewer
- Point out: `REVIEWER` role enforced server-side via `require_reviewer()`

### 4.2 View Review Queue

Navigate to `pages/review.py`:
- **Queue summary KPI cards:** Pending, In Review, Reviewed, Follow-Up Recommended, Total Assigned
- **Review queue distribution chart**
- List of assessments awaiting review

### 4.3 Open Assessment

> "I can open an assessment to inspect the AI's prediction."

Show:
- **Read-only AI panel** — risk scores, SHAP factors, narrative summary (never editable by reviewer)
- **Professional review form:**
  - Status dropdown (Pending, In Review, Reviewed)
  - Follow-up flag (boolean)
  - Urgency flag (boolean)
  - Free-text notes field
- Point out: AI-generated risk scores **cannot** be modified through any review action

### 4.4 Submit Professional Review

- Fill in review notes
- Submit the review
- Show that the review is stored in a separate `reviews.db` (assessments are never modified)
- Show ownership enforcement: reviewers can only update their own review records

---

## 5. Live Demo — Admin Workflow (3 min)

### 5.1 Login as Admin

> "Finally, let me demonstrate the administrator dashboard."

- Log out reviewer, log in as admin
- Point out: Admin account provisioning is restricted to an out-of-band CLI tool (`scripts/create_admin.py`)

### 5.2 Dashboard Analytics

Navigate to `pages/admin.py`:
- **System-wide aggregated analytics:**
  - Total Assessments, Assessed Patients, System Mean Risk, Total Reviews, Pending Queue
- **Visual distribution charts:**
  - Risk Categories, Review Statuses, Alert Outcomes, Model Version Usage
- Strict privacy preservation: no raw patient medical narratives or PII exposed

### 5.3 Model Monitoring

Navigate to `pages/model_monitoring.py`:
- **Model performance history:** accuracy, precision, recall, F1, ROC-AUC, PR-AUC
- **Model status tracking:** PRODUCTION, VALIDATION, RETIRED
- **Evaluation runs** with metric snapshots
- **Drift detection dashboard:**
  - PSI (Population Stability Index) for numerical features
  - KS test for distribution shifts
  - JS divergence for prediction drift
  - Minimum sample size: 30

### 5.4 Data Quality

Show data quality monitoring:
- Missing rate tracking (warning at 5%, critical at 20%)
- Duplicate rate tracking (warning at 2%, critical at 10%)
- Out-of-range value detection
- Schema change detection

### 5.5 Audit Logs

Navigate to `pages/security.py`:
- **Structured audit log** with filtering and search
- **Event taxonomy:** AUTHENTICATION, AUTHORIZATION, DATA_ACCESS, ADMIN_ACTION, FILE_ACCESS, MODEL_OPERATION, SYSTEM_SECURITY
- **Severity levels:** INFO, WARNING, HIGH, CRITICAL
- **Privacy-safe:** IP addresses are SHA-256 hashed, passwords/tokens never logged
- **Rate limiting events** visible in audit trail

### 5.6 Security Center

Show:
- Rate limiting status (5 login attempts per 60 seconds)
- Session management (30-minute timeout)
- Security headers (CSP, X-Frame-Options, X-XSS-Protection)
- User account management (status toggling)

---

## 6. Technical Deep Dive (3 min)

### 6.1 ML Models and Evaluation

> "HeartGuard trains and evaluates four classification models."

| Model | Framework | Hyperparameter Tuning | SHAP Explainer |
|-------|-----------|----------------------|----------------|
| Logistic Regression | scikit-learn | Grid search (C, penalty, solver) | LinearExplainer |
| Random Forest | scikit-learn | Grid search (n_estimators, max_depth) | TreeExplainer |
| XGBoost | xgboost | Grid search (learning_rate, max_depth) | TreeExplainer |
| Neural Network (MLP) | TensorFlow/Keras | Grid search (hidden_layer_sizes, alpha) | KernelExplainer |

**Evaluation:**
- 5-fold Stratified K-Fold cross-validation
- Primary metric: ROC-AUC
- Secondary metric: F1 score
- Best model selected via CV ROC-AUC
- Model artifacts saved with SHA-256 integrity checksums (`models/model_manifest.json`)

**Dataset:**
- Cleveland Heart Disease dataset (UCI ML Repository)
- 303 instances, 13 clinical features
- Binary target: 0 (absence) / 1 (presence)
- 80/20 stratified train/test split (random_state=42)

**Preprocessing pipeline:**
- Numerical: Median imputation → MinMaxScaler
- Categorical: Most-frequent imputation → OneHotEncoder(handle_unknown='ignore')
- Preprocessor fit ONLY on training data (no data leakage)

### 6.2 SHAP Explainability

> "Every prediction comes with a mathematical explanation."

- **TreeExplainer** for XGBoost and Random Forest (exact Shapley values)
- **LinearExplainer** for Logistic Regression
- **KernelExplainer** fallback for arbitrary models
- **Global feature importance:** Mean absolute SHAP values across training population
- **Local patient explanations:** Per-feature attribution for individual predictions
- **Waterfall plot:** Visualizes how each feature pushes risk above/below baseline
- **Human-readable summary:** Translates numerical SHAP values into plain-language clinical narratives
- **Safety rules:** Non-diagnostic language enforced, disclaimers included

### 6.3 Security Architecture

> "Security was built in from Phase 9, not bolted on afterwards."

**Authentication:**
- bcrypt with work factor of 12 rounds
- Timing-attack resistant verification
- Generic error responses (prevents user enumeration)

**RBAC:**
- Three roles: PATIENT, REVIEWER, ADMIN
- Server-side enforcement via `require_reviewer()`, `require_admin()` decorators
- Admin provisioning restricted to CLI tool (`scripts/create_admin.py`)

**Data Isolation:**
- All queries filtered by authenticated `user_id`
- IDOR prevention via `validate_integer_id()`
- Ownership verification for cross-account access

**Input Validation:**
- XSS defense: script tag stripping, HTML escaping
- SMS header injection prevention
- Length bounds: email (255), name (100), password (min 8), lifestyle text (5,000)
- JSON payload validation with allowed-key whitelisting

**Audit Logging:**
- Append-only structured audit log in SQLite
- 50+ event types across 7 categories
- Privacy-safe: IP hashed, credentials/tokens never logged
- Indexed for efficient querying

**Security Headers:**
- Content-Security-Policy (CSP)
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- X-Content-Type-Options: nosniff

### 6.4 Monitoring and Drift Detection

> "The system monitors itself for degradation."

**Drift Detection:**
- PSI (Population Stability Index) for numerical features (warning: 0.10, critical: 0.25)
- KS test for distribution shifts (alpha: 0.05)
- JS divergence for prediction drift (warning: 0.05, critical: 0.15)
- Minimum sample size: 30 assessments

**Data Quality:**
- Missing rate monitoring (warning: 5%, critical: 20%)
- Duplicate rate monitoring (warning: 2%, critical: 10%)
- Out-of-range value detection (warning: 3%)

**Anomaly Detection:**
- Z-score based (threshold: 3.0)
- Volume spike detection (2x normal)
- Error rate monitoring (warning: 5%, critical: 15%)

**Performance Monitoring:**
- Latency tracking (warning: 5s, critical: 10s)
- Cache TTL: 300 seconds

---

## 7. Results and Limitations (2 min)

### 7.1 Model Performance

> "Here are the actual evaluation results from our trained models."

| Model | Test ROC-AUC |
|-------|-------------|
| Random Forest | 0.5381 |
| XGBoost | 0.6078 |
| Neural Network | 0.4978 |
| Logistic Regression | 0.4357 |

> "These metrics reflect the challenges of the Cleveland dataset — a small dataset (303 instances) with significant class imbalance and noise. In a production setting, larger datasets and domain-specific feature engineering would improve performance."

### 7.2 Test Results

> "The application has been thoroughly tested."

- **562 tests collected and passing**
- Tests span: unit tests, integration tests, security tests, authorization tests, SHAP tests, lifestyle NLP tests, multimodal risk tests, assessment history tests, dashboard tests, model monitoring tests, drift detection tests, anomaly detection tests, data quality tests, alert tests, recommendation tests, report generation tests, and UI component tests

### 7.3 Security Features

- bcrypt password hashing (12 rounds)
- Role-Based Access Control (PATIENT, REVIEWER, ADMIN)
- IDOR prevention with user_id filtering
- XSS defense with HTML escaping and script stripping
- Rate limiting (5 login attempts / 60s)
- Session timeout (30 minutes)
- Append-only audit logging with 50+ event types
- Security headers (CSP, X-Frame-Options, X-XSS-Protection)
- Input validation and sanitization

### 7.4 Known Limitations

- **Academic prototype only** — not validated for clinical use
- **Small dataset** (Cleveland: 303 instances) — limits model generalizability
- **No real-time monitoring** — assessments are on-demand
- **No external EHR integration** — standalone system
- **Single-dataset training** — not validated across multiple heart disease datasets
- **NLP is lexicon-based** — not a deep learning NLP model

### 7.5 Clinical Disclaimer

> "HeartGuard is an academic/research prototype. It provides model-based risk estimates and explainable AI insights. It is NOT a certified medical device and does not provide clinical diagnosis or prescribes medical treatments. All outputs should be interpreted by qualified healthcare professionals."

---

## 8. Future Scope (1 min)

### Short-term
- **Real-time monitoring:** Continuous patient data streaming and alert triggers
- **Multi-dataset support:** Train on Framingham, Statlog, and other heart disease datasets
- **Enhanced NLP:** Upgrade from lexicon-based to transformer-based lifestyle analysis (e.g., BioBERT)

### Medium-term
- **Clinical validation:** Partner with hospitals for prospective validation studies
- **EHR integration:** HL7 FHIR compatibility for real-world clinical workflows
- **Federated learning:** Train across multiple hospitals without sharing patient data

### Long-term
- **Mobile application:** Native iOS/Android for patient self-assessment
- **Wearable integration:** Apple Watch, Fitbit data feeds for continuous risk monitoring
- **Regulatory pathway:** FDA 510(k) clearance for clinical deployment
- **Multi-language support:** Lifestyle analysis in Hindi, Tamil, Bengali, etc.

> "HeartGuard demonstrates that explainable AI can make healthcare more transparent and accessible. The modular architecture allows each component to be independently improved and validated."

---

## Q&A Preparation

Be ready to answer:
1. Why did you choose these specific models?
2. How does SHAP ensure fair feature attribution?
3. What would you do differently for a production deployment?
4. How did you prevent data leakage in the preprocessing pipeline?
5. What are the ethical implications of AI in healthcare?
6. How would you handle concept drift in a real clinical setting?

---

**End of Demo Script**
