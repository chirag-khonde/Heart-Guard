# HeartGuard Data Dictionary

## Cleveland Heart Disease Dataset (Primary)

| Feature | Description | Data Type | Role | Expected Range / Categories |
|---------|-------------|-----------|------|----------------------------|
| `age` | Age of the patient in years | Numerical | Input | 1–150 |
| `sex` | Sex of the patient | Categorical (binary) | Input | 0 = female, 1 = male |
| `chest_pain_type` | Type of chest pain experienced | Categorical | Input | 0 = typical angina, 1 = atypical angina, 2 = non-anginal pain, 3 = asymptomatic |
| `resting_bp` | Resting blood pressure on admission (mm Hg) | Numerical | Input | 1–300 |
| `cholesterol` | Serum cholesterol (mg/dl) | Numerical | Input | 1–800 |
| `fasting_blood_sugar` | Fasting blood sugar > 120 mg/dl | Categorical (binary) | Input | 0 = false, 1 = true |
| `resting_ecg` | Resting electrocardiographic results | Categorical | Input | 0 = normal, 1 = ST-T wave abnormality, 2 = left ventricular hypertrophy |
| `max_heart_rate` | Maximum heart rate achieved during exercise | Numerical | Input | 1–300 |
| `exercise_angina` | Exercise-induced angina | Categorical (binary) | Input | 0 = no, 1 = yes |
| `st_depression` | ST depression induced by exercise relative to rest (oldpeak) | Numerical | Input | 0–20 |
| `num_major_vessels` | Number of major vessels coloured by fluoroscopy | Numerical | Input | 0–4 |
| `target` | Heart disease diagnosis | Binary (target) | Output | 0 = absence, 1 = presence |

### Source Names

The Cleveland dataset CSV may use either of these naming conventions:

| Canonical Name | UCI Source Name | Kaggle Source Name |
|---------------|-----------------|-------------------|
| `age` | `age` | `age` |
| `sex` | `sex` | `sex` |
| `chest_pain_type` | `cp` | `chest_pain_type` |
| `resting_bp` | `trestbps` | `trestbps` |
| `cholesterol` | `chol` | `chol` |
| `fasting_blood_sugar` | `fbs` | `fbs` |
| `resting_ecg` | `restecg` | `restecg` |
| `max_heart_rate` | `thalach` | `thalach` |
| `exercise_angina` | `exang` | `exang` |
| `st_depression` | `oldpeak` | `oldpeak` |
| `num_major_vessels` | `ca` | `ca` |
| `target` | `num` | `target` |

### Target Normalisation

The original Cleveland dataset may use a severity scale (0–4) where 0 indicates absence and 1–4 indicate varying degrees of heart disease. HeartGuard normalises this to binary:

- **0** = absence of heart disease
- **1** = presence of heart disease (any severity > 0)

---

## Framingham Heart Study Dataset (Secondary)

The Framingham dataset is used for secondary evaluation and cross-population generalisability analysis. It is **not** merged with the Cleveland dataset.

| Feature | Description | Data Type | Role |
|---------|-------------|-----------|------|
| `age` | Age in years | Numerical | Input |
| `male` | Sex (mapped to `sex` in HeartGuard schema) | Categorical (binary) | Input |
| `totchol` | Total cholesterol (mg/dl) | Numerical | Input |
| `sysbp` | Systolic blood pressure (mm Hg) | Numerical | Input |
| `diabp` | Diastolic blood pressure (mm Hg) | Numerical | Input |
| `glucose` | Casual serum glucose (mg/dl) | Numerical | Input |
| `heart_rate` | Heart rate (beats/min) | Numerical | Input |
| `cigarettesperday` | Average number of cigarettes smoked per day | Numerical | Input |
| `diabetes` | Diabetic status | Categorical (binary) | Input |
| `bpmeds` | On blood pressure medication | Categorical (binary) | Input |
| `prevmi` | History of myocardial infarction | Categorical (binary) | Input |
| `prevcvd` | History of cardiovascular disease | Categorical (binary) | Input |
| `prevhyp` | History of hypertension | Categorical (binary) | Input |
| `cvd10` | 10-year cardiovascular disease risk | Categorical (binary) | Output |

### Mappable Features

Only a subset of Framingham features can be mapped to the HeartGuard canonical schema:

| Framingham | HeartGuard Canonical |
|-----------|---------------------|
| `age` | `age` |
| `male` | `sex` |
| `totchol` | `cholesterol` |
| `sysbp` | `resting_bp` |

Features such as `chest_pain_type`, `resting_ecg`, `max_heart_rate`, `exercise_angina`, `st_depression`, and `num_major_vessels` do not have direct equivalents in the Framingham dataset.

---

## Deterministic Feature Order

HeartGuard uses a fixed feature ordering (`HEARTGUARD_FEATURES`) across training, evaluation, prediction, SHAP, and Streamlit input:

```
age, sex, chest_pain_type, resting_bp, cholesterol,
fasting_blood_sugar, resting_ecg, max_heart_rate,
exercise_angina, st_depression, num_major_vessels
```

This ordering is deterministic and must never depend on dictionary ordering or arbitrary DataFrame column ordering.
