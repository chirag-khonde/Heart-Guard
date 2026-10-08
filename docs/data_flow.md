# HeartGuard — Data Flow Documentation

> Traces the complete data flow through every major pathway in the application.

---

## 1. User Input → Validation → Preprocessing

### Clinical Data Entry

```
pages/risk_assessment.py
    │
    ├── st.number_input() / st.selectbox() for 11 clinical features:
    │   age, sex, chest_pain_type, resting_bp, cholesterol,
    │   fasting_blood_sugar, resting_ecg, max_heart_rate,
    │   exercise_angina, st_depression, num_major_vessels
    │
    ▼
src/risk_engine/risk_validation.py::validate_clinical_input(clinical_data)
    │
    ├── Validates each field is present and within biological bounds:
    │   age: (1, 150), resting_bp: (1, 300), cholesterol: (1, 800),
    │   max_heart_rate: (1, 300), st_depression: (0, 20),
    │   num_major_vessels: (0, 4)
    │
    ├── Validates binary features (sex, fasting_blood_sugar, exercise_angina) ∈ {0, 1}
    │
    └── Returns validated_clinical dict (or raises ValueError)
```

### Lifestyle Text Entry

```
pages/risk_assessment.py  OR  pages/lifestyle_analyzer.py
    │
    ├── st.text_area() → lifestyle_text (max 2000 chars)
    │
    ▼
src/risk_engine/risk_validation.py::validate_lifestyle_input(lifestyle_text)
    │
    ├── src/security/input_validator.py::validate_lifestyle_text_length(text)
    │   Rejects empty, blank, or >2000 character input
    │
    └── Returns validated text string
```

### User Registration

```
pages/register.py
    │
    ├── st.text_input() → name, email, password, confirm_password
    │
    ▼
src/auth/auth_service.py::register_user(name, email, password, confirm_password)
    │
    ├── _validate_name(name) → non-empty, ≤100 chars
    ├── _validate_email_format(email) → RFC-5322 regex, ≤254 chars
    ├── src/security/input_validator.py::validate_password_strength(password)
    │   ├── ≥8 chars, ≤128 chars
    │   ├── Not in COMMON_PASSWORDS blacklist
    │   ├── Must contain letters and numbers
    │   └── Raises ValueError on failure
    ├── password == confirm_password check
    ├── _normalise_email(email) → lowercase, strip
    ├── hash_password(password) → bcrypt hash (12 rounds)
    ├── src/auth/user_repository.py::create_user() → parameterized INSERT
    │   (raises ValueError on duplicate email)
    ├── SecurityLogger.log_authentication(success=True)
    └── Returns user.to_safe_dict()
```

### User Login

```
pages/login.py
    │
    ├── src/security/rate_limiter.py::check_rate_limit("login", email)
    │   BLOCKED? → display cooldown timer, st.stop()
    │
    ├── src/security/rate_limiter.py::is_rate_limited() → session-level check
    │
    ▼
src/auth/auth_service.py::authenticate_user(email, password, ip_address)
    │
    ├── _normalise_email(email) → lowercase
    ├── find_by_email(clean_email, db_path) → User or None
    │   ├── User found but not active → verify_password(dummy_hash) → return None
    │   ├── User not found → verify_password(dummy_hash) → timing normalization
    │   └── Returns None on both paths (generic error)
    │
    ├── verify_password(password, user.password_hash)
    │   └── bcrypt.checkpw() — constant-time comparison
    │
    ├── SecurityLogger.log_authentication(success/failure)
    │
    └── Returns user.to_safe_dict() or None
        │
        ▼ (on success)
src/auth/session_manager.py::create_session(user)
    ├── clear_session() → purge existing state
    ├── secrets.token_hex(24) → session_token
    ├── Store in st.session_state:
    │   _hg_user_id, _hg_role, _hg_name,
    │   _hg_authenticated, _hg_session_token, _hg_last_activity
    └── Returns session_token
```

---

## 2. Preprocessing → Model Prediction → Risk Calculation

### Clinical ML Prediction

