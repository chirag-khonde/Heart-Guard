# HeartGuard Data Quality Monitoring

Phase 17 — Advanced Analytics, Monitoring & Model Drift

## Overview

Data quality monitoring tracks the health and integrity of assessment data
flowing through the HeartGuard system. It detects missing values, invalid
data, out-of-range values, duplicates, schema changes, and unexpected
categories.

## Data Quality Checks

### 1. Missing Value Analysis
Tracks the rate of missing values per feature across assessment records.

| Feature | Expected Type | Missing Handling |
|---------|--------------|------------------|
| age | Numeric | Warning at 5%, Critical at 20% |
| resting_bp | Numeric | Warning at 5%, Critical at 20% |
| cholesterol | Numeric | Warning at 5%, Critical at 20% |
| max_heart_rate | Numeric | Warning at 5%, Critical at 20% |
| st_depression | Numeric | Warning at 5%, Critical at 20% |
| num_major_vessels | Numeric | Warning at 5%, Critical at 20% |
| sex | Categorical (0/1) | Warning at 5%, Critical at 20% |
| chest_pain_type | Categorical (0-3) | Warning at 5%, Critical at 20% |
| fasting_blood_sugar | Categorical (0/1) | Warning at 5%, Critical at 20% |
| resting_ecg | Categorical (0-2) | Warning at 5%, Critical at 20% |
| exercise_angina | Categorical (0/1) | Warning at 5%, Critical at 20% |

### 2. Invalid Value Detection
Checks for non-numeric values in numeric fields and unexpected types.

### 3. Out-of-Range Detection
Validates values against clinical validation bounds:

| Feature | Min | Max |
|---------|-----|-----|
| age | 1 | 150 |
| resting_bp | 1 | 300 |
| cholesterol | 1 | 800 |
| max_heart_rate | 1 | 300 |
| st_depression | 0 | 20 |
| num_major_vessels | 0 | 4 |

### 4. Duplicate Detection
Identifies records with identical assessment_id, user_id, and timestamp.
Duplicate rate warning at 2%, critical at 10%.

### 5. Schema Monitoring
Detects unexpected categories in categorical features:

| Feature | Expected Categories |
|---------|-------------------|
| sex | 0, 1 |
| chest_pain_type | 0, 1, 2, 3 |
| fasting_blood_sugar | 0, 1 |
| resting_ecg | 0, 1, 2 |
| exercise_angina | 0, 1 |

## Quality Status Values

- **HEALTHY**: All checks within normal thresholds
- **WARNING**: One or more checks exceed warning thresholds
- **DEGRADED**: One or more checks exceed critical thresholds
- **INSUFFICIENT_DATA**: Fewer than 10 records for analysis

## Dashboard

The data quality dashboard displays:
- Total Records
- Valid Records
- Invalid Records
- Missing Data Rate
- Duplicate Rate
- Schema Status
- Per-feature missing rates
- Quality issues list

## Configuration

Quality thresholds are centralized in `config/monitoring.py`:

```bash
DQ_MISSING_RATE_WARNING=0.05
DQ_MISSING_RATE_CRITICAL=0.20
DQ_DUPLICATE_RATE_WARNING=0.02
DQ_DUPLICATE_RATE_CRITICAL=0.10
DQ_OUT_OF_RANGE_WARNING=0.03
DQ_MIN_RECORDS=10
```

## Limitations

1. Analysis requires a minimum of 10 records
2. Schema monitoring only checks known expected categories
3. Duplicate detection is based on exact matches
4. Missing data analysis depends on JSON parsing of clinical_data_json
5. Quality metrics describe data patterns, not clinical validity
