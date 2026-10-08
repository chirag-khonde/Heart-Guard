# HeartGuard — System Architecture

> Version 1.0.0 · Phase 18 — Advanced Dashboard & Visualizations

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STREAMLIT FRONTEND                                 │
│  app.py ──► pages/ ──► src/ui/ (sidebar, theme, forms, charts, tables)     │
│  Authentication Gate: pages/login.py → session_manager.py                   │
└──────────┬──────────────────────────────────────────────┬──────────────────┘
           │                                              │
           ▼                                              ▼
┌──────────────────────┐                ┌──────────────────────────────────┐
│   AUTHENTICATION     │                │         BACKEND MODULES          │
│   src/auth/          │                │                                  │
│   ├─ auth_service    │                │  ┌─────────────┐ ┌────────────┐ │
│   ├─ authorization   │                │  │ src/ml/     │ │ src/nlp/   │ │
│   ├─ session_manager │                │  │ predict     │ │ lifestyle  │ │
│   ├─ password_service│                │  │ registry    │ │ analyzer   │ │
│   ├─ user_repository │                │  │ train       │ │ scoring    │ │
│   └─ models          │                │  └──────┬──────┘ └─────┬──────┘ │
└──────────┬───────────┘                │         │              │         │
           │                            │         ▼              ▼         │
           │                            │  ┌──────────────────────────┐   │
           │                            │  │   RISK ENGINE            │   │
           │                            │  │   src/risk_engine/       │   │
           │                            │  │   multimodal_risk.py     │   │
           │                            │  │   (70% Clinical +        │   │
           │                            │  │    30% Lifestyle)        │   │
           │                            │  └──────────┬───────────────┘   │
           │                            │             │                    │
           │                            │             ▼                    │
           │                            │  ┌──────────────────────────┐   │
           │                            │  │     EXPLAINABILITY       │   │
           │                            │  │     src/explainability/  │   │
           │                            │  │     SHAPExplainerService │   │
           │                            │  │     shap_explainer.py    │   │
           │                            │  └──────────────────────────┘   │
           │                            └──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PERSISTENCE LAYER                                 │
