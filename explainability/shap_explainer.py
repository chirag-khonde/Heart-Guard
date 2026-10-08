"""SHAP explainability module for HeartGuard.

Provides SHAP-based global and local explanations for trained models.
Dynamically selects the appropriate SHAP explainer based on the model type.

SHAP values describe model behavior, not clinical causation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from config.settings import MODEL_DIRECTORY, REPORT_DIRECTORY
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Clinical terminology mapping for display
CLINICAL_LABELS: dict[str, str] = {
    "age": "Age",
    "resting_bp": "Resting Blood Pressure",
    "cholesterol": "Cholesterol",
    "max_heart_rate": "Maximum Heart Rate",
    "st_depression": "ST Depression",
    "num_major_vessels": "Number of Major Vessels",
    "sex_0": "Sex (Female)",
    "sex_1": "Sex (Male)",
    "chest_pain_type_0": "Chest Pain Type 0",
    "chest_pain_type_1": "Chest Pain Type 1",
    "chest_pain_type_2": "Chest Pain Type 2",
    "chest_pain_type_3": "Chest Pain Type 3",
    "fasting_blood_sugar_0": "Fasting Blood Sugar <= 120",
    "fasting_blood_sugar_1": "Fasting Blood Sugar > 120",
    "resting_ecg_0": "Resting ECG Normal",
    "resting_ecg_1": "Resting ECG ST-T Abnormality",
    "resting_ecg_2": "Resting ECG Left Ventricular Hypertrophy",
    "exercise_angina_0": "Exercise Angina Absent",
    "exercise_angina_1": "Exercise Angina Present",
}

# Tolerance for treating SHAP values as approximately zero
NEUTRAL_TOLERANCE: float = 1e-6


# ---------------------------------------------------------------------------
# Model and artifact loading
# ---------------------------------------------------------------------------


def load_explainable_model() -> tuple[Any, str]:
    """Load the best trained model and determine its type.

    Reads reports/best_model.json to identify the best model,
    then loads the corresponding .pkl file from models/.

    Returns:
        Tuple of (model, model_name).

    Raises:
        FileNotFoundError: If best_model.json or model file is missing.
    """
    best_path = REPORT_DIRECTORY / "best_model.json"
    if not best_path.exists():
        raise FileNotFoundError(
            f"Best model info not found at {best_path}. "
            "Run Phase 4 training first."
        )

    with open(best_path, "r", encoding="utf-8") as f:
        best_info = json.load(f)

    model_name = best_info["model_name"]
    model_path = MODEL_DIRECTORY / f"{model_name}.pkl"

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}"
        )

    model = joblib.load(model_path)
    logger.info("Loaded best model '%s' from %s", model_name, model_path)
    return model, model_name


def load_feature_names() -> list[str]:
    """Load transformed feature names from models/feature_names.json.

    Returns:
        List of feature name strings.

    Raises:
        FileNotFoundError: If feature_names.json is missing.
    """
    path = MODEL_DIRECTORY / "feature_names.json"
    if not path.exists():
        raise FileNotFoundError(f"Feature names not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        names = json.load(f)

    logger.info("Loaded %d feature names", len(names))
    return names


def load_training_data() -> pd.DataFrame:
    """Load the training dataset for SHAP background data.

    Returns:
        DataFrame of training features (without target), preprocessed
        to match the model's expected feature space.

    Raises:
        FileNotFoundError: If training data is missing.
    """
    path = PROCESSED_DATA_DIRECTORY / "cleveland_train.csv"
    if not path.exists():
        raise FileNotFoundError(f"Training data not found at {path}")

    df = pd.read_csv(path)
    if "target" in df.columns:
        df = df.drop(columns=["target"])

    feature_names = load_feature_names()
    for col in feature_names:
        if col not in df.columns:
            logger.warning("Missing column '%s' in training data, filling with 0", col)
            df[col] = 0.0
    df = df[feature_names]

    logger.info("Loaded training data: %d rows x %d cols", len(df), len(df.columns))
    return df


# Lazy import for PROCESSED_DATA_DIRECTORY
from config.settings import PROCESSED_DATA_DIRECTORY


# ---------------------------------------------------------------------------
# Explainer creation
# ---------------------------------------------------------------------------


def _is_tree_model(model: Any) -> bool:
    """Check if a model is tree-based (XGBoost or Random Forest)."""
    tree_types = (
        "XGBClassifier", "XGBRegressor",
        "RandomForestClassifier", "RandomForestRegressor",
        "GradientBoostingClassifier", "GradientBoostingRegressor",
        "DecisionTreeClassifier", "DecisionTreeRegressor",
        "ExtraTreesClassifier", "ExtraTreesRegressor",
    )
    return type(model).__name__ in tree_types


def _is_linear_model(model: Any) -> bool:
    """Check if a model is linear (Logistic Regression, Linear SVM, etc.)."""
    linear_types = (
        "LogisticRegression", "LogisticRegressionCV",
        "LinearSVC", "SGDClassifier",
        "LinearRegression", "Ridge", "Lasso",
    )
    return type(model).__name__ in linear_types


def create_shap_explainer(
    model: Any,
    X_background: pd.DataFrame | None = None,
) -> tuple[Any, str]:
    """Create a SHAP explainer appropriate for the given model type.

    For tree-based models (XGBoost, Random Forest), uses TreeExplainer.
    For linear models (Logistic Regression), uses LinearExplainer.
    For other models, falls back to KernelExplainer with a sample background.

    Args:
        model: Trained model object.
        X_background: Background dataset for the explainer. If None,
            uses the training data.

    Returns:
        Tuple of (explainer, explainer_type_name).

    Raises:
        ValueError: If no compatible explainer can be created.
    """
    if X_background is None:
        X_background = load_training_data()

    model_type = type(model).__name__

    if _is_tree_model(model):
        logger.info("Creating TreeExplainer for %s", model_type)
        explainer = shap.TreeExplainer(model)
        return explainer, "TreeExplainer"

    if _is_linear_model(model):
        logger.info("Creating LinearExplainer for %s", model_type)
        explainer = shap.LinearExplainer(model, X_background)
        return explainer, "LinearExplainer"

    # Fallback: KernelExplainer (slow, approximate)
    logger.warning(
        "No exact explainer for %s. Using KernelExplainer (may be slow).",
        model_type,
    )
    sample = X_background.sample(min(100, len(X_background)), random_state=42)
    explainer = shap.KernelExplainer(model.predict_proba, sample)
    return explainer, "KernelExplainer"


# ---------------------------------------------------------------------------
# SHAP value calculation
# ---------------------------------------------------------------------------


def calculate_shap_values(
    explainer: Any,
    X: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate SHAP values for given features.

    Handles different SHAP output formats:
    - ndarray shape (n_samples, n_features) — single output
    - ndarray shape (n_samples, n_features, n_classes) — multi-class
    - list of arrays — legacy format

    For binary classification, extracts the positive class (class 1) values.

    Args:
        explainer: Fitted SHAP explainer.
        X: Feature DataFrame to explain.

    Returns:
        Tuple of (shap_values_1d, base_values_per_sample) where
        shap_values_1d has shape (n_samples, n_features) for the
        positive class, and base_values_per_sample has shape (n_samples,).

    Raises:
        RuntimeError: If SHAP values cannot be computed.
    """
    try:
        raw_output = explainer.shap_values(X)
    except Exception as exc:
        raise RuntimeError(f"SHAP shap_values() failed: {exc}") from exc

    # Normalise output format to (n_samples, n_features)
    if isinstance(raw_output, list):
        # Legacy format: list of arrays, one per class
        # For binary classification, take class 1 (positive)
        if len(raw_output) >= 2:
            shap_arr = np.array(raw_output[1])
        else:
            shap_arr = np.array(raw_output[0])
    elif isinstance(raw_output, np.ndarray):
        if raw_output.ndim == 3:
            # shape (n_samples, n_features, n_classes) — take class 1
            shap_arr = raw_output[:, :, 1]
        elif raw_output.ndim == 2:
            shap_arr = raw_output
        else:
            raise RuntimeError(
                f"Unexpected SHAP output shape: {raw_output.shape}"
            )
    else:
        raise RuntimeError(f"Unexpected SHAP output type: {type(raw_output)}")

    # Get base values per sample
    base_values = _extract_base_values(explainer, len(X))

    # Validate alignment
    n_features = shap_arr.shape[1]
    if hasattr(X, "columns") and n_features != len(X.columns):
        logger.warning(
            "SHAP feature count (%d) != input feature count (%d). "
            "This may indicate a feature mismatch.",
            n_features, len(X.columns),
        )

    logger.info(
        "SHAP values computed: shape=%s, base_value_mean=%.4f",
        shap_arr.shape, float(np.mean(base_values)),
    )
    return shap_arr, base_values


