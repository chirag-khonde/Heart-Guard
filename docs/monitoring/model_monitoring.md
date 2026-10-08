# HeartGuard Model Monitoring

Phase 17 — Advanced Analytics, Monitoring & Model Drift

## Overview

Model monitoring provides continuous observation of ML model behavior in production.
It observes the existing system without modifying the clinical prediction model,
trained model weights, risk thresholds, or clinical feature definitions.

## Architecture

```
                 HEARTGUARD
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   Application     Data          Model
   Metrics       Quality       Monitoring
       │             │             │
       └─────────────┼─────────────┘
                     ▼
              Analytics Layer
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   Admin Analytics       Monitoring Events
```

## Model Performance Monitoring

### Metrics Tracked
- **Accuracy**: Overall prediction accuracy
- **Precision**: Positive predictive value
- **Recall**: Sensitivity / true positive rate
- **F1 Score**: Harmonic mean of precision and recall
- **ROC-AUC**: Area under the receiver operating characteristic curve
- **PR-AUC**: Area under the precision-recall curve
- **Specificity**: True negative rate
- **Balanced Accuracy**: Average of sensitivity and specificity
- **Brier Score**: Probability calibration metric

### Data Source
Model performance metrics are sourced from Phase 14 evaluation runs stored in
`data/evaluations/evaluation.db`. The monitoring layer reads these metrics
without retraining or modifying the model.

### Model Status
Models are tracked with the following statuses:
- **PRODUCTION**: Currently active best model
- **VALIDATION**: Evaluated but not selected as best
- **RETIRED**: No longer in use
- **UNKNOWN**: Status not determined

## Data Drift Detection

### Reference vs Current
- **Reference**: Training data distribution (from Cleveland dataset)
- **Current**: Recent production assessment data

### Numerical Features Monitored
- age, resting_bp, cholesterol, max_heart_rate, st_depression, num_major_vessels

### Categorical Features Monitored
- sex, chest_pain_type, fasting_blood_sugar, resting_ecg, exercise_angina

### Statistical Methods
- **PSI (Population Stability Index)**: Distribution shift measurement
- **KS Test (Kolmogorov-Smirnov)**: Distribution comparison for numerical features
- **Jensen-Shannon Divergence**: Symmetric distribution comparison
- **Chi-Square Test**: Categorical distribution comparison

### Drift Thresholds (Engineering)
| Metric | Warning | Critical |
|--------|---------|----------|
| PSI | 0.10 | 0.25 |
| JS Divergence | 0.05 | 0.15 |
| KS Alpha | 0.05 | - |

These are engineering monitoring thresholds, NOT clinical thresholds.

### Minimum Sample Size
Drift analysis requires a minimum of 30 samples per distribution.
Below this threshold, results are reported as INSUFFICIENT_DATA.

### Drift Status Values
- **HEALTHY**: No significant drift detected
- **WARNING**: Moderate drift detected
- **DRIFT_DETECTED**: Significant drift detected
- **INSUFFICIENT_DATA**: Not enough data for analysis

## Prediction Drift

Monitors changes in model prediction category distributions over time.
Compares the last 30 days against historical distributions.

### Thresholds
- Distribution shift > 10%: WARNING
- Distribution shift > 20%: DRIFT_DETECTED

## Confidence Monitoring

If the model produces probability values, the system monitors:
- Mean confidence across predictions
- Percentage of low-confidence predictions (< 40%)
- Confidence distribution over time

Note: Model confidence is NOT medical certainty.

## Data Quality Monitoring

### Checks Performed
1. **Missing Values**: Per-feature missingness rate
2. **Invalid Values**: Non-numeric values in numeric fields
3. **Out-of-Range Values**: Values outside validation bounds
4. **Duplicate Records**: Duplicate assessment detection
5. **Schema Changes**: Unexpected categories in categorical features
6. **Unexpected Categories**: Categories not in the expected set

### Quality Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Missing Rate | 5% | 20% |
| Duplicate Rate | 2% | 10% |
| Out-of-Range Rate | 3% | - |

## Anomaly Detection

Lightweight statistical anomaly detection for operational metrics:
- Assessment volume anomalies (Z-score > 3.0)
- Prediction distribution anomalies
- Error rate anomalies (> 5%)
- Latency spikes (> 3x normal)

**Important**: Anomaly detection does NOT create medical diagnoses.
It detects unusual data patterns, not medical abnormalities.

## Performance Monitoring

### Metrics Tracked
- Inference latency (ms)
- Request counts and response times
- Error rates by component
- Report generation time

### Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Inference Latency | 5000ms | 10000ms |
| Error Rate | 5% | 15% |

## Monitoring Events

### Event Types
- DATA_DRIFT_DETECTED
- PREDICTION_DRIFT_DETECTED
- DATA_QUALITY_DEGRADED
- MODEL_PERFORMANCE_DEGRADED
- ANOMALY_DETECTED
- SCHEMA_CHANGE_DETECTED
- HIGH_ERROR_RATE
- HIGH_LATENCY

### Severity Levels
- INFO: Informational
- WARNING: Attention needed
- HIGH: Significant issue
- CRITICAL: Immediate attention required

### Event Lifecycle
1. Event created with status OPEN
2. Admin acknowledges → status becomes ACKNOWLEDGED
3. Events are retained for 90 days (configurable)

## Configuration

All monitoring thresholds are centralized in `config/monitoring.py`.
Environment variables can override defaults:

```bash
DRIFT_PSI_WARNING=0.10
DRIFT_PSI_CRITICAL=0.25
DRIFT_MIN_SAMPLE_SIZE=30
DQ_MISSING_RATE_WARNING=0.05
CONFIDENCE_LOW_THRESHOLD=0.40
ANOMALY_ZSCORE_THRESHOLD=3.0
EVENT_RETENTION_DAYS=90
```

## Limitations

1. Drift detection is statistical, not clinical
2. Small sample sizes produce unreliable results
3. Drift does NOT automatically mean the model is unsafe
4. Performance metrics depend on available evaluation data
5. Anomaly detection uses simple statistical methods
6. Monitoring supports human review, not automatic decisions

## Model Governance

If drift is detected:
1. Flag the drift for review
2. Investigate data quality
3. Validate model performance
4. Approve any model changes
5. Deploy new version through proper channels

**No automatic retraining or model replacement occurs.**