```
src/risk_engine/multimodal_risk.py::MultimodalRiskEngine.assess()
    │
    ├── 1. _ensure_loaded()
    │   ├── ModelRegistry.get() → loads model from models/*.pkl
    │   ├── load_preprocessor(MODEL_DIRECTORY / "preprocessor.pkl")
    │   │   └── ColumnTransformer with numerical (StandardScaler) and
    │   │       categorical (OneHotEncoder) pipelines
    │   ├── Load feature names from models/feature_names.json
    │   └── Initialize LifestyleAnalyzer()
    │
    ├── 2. _preprocess_clinical_data(validated_clinical)
    │   ├── pd.DataFrame([clinical_dict])
    │   ├── preprocessor.transform(df_row) → raw_transformed
    │   ├── Columns from preprocessor.get_feature_names_out()
    │   ├── Fill missing dummy columns with 0.0
    │   └── Return X_df[feature_names] aligned to model's expected space
    │
    ├── 3. Clinical ML prediction
    │   ├── model.predict(X_transformed) → y_pred (0 or 1)
    │   ├── model.predict_proba(X_transformed) → clinical_probability (0.0-1.0)
    │   ├── clinical_risk = clinical_probability * 100.0
    │   └── validate_clinical_risk(clinical_risk) → bounded [0, 100]
    │
    └── Returns clinical_risk (float, 0-100%)
```

### Lifestyle NLP Analysis

```
src/risk_engine/multimodal_risk.py::MultimodalRiskEngine.assess()
    │
    ├── LifestyleAnalyzer.analyze(validated_lifestyle)
    │   │
    │   ├── normalize_text(raw_text)
    │   │   ├── unicodedata.normalize("NFKD") → unicode normalization
    │   │   ├── .lower() → lowercase
    │   │   ├── remove_unnecessary_punctuation() → clean non-alphanumeric
    │   │   └── normalize_whitespace() → collapse spaces
    │   │
    │   ├── tokenize_text(raw_text)
    │   │   └── NLTK word_tokenize with regex fallback
    │   │
    │   ├── Run 6 detectors on normalized text:
    │   │   │
    │   │   ├── _detect_smoking(text)
    │   │   │   ├── Match primary_keywords + variation_keywords
    │   │   │   │   (smoke, smoking, cigarette, tobacco, nicotine, cigar, vape...)
    │   │   │   ├── _is_phrase_negated(text, start, end, window=35)
    │   │   │   │   Check preceding 35 chars for NEGATION_TERMS
    │   │   │   │   (no, not, never, don't, stopped, quit, avoid...)
    │   │   │   └── Returns (matched_terms, evidence_snippets)
    │   │   │
    │   │   ├── _detect_physical_inactivity(text)
    │   │   │   ├── Check POSITIVE_EXERCISE_TERMS first
    │   │   │   │   (exercise regularly, work out, gym, active lifestyle...)
    │   │   │   ├── Check negated exercise patterns via regex
    │   │   │   ├── Check explicit inactivity keywords
    │   │   │   │   (sedentary, desk job, mostly sitting, couch potato...)
    │   │   │   └── Returns ([], []) if unnegated positive exercise found
    │   │   │
    │   │   ├── _detect_unhealthy_diet(text)
    │   │   │   ├── Match keywords: oily food, junk, fast food, fried...
    │   │   │   └── Negation-aware matching
    │   │   │
    │   │   ├── _detect_poor_sleep(text)
    │   │   │   ├── Numeric pattern: "sleep X hours" where X < 6
    │   │   │   └── Symptom keywords: insomnia, poor sleep, sleep deprivation...
    │   │   │
    │   │   ├── _detect_family_history(text)
    │   │   │   └── Keywords: family history, heart attack, cardiac...
    │   │   │
    │   │   └── _detect_alcohol_use(text)
    │   │       ├── Explicit alcoholic terms: alcohol, beer, wine, liquor...
    │   │       ├── Contextual "drink" with disambiguation:
    │   │       │   ├── NON_ALCOHOLIC_DRINKS exclusion
    │   │       │   │   (water, milk, tea, coffee, juice, soda...)
    │   │       │   └── Look-ahead for alcohol qualifiers
    │   │       └── Returns (matched_terms, evidence_snippets)
    │   │
    │   ├── calculate_lifestyle_score(detected_factors)
    │   │   ├── Sum unique category risk_points:
    │   │   │   smoking=25, family_history=20, unhealthy_diet=18,
    │   │   │   physical_inactivity=15, poor_sleep=12, alcohol_use=10
    │   │   ├── Cap at MAX_LIFESTYLE_SCORE (100)
    │   │   └── Returns int score
    │   │
    │   ├── get_risk_category(score)
    │   │   ├── 0-29:  LOW
    │   │   ├── 30-59: MODERATE
    │   │   ├── 60-84: HIGH
    │   │   └── 85-100: CRITICAL
    │   │
    │   ├── get_top_lifestyle_risk_factors(detected_factors, top_n=3)
    │   │
    │   └── Returns structured result dict:
    │       raw_text, normalized_text, tokens, lifestyle_score,
    │       risk_category, detected_risk_factors, top_risk_factors,
    │       score_breakdown, summary, disclaimer
    │
    └── lifestyle_risk = float(result["lifestyle_score"])
        validate_lifestyle_risk(lifestyle_risk) → bounded [0, 100]
```