def _extract_base_values(explainer: Any, n_samples: int) -> np.ndarray:
    """Extract base values from the explainer, broadcast to per-sample."""
    expected = getattr(explainer, "expected_value", None)
    if expected is None:
        return np.zeros(n_samples)

    if isinstance(expected, (int, float)):
        return np.full(n_samples, float(expected))

    expected_arr = np.array(expected)
    if expected_arr.ndim == 0:
        return np.full(n_samples, float(expected_arr))
    if expected_arr.ndim == 1:
        # Multi-class: take class 1
        if len(expected_arr) >= 2:
            return np.full(n_samples, float(expected_arr[1]))
        return np.full(n_samples, float(expected_arr[0]))
    return np.full(n_samples, float(expected_arr.flat[0]))


# ---------------------------------------------------------------------------
# Feature contribution helpers
# ---------------------------------------------------------------------------


def get_feature_contributions(
    shap_values_row: np.ndarray,
    feature_names: list[str],
) -> pd.DataFrame:
    """Map SHAP values to feature names and compute absolute importance.

    Args:
        shap_values_row: SHAP values for a single sample, shape (n_features,).
        feature_names: List of feature names.

    Returns:
        DataFrame with columns: feature, shap_value, absolute_importance,
        direction, clinical_label.
    """
    if len(shap_values_row) != len(feature_names):
        raise ValueError(
            f"SHAP value count ({len(shap_values_row)}) != "
            f"feature name count ({len(feature_names)})"
        )

    records = []
    for name, val in zip(feature_names, shap_values_row):
        abs_val = abs(float(val))
        if abs_val < NEUTRAL_TOLERANCE:
            direction = "neutral"
        elif float(val) > 0:
            direction = "increases_risk"
        else:
            direction = "decreases_risk"

        records.append({
            "feature": name,
            "shap_value": round(float(val), 6),
            "absolute_importance": round(abs_val, 6),
            "direction": direction,
            "clinical_label": CLINICAL_LABELS.get(name, name),
        })

    df = pd.DataFrame(records)
    df = df.sort_values("absolute_importance", ascending=False).reset_index(drop=True)
    return df


