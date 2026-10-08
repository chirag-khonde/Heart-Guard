# Model Card — HeartGuard Clinical Risk Model

## Model Details

| Field | Value |
|-------|-------|
| **Model name** | HeartGuard Clinical Risk Classifier |
| **Model type** | Logistic Regression (selected), with Random Forest, XGBoost, and MLP alternatives |
| **Framework** | scikit-learn 1.x |
| **Version** | 1.0.0 |
| **Developed by** | HeartGuard Team |
| **Project** | HeartGuard — Cardiovascular Risk Assessment System |
| **Date** | 2026-09-07 |

## Model Purpose and Intended Use

This model is a **research and screening aid** designed to:

- Estimate the probability of cardiovascular disease presence based on 11 clinical features
- Provide a clinical risk component (70% weight) in the HeartGuard multimodal risk assessment
- Support healthcare professionals with an additional data-driven signal during patient assessment

**Intended setting:** Clinical decision support in conjunction with professional medical judgment.

## Not Intended Use

This model is **NOT** a diagnostic tool. It must NOT be used to:

- Diagnose or confirm heart disease
- Replace clinical examination, laboratory tests, or imaging
- Make treatment decisions without professional medical oversight
- Serve as the sole basis for clinical action
- Operate without a qualified healthcare professional in the loop

All system outputs include a disclaimer stating: *"This is an experimental model estimate, not a clinical diagnosis."*

## Training Data

| Property | Value |
|----------|-------|
| **Dataset** | Cleveland Heart Disease dataset (UCI Machine Learning Repository) |
| **Samples** | ~303 records |
| **Features** | 11 input features (6 numerical, 5 categorical/binary) |
| **Target** | Binary (0 = no disease, 1 = disease present) |
| **Original target** | Multi-class severity scale (0–4), normalized to binary |
| **Split** | 80% train / 20% test, stratified |
| **Preprocessing** | Median imputation + MinMax scaling (numerical), Most-frequent imputation + One-hot encoding (categorical) |

### Data Limitations

- Single-center dataset from 1988
- Small sample size (~303)
- Potential demographic bias (specific population characteristics)
- No external validation dataset used

## Features Used

### Input Features (11)

| Feature | Type | Description |
|---------|------|-------------|
| `age` | Numerical | Age in years |
| `resting_bp` | Numerical | Resting blood pressure (mm Hg) |
| `cholesterol` | Numerical | Serum cholesterol (mg/dl) |
| `max_heart_rate` | Numerical | Maximum heart rate achieved |
| `st_depression` | Numerical | ST depression induced by exercise |
| `num_major_vessels` | Numerical | Number of major vessels (0–4) |
| `sex` | Binary | Sex (0/1) |
| `chest_pain_type` | Categorical | Chest pain type (0–3) |
| `fasting_blood_sugar` | Binary | Fasting blood sugar > 120 mg/dl |
| `resting_ecg` | Categorical | Resting ECG results (0–2) |
| `exercise_angina` | Binary | Exercise-induced angina |

### Post-Processing Feature Space (19 features)

After one-hot encoding, the model operates on 19 features:
- 6 numerical features (scaled to [0, 1])
- 13 one-hot encoded columns (sex × 2, chest_pain_type × 4, fasting_blood_sugar × 2, resting_ecg × 3, exercise_angina × 2)

## Model Architecture

**Selected model:** Logistic Regression

| Hyperparameter | Value |
|----------------|-------|
| C (regularization) | 1.0 |
| Solver | lbfgs |
| Max iterations | 500 |
| Random state | 42 |

### Alternative Models (also available)

| Model | Key Hyperparameters |
|-------|-------------------|
| Random Forest | n_estimators=200, max_depth=8, min_samples_split=5 |
| XGBoost | n_estimators=300, max_depth=4, lr=0.05, subsample=0.8 |
| Neural Network (MLP) | layers=(64,32,16), ReLU, alpha=0.0001, lr=0.001 |

## Evaluation Results

### Cross-Validation (5-fold Stratified)