### Multimodal Risk Combination

```
src/risk_engine/multimodal_risk.py::calculate_multimodal_risk(clinical_risk, lifestyle_risk)
    │
    ├── validate_weights(0.70, 0.30)
    ├── validate_clinical_risk(clinical_risk) → bounded [0, 100]
    ├── validate_lifestyle_risk(lifestyle_risk) → bounded [0, 100]
    │
    ├── overall_risk = (clinical_risk × 0.70) + (lifestyle_risk × 0.30)
    │
    └── validate_overall_risk(overall_risk) → bounded [0, 100]
```

---

## 3. Risk Calculation → SHAP Explanation → Recommendations

### SHAP Explanation Generation

```
src/risk_engine/multimodal_risk.py::MultimodalRiskEngine.assess()
    │
    ├── if include_shap:
    │   │
    │   ├── src/explainability/service.py::SHAPExplainerService()
    │   │   │
    │   │   ├── _ensure_loaded()
    │   │   │   ├── load_explainable_model()
    │   │   │   │   └── reads reports/best_model.json → loads model_name.pkl
    │   │   │   ├── load_feature_names()
    │   │   │   │   └── reads models/feature_names.json
    │   │   │   ├── load_training_data()
    │   │   │   │   └── reads data/processed/cleveland_train.csv (242 samples)
    │   │   │   ├── create_shap_explainer(model, training_data)
    │   │   │   │   ├── _is_tree_model(model)? → TreeExplainer
    │   │   │   │   ├── _is_linear_model(model)? → LinearExplainer
    │   │   │   │   └── else → KernelExplainer (100-sample background)
    │   │   │   └── save_explainer_metadata()
    │   │   │
    │   │   └── explain_patient(patient_data, save_artifacts=False)
    │   │       │
    │   │       ├── _preprocess_input(X_row)
    │   │       │   └── preprocessor.transform() → align to model features
    │   │       │
    │   │       ├── model.predict(X_transformed) → prediction
    │   │       ├── model.predict_proba(X_transformed) → probability
    │   │       │
    │   │       ├── calculate_shap_values(explainer, X_transformed)
    │   │       │   ├── explainer.shap_values(X) → raw_output
    │   │       │   ├── Normalize to (n_samples, n_features) for class 1
    │   │       │   └── _extract_base_values() → base_values per sample
    │   │       │
    │   │       ├── get_feature_contributions(shap_row, feature_names)
    │   │       │   ├── Map SHAP values to feature names
    │   │       │   ├── Classify direction: increases_risk / decreases_risk / neutral
    │   │       │   └── Sort by absolute_importance descending
    │   │       │
    │   │       ├── get_local_explanation(shap_row, base_val, features, X, pred, prob)
    │   │       │   └── Structured dict with base_value, prediction, probability, features
    │   │       │
    │   │       ├── generate_human_readable_summary(contributions, patient_values, pred, prob)
    │   │       │   └── Multi-line text with top 3 positive/negative contributors
    │   │       │
    │   │       └── get_top_risk_factors(shap_row, feature_names, top_n=3)
    │   │           └── Filter positive SHAP values only (increasing risk)
    │   │
    │   └── clinical_explanation = {
    │       base_value, top_features[:5], top_risk_factors,
    │       human_readable_summary, waterfall_plot
    │   }
    │
    └── Result assembled with clinical_explanation included
```