def get_top_features(
    shap_values_row: np.ndarray,
    feature_names: list[str],
    top_n: int = 10,
) -> pd.DataFrame:
    """Get top N most influential features by absolute SHAP value.

    Args:
        shap_values_row: SHAP values for a single sample.
        feature_names: Feature names.
        top_n: Number of top features to return.

    Returns:
        DataFrame of top features sorted by absolute importance.
    """
    contributions = get_feature_contributions(shap_values_row, feature_names)
    return contributions.head(top_n)


def get_top_risk_factors(
    shap_values_row: np.ndarray,
    feature_names: list[str],
    top_n: int = 3,
) -> pd.DataFrame:
    """Get top N features contributing toward higher predicted risk.

    Only returns features with positive SHAP values (increasing risk).
    If fewer than top_n positive contributors exist, returns available ones.

    Args:
        shap_values_row: SHAP values for a single sample.
        feature_names: Feature names.
        top_n: Maximum number of risk factors.

    Returns:
        DataFrame of positive contributors sorted by SHAP value descending.
    """
    contributions = get_feature_contributions(shap_values_row, feature_names)
    positive = contributions[contributions["direction"] == "increases_risk"]
    return positive.head(top_n)


# ---------------------------------------------------------------------------
# Local explanation
# ---------------------------------------------------------------------------


