# HeartGuard — Dashboard, Visualization & User Experience (Phase 12)

## Overview

Phase 12 transforms HeartGuard's user interface and visualization capabilities into
a professional, modern, responsive AI healthcare research platform. The system operates
as an academic research prototype with strict separation between experimental AI risk estimations
and professional human clinical reviews.

---

## 1. Patient Dashboard (`pages/dashboard.py`)

The patient dashboard is the central entry point for authenticated patient users.
It renders an overview of personal cardiovascular health assessments:

- **Welcome Banner**: Displays personalized greeting (`Welcome back, [Name].`), current role, and prominent academic/research prototype disclaimer.
- **Top Metric Cards (KPI Row)**:
  - **Model-Based Risk**: Latest calculated multimodal risk score (e.g. `72.4%`).
  - **Risk Category**: Standardized tier (`LOW`, `ELEVATED`, `HIGH`, `CRITICAL`) with text and icon badges.
  - **Total Assessments**: Number of assessments completed by the authenticated user.
  - **Professional Review Status**: Review outcome (`Pending`, `In Review`, `Reviewed`, `Follow-up Recommended`, `Not Reviewed`).
  - **Latest Alert Status**: Emergency notification state (`Not Triggered`, `Triggered`, `Alert Sent`, `Alert Failed`).
- **Latest Assessment Summary**: Detailed summary card with assessment date, recommendations, comparison against previous evaluation (percentage-point deltas), and direct links to history and PDF reports.
- **Risk Component Decomposition**: Breakdown cards and Altair comparative bar chart illustrating the weighted contribution of Clinical ML (70%) and Lifestyle NLP (30%).
- **Chronological Risk Trend**: Interactive Altair line chart plotting historical multimodal risk trajectories over time on a bounded 0–100% scale.
- **Top Model Factors (Explainable AI / SHAP)**: Horizontal feature contribution bar chart identifying key statistical drivers of the model's output without diagnostic causality claims.
- **Structured Lifestyle Insights**: Visual indicators for detected lifestyle factors (physical activity, sleep, stress, smoking, diet, alcohol, sedentary habits).
- **Recent Assessments**: Tabular view of the 5 most recent assessments with a link to full history.
- **Quick Actions**: One-click shortcuts for starting new assessments, viewing history, and generating reports.

---

## 2. Reviewer Dashboard & Portal (`pages/review.py`)

A dedicated portal for authorized `REVIEWER`-role clinical professionals:

- **Review Queue KPIs**: Top metrics displaying Pending Reviews, In Review, Reviewed, Follow-Up Recommended, and Total Assigned.
- **Review Queue Visual Distribution**: Expandable Altair distribution chart illustrating review status allocations across the platform.
- **Queue Table**: Priority-sorted table highlighting high-urgency and follow-up flags.
- **Assessment Inspection & Explainability**: Side-by-side read-only inspection of AI risk scores, risk component breakdowns, SHAP feature importance charts, and structured lifestyle habits.
- **Professional Review Workspace**: Form for recording structured clinical observations, updating status, and setting urgency and follow-up flags.

---

## 3. Admin Dashboard (`pages/admin.py`)

System-wide administrative interface providing high-level operational visibility:

- **User Statistics**: Aggregate counts for Patient accounts, Reviewer accounts, Admin accounts, and total active users.
- **Assessment & Review KPIs**: Total assessments conducted, distinct active patients, system mean risk score, total reviews, and pending queue size.
- **Visual Distribution Charts**:
  - **Risk Category Distribution**: Visual bar chart of assessments across risk tiers (`Low`, `Elevated`, `High`, `Critical`).
  - **Review Distribution**: Breakdown of professional review outcomes.
  - **Alert Dispatch Statistics**: Outcome breakdown of emergency notification attempts.
  - **Model Version Usage**: Traceability breakdown of active model versions.
- **User Directory & Security Audit Log**: Audited view of system accounts and recent security events.

---

## 4. Design System & UI Components (`src/ui/`)

Reusable, accessible UI components built with Streamlit and Altair:

| Module | Purpose | Key Components |
|---|---|---|
| [`src/ui/badges.py`](file:///c:/Alpha/HeartGuard/src/ui/badges.py) | Accessible status indicators | `get_risk_category_badge`, `get_review_status_badge`, `get_alert_status_badge` |
| [`src/ui/cards.py`](file:///c:/Alpha/HeartGuard/src/ui/cards.py) | Metric and summary cards | `render_metric_card`, `render_risk_components_cards`, `render_assessment_summary_card`, `format_risk_percentage` |
| [`src/ui/charts.py`](file:///c:/Alpha/HeartGuard/src/ui/charts.py) | Altair visualization charts | `prepare_risk_trend_chart`, `prepare_risk_components_chart`, `prepare_shap_chart`, `prepare_category_distribution_chart`, `prepare_review_distribution_chart`, `prepare_alert_distribution_chart` |
| [`src/ui/tables.py`](file:///c:/Alpha/HeartGuard/src/ui/tables.py) | Formatted data tables | `render_recent_assessments_table`, `render_reviewer_queue_table` |
| [`src/ui/dashboard_components.py`](file:///c:/Alpha/HeartGuard/src/ui/dashboard_components.py) | High-level containers | `render_dashboard_header`, `render_empty_dashboard_state`, `render_quick_actions`, `render_lifestyle_insights`, `safe_render_section` |

---

## 5. Privacy, Security & Data Isolation

- **Zero Cross-User Data Leakage**: Dashboard queries (`AnalyticsService.get_user_recent_assessments`, `AnalyticsService.calculate_user_statistics`, `TrendService.get_risk_trends`) enforce strict `user_id` filtering at the database layer.
- **Admin Aggregate Privacy**: Admin dashboards display aggregate metrics only. Raw patient medical records and free-text lifestyle narratives are never rendered on the admin dashboard or written to audit logs.
- **Role-Based Navigation**: UI navigation dynamically reflects user permissions, but backend authorization guards (`require_authentication`, `require_reviewer`, `require_role`) enforce access control independently of UI visibility.
- **No In-Memory Cache Cross-Contamination**: Analytics computations read directly from user-scoped database records without global shared caches.

---

## 6. Performance & Graceful Degradation

- **No Model Inference on Page Load**: Dashboards render exclusively from persisted historical data. Model inference, SHAP generation, and NLP parsing are never re-executed during dashboard browsing.
- **Safe Section Wrappers (`safe_render_section`)**: Dashboard sections execute within isolated try/except boundaries. An isolated failure in one component displays a non-intrusive warning without crashing the entire page.
- **Sub-Second Response Times**: Verified to render and aggregate 100+ stored assessments in under 1.0 second.

---

## 7. Medical & Clinical Disclaimers

HeartGuard enforces non-diagnostic terminology across all UI views:
- Risk scores are explicitly labeled **"Model-Based Risk"** or **"AI Assessment"**, never "Confirmed Disease" or "Medical Diagnosis".
- SHAP charts are described as **"Factors Influencing Model Output"** or **"Model Feature Contributions"**, never "Causes" or "Proof".
- Professional reviews are designated as **"Professional Observations"**, never "Prescriptions" or "Treatment Decisions".
- High and critical risk scores trigger an immediate **Emergency Medical Notice** advising prompt professional evaluation.
