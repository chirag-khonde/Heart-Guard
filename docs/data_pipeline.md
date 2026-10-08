# HeartGuard Data Pipeline

## Overview

The HeartGuard data pipeline prepares clinical heart disease datasets for machine learning model training. It follows the CRISP-DM methodology and implements strict data leakage prevention.

## Pipeline Flow

```
RAW DATA
   ↓
DATA LOADING (src/data/loader.py)
   ↓
SCHEMA VALIDATION
   ↓
DATA QUALITY CHECK (src/data/quality.py)
   ↓
CLEANING (duplicates, missing values)
   ↓
TARGET PREPARATION (binary normalisation)
   ↓
TRAIN/TEST SPLIT (80/20, stratified)
   ↓
PREPROCESSOR (src/data/preprocessing.py)
   ↓
FEATURE TRANSFORMATION (MinMaxScaler + OneHotEncoder)
   ↓
ML-READY DATA
   ↓
DATA QUALITY / EDA REPORTS
   ↓
READY FOR PHASE 4 MODEL TRAINING
```

## Quick Start

```python
from src.data.pipeline import prepare_cleveland_pipeline

result = prepare_cleveland_pipeline()

X_train = result.X_train
X_test  = result.X_test
y_train = result.y_train
y_test  = result.y_test
preprocessor = result.preprocessor
feature_names = result.feature_names
```

## Pipeline Steps

### 1. Data Loading

- Loads CSV from `data/raw/heart.csv`
- Normalises column names (lowercase, underscores)
- Applies canonical column mapping (e.g. `cp` → `chest_pain_type`)
- Validates all required columns are present

### 2. Data Cleaning

- Detects and reports exact duplicate rows
- Removes exact duplicates (logs action)
- Analyses missing values per column
- Detects invalid clinical values (out-of-range)
- Detects outliers using IQR method (reported, not removed)

### 3. Target Preparation

- Normalises Cleveland target to binary (0/1)
- Severity values 1–4 are mapped to 1 (presence)
- Analyses class distribution and imbalance ratio

### 4. Train/Test Split

- **80/20 stratified split** preserving class proportions
- **random_state = 42** for reproducibility
- Split occurs **before** any preprocessing fit

### 5. Preprocessing

| Component | Strategy |
|-----------|----------|
| Numerical imputation | Median (fitted on train only) |
| Numerical scaling | MinMaxScaler (fitted on train only) |
| Categorical imputation | Most-frequent (fitted on train only) |
| Categorical encoding | OneHotEncoder(handle_unknown='ignore') |

### 6. Artefact Persistence

The pipeline saves:

| Artefact | Location |
|----------|----------|
| Training data | `data/processed/cleveland_train.csv` |
| Test data | `data/processed/cleveland_test.csv` |
| Clean data | `data/processed/cleveland_clean.csv` |
| Fitted preprocessor | `models/preprocessor.pkl` |
| Data quality report | `reports/data_quality/cleveland_data_quality.json` |
| EDA summary | `reports/data_quality/cleveland_eda_summary.json` |
| Dataset metadata | `reports/data_quality/dataset_metadata.json` |
| Leakage check | `reports/data_quality/data_leakage_check.json` |

## Data Leakage Prevention

```
Correct:
  Raw data
    → Train/test split
    → Fit preprocessor on X_train ONLY
    → Transform X_train
    → Transform X_test

Incorrect:
  Raw data
    → Fit preprocessor on ALL data
    → Split
```

The pipeline verifies:
- Preprocessor is fitted only on training data
- Target is excluded from input features
- Test statistics are never used for preprocessing

## Cross-Validation Utility

```python
from src.ml.cross_validation import create_cv_strategy, get_cv_splits

cv = create_cv_strategy()  # StratifiedKFold, 5 folds, shuffle=True, random_state=42
splits = get_cv_splits(cv, X_train, y_train)
```

## Framingham Dataset

The Framingham dataset is inspected separately and **not merged** with Cleveland:

```python
from src.data.pipeline import inspect_framingham_dataset

summary = inspect_framingham_dataset()
```

Only 4 of Framingham's features map to the HeartGuard canonical schema (`age`, `sex`, `cholesterol`, `resting_bp`).

## Running the Pipeline

```bash
# Run full test suite
pytest -q

# Run pipeline validation script
python scripts/validate_phase3.py
```

## Module Reference

| Module | Purpose |
|--------|---------|
| `src/data/loader.py` | Dataset loading and schema validation |
| `src/data/preprocessing.py` | Preprocessing pipeline (imputation, scaling, encoding) |
| `src/data/pipeline.py` | End-to-end pipeline orchestration |
| `src/data/quality.py` | Data quality report generation |
| `src/data/features.py` | Feature constants and column mappings |
| `src/ml/cross_validation.py` | Stratified k-fold CV utility |
| `src/utils/validators.py` | Clinical value validation |
| `src/utils/exceptions.py` | Custom exception classes |