| Metric | Logistic Regression | Random Forest | XGBoost | Neural Network |
|--------|-------------------|---------------|---------|----------------|
| Accuracy | 0.5289 ± 0.0835 | 0.5037 ± 0.0557 | 0.5126 ± 0.0790 | 0.5414 ± 0.0681 |
| Precision | 0.5644 ± 0.0640 | 0.5469 ± 0.0405 | 0.5642 ± 0.0728 | 0.5832 ± 0.0699 |
| Recall | 0.6754 ± 0.1196 | 0.6463 ± 0.0915 | 0.5656 ± 0.0880 | 0.6830 ± 0.0971 |
| F1 | 0.6136 ± 0.0852 | 0.5917 ± 0.0623 | 0.5646 ± 0.0799 | 0.6246 ± 0.0598 |
| ROC-AUC | **0.5411 ± 0.1018** | 0.4742 ± 0.0601 | 0.4827 ± 0.0910 | 0.5311 ± 0.1253 |

### Test Set Performance (Logistic Regression — selected model)

| Metric | Value |
|--------|-------|
| Accuracy | 0.4098 |
| Precision | 0.4706 |
| Recall | 0.4706 |
| F1 | 0.4706 |
| ROC-AUC | 0.4357 |

### All Test Set Results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|-----|---------|
| Logistic Regression | 0.4098 | 0.4706 | 0.4706 | 0.4706 | 0.4357 |
| Random Forest | 0.5738 | 0.5870 | 0.7941 | 0.6750 | 0.5381 |
| XGBoost | 0.5902 | 0.6286 | 0.6471 | 0.6377 | 0.6078 |
| Neural Network | 0.5574 | 0.6000 | 0.6176 | 0.6087 | 0.4978 |

> **Important:** All models demonstrate poor discriminative ability. The best cross-validation ROC-AUC is 0.5411, well below the 0.70 threshold typically considered acceptable for clinical screening tools.

## Limitations and Bias Considerations

### Limitations

1. **Small dataset size:** ~303 samples provides insufficient statistical power for robust generalization.
2. **Low predictive performance:** All models achieve ROC-AUC below 0.61 on the test set, indicating limited clinical utility.
3. **Historical data:** Training data collected in 1988 may not reflect current patient demographics, disease patterns, or clinical practices.
4. **Single-center bias:** Data from one medical center may not generalize to other populations or healthcare settings.
5. **Limited feature set:** Only 11 clinical features are used; modern cardiovascular assessment typically includes additional biomarkers and imaging data.
6. **Binary target simplification:** Multi-class severity information is collapsed to binary, losing potentially useful clinical granularity.

### Bias Considerations

- **Demographic bias:** The Cleveland dataset may underrepresent certain age groups, ethnicities, or genders.
- **Sex as feature:** The model includes sex as a binary feature. This reflects known physiological differences in cardiovascular presentation but may introduce bias in predictions for underrepresented groups.
- **Temporal bias:** 1988-era clinical thresholds and population characteristics may not apply to contemporary patients.
- **Selection bias:** Hospital-based cohort may over-represent symptomatic patients compared to the general population.

## Explainability

The model provides explainability through:

1. **SHAP (SHapley Additive exPlanations):** Individual prediction explanations via `SHAPExplainerService`, generating:
   - Per-feature contribution values
   - Top risk factor identification
   - Human-readable summaries
   - Waterfall plot visualizations

2. **Feature importance:** Built-in `feature_importances_` for tree-based models (Random Forest, XGBoost), visualized as top-10 bar charts.

3. **Logistic Regression coefficients:** Linear model provides interpretable feature weights.

## Monitoring

Post-deployment monitoring approaches:

- **Model Registry:** SHA-256 integrity verification of model artifacts against manifest
- **Health checks:** Registry reports loaded/error status per model
- **Assessment logging:** All predictions logged to `assessments.db` for audit trail
- **User feedback:** Review system (`reviews.db`) for clinician feedback on predictions
- **Data drift detection:** Available via evaluation pipeline (`EVALUATION_CV_FOLDS=5`)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-09-07 | Initial production release. Logistic Regression selected as best model by CV ROC-AUC. |

### Artifact Versions

All model artifacts are versioned and tracked in `models/model_metadata.json`. The model registry ensures integrity via SHA-256 checksums stored in `models/model_manifest.json`.

| Artifact | Version |
|----------|---------|
| Logistic Regression | v1 |
| Random Forest | v1 |
| XGBoost | v1 |
| Neural Network | v1 |
| Preprocessor | v1 |
