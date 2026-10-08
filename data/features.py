"""Feature definitions and column mappings for HeartGuard.

Centralized feature lists, canonical schema, and column name mappings
for the Cleveland and Framingham datasets.
"""

# ---------------------------------------------------------------------------
# Cleveland canonical schema
# ---------------------------------------------------------------------------

NUMERICAL_FEATURES: list[str] = [
    "age",
    "resting_bp",
    "cholesterol",
    "max_heart_rate",
    "st_depression",
    "num_major_vessels",
]

CATEGORICAL_FEATURES: list[str] = [
    "sex",
    "chest_pain_type",
    "fasting_blood_sugar",
    "resting_ecg",
    "exercise_angina",
]

TARGET_COLUMN: str = "target"

ALL_FEATURES: list[str] = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

# Deterministic feature ordering used across training, evaluation, prediction,
# SHAP, Streamlit input, and saved model inference.  The order must never
# depend on dictionary ordering or arbitrary DataFrame column ordering.
HEARTGUARD_FEATURES: list[str] = [
    "age",
    "sex",
    "chest_pain_type",
    "resting_bp",
    "cholesterol",
    "fasting_blood_sugar",
    "resting_ecg",
    "max_heart_rate",
    "exercise_angina",
    "st_depression",
    "num_major_vessels",
]

# ---------------------------------------------------------------------------
# Cleveland column mapping  (source name -> canonical name)
# ---------------------------------------------------------------------------

CLEVELAND_COLUMN_MAP: dict[str, str] = {
    "age": "age",
    "sex": "sex",
    "cp": "chest_pain_type",
    "trestbps": "resting_bp",
    "chol": "cholesterol",
    "fbs": "fasting_blood_sugar",
    "restecg": "resting_ecg",
    "thalach": "max_heart_rate",
    "exang": "exercise_angina",
    "oldpeak": "st_depression",
    "ca": "num_major_vessels",
    "target": "target",
}

# Common alternative names that may appear in different CSV exports
CLEVELAND_ALT_NAMES: dict[str, str] = {
    "chest_pain": "chest_pain_type",
    "trest_bps": "resting_bp",
    "rest_bp": "resting_bp",
    "maximum_heart_rate": "max_heart_rate",
    "heart_rate": "max_heart_rate",
    "st_depr": "st_depression",
    "num_vessels": "num_major_vessels",
    "major_vessels": "num_major_vessels",
    "thal": "target",
    "condition": "target",
    "num": "target",
}

# ---------------------------------------------------------------------------
# Cleveland expected column sets (for raw CSV before mapping)
# ---------------------------------------------------------------------------

# Standard 13-feature Cleveland dataset column names (lowercase, stripped)
CLEVELAND_STANDARD_COLUMNS: set[str] = {
    "age", "sex", "cp", "trestbps", "chol", "fbs",
    "restecg", "thalach", "exang", "oldpeak", "ca", "target",
}

# Cleveland with 14 columns (includes 'thal')
CLEVELAND_14_COLUMNS: set[str] = CLEVELAND_STANDARD_COLUMNS | {"thal"}

# ---------------------------------------------------------------------------
# Framingham feature mapping (limited — many features differ)
# ---------------------------------------------------------------------------

FRAMINGHAM_COLUMN_MAP: dict[str, str] = {
    "age": "age",
    "male": "sex",
    "totchol": "cholesterol",
    "sysbp": "resting_bp",
    "diabp": "diastolic_bp",
    "glucose": "glucose",
    "heart_rate": "max_heart_rate",
    "cigarettesperday": "cigarettes_per_day",
    "diabetes": "diabetes",
    "bpmeds": "bp_meds",
    "prevmi": "prev_mi",
    "prevcvd": "prev_cvd",
    "prevhyp": "prev_hyp",
    "timeframe": "timeframe",
    "year": "study_year",
    "density": "density",
    "glmstatus": "glm_status",
    "cvd10": "ten_year_cvd",
}

# Features that can be mapped to HeartGuard canonical schema from Framingham
FRAMINGHAM_MAPPABLE_FEATURES: dict[str, str] = {
    "age": "age",
    "male": "sex",
    "totchol": "cholesterol",
    "sysbp": "resting_bp",
}

# ---------------------------------------------------------------------------
# Cleveland target normalization
# ---------------------------------------------------------------------------

# Cleveland target values that indicate heart disease presence
# Different versions use 0/1, 0/1/2/3/4, or 0-4 scale
CLEVELAND_TARGET_PRESENCE_VALUES: set[int] = {1, 2, 3, 4}

# ---------------------------------------------------------------------------
# Data validation bounds
# ---------------------------------------------------------------------------

VALIDATION_BOUNDS: dict[str, tuple[float, float]] = {
    "age": (1, 150),
    "resting_bp": (1, 300),
    "cholesterol": (1, 800),
    "max_heart_rate": (1, 300),
    "st_depression": (0, 20),
    "num_major_vessels": (0, 4),
}

# Binary features that should only contain 0 or 1
BINARY_FEATURES: list[str] = [
    "sex",
    "fasting_blood_sugar",
    "exercise_angina",
]
