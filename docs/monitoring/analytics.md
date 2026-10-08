# HeartGuard Analytics

Phase 17 — Advanced Analytics, Monitoring & Model Drift

## Overview

HeartGuard provides comprehensive analytics across three user roles:
- **Patient**: Personal risk analytics and assessment insights
- **Admin**: System-wide analytics, model monitoring, and security analytics
- **Reviewer**: Authorized analytics within role permissions

## Patient Analytics

### Available Metrics
- Total assessments count
- Latest risk score and category
- Average risk across all assessments
- Risk category distribution
- Model-based risk trend over time
- Assessment history table

### Privacy
Patient analytics only show data belonging to the authenticated patient.
No other patient's data is exposed.

### Medical Disclaimer
Patient analytics use language like "Model-based risk trend" rather than
"disease progression." Changes in risk scores represent changes in model
inputs and outputs, not necessarily changes in health status.

## Admin Analytics Dashboard

### Sections
1. **Assessment Overview**: Total predictions, unique patients, mean risk
2. **Risk Distribution**: Category breakdown with charts
3. **Prediction Trend**: Daily/weekly prediction volume
4. **Model Version Analytics**: Predictions grouped by model version
5. **Alert Analytics**: Alert counts, success rates, trends
6. **Recommendation Analytics**: Recommendation counts, categories, frequency
7. **Explainability Analytics**: Aggregate SHAP feature importance
8. **Security Analytics**: Failed logins, auth failures, admin actions
9. **Anomaly Detection**: Volume and distribution anomalies
10. **Monitoring Events**: Recent system monitoring events

### Time Filters
- All Time
- Last 7 Days
- Last 30 Days
- Last 90 Days

## Model Monitoring Dashboard

### Sections
1. **Model Performance**: Latest metrics, model comparison, metric history
2. **Data Drift**: Feature distributions, drift analysis
3. **Prediction Drift**: Prediction distribution changes
4. **Data Quality**: Missing data, duplicates, schema issues
5. **System Performance**: Latency, error rates, request counts
6. **Monitoring Events**: Event log with severity and status

## Analytics API

### Data Sources
- Assessment records (assessments.db)
- Alert history (alerts.db)
- Recommendation records (recommendations.db)
- Audit log (audit.db)
- Evaluation runs (evaluation.db)
- Performance metrics (monitoring.db)
- Monitoring events (monitoring.db)

### Aggregation
Analytics are computed using database-level aggregation where possible.
Large datasets use SQL GROUP BY rather than loading all records into memory.

### Caching
Performance metrics use a 5-minute cache to avoid repeated database queries.
Cache is per-session and does not persist across Streamlit reruns.

### Privacy
- Aggregate statistics only (counts, averages, distributions)
- No patient names, emails, or raw medical data exposed
- SHAP analytics use aggregate statistical views
- Audit events never contain passwords, tokens, or clinical data

## Monitoring Events

### Event Lifecycle
1. System detects anomaly/drift/quality issue
2. Monitoring event created with severity and details
3. Admin views events in monitoring dashboard
4. Admin acknowledges events that require action
5. Events are retained for 90 days

### Event Types
| Event Type | Description |
|-----------|-------------|
| DATA_DRIFT_DETECTED | Feature distribution shift |
| PREDICTION_DRIFT_DETECTED | Prediction distribution shift |
| DATA_QUALITY_DEGRADED | Data quality issue detected |
| MODEL_PERFORMANCE_DEGRADED | Model metrics declined |
| ANOMALY_DETECTED | Operational anomaly |
| SCHEMA_CHANGE_DETECTED | Unexpected schema change |
| HIGH_ERROR_RATE | Elevated error rate |
| HIGH_LATENCY | Elevated latency |

## Configuration

All analytics thresholds are in `config/monitoring.py`.
Environment variables can override defaults.

## Limitations

1. Analytics depend on available data in the databases
2. Small datasets produce less reliable statistics
3. Drift detection requires minimum 30 samples
4. Performance metrics require explicit recording
5. Analytics are refreshed on page load, not real-time
6. Historical data may be limited in early deployment