def get_local_explanation(
    shap_values_row: np.ndarray,
    base_value: float,
    feature_names: list[str],
    X_row: pd.DataFrame | None = None,
    prediction: int | None = None,
    probability: float | None = None,
) -> dict[str, Any]:
    """Build a structured local explanation for one patient.

    Args:
        shap_values_row: SHAP values for the patient.
        base_value: SHAP base value (expected model output).
        feature_names: Feature names.
        X_row: Original feature values for the patient (optional).
        prediction: Model predicted class (optional).
        probability: Model predicted probability for class 1 (optional).

    Returns:
        Structured explanation dictionary.
    """
    contributions = get_feature_contributions(shap_values_row, feature_names)

    features_list = []
    for _, row in contributions.iterrows():
        feat_name = row["feature"]
        entry: dict[str, Any] = {
            "name": feat_name,
            "clinical_label": row["clinical_label"],
            "shap_value": row["shap_value"],
            "direction": row["direction"],
            "absolute_importance": row["absolute_importance"],
        }
        if X_row is not None and feat_name in X_row.columns:
            entry["value"] = float(X_row.iloc[0][feat_name])
        features_list.append(entry)

    explanation: dict[str, Any] = {
        "base_value": round(float(base_value), 6),
        "prediction": prediction,
        "probability": round(float(probability), 6) if probability is not None else None,
        "features": features_list,
    }

    logger.info(
        "Local explanation built: prediction=%s, probability=%s, base_value=%.4f",
        prediction, probability, float(base_value),
    )
    return explanation


# ---------------------------------------------------------------------------
# Global feature importance
# ---------------------------------------------------------------------------


def get_global_feature_importance(
    shap_values: np.ndarray,
    feature_names: list[str],
) -> pd.DataFrame:
    """Compute mean absolute SHAP value for each feature across all samples.

    Args:
        shap_values: SHAP values for multiple samples, shape (n_samples, n_features).
        feature_names: Feature names.

    Returns:
        DataFrame with columns: feature, mean_absolute_shap, rank.
    """
    if shap_values.ndim != 2:
        raise ValueError(f"Expected 2D SHAP values, got shape {shap_values.shape}")

    mean_abs = np.mean(np.abs(shap_values), axis=0)
    records = []
    for name, val in zip(feature_names, mean_abs):
        records.append({
            "feature": name,
            "mean_absolute_shap": round(float(val), 6),
            "clinical_label": CLINICAL_LABELS.get(name, name),
        })

    df = pd.DataFrame(records)
    df = df.sort_values("mean_absolute_shap", ascending=False).reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)
    return df


# ---------------------------------------------------------------------------
# Human-readable summary
# ---------------------------------------------------------------------------


