# ML Pipeline Documentation

## Overview

HeartGuard uses a multimodal machine learning pipeline that combines clinical ML predictions (70% weight) with NLP-based lifestyle risk scoring (30% weight) to produce an overall cardiovascular risk assessment. The clinical models are trained on the Cleveland Heart Disease dataset.

## Dataset

**Source:** Cleveland Heart Disease dataset (UCI Machine Learning Repository)

**Location:** `data/raw/heart.csv`

**Size:** ~303 samples with 13 input features and 1 binary target

**Target variable:** Binary (0 = absence, 1 = presence of heart disease). Original multi-class severity values (0–4) are normalized to binary via `normalize_cleveland_target()`.

### Features

| Feature | Type | Description |
|---------|------|-------------|
| `age` | Numerical | Age in years |
| `resting_bp` | Numerical | Resting blood pressure (mm Hg) |
| `cholesterol` | Numerical | Serum cholesterol (mg/dl) |
| `max_heart_rate` | Numerical | Maximum heart rate achieved |
| `st_depression` | Numerical | ST depression induced by exercise (oldpeak) |
| `num_major_vessels` | Numerical | Number of major vessels colored by fluoroscopy (0–4) |
| `sex` | Binary | Sex (0 = female, 1 = male) |
| `chest_pain_type` | Categorical | Chest pain type (0–3) |
| `fasting_blood_sugar` | Binary | Fasting blood sugar > 120 mg/dl (0/1) |
| `resting_ecg` | Categorical | Resting electrocardiographic results (0–2) |
| `exercise_angina` | Binary | Exercise-induced angina (0/1) |

## Feature Engineering

### Clinical Features (11 raw → 19 after encoding)

Defined in `src/data/features.py`:

- **Numerical (6):** `age`, `resting_bp`, `cholesterol`, `max_heart_rate`, `st_depression`, `num_major_vessels`
- **Categorical (5):** `sex`, `chest_pain_type`, `fasting_blood_sugar`, `resting_ecg`, `exercise_angina`

After one-hot encoding, the model receives **19 features** (6 numerical + 13 one-hot encoded columns).

### Lifestyle Features (NLP)

The NLP pipeline (`src/nlp/lifestyle_analyzer.py`) extracts risk signals from free-text patient descriptions across 6 categories:

1. **Smoking** — primary/variation keyword matching with negation detection
2. **Physical inactivity** — sedentary indicators, negative exercise patterns, positive exercise counter-checks
3. **Unhealthy diet** — junk food, high-salt, processed food keywords
4. **Poor sleep** — numeric sleep hour detection (< 6 hours), symptom keywords (insomnia, sleep deprivation)
5. **Family history** — cardiovascular family history mentions
6. **Alcohol use** — alcohol keywords with disambiguation for non-alcoholic drinks

Each category has configurable risk points and severity levels defined in the risk lexicon.

## Preprocessing Pipeline

Implemented in `src/data/preprocessing.py` using scikit-learn `ColumnTransformer`:

### Numerical Features
1. **Missing value imputation:** Median strategy (`SimpleImputer(strategy="median")`)
2. **Scaling:** Min-Max scaling (`MinMaxScaler`) — normalizes to [0, 1]

### Categorical Features
1. **Missing value imputation:** Most frequent strategy (`SimpleImputer(strategy="most_frequent")`)
2. **Encoding:** One-hot encoding (`OneHotEncoder(handle_unknown="ignore", sparse_output=False)`)

### Data Splitting
- **Train/Test split:** 80/20 with stratification (`stratify=y`)
- **Random state:** 42 (reproducible across runs)
- **Preprocessor fit:** Always fitted on training data only to prevent data leakage

## Model Training

### Training Pipeline (`src/ml/train_models.py`)

The training pipeline follows a 5-step process:

1. **Data Pipeline:** Load Cleveland data → normalize target → split → preprocess
2. **Cross-Validation:** 5-fold stratified CV with leakage-free sklearn Pipelines
3. **Full Training:** Train all 4 models on the complete training set
4. **Evaluation:** Evaluate all models on the held-out test set
5. **Selection & Persistence:** Select best model, save all artifacts

### Models

| Model | Hyperparameters | Description |
|-------|----------------|-------------|
| **Logistic Regression** | C=1.0, solver=lbfgs, max_iter=500 | Linear baseline classifier |
| **Random Forest** | n_estimators=200, max_depth=8, min_samples_split=5 | Bagging ensemble |
| **XGBoost** | n_estimators=300, max_depth=4, lr=0.05, subsample=0.8 | Boosting ensemble |
| **Neural Network (MLP)** | layers=(64,32,16), activation=relu, alpha=0.0001, lr=0.001, max_iter=50 | Multilayer perceptron |

All models use `random_state=42` for reproducibility.

### Cross-Validation

- **Strategy:** `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`
- Each fold builds a fresh sklearn `Pipeline(preprocessor, classifier)` to prevent data leakage

## Model Evaluation

### Cross-Validation Results (5-fold Stratified)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|-----|---------|
| Logistic Regression | 0.5289 ± 0.0835 | 0.5644 ± 0.0640 | 0.6754 ± 0.1196 | 0.6136 ± 0.0852 | **0.5411 ± 0.1018** |
| Random Forest | 0.5037 ± 0.0557 | 0.5469 ± 0.0405 | 0.6463 ± 0.0915 | 0.5917 ± 0.0623 | 0.4742 ± 0.0601 |
| XGBoost | 0.5126 ± 0.0790 | 0.5642 ± 0.0728 | 0.5656 ± 0.0880 | 0.5646 ± 0.0799 | 0.4827 ± 0.0910 |
| Neural Network | 0.5414 ± 0.0681 | 0.5832 ± 0.0699 | 0.6830 ± 0.0971 | 0.6246 ± 0.0598 | 0.5311 ± 0.1253 |