### Recommendations Generation

```
src/recommendations/recommendation_service.py::RecommendationService.get_or_create_insights()
    │
    ├── Authorization: user_id must own assessment (unless staff override)
    │
    ├── Check recommendations.db for existing insights
    │   ├── Found? → return cached AssessmentInsights
    │   └── Not found? → generate
    │
    ├── RecommendationEngine.generate_insights(assessment_data)
    │   ├── Analyze clinical_risk, lifestyle_risk, overall_risk
    │   ├── Analyze detected lifestyle factors
    │   ├── Analyze top clinical SHAP factors
    │   ├── Apply recommendation_rules.py rule definitions
    │   └── Generate:
    │       ├── summary_text (personalized narrative)
    │       ├── top_factors (up to 4 feature explanations)
    │       └── recommendations (up to 6 actionable guidance items)
    │           each with: title, description, category, priority
    │
    ├── Persist to recommendations.db
    │   └── INSERT INTO recommendations (recommendation_id, assessment_id, ...)
    │
    └── Return AssessmentInsights object
```

---

## 4. Results → Storage → Dashboard

### Assessment Storage

```
pages/risk_assessment.py
    │
    ├── MultimodalRiskEngine.assess() → risk_result
    │
    ├── src/analytics/history_service.py::HistoryService.create_assessment()
    │   │
    │   ├── init_assessment_db() → ensure schema exists
    │   │
    │   ├── Generate assessment_id (uuid4 hex[:8])
    │   │
    │   ├── Insert into assessments table:
    │   │   assessment_id, user_id, created_at, clinical_risk,
    │   │   lifestyle_risk, overall_risk, risk_category,
    │   │   recommendation, model_version, narrative_summary,
    │   │   alert_status, top_clinical_factors_json (JSON),
    │   │   lifestyle_factors_json (JSON), clinical_data_json (JSON)
    │   │
    │   └── Return Assessment object
    │
    └── Store in st.session_state["assessment_result"] for immediate display
```

### Dashboard Retrieval

```
pages/dashboard.py
    │
    ├── src/analytics/analytics_service.py::AnalyticsService
    │   │
    │   ├── calculate_user_statistics(user_id)
    │   │   ├── HistoryService.get_user_assessments(user_id)
    │   │   ├── Count total, compute average risk, count critical
    │   │   └── Return {total_assessments, latest_risk, average_risk, ...}
    │   │
    │   ├── get_user_recent_assessments(user_id, limit=5)
    │   │   ├── HistoryService.get_user_assessments(user_id, limit=5)
    │   │   ├── Attach review_status from ReviewService
    │   │   └── Return list of assessment dicts
    │   │
    │   └── get_category_distribution(user_id)
    │       ├── SQL GROUP BY risk_category
    │       └── Return {category: count} dict
    │
    └── Render metrics, charts, tables in Streamlit
```

### History & Trends

```
pages/history.py
    │
    ├── HistoryService.get_user_assessments(user_id, sort_order="desc")
    │   └── SELECT * FROM assessments WHERE user_id=? ORDER BY created_at DESC
    │
    ├── TrendService.get_risk_trends(user_id)
    │   ├── Fetch all user assessments
    │   └── Build trend list: [{date, overall_risk, clinical_risk, lifestyle_risk}]
    │
    └── TrendService.compare_assessments(latest, previous)
        ├── Compute delta for overall_risk, clinical_risk, lifestyle_risk
        ├── Detect category changes
        └── Return comparison dict with interpretation text
```

---

## 5. Alerts → SMS Notification