│                                                                             │
│  ┌─────────────┐  ┌───────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ heartguard  │  │ audit.db  │  │ assessments  │  │ reviews.db        │  │
│  │ _auth.db    │  │           │  │ .db          │  │                   │  │
│  │ (users)     │  │ (security │  │ (assessments │  │ (professional     │  │
│  │             │  │  events)  │  │  + clinical  │  │  reviews)         │  │
│  │             │  │           │  │  data JSON)  │  │                   │  │
│  └─────────────┘  └───────────┘  └──────────────┘  └───────────────────┘  │
│                                                                             │
│  ┌─────────────┐  ┌───────────┐  ┌──────────────┐                         │
│  │ alerts.db   │  │ recommend │  │ monitoring   │                         │
│  │             │  │ ations.db │  │ .db          │                         │
│  │ (alert      │  │           │  │              │                         │
│  │  history)   │  │ (AI       │  │ (drift, data │                         │
│  │             │  │  insights)│  │  quality,    │                         │
│  │             │  │           │  │  monitoring  │                         │
│  │             │  │           │  │  events)     │                         │
│  └─────────────┘  └───────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                   │
│  ┌─────────────────┐  ┌──────────────────────┐  ┌───────────────────────┐  │
│  │ Twilio SMS API  │  │ Model Artifacts      │  │ PDF Reports           │  │
│  │ (Emergency      │  │ (models/*.pkl)       │  │ (ReportLab)           │  │
│  │  Alerts)        │  │                      │  │                       │  │
│  └─────────────────┘  └──────────────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Frontend (Streamlit) Architecture

### Entry Point

**`app.py`** is the Streamlit application entry point. It enforces an authentication gate via `src/auth/session_manager.py:is_authenticated()`, renders a role-aware home screen with navigation cards, and delegates to `pages/` for sub-routes.

### Pages (`pages/`)

| Page | Purpose | Access |
|---|---|---|
| `login.py` | User login form | Public |
| `register.py` | Patient self-registration | Public |
| `risk_assessment.py` | Clinical + Lifestyle multimodal assessment | PATIENT+ |
| `lifestyle_analyzer.py` | NLP-based lifestyle risk scoring | PATIENT+ |
| `explainable_ai.py` | SHAP-based feature importance | PATIENT+ |
| `history.py` | Assessment history & PDF report generation | PATIENT+ |
| `dashboard.py` | Personal summary & pipeline health | PATIENT+ |
| `patient_analytics.py` | Patient-level analytics | PATIENT+ |
| `review.py` | Doctor review portal (read-only AI scores) | REVIEWER |
| `admin.py` | Admin user management | ADMIN |
| `analytics_dashboard.py` | System-wide analytics | ADMIN |
| `model_monitoring.py` | Drift detection & data quality | ADMIN |
| `model_performance.py` | Model metrics & comparison | ADMIN |
| `security.py` | Security status & profile | PATIENT+ |
| `about.py` | About & disclaimers | Public |

### UI Components (`src/ui/`)

- **`sidebar.py`** — `render_sidebar()` provides role-based navigation, user info display, and logout. Called once per page.
- **`theme.py`** — `inject_global_theme()` injects a CSS design system with custom properties (colors, spacing, shadows). CSS is injected once per page via a guard variable.
- **`forms.py`** — Reusable form components for clinical data entry.
- **`charts.py`** — Matplotlib/Plotly chart builders (risk gauges, trend lines, SHAP visualizations).
- **`tables.py`** — Styled DataFrame renderers.
- **`cards.py`** — Metric cards and summary containers.
- **`badges.py`** — Risk category and status badges.

---

## Backend Modules

### Authentication & Authorization (`src/auth/`)

| File | Responsibility |
|---|---|
| `auth_service.py` | `register_user()`, `authenticate_user()`, `create_admin_user()`, `create_reviewer_user()` — orchestrates registration/login with input validation, bcrypt hashing, timing-attack mitigation, and audit logging |
| `authorization.py` | `require_authentication()`, `require_role()`, `require_reviewer()`, `is_admin()`, `is_patient()`, `is_reviewer()` — server-side role enforcement; calls `st.stop()` on violation |
| `session_manager.py` | `create_session()`, `is_authenticated()`, `check_session_timeout()`, `clear_session()`, `get_current_user()` — Streamlit session_state management with 30-minute inactivity timeout and session rotation |
| `password_service.py` | `hash_password()`, `verify_password()` — bcrypt (12 rounds), constant-time comparison |
| `user_repository.py` | `create_user()`, `find_by_email()`, `find_by_id()`, `list_users()`, `deactivate_user()`, `update_user_role()` — parameterized SQLite queries |
| `models.py` | `User` dataclass, `init_auth_db()` — schema definition |

**Roles:** `PATIENT`, `ADMIN`, `REVIEWER` (defined in `config/settings.py`)

### ML Pipeline (`src/ml/`)

| File | Responsibility |
|---|---|
| `predict.py` | `predict_with_model()`, `predict_batch()`, `predict_probability()` — inference wrappers |
| `model_registry.py` | `ModelRegistry` singleton — SHA-256 integrity verification, lazy loading, health reporting. Models: `random_forest` (required), `preprocessor` (required), `xgboost`, `neural_network`, `logistic_regression`, `feature_names` (optional) |
| `train_models.py` | `train_all_models()` — unified training loop for 4 models (LogisticRegression, RandomForest, XGBoost, NeuralNetwork) using sklearn Pipelines for leak-free CV |
| `cross_validation.py` | `create_cv_strategy()` — StratifiedKFold |
| `evaluate.py` | `evaluate_all_models()`, `plot_confusion_matrix()`, `plot_roc_comparison()`, `plot_metrics_comparison()` |
| `models/` | Individual model factory functions: `logistic_regression_model.py`, `random_forest_model.py`, `xgboost_model.py`, `neural_network_model.py` |

**Model artifacts:** `models/*.pkl`, `models/model_manifest.json`, `models/feature_names.json`, `reports/best_model.json`

### Risk Engine (`src/risk_engine/`)

| File | Responsibility |
|---|---|
| `multimodal_risk.py` | `MultimodalRiskEngine` class — `assess()` method orchestrates: clinical ML prediction → lifestyle NLP analysis → 70/30 weighted combination → SHAP explanation → structured result |
| `risk_categories.py` | `get_overall_risk_category()`, `get_recommended_action()`, `get_alert_level()` — thresholds: >85% CRITICAL, 60-85% APPOINTMENT_RECOMMENDED, <60% MONITORING |
| `risk_explanation.py` | `generate_overall_explanation()` — human-readable narrative generation |
| `risk_validation.py` | `validate_clinical_input()`, `validate_clinical_risk()`, `validate_lifestyle_risk()`, `validate_overall_risk()`, `validate_weights()` — input sanitization |

**Weights:** Clinical 70% (`CLINICAL_WEIGHT`), Lifestyle 30% (`LIFESTYLE_WEIGHT`)

### Explainability (`src/explainability/`)

| File | Responsibility |
|---|---|
| `service.py` | `SHAPExplainerService` — high-level API: `explain_patient()`, `global_importance()`, `get_top_risk_factors()` |
| `shap_explainer.py` | `create_shap_explainer()` — auto-selects TreeExplainer/LinearExplainer/KernelExplainer based on model type. `calculate_shap_values()`, `get_feature_contributions()`, `get_local_explanation()`, `get_global_feature_importance()`, `generate_human_readable_summary()`. Visualization: `create_waterfall_plot()`, `create_global_importance_plot()`, `create_summary_plot()`, `create_local_importance_plot()` |

**SHAP explainer selection:** Tree models → `TreeExplainer`; Linear models → `LinearExplainer`; Fallback → `KernelExplainer`

### NLP Lifestyle Analyzer (`src/nlp/`)

| File | Responsibility |
|---|---|
| `lifestyle_analyzer.py` | `LifestyleAnalyzer` class — `analyze()` runs 6 detectors: `_detect_smoking()`, `_detect_physical_inactivity()`, `_detect_unhealthy_diet()`, `_detect_poor_sleep()`, `_detect_family_history()`, `_detect_alcohol_use()`. Uses negation detection, clause boundary awareness, and alcohol disambiguation |
| `risk_lexicon.py` | `RISK_LEXICON` — 6 categories with primary/variation keywords, risk points (smoking=25, family_history=20, unhealthy_diet=18, physical_inactivity=15, poor_sleep=12, alcohol_use=10), severity levels, and `NEGATION_TERMS` |
| `scoring.py` | `calculate_lifestyle_score()` — sum of unique category points capped at 100; `get_risk_category()` — LOW(0-29), MODERATE(30-59), HIGH(60-84), CRITICAL(85-100) |
| `text_preprocessor.py` | `normalize_text()` — unicode normalization, lowercase, punctuation cleaning; `tokenize_text()` — NLTK word_tokenize with regex fallback |
| `explanation.py` | `generate_lifestyle_summary()`, `get_top_lifestyle_risk_factors()` — human-readable output |

### Alert System (`src/alerts/`)

| File | Responsibility |
|---|---|
| `alert_manager.py` | `AlertManager.process_risk_result()` — threshold triage (>85% triggers critical alert), message templating, idempotent Twilio dispatch, demo mode simulation, audit logging |
| `alert_service.py` | `send_sms_alert()`, `check_alert_threshold()`, `log_alert()` — convenience wrappers |
| `twilio_service.py` | `TwilioSMSService` — wraps Twilio SDK: `send_sms()`, `is_configured()`, credential security, error sanitization |
| `alert_templates.py` | `build_critical_doctor_message()`, `build_critical_emergency_message()`, `build_test_message()` |
| `alert_history.py` | `record_alert()`, `is_alert_already_sent()` — idempotent alert audit trail |
| `alert_validation.py` | `validate_alert_config()`, `validate_phone_number()`, `validate_twilio_config()`, `mask_phone_number()` |

**Threshold:** Critical alerts trigger when `overall_risk > 85.0%` (`CRITICAL_THRESHOLD`)

### Report Generation (`src/reports/`)

| File | Responsibility |
|---|---|
| `report_generator.py` | `ReportGenerator.generate_assessment_report()` — builds 5-page PDF via ReportLab: Executive Summary, Risk Components & SHAP Analysis, Historical Trends (matplotlib chart), AI Insights & Recommendations, Alerts & Disclaimers |
| `report_templates.py` | Styles, colors, `NumberedCanvas`, `STANDARD_DISCLAIMER`, `CRITICAL_WARNING` |
| `report_utils.py` | Utility helpers |

**Authorization:** `HistoryService.user_owns_assessment()` enforced before generation. Reports stored in `reports/` directory.

### Professional Review (`src/review/`)

| File | Responsibility |
|---|---|
| `review_service.py` | `ReviewService` — `create_review()`, `update_review()`, `get_pending_assessments()`, `get_assessment_with_review()`, `get_review_statistics()`. Ownership enforcement: reviewer may only update their own reviews. Cross-DB JOINs between `assessments.db` and `reviews.db` |
| `models.py` | `ProfessionalReview` dataclass, `init_review_db()` |
| `review_constants.py` | `REVIEW_STATUSES` (PENDING, IN_REVIEW, REVIEWED, ACCEPTED, MODIFIED, REJECTED), `PROFESSIONAL_NOTES_MAX_LENGTH` |

**Invariant:** No method mutates the `assessments` table. AI risk scores are read-only.

### Security (`src/security/`)

| File | Responsibility |
|---|---|
| `audit_logger.py` | `log_event()` — writes to `audit_log` table in `audit.db`. `sanitize_detail()` redacts passwords/tokens. 30+ event types across 7 categories. `get_filtered_events()`, `get_audit_statistics()` |
| `input_validator.py` | `validate_email()`, `validate_name()`, `validate_identifier()`, `validate_password_strength()`, `validate_lifestyle_text_length()`, `sanitize_text_for_display()`, `sanitize_sms_content()`, `sanitize_filename()`, `validate_json_payload()` |
| `rate_limiter.py` | `InMemoryRateLimiter` — thread-safe sliding window. `check_rate_limit()` for API endpoints. Session-based login rate limiting: 5 attempts per 60 seconds (`LOGIN_MAX_ATTEMPTS`, `LOGIN_COOLDOWN_SECONDS`) |
| `security_logger.py` | `SecurityLogger` — high-level logging for auth events, rate limits, admin actions |
| `authorization_service.py` | Additional authorization helpers |
| `file_security.py` | File upload validation (magic numbers, MIME types, size limits) |
| `privacy.py` | Data minimization and PII protection |

### Analytics & Monitoring (`src/analytics/`)

| File | Responsibility |
|---|---|
| `analytics_service.py` | `AnalyticsService` — `calculate_user_statistics()`, `get_admin_aggregated_analytics()`, `get_category_distribution()` |
| `history_service.py` | `HistoryService` — CRUD for assessments in `assessments.db`. `get_user_assessments()`, `get_assessment_by_id()`, `user_owns_assessment()` (IDOR protection) |
| `trend_service.py` | `TrendService` — `get_risk_trends()`, `compare_assessments()` |
| `drift_detection.py` | PSI, KS test, Jensen-Shannon divergence, prediction shift detection. Compares reference (training) distributions against production data |
| `data_quality_monitoring.py` | Missing rate, duplicate rate, out-of-range detection |
| `anomaly_detection.py` | Z-score anomaly detection, volume/latency/error-rate spikes |
| `performance_monitoring.py` | Latency tracking, error rate monitoring, cache TTL |
| `model_monitoring.py` | Model status lifecycle (PRODUCTION, VALIDATION, RETIRED) |
| `monitoring_events.py` | `init_monitoring_db()`, event CRUD in `monitoring.db` |
| `prediction_analytics.py` | Prediction distribution analysis |
| `risk_analytics.py` | Risk score distribution analysis |
| `alert_analytics.py` | Alert delivery statistics |
| `explainability_analytics.py` | SHAP value distribution tracking |
| `security_analytics.py` | Security event aggregation |
| `recommendation_analytics.py` | Recommendation coverage statistics |

### Recommendations (`src/recommendations/`)

| File | Responsibility |
|---|---|
| `recommendation_service.py` | `RecommendationService.get_or_create_insights()` — fetch or generate AI insights with ownership enforcement |
| `recommendation_engine.py` | `RecommendationEngine` — rule-based insight generation from assessment data |
| `recommendation_models.py` | `AssessmentInsights`, `Recommendation` dataclasses, `init_recommendation_db()` |
| `recommendation_rules.py` | Rule definitions for personalized guidance |
| `recommendation_validator.py` | Input validation for recommendation queries |

### Data Pipeline (`src/data/`)

| File | Responsibility |
|---|---|
| `pipeline.py` | `prepare_cleveland_pipeline()` — end-to-end: load → clean → split → preprocess → persist |
| `loader.py` | `load_cleveland_dataset()`, `normalize_cleveland_target()` |
| `preprocessing.py` | `create_preprocessor()` (ColumnTransformer), `fit_preprocessor()`, `transform_data()`, `split_dataset()` |
| `features.py` | `HEARTGUARD_FEATURES` (11 canonical features), `NUMERICAL_FEATURES` (6), `CATEGORICAL_FEATURES` (5), `CLEVELAND_COLUMN_MAP` |
| `quality.py` | `generate_data_quality_report()` |

### Other Modules

| Module | Purpose |
|---|---|
| `src/health/` | `health_service.py` — system health checks |
| `src/startup/` | `startup_validator.py` — pre-flight validation |
| `src/evaluation/` | 14 evaluation modules: calibration, confusion matrix, cross-validation, error analysis, leakage check, model comparison, PR/ROC analysis, threshold analysis, multimodal/NLP evaluation |
| `src/utils/` | Logger, exceptions, validators |

---

## Database Architecture

HeartGuard uses **7 SQLite databases** for data isolation:

```
data/
├── auth/
│   └── heartguard_auth.db      # User accounts (users table)
├── security/
│   └── audit.db                # Security audit trail (audit_log table)
├── assessments/
│   ├── assessments.db          # Patient assessments (assessments table)
│   ├── reviews.db              # Professional reviews (professional_reviews table)
│   └── recommendations.db      # AI recommendations (recommendations table)
├── alerts/
│   └── alerts.db               # Alert history (alerts table)
├── evaluations/
│   └── evaluation.db           # Model evaluation results
└── monitoring/
    └── monitoring.db           # Drift detection, data quality, monitoring events
```

### Database Schemas

**`heartguard_auth.db` — `users` table:**
```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'PATIENT',
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
```

**`audit.db` — `audit_log` table:**
```sql
CREATE TABLE audit_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT NOT NULL,
    event_type    TEXT NOT NULL,
    user_id       INTEGER,
    role          TEXT,
    status        TEXT NOT NULL,
    detail        TEXT,
    resource_type TEXT,
    resource_id   TEXT,
    category      TEXT,
    severity      TEXT DEFAULT 'INFO',
    ip_hash       TEXT
);
```

**`assessments.db` — `assessments` table:**
```sql
CREATE TABLE assessments (
    id                         INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id              TEXT NOT NULL UNIQUE,
    user_id                    INTEGER NOT NULL,
    created_at                 TEXT NOT NULL,
    clinical_risk              REAL NOT NULL,
    lifestyle_risk             REAL NOT NULL,
    overall_risk               REAL NOT NULL,
    risk_category              TEXT NOT NULL,
    recommendation             TEXT NOT NULL,
    model_version              TEXT NOT NULL,
    narrative_summary          TEXT,
    alert_status               TEXT NOT NULL DEFAULT 'NOT_TRIGGERED',
    top_clinical_factors_json  TEXT,
    lifestyle_factors_json     TEXT,
    clinical_data_json         TEXT
);
```

**`reviews.db` — `professional_reviews` table:**
```sql
CREATE TABLE professional_reviews (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           TEXT NOT NULL UNIQUE,
    assessment_id       TEXT NOT NULL,
    reviewer_id         INTEGER NOT NULL,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    review_status       TEXT NOT NULL DEFAULT 'PENDING',
    professional_notes  TEXT,
    follow_up_required  INTEGER NOT NULL DEFAULT 0,
    urgency_flag        INTEGER NOT NULL DEFAULT 0
);
```

**`recommendations.db` — `recommendations` table:**
Stores per-assessment AI insights (summary, top factors, personalized recommendations) with user ownership tracking.

**`monitoring.db` — `monitoring_events` table:**
```sql
CREATE TABLE monitoring_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        TEXT NOT NULL UNIQUE,
    timestamp       TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    severity        TEXT NOT NULL,
    component       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'OPEN',
    metric_name     TEXT,
    metric_value    REAL,
    threshold_value REAL,
    model_version   TEXT,
    message         TEXT NOT NULL,
    details_json    TEXT,
    acknowledged_by TEXT,
    acknowledged_at TEXT
);
```

---

## ML Pipeline Architecture

```
┌──────────────────┐     ┌──────────────────┐
│ Cleveland Dataset │     │  User Clinical   │
│ (data/raw/)      │     │  Input (Form)    │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐     ┌──────────────────┐
│ src/data/        │     │ validate_        │
│ pipeline.py      │     │ clinical_input() │
│ load → clean →   │     │ src/risk_engine/ │
│ split → preprocess│    │ risk_validation  │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐     ┌──────────────────┐
│ src/ml/          │     │ preprocessor.pkl │
│ train_models.py  │     │ (ColumnTransformer)│
│ CV + Train 4     │     └────────┬─────────┘
│ models           │              │
└────────┬─────────┘              ▼
         │              ┌──────────────────┐
         ▼              │ model.predict()  │
┌──────────────────┐    │ model.predict_   │
│ models/*.pkl     │    │   proba()        │
│ best_model.json  │    │ clinical_risk    │
│ model_results.json│   └──────────────────┘
└──────────────────┘
```

**Models trained:**
1. `logistic_regression` — `LogisticRegression`
2. `random_forest` — `RandomForestClassifier`
3. `xgboost` — `XGBClassifier`
4. `neural_network` — `MLPClassifier`

**Best model selection:** By CV ROC-AUC (primary), F1 (secondary). Stored in `reports/best_model.json`.

**Model Registry (`ModelRegistry`):**
- Singleton pattern with lazy loading
- SHA-256 integrity verification against `models/model_manifest.json`
- Required models: `random_forest`, `preprocessor`
- Optional models: `xgboost`, `neural_network`, `logistic_regression`, `feature_names`

---

## Explainability Architecture

```
Patient Clinical Data
        │
        ▼
┌──────────────────┐
│ src/data/        │
│ preprocessing.py │  Load preprocessor.pkl
│ (transform)      │  Align to model feature space
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ src/explainability│
│ service.py       │
│ SHAPExplainer    │
│ Service          │
└────────┬─────────┘
         │
         ├──► model.predict() → prediction, probability
         │
         ├──► shap_explainer.py
         │    create_shap_explainer()
         │      Tree models → TreeExplainer
         │      Linear models → LinearExplainer
         │      Fallback → KernelExplainer
         │
         ├──► calculate_shap_values() → shap_values, base_values
         │
         ├──► get_feature_contributions() → DataFrame[feature, shap_value, direction]
         │
         ├──► get_local_explanation() → structured dict
         │
         ├──► generate_human_readable_summary() → text
         │
         └──► Visualizations
              ├── create_waterfall_plot()
              ├── create_global_importance_plot()
              ├── create_summary_plot()
              └── create_local_importance_plot()
```

**Key functions:**
- `load_explainable_model()` — reads `reports/best_model.json` to identify best model, loads corresponding `.pkl`
- `load_feature_names()` — reads `models/feature_names.json`
- `load_training_data()` — reads `data/processed/cleveland_train.csv` for SHAP background data
- `get_top_risk_factors()` — positive SHAP values only (features increasing risk)

---

## Alert System Architecture

```
MultimodalRiskEngine.assess()
        │
        ▼
┌──────────────────┐
│ AlertManager     │
│ process_risk_    │
│ result()         │
└────────┬─────────┘
         │
         ├── overall_risk > 85%?
         │   NO  → return NOT_TRIGGERED
         │   YES → continue
         │
         ├── alerts_enabled?
         │   NO  → record "DISABLED" alerts, return demo result
         │   YES → continue
         │
         ├── build_critical_doctor_message()
         │   build_critical_emergency_message()
         │
         ├── is_alert_already_sent()? (idempotency)
         │
         ├── TwilioSMSService.send_sms() → doctor
         ├── TwilioSMSService.send_sms() → emergency contact
         │
         ├── record_alert() → alerts.db (audit trail)
         │
         └── return delivery status dict
```

**Components:**
- `TwilioSMSService` — wraps Twilio SDK with credential security and error sanitization
- `alert_history.py` — `is_alert_already_sent()` prevents duplicate notifications per assessment
- `alert_templates.py` — templated messages with patient name/age
- Demo mode (`ALERTS_ENABLED=false`) simulates the full flow without sending SMS

---

## Report Generation Architecture

```
ReportGenerator.generate_assessment_report(assessment_id, user_id)
        │
        ├── HistoryService.user_owns_assessment() → authorization
        ├── HistoryService.get_assessment_by_id()
        ├── HistoryService.get_user_assessments() → historical context
        ├── TrendService.get_risk_trends()
        ├── TrendService.compare_assessments()
        ├── RecommendationService.get_or_create_insights()
        │
        ▼
┌──────────────────────────────────────────────────────┐
│ ReportLab SimpleDocTemplate → 5-page PDF             │
│                                                      │
│ Page 1: Executive Summary                            │
│   ├── Metadata table (ID, date, model, alert status) │
│   ├── Overall risk callout (score + category)        │
│   └── Narrative summary                              │
│                                                      │
│ Page 2: Risk Components & Explainability             │
│   ├── Component breakdown table (70/30)              │
│   ├── Top clinical risk drivers (SHAP)               │
│   └── Detected lifestyle signals                     │
│                                                      │
│ Page 3: Historical Context                           │
│   ├── Previous vs current comparison table           │
│   └── Risk trend trajectory chart (matplotlib)       │
│                                                      │
│ Page 4: AI Insights & Recommendations                │
│   ├── Personalized summary                           │
│   ├── Top model contributors                         │
│   └── Actionable recommendations table               │
│                                                      │
│ Page 5: Alerts & Disclaimers                         │
│   ├── Alert dispatch status                          │
│   ├── Critical alert banner (if applicable)          │
│   └── Medical & research disclaimers                 │
└──────────────────────────────────────────────────────┘
        │
        ▼
   bytes (PDF) → Streamlit download button
```

---

## Authentication & Authorization Flow

```
User → pages/login.py
        │
        ├── check_rate_limit("login", email)
        │   BLOCKED? → display cooldown timer
        │
        ├── AuthService.authenticate_user(email, password)
        │   │
        │   ├── _normalise_email() → lowercase
        │   ├── find_by_email() → User or None
        │   │   None? → verify_password(dummy_hash) → timing normalization
        │   │
        │   ├── verify_password(password, user.password_hash)
        │   │   bcrypt.checkpw() — constant-time
        │   │
        │   ├── SecurityLogger.log_authentication()
        │   │
        │   └── return user.to_safe_dict() or None
        │
        ├── record_failed_attempt() / reset_attempts()
        │
        └── session_manager.create_session(user)
            ├── secrets.token_hex(24) → session_token
            ├── st.session_state[_hg_user_id, _hg_role, _hg_name, ...]
            └── return token

Per-Page Guard (top of every protected page):
    require_authentication() → is_authenticated()? st.stop()
    require_role("ADMIN")   → get_current_role() != "ADMIN"? st.stop()
    require_reviewer()      → get_current_role() != "REVIEWER"? st.stop()

Session Timeout:
    check_session_timeout() called on every is_authenticated() check
    SESSION_INACTIVITY_LIMIT_SECONDS = 1800 (30 minutes)
    On timeout: clear_session(), log "session_expired"
```

---

## Security Architecture

### Defense Layers

1. **Authentication:** bcrypt password hashing (12 rounds), timing-attack mitigation (dummy hash verification), generic error messages (never reveals email existence)
2. **Authorization:** Server-side role enforcement via `require_role()`, IDOR protection via ownership checks (`user_owns_assessment()`)
3. **Session Security:** 30-minute inactivity timeout, session rotation on login, sensitive key purge on logout
4. **Rate Limiting:** Sliding window rate limiter (`InMemoryRateLimiter`), per-endpoint policies (login: 5/60s, assessment_create: 10/60s, report_generate: 10/60s)
5. **Input Validation:** XSS defense (`sanitize_text_for_display()`), HTML stripping, JSON payload validation, password strength policy (min 8 chars, letters+numbers, common password blacklist)
6. **Audit Logging:** 30+ event types across 7 categories, tamper-evident records, IP hashing (SHA-256), detail sanitization (redacts passwords/tokens/secrets)
7. **File Security:** Magic number validation, MIME type checks, 5MB upload limit, filename sanitization (path traversal prevention)
8. **HTTP Security Headers:** X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, CSP, Referrer-Policy
9. **Privacy:** Data minimization, PII protection, `assessment_result`/`pdf_report_bytes` purged from session on logout
10. **Credential Security:** Twilio tokens never logged, error messages sanitized, `SECRET_KEY_IS_DEFAULT` detection

### Security Configuration

Defined in `config/security.py`:
- `SESSION_TIMEOUT_MINUTES = 30`
- `RATE_LIMITS` dict with per-endpoint policies
- `MAX_UPLOAD_SIZE_BYTES = 5MB`
- `COMMON_PASSWORDS` blacklist
- `EVENT_CATEGORIES` and `EVENT_SEVERITIES` taxonomy
- `SECURITY_HEADERS` for HTTP response hardening

---

## Analytics & Monitoring Architecture

### Monitoring Pipeline

```
┌────────────────────────────────────────────┐
│            Monitoring Engine               │
│         src/analytics/                     │
│                                            │
│  ┌──────────────┐  ┌───────────────────┐   │
│  │ drift_       │  │ data_quality_     │   │
│  │ detection.py │  │ monitoring.py     │   │
│  │              │  │                   │   │
│  │ PSI, KS, JS  │  │ Missing rates     │   │
│  │ divergence   │  │ Duplicate rates   │   │
│  └──────┬───────┘  │ Out-of-range      │   │
│         │          └────────┬──────────┘   │
│         │                   │              │
│  ┌──────▼───────┐  ┌───────▼──────────┐   │
│  │ anomaly_     │  │ performance_     │   │
│  │ detection.py │  │ monitoring.py    │   │
│  │              │  │                  │   │
│  │ Z-score      │  │ Latency tracking │   │
│  │ Volume spike │  │ Error rate       │   │
│  └──────┬───────┘  └───────┬──────────┘   │
│         │                   │              │
│         ▼                   ▼              │
│  ┌─────────────────────────────────────┐   │
│  │ monitoring_events.py                │   │
│  │ → monitoring.db (monitoring_events) │   │
│  └─────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

**Drift Detection (`drift_detection.py`):**
- PSI (Population Stability Index): warning >0.10, critical >0.25
- KS test: alpha=0.05
- Jensen-Shannon divergence: warning >0.05, critical >0.15
- Prediction shift threshold: 0.10
- Minimum sample size: 30
- Reference window: 90 days, Current window: 30 days

**Monitoring Event Types:**
`DATA_DRIFT_DETECTED`, `PREDICTION_DRIFT_DETECTED`, `DATA_QUALITY_DEGRADED`, `MODEL_PERFORMANCE_DEGRADED`, `ANOMALY_DETECTED`, `SCHEMA_CHANGE_DETECTED`, `HIGH_ERROR_RATE`, `HIGH_LATENCY`, `LOW_CONFIDENCE`

**Severity Levels:** INFO, WARNING, HIGH, CRITICAL

**Model Status Lifecycle:** PRODUCTION → VALIDATION → RETIRED

---

## Configuration (`config/settings.py`)

Centralized configuration loaded from environment variables (`.env` in development):

- **Environment:** `ENVIRONMENT` (development/testing/production)
- **Risk weights:** `CLINICAL_WEIGHT=0.70`, `LIFESTYLE_WEIGHT=0.30`
- **Risk thresholds:** LOW<60%, MODERATE 60-75%, HIGH 75-85%, CRITICAL>85%
- **Database paths:** 7 SQLite DBs with configurable paths via env vars
- **Twilio:** Account SID, auth token, phone numbers (env vars)
- **Logging:** Level, directory, file rotation (10MB, 5 backups)
- **Input limits:** `LIFESTYLE_TEXT_MAX_LENGTH=2000`, `PASSWORD_MIN_LENGTH=8`
- **Rate limits:** `LOGIN_MAX_ATTEMPTS=5`, `LOGIN_COOLDOWN_SECONDS=60`
- **Retentions:** `REPORT_RETENTION_DAYS=30`, `TEMP_FILE_RETENTION_HOURS=24`

---

## Directory Structure

```
HeartGuard/
├── app.py                    # Streamlit entry point
├── config/
│   ├── settings.py           # Centralized configuration
│   ├── security.py           # Security policies
│   └── monitoring.py         # Monitoring thresholds
├── pages/                    # Streamlit page routes (16 files)
├── src/
│   ├── auth/                 # Authentication & authorization
│   ├── ml/                   # ML models & training
│   ├── risk_engine/          # Multimodal risk calculation
│   ├── explainability/       # SHAP explainability
│   ├── nlp/                  # Lifestyle text analysis
│   ├── alerts/               # Emergency SMS alerts
│   ├── reports/              # PDF report generation
│   ├── review/               # Professional review workflow
│   ├── security/             # Security infrastructure
│   ├── analytics/            # Analytics & monitoring
│   ├── recommendations/      # AI recommendations
│   ├── data/                 # Data pipeline
│   ├── ui/                   # Streamlit UI components
│   ├── health/               # System health checks
│   ├── evaluation/           # Model evaluation (14 modules)
│   ├── startup/              # Pre-flight validation
│   └── utils/                # Logger, exceptions, validators
├── models/                   # Trained model artifacts (.pkl)
├── data/                     # Datasets & SQLite databases
│   ├── raw/                  # Source datasets
│   ├── processed/            # Preprocessed data
│   ├── auth/                 # heartguard_auth.db
│   ├── security/             # audit.db
│   ├── assessments/          # assessments.db, reviews.db, recommendations.db
│   ├── alerts/               # alerts.db
│   ├── evaluations/          # evaluation.db
│   └── monitoring/           # monitoring.db
├── reports/                  # Generated reports & training artifacts
├── logs/                     # Application logs
├── notebooks/                # Jupyter notebooks
├── assets/                   # Static assets
├── tests/                    # Test suite
├── scripts/                  # Utility scripts
├── Dockerfile                # Container build
└── requirements.txt          # Python dependencies
```