def generate_human_readable_summary(
    contributions: pd.DataFrame,
    patient_values: pd.Series | None = None,
    prediction: int | None = None,
    probability: float | None = None,
) -> str:
    """Generate a human-readable explanation of the model's prediction.

    Args:
        contributions: DataFrame from get_feature_contributions().
        patient_values: Patient's actual feature values (optional).
        prediction: Model predicted class.
        probability: Model predicted probability.

    Returns:
        Multi-line explanation string.
    """
    lines: list[str] = []

    if prediction is not None:
        label = "presence" if prediction == 1 else "absence"
        lines.append(f"Model prediction: {label} of heart disease")
    if probability is not None:
        lines.append(f"Model-estimated probability: {probability:.1%}")
    lines.append("")

    # Top positive contributors
    positive = contributions[contributions["direction"] == "increases_risk"].head(3)
    if len(positive) > 0:
        lines.append("Factors contributing toward higher predicted risk:")
        for i, (_, row) in enumerate(positive.iterrows(), 1):
            label = row["clinical_label"]
            val_str = ""
            if patient_values is not None and row["feature"] in patient_values.index:
                val_str = f" (value: {patient_values[row['feature']]})"
            lines.append(
                f"  {i}. {label}{val_str} "
                f"contributed positively (SHAP: {row['shap_value']:+.4f})"
            )

    # Top negative contributors
    negative = contributions[contributions["direction"] == "decreases_risk"].head(3)
    if len(negative) > 0:
        lines.append("")
        lines.append("Factors contributing toward lower predicted risk:")
        for i, (_, row) in enumerate(negative.iterrows(), 1):
            label = row["clinical_label"]
            val_str = ""
            if patient_values is not None and row["feature"] in patient_values.index:
                val_str = f" (value: {patient_values[row['feature']]})"
            lines.append(
                f"  {i}. {label}{val_str} "
                f"contributed negatively (SHAP: {row['shap_value']:+.4f})"
            )

    lines.append("")
    lines.append(
        "Note: These explanations describe model behavior and should not be "
        "interpreted as clinical causation."
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Visualisation: waterfall plot
# ---------------------------------------------------------------------------


def create_waterfall_plot(
    shap_values_row: np.ndarray,
    base_value: float,
    feature_names: list[str],
    X_row: pd.DataFrame | None = None,
    output_dir: str | Path | None = None,
    filename: str = "shap_waterfall.png",
) -> Path:
    """Create and save a SHAP waterfall plot for a single patient.

    Shows base value, feature contributions, and final model output.

    Args:
        shap_values_row: SHAP values for the patient.
        base_value: SHAP base value.
        feature_names: Feature names.
        X_row: Patient feature values (optional).
        output_dir: Directory for the saved figure.
        filename: Output filename.

    Returns:
        Path to saved waterfall plot.
    """
    if output_dir is None:
        output_dir = REPORT_DIRECTORY / "figures"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build an Explanation object for SHAP's waterfall plot
    if X_row is not None:
        data = X_row.values.flatten()
    else:
        data = np.zeros(len(feature_names))

    explanation = shap.Explanation(
        values=shap_values_row,
        base_values=base_value,
        data=data,
        feature_names=feature_names,
    )

    fig, ax = plt.subplots(figsize=(10, 7))
    shap.plots.waterfall(explanation, show=False, max_display=15)
    plt.tight_layout()
    path = output_dir / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close("all")
    logger.info("Waterfall plot saved to %s", path)
    return path


# ---------------------------------------------------------------------------
# Visualisation: global importance bar chart
# ---------------------------------------------------------------------------


def create_global_importance_plot(
    global_importance: pd.DataFrame,
    output_dir: str | Path | None = None,
    filename: str = "shap_global_importance.png",
) -> Path:
    """Create and save a bar chart of global feature importance.

    Args:
        global_importance: DataFrame from get_global_feature_importance().
        output_dir: Directory for the saved figure.
        filename: Output filename.

    Returns:
        Path to saved figure.
    """
    if output_dir is None:
        output_dir = REPORT_DIRECTORY / "figures"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = global_importance.sort_values("mean_absolute_shap", ascending=True).tail(15)

    fig, ax = plt.subplots(figsize=(8, 6))
    labels = [CLINICAL_LABELS.get(f, f) for f in df["feature"]]
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(df)))
    ax.barh(labels, df["mean_absolute_shap"], color=colors, edgecolor="black")
    ax.set_xlabel("Mean |SHAP Value|")
    ax.set_title("Global Feature Importance (SHAP)")
    fig.tight_layout()
    path = output_dir / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Global importance plot saved to %s", path)
    return path


# ---------------------------------------------------------------------------
# Visualisation: summary plot
# ---------------------------------------------------------------------------


def create_summary_plot(
    shap_values: np.ndarray,
    feature_names: list[str],
    X: pd.DataFrame | None = None,
    output_dir: str | Path | None = None,
    filename: str = "shap_summary.png",
) -> Path:
    """Create and save a SHAP summary (beeswarm) plot.

    Args:
        shap_values: SHAP values for multiple samples.
        feature_names: Feature names.
        X: Feature DataFrame (optional, used for dot colors).
        output_dir: Directory for the saved figure.
        filename: Output filename.

    Returns:
        Path to saved figure.
    """
    if output_dir is None:
        output_dir = REPORT_DIRECTORY / "figures"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    shap.summary_plot(
        shap_values,
        features=X.values if X is not None else None,
        feature_names=feature_names,
        show=False,
        max_display=15,
    )
    plt.tight_layout()
    path = output_dir / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close("all")
    logger.info("Summary plot saved to %s", path)
    return path


# ---------------------------------------------------------------------------
# Visualisation: local importance (horizontal bar)
# ---------------------------------------------------------------------------