```
pages/risk_assessment.py
    │
    ├── risk_result = MultimodalRiskEngine.assess()
    │
    ├── src/alerts/alert_manager.py::AlertManager.process_risk_result(risk_result)
    │   │
    │   ├── Extract overall_risk from risk_result["combined"]["risk"]
    │   │
    │   ├── alert_triggered = overall_risk > CRITICAL_THRESHOLD (85.0)?
    │   │   NO → return NOT_TRIGGERED status
    │   │   YES → continue
    │   │
    │   ├── alerts_enabled check (DEMO_MODE = not ALERTS_ENABLED)
    │   │   NO → record "DISABLED" alerts, return demo result
    │   │   YES → continue
    │   │
    │   ├── build_critical_doctor_message(overall_risk, patient_name, age)
    │   ├── build_critical_emergency_message(overall_risk, patient_name, age)
    │   │
    │   ├── Doctor SMS:
    │   │   ├── is_alert_already_sent(assessment_id, "doctor")? → skip
    │   │   ├── TwilioSMSService.send_sms(doctor_phone, message)
    │   │   │   ├── validate_phone_number(to) → E.164 format
    │   │   │   ├── client.messages.create(body, from_, to)
    │   │   │   └── Return {success, message_sid, status}
    │   │   └── record_alert(assessment_id, risk_score, ..., status)
    │   │
    │   ├── Emergency Contact SMS:
    │   │   ├── is_alert_already_sent(assessment_id, "emergency_contact")? → skip
    │   │   ├── TwilioSMSService.send_sms(emergency_phone, message)
    │   │   └── record_alert(assessment_id, risk_score, ..., status)
    │   │
    │   └── Return delivery status:
    │       alert_triggered, notification_status (SUCCESS/PARTIAL_SUCCESS/FAILED),
    │       sms_attempted, demo_mode, recipients, sms_preview
    │
    └── Display alert result in UI
```

### Alert History Persistence

```
src/alerts/alert_history.py::record_alert()
    │
    ├── Insert into alerts.db:
    │   assessment_id, risk_score, risk_level,
    │   recipient_type (doctor/emergency_contact/test),
    │   recipient_phone, status (SUCCESS/FAILED/DISABLED),
    │   message_sid, error_message, timestamp
    │
    └── Idempotency check:
        is_alert_already_sent(assessment_id, recipient_type)
        └── SELECT WHERE assessment_id=? AND recipient_type=? AND status='SUCCESS'
```

---

## 6. Reports → PDF Generation

```
pages/history.py
    │
    ├── User clicks "Generate PDF Report"
    │
    ▼
src/reports/report_generator.py::ReportGenerator.generate_assessment_report(assessment_id, user_id)
    │
    ├── 1. Authorization
    │   └── HistoryService.user_owns_assessment(user_id, assessment_id)
    │       └── SELECT WHERE assessment_id=? AND user_id=?
    │           Different user? → raise PermissionError
    │
    ├── 2. Data retrieval
    │   ├── HistoryService.get_assessment_by_id(assessment_id, user_id)
    │   ├── HistoryService.get_user_assessments(user_id, sort_order="desc")
    │   │   → find previous_assessment for comparison
    │   ├── TrendService.get_risk_trends(user_id)
    │   ├── TrendService.compare_assessments(assessment, previous_assessment)
    │   └── RecommendationService.get_or_create_insights(assessment_id, user_id)
    │
    ├── 3. Build PDF (ReportLab SimpleDocTemplate)
    │   │
    │   ├── PAGE 1: Executive Summary
    │   │   ├── Title, subtitle, HR
    │   │   ├── Metadata table (ID, date, model, alert status)
    │   │   ├── Risk callout (overall_risk %, category, recommended action)
    │   │   └── Narrative summary paragraph
    │   │
    │   ├── PAGE 2: Risk Components & Explainability
    │   │   ├── Component breakdown table:
    │   │   │   Clinical ML: raw_score × 70% = weighted_contribution
    │   │   │   Lifestyle NLP: raw_score × 30% = weighted_contribution
    │   │   │   Combined: overall_risk
    │   │   ├── Top clinical risk drivers (SHAP) table:
    │   │   │   assessment.get_top_clinical_factors()[:5]
    │   │   │   → rank, clinical_label, shap_value
    │   │   └── Detected lifestyle signals table:
    │   │       assessment.get_lifestyle_factors()[:5]
    │   │       → display_name, severity, risk_points
    │   │
    │   ├── PAGE 3: Historical Context
    │   │   ├── Previous vs current comparison table
    │   │   │   → overall_risk, clinical_risk, lifestyle_risk, category
    │   │   ├── Trend interpretation text
    │   │   └── Risk trend trajectory chart:
    │   │       _render_trend_chart_to_image(trends)
    │   │       → matplotlib line chart (overall, clinical, lifestyle)
    │   │       → io.BytesIO PNG image
    │   │
    │   ├── PAGE 4: AI Insights & Recommendations
    │   │   ├── Personalized summary text
    │   │   ├── Top model contributors (up to 4)
    │   │   └── Recommendations table (up to 6):
    │   │       priority, category, title + description
    │   │
    │   └── PAGE 5: Alerts & Disclaimers
    │       ├── Alert dispatch status table
    │       ├── Critical alert banner (if CRITICAL)
    │       └── Medical & research disclaimers
    │
    ├── 4. Build with NumberedCanvas (page numbers)
    │
    └── 5. Return buffer.getvalue() → bytes (PDF)
        │
        ▼ (back in Streamlit)
    st.download_button("Download PDF", data=pdf_bytes, ...)
```