### Test Set Results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|-----|---------|
| Logistic Regression | 0.4098 | 0.4706 | 0.4706 | 0.4706 | 0.4357 |
| Random Forest | 0.5738 | 0.5870 | 0.7941 | 0.6750 | 0.5381 |
| XGBoost | 0.5902 | 0.6286 | 0.6471 | 0.6377 | **0.6078** |
| Neural Network | 0.5574 | 0.6000 | 0.6176 | 0.6087 | 0.4978 |

### Evaluation Metrics

- **ROC-AUC:** Primary selection metric (area under receiver operating characteristic curve)
- **F1 Score:** Secondary selection metric (harmonic mean of precision and recall)
- **Precision:** True positive rate (exactness)
- **Recall:** Sensitivity / true positive rate (completeness)
- **Accuracy:** Overall correctness

Visualizations generated per training run:
- Confusion matrices for each model
- ROC comparison curves
- Metrics comparison bar chart
- Neural network training loss curve
- Feature importance plots (Random Forest, XGBoost)

## Model Selection

**Best model:** Logistic Regression

Selected by highest cross-validation ROC-AUC (primary) with F1 as tiebreaker.

| Criterion | Value |
|-----------|-------|
| Model name | `logistic_regression` |
| CV ROC-AUC (mean) | 0.5411 |
| CV F1 (mean) | 0.6136 |

> **Note:** The selected model reflects the best performance on this particular dataset split. ROC-AUC values below 0.6 indicate limited discriminative ability. See [Limitations](#limitations).

## Prediction Pipeline

Implemented in `src/ml/predict.py`:

1. Load trained model via `ModelRegistry`
2. Load fitted preprocessor (`models/preprocessor.pkl`)
3. Transform input features through the preprocessor
4. Call `model.predict()` for binary classification
5. Call `model.predict_proba()` for probability estimates

All predictions are returned as `{"prediction": 0|1, "probability": float, "model_name": str}`.

## Multimodal Risk Calculation

Implemented in `src/risk_engine/multimodal_risk.py`:

```
Overall Risk = (Clinical Risk × 0.70) + (Lifestyle Risk × 0.30)
```

| Component | Weight | Source |
|-----------|--------|--------|
| Clinical | 70% | ML model `predict_proba()` output × 100 |
| Lifestyle | 30% | NLP analyzer score (0–100) based on 6 risk categories |

### Risk Categories

| Risk Range | Category | Recommended Action |
|------------|----------|-------------------|
| > 85% | CRITICAL | Immediate medical consultation recommended |
| 60% – 85% | APPOINTMENT_RECOMMENDED | Medical appointment recommendation |
| < 60% | MONITORING | Regular monitoring recommended |

### Clinical Explanation (SHAP)

When enabled, the system generates SHAP-based explanations for individual predictions using `SHAPExplainerService`, providing:
- Feature contribution values
- Top risk factors
- Human-readable summary
- Waterfall plot visualization

## Model Artifacts and Versioning

### Saved Artifacts

| Artifact | Location | Format |
|----------|----------|--------|
| Trained models (×4) | `models/*.pkl` | joblib pickle |
| Fitted preprocessor | `models/preprocessor.pkl` | joblib pickle |
| Feature names | `models/feature_names.json` | JSON |
| Model metadata | `models/model_metadata.json` | JSON |
| Model manifest | `models/model_manifest.json` | JSON (with SHA-256 checksums) |
| Best model report | `reports/best_model.json` | JSON |
| Model comparison | `reports/model_comparison.csv` | CSV |
| Training summary | `reports/training/training_summary.json` | JSON |
| NN training history | `reports/training/neural_network_history.json` | JSON |
| Visualizations | `reports/figures/*.png` | PNG |

### Model Registry

`ModelRegistry` (singleton) provides:
- SHA-256 integrity verification against the model manifest
- Lazy loading with caching
- Version tracking
- Health status reporting
- Safe fallback on load errors (required models raise `ModelIntegrityError`)

## Limitations

1. **Small dataset:** ~303 samples is insufficient for robust model generalization. All models show poor discriminative ability (test ROC-AUC range: 0.44–0.61).

2. **Low model performance:** ROC-AUC values significantly below 0.70 indicate the models have limited predictive power on this dataset. The "best" model (Logistic Regression) achieves only 0.4357 test ROC-AUC.

3. **Dataset bias:** The Cleveland dataset originates from a single medical center (1988), potentially reflecting population-specific patterns that may not generalize to other demographics.

4. **Feature limitations:** Only 11 clinical features are available. Additional biomarkers (e.g., HbA1c, CRP, BNP) and imaging data could improve performance.

5. **NLP rule-based approach:** Lifestyle analysis uses pattern matching rather than contextual understanding, which may miss nuanced risk signals or produce false positives.

6. **Static model:** The model is trained once and not continuously updated. Performance may degrade over time as patient populations shift.

7. **Not a diagnostic tool:** All outputs are experimental risk estimates, not clinical diagnoses. The system explicitly disclaims diagnostic use in all user-facing outputs.

8. **Target normalization:** Binary normalization of the multi-class Cleveland target (0–4 → 0/1) discards severity information that could be clinically relevant.