def create_local_importance_plot(
    contributions: pd.DataFrame,
    output_dir: str | Path | None = None,
    filename: str = "shap_local_importance.png",
) -> Path:
    """Create and save a horizontal bar chart of local feature importance.

    Shows top 10 features with positive/negative contributions.

    Args:
        contributions: DataFrame from get_feature_contributions().
        output_dir: Directory for the saved figure.
        filename: Output filename.

    Returns:
        Path to saved figure.
    """
    if output_dir is None:
        output_dir = REPORT_DIRECTORY / "figures"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    top = contributions.head(10).sort_values("shap_value", ascending=True)

    fig, ax = plt.subplots(figsize=(8, 6))
    labels = [CLINICAL_LABELS.get(f, f) for f in top["feature"]]
    colors = ["#e74c3c" if v > 0 else "#3498db" for v in top["shap_value"]]
    ax.barh(labels, top["shap_value"], color=colors, edgecolor="black")
    ax.axvline(x=0, color="black", linewidth=0.8)
    ax.set_xlabel("SHAP Value")
    ax.set_title("Patient Feature Contributions")
    fig.tight_layout()
    path = output_dir / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Local importance plot saved to %s", path)
    return path


# ---------------------------------------------------------------------------
# Artifact export
# ---------------------------------------------------------------------------


def save_global_importance_csv(
    global_importance: pd.DataFrame,
    output_dir: str | Path | None = None,
) -> Path:
    """Save global feature importance to CSV.

    Args:
        global_importance: DataFrame from get_global_feature_importance().
        output_dir: Output directory.

    Returns:
        Path to saved CSV.
    """
    if output_dir is None:
        output_dir = REPORT_DIRECTORY / "explainability"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / "shap_global_importance.csv"
    global_importance.to_csv(path, index=False)
    logger.info("Global importance CSV saved to %s", path)
    return path


def save_local_explanation_json(
    explanation: dict[str, Any],
    output_dir: str | Path | None = None,
) -> Path:
    """Save a local explanation to JSON.

    Args:
        explanation: Dict from get_local_explanation().
        output_dir: Output directory.

    Returns:
        Path to saved JSON.
    """
    if output_dir is None:
        output_dir = REPORT_DIRECTORY / "explainability"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / "shap_local_explanation.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(explanation, f, indent=2, default=str)
    logger.info("Local explanation saved to %s", path)
    return path


def save_explainer_metadata(
    model_name: str,
    explainer_type: str,
    feature_names: list[str],
    background_source: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Save explainer metadata to JSON.

    Args:
        model_name: Name of the model being explained.
        explainer_type: Type of SHAP explainer used.
        feature_names: Feature names.
        background_source: Description of background data source.
        output_dir: Output directory.

    Returns:
        Path to saved JSON.
    """
    import shap as shap_module

    if output_dir is None:
        output_dir = REPORT_DIRECTORY / "explainability"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "best_model": model_name,
        "model_type": model_name,
        "explainer_type": explainer_type,
        "shap_version": shap_module.__version__,
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "background_data_source": background_source,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    path = output_dir / "explainer_metadata.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Explainer metadata saved to %s", path)
    return path


def save_explainability_summary(
    model_name: str,
    explainer_type: str,
    global_importance: pd.DataFrame,
    local_explanation: dict[str, Any] | None,
    output_dir: str | Path | None = None,
) -> Path:
    """Save explainability summary report.

    Args:
        model_name: Name of the model.
        explainer_type: Type of SHAP explainer.
        global_importance: Global feature importance DataFrame.
        local_explanation: Local explanation dict (optional).
        output_dir: Output directory.

    Returns:
        Path to saved JSON.
    """
    if output_dir is None:
        output_dir = REPORT_DIRECTORY / "explainability"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    top_global = global_importance.head(10).to_dict("records")

    summary: dict[str, Any] = {
        "model": model_name,
        "explainer": explainer_type,
        "feature_count": len(global_importance),
        "top_global_features": top_global,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if local_explanation is not None:
        summary["prediction"] = local_explanation.get("prediction")
        summary["probability"] = local_explanation.get("probability")
        summary["base_value"] = local_explanation.get("base_value")
        top_local = [
            f for f in local_explanation.get("features", [])
            if f["direction"] == "increases_risk"
        ][:3]
        summary["local_top_features"] = top_local

    path = output_dir / "explainability_summary.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info("Explainability summary saved to %s", path)
    return path