---

## 7. Review → Professional Review Workflow

### Reviewer Claims Assessment

```
pages/review.py
    │
    ├── require_reviewer() → enforce REVIEWER role
    │
    ├── ReviewService.get_pending_assessments()
    │   │
    │   ├── Cross-DB query (ATTACH DATABASE):
    │   │   SELECT a.* FROM assessments a
    │   │   LEFT JOIN rdb.professional_reviews r
    │   │   ON a.assessment_id = r.assessment_id
    │   │   WHERE r.review_id IS NULL
    │   │   ORDER BY a.created_at DESC
    │   │
    │   └── Returns assessments with no review record
    │
    ├── Reviewer clicks "Claim Assessment"
    │
    ▼
ReviewService.create_review(reviewer_id, assessment_id)
    │
    ├── Verify assessment exists (SELECT 1 FROM assessments)
    │   Not found? → raise ValueError
    │
    ├── Idempotency: check for existing review
    │   Exists? → return existing review
    │
    ├── INSERT INTO professional_reviews:
    │   review_id (uuid4 hex[:12]),
    │   assessment_id, reviewer_id,
    │   created_at, updated_at,
    │   review_status = 'PENDING',
    │   professional_notes = '',
    │   follow_up_required = False,
    │   urgency_flag = False
    │
    └── Returns ProfessionalReview object
```

### Reviewer Updates Review

```
pages/review.py
    │
    ├── ReviewService.get_assessment_with_review(assessment_id)
    │   ├── Fetch assessment from assessments.db (READ-ONLY)
    │   └── Fetch review from reviews.db
    │
    ├── Reviewer fills in form:
    │   ├── review_status (dropdown: IN_REVIEW, ACCEPTED, MODIFIED, REJECTED)
    │   ├── professional_notes (textarea, max length enforced)
    │   ├── follow_up_required (checkbox)
    │   └── urgency_flag (checkbox)
    │
    ▼
ReviewService.update_review(review_id, reviewer_id, ...)
    │
    ├── Ownership check: existing.reviewer_id != reviewer_id?
    │   → raise PermissionError
    │
    ├── Validate review_status ∈ REVIEW_STATUSES
    ├── Validate professional_notes ≤ PROFESSIONAL_NOTES_MAX_LENGTH
    │
    ├── UPDATE professional_reviews SET ... WHERE review_id=? AND reviewer_id=?
    │   (enforces both review_id and reviewer_id in WHERE clause)
    │
    └── Returns updated ProfessionalReview
```

### Admin Views All Reviews

```
pages/admin.py
    │
    ├── ReviewService.get_all_reviews()
    │   └── SELECT * FROM professional_reviews ORDER BY updated_at DESC
    │
    ├── ReviewService.get_all_assessments_with_review_status()
    │   ├── Cross-DB LEFT JOIN query
    │   ├── Priority sort: urgency_flag first, then created_at DESC
    │   └── Returns unified list with assessment + review fields
    │
    └── ReviewService.get_review_statistics()
        ├── GROUP BY review_status → status_counts
        ├── SUM(follow_up_required) → follow_up_total
        ├── SUM(urgency_flag) → urgency_total
        ├── Count unassigned pending assessments
        └── Return aggregated statistics dict
```

---

## 8. Analytics → Monitoring → Drift Detection

### Drift Detection Pipeline

```
pages/model_monitoring.py
    │
    ├── src/analytics/drift_detection.py
    │   │
    │   ├── Load reference data (training set)
    │   │   └── data/processed/cleveland_train.csv
    │   │
    │   ├── Load current data (recent assessments)
    │   │   └── SELECT clinical_data_json FROM assessments
    │   │       WHERE created_at >= datetime('now', '-30 days')
    │   │
    │   ├── For each NUMERICAL_FEATURE:
    │   │   ├── _psi(reference, current) → PSI value
    │   │   │   ├── Bin both distributions (10 bins)
    │   │   │   ├── Clip histograms ≥ 1e-6
    │   │   │   └── Sum((current - reference) × log(current/reference))
    │   │   │
    │   │   ├── _ks_statistic(reference, current) → (stat, p_value)
    │   │   │   └── scipy.stats.ks_2samp()
    │   │   │
    │   │   └── Status determination:
    │   │       PSI > 0.25 → CRITICAL (DRIFT_DETECTED)
    │   │       PSI > 0.10 → WARNING
    │   │       KS p < 0.05 → WARNING
    │   │       else → HEALTHY
    │   │
    │   ├── For each CATEGORICAL_FEATURE:
    │   │   ├── _categorical_psi(ref_counts, cur_counts)
    │   │   └── Chi-square test
    │   │
    │   ├── Prediction drift:
    │   │   ├── Compare prediction distributions
    │   │   └── DRIFT_PREDICTION_SHIFT_THRESHOLD = 0.10
    │   │
    │   └── Return drift_report dict:
    │       status, feature_drift, prediction_drift, metrics
    │
    ├── src/analytics/data_quality_monitoring.py
    │   ├── Missing rate: DQ_MISSING_RATE_WARNING=0.05, CRITICAL=0.20
    │   ├── Duplicate rate: DQ_DUPLICATE_RATE_WARNING=0.02, CRITICAL=0.10
    │   ├── Out-of-range: DQ_OUT_OF_RANGE_WARNING=0.03
    │   └── Min records: DQ_MIN_RECORDS=10
    │
    ├── src/analytics/anomaly_detection.py
    │   ├── Z-score threshold: ANOMALY_ZSCORE_THRESHOLD=3.0
    │   ├── Volume spike: ANOMALY_VOLUME_SPIKE_FACTOR=2.0
    │   ├── Latency spike: ANOMALY_LATENCY_SPIKE_FACTOR=3.0
    │   └── Error rate: ANOMALY_ERROR_RATE_THRESHOLD=0.05
    │
    ├── src/analytics/performance_monitoring.py
    │   ├── PERF_LATENCY_WARNING_MS=5000.0, CRITICAL=10000.0
    │   ├── PERF_ERROR_RATE_WARNING=0.05, CRITICAL=0.15
    │   └── PERF_CACHE_TTL_SECONDS=300
    │
    └── Event creation:
        src/analytics/monitoring_events.py::create_event()
        └── INSERT INTO monitoring_events:
            event_id, timestamp, event_type, severity,
            component, status, metric_name, metric_value,
            threshold_value, message, details_json
```

### Analytics Dashboard

```
pages/analytics_dashboard.py (ADMIN only)
    │
    ├── AnalyticsService.get_admin_aggregated_analytics()
    │   ├── SQL aggregations across entire assessments table:
    │   │   COUNT(*), COUNT(DISTINCT user_id), AVG(overall_risk)
    │   ├── Category distribution (GROUP BY risk_category)
    │   ├── Model version distribution
    │   ├── Alert status distribution
    │   └── Review statistics (from ReviewService)
    │
    ├── src/analytics/prediction_analytics.py
    │   └── Prediction distribution analysis
    │
    ├── src/analytics/risk_analytics.py
    │   └── Risk score distribution analysis
    │
    ├── src/analytics/explainability_analytics.py
    │   └── SHAP value distribution tracking
    │
    ├── src/analytics/alert_analytics.py
    │   └── Alert delivery statistics
    │
    └── src/analytics/security_analytics.py
        └── Security event aggregation (from audit.db)
```

### Patient Analytics

```
pages/patient_analytics.py
    │
    ├── AnalyticsService.calculate_user_statistics(user_id)
    │   └── total_assessments, latest_risk, average_risk, critical_count
    │
    ├── AnalyticsService.get_category_distribution(user_id)
    │   └── {risk_category: count} for the user
    │
    ├── TrendService.get_risk_trends(user_id)
    │   └── [{date, overall_risk, clinical_risk, lifestyle_risk}]
    │
    └── Charts rendered via src/ui/charts.py
        ├── Risk gauge chart
        ├── Trend line chart
        └── Category distribution pie chart
```

---

## Data Flow Summary Diagram

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐
│  User Input │───►│  Validation  │───►│ Preprocessing  │
│ (Form/Text) │    │  (sanitize)  │    │ (transform)    │
└─────────────┘    └──────────────┘    └───────┬────────┘
                                               │
                    ┌──────────────────────────┘
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                     MULTIMODAL RISK ENGINE                       │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────────┐  │
│  │ Clinical ML  │    │ Lifestyle    │    │ 70/30 Weighted     │  │
│  │ Prediction   │    │ NLP Analysis │───►│ Combination        │  │
│  │ (model.pkl)  │    │ (lexicon)    │    │                    │  │
│  └──────┬───────┘    └──────┬───────┘    └─────────┬──────────┘  │
│         │                   │                      │             │
│         ▼                   ▼                      ▼             │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────────┐  │
│  │ SHAP         │    │ Risk         │    │ Risk Category      │  │
│  │ Explainability│   │ Categories   │    │ & Recommendations  │  │
│  └──────┬───────┘    └──────┬───────┘    └─────────┬──────────┘  │
└─────────┼───────────────────┼──────────────────────┼─────────────┘
          │                   │                      │
          ▼                   ▼                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                     OUTPUT LAYER                                  │
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │Assessment│ │  SHAP    │ │  PDF     │ │  SMS     │ │Review  │ │
│  │ Storage  │ │ Plots    │ │ Report   │ │  Alert   │ │ Record │ │
│  │(assess.  │ │ (reports/│ │(ReportLab│ │ (Twilio) │ │(reviews│ │
│  │  .db)    │ │ figures/)│ │  bytes)  │ │          │ │  .db)  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                 MONITORING LAYER                             │ │
│  │  Drift Detection → Data Quality → Anomaly Detection → Events│ │
│  │  (PSI, KS, JS)   (missing/dup)  (z-score)    (monitoring.db)│ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Key Data Stores Reference

| Store | Location | Contents |
|---|---|---|
| `heartguard_auth.db` | `data/auth/` | User accounts (id, name, email, password_hash, role) |
| `audit.db` | `data/security/` | Security audit trail (30+ event types, 7 categories) |
| `assessments.db` | `data/assessments/` | Assessment records with clinical/lifestyle JSON blobs |
| `reviews.db` | `data/assessments/` | Professional review records |
| `recommendations.db` | `data/assessments/` | AI-generated insights and recommendations |
| `alerts.db` | `data/alerts/` | SMS alert delivery history |
| `monitoring.db` | `data/monitoring/` | Drift, quality, anomaly, and performance events |
| `models/*.pkl` | `models/` | Trained model artifacts |
| `reports/*.json` | `reports/` | Model results, best model, training summaries |
| `reports/figures/*.png` | `reports/figures/` | SHAP plots, confusion matrices, ROC curves |
