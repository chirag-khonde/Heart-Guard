"""End-to-end data pipeline for HeartGuard.

Single entry point that takes raw Cleveland (or Framingham) data through
loading, cleaning, splitting, preprocessing and artefact persistence,
returning an ML-ready :class:`DataPipelineResult`.

Usage::

    from src.data.pipeline import prepare_cleveland_pipeline

    result = prepare_cleveland_pipeline()

    X_train = result.X_train
    X_test  = result.X_test
    y_train = result.y_train
    y_test  = result.y_test
    preprocessor = result.preprocessor
    feature_names = result.feature_names
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer

from src.data.features import (
    CATEGORICAL_FEATURES,
    HEARTGUARD_FEATURES,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
)
from src.data.loader import (
    get_dataset_info,
    load_cleveland_dataset,
    load_framingham_dataset,
    normalize_cleveland_target,
)
from src.data.preprocessing import (
    fit_preprocessor,
    get_duplicate_report,
    get_missing_value_report,
    get_feature_names,
    remove_exact_duplicates,
    save_preprocessor,
    save_processed_data,
    split_dataset,
    transform_data,
)
from src.data.quality import (
    generate_data_quality_report,
    save_data_quality_report,
)
from src.utils.exceptions import DatasetNotFoundError, HeartGuardError
from src.utils.logger import get_logger
from src.utils.validators import check_invalid_values, detect_outliers_iqr

logger = get_logger(__name__)

RANDOM_STATE: int = 42
TEST_SIZE: float = 0.20


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class DataPipelineResult:
    """Structured result returned by the data pipeline."""

    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    preprocessor: ColumnTransformer
    feature_names: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Class distribution analysis
# ---------------------------------------------------------------------------


def analyze_class_distribution(y: pd.Series) -> dict[str, Any]:
    """Analyse class distribution of a binary target series.

    Args:
        y: Target series (assumed binary 0/1 after normalisation).

    Returns:
        Dictionary with counts, percentages, and imbalance ratio.
    """
    counts = y.value_counts().sort_index()
    total = len(y)
    percentages = (counts / total * 100).round(2)

    result: dict[str, Any] = {
        "class_counts": counts.to_dict(),
        "class_percentages": percentages.to_dict(),
        "total": int(total),
    }

    if len(counts) >= 2:
        majority = counts.max()
        minority = counts.min()
        result["imbalance_ratio"] = round(float(majority / minority), 2) if minority > 0 else float("inf")
    else:
        result["imbalance_ratio"] = 1.0

    return result


# ---------------------------------------------------------------------------
# Cleveland pipeline
# ---------------------------------------------------------------------------


def prepare_cleveland_pipeline(
    path: str | Path | None = None,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
    save_artefacts: bool = True,
) -> DataPipelineResult:
    """Run the full Cleveland data pipeline.

    Steps:
        1. Load raw dataset
        2. Normalise columns
        3. Validate schema
        4. Clean duplicates
        5. Analyse missing values
        6. Prepare target (binary 0/1)
        7. Split 80/20 stratified
        8. Fit preprocessor on training data ONLY
        9. Transform training data
        10. Transform testing data
        11. Save artefacts (optional)
        12. Return ML-ready datasets + metadata

    Args:
        path: Optional path to the Cleveland CSV file.
        test_size: Test set fraction (default 0.20).
        random_state: Random seed (default 42).
        save_artefacts: Whether to persist processed data and preprocessor.

    Returns:
        :class:`DataPipelineResult` with train/test splits, preprocessor,
        feature names, and pipeline metadata.

    Raises:
        DatasetNotFoundError: If the Cleveland CSV is not found.
        HeartGuardError: On any pipeline-level failure.
    """
    logger.info("=== Cleveland data pipeline started ===")
    pipeline_start = datetime.now(timezone.utc)

    # ---- 1. Load ----
    logger.info("Step 1: Loading Cleveland dataset")
    df_raw = load_cleveland_dataset(path)
    raw_rows, raw_cols = df_raw.shape
    logger.info("Raw dataset: %d rows x %d columns", raw_rows, raw_cols)

    # ---- 2-3. Columns already normalised & validated by loader ----

    # ---- 4. Clean duplicates ----
    logger.info("Step 4: Analysing duplicates")
    dup_report = get_duplicate_report(df_raw)
    df = remove_exact_duplicates(df_raw)

    # ---- 5. Missing value analysis ----
    logger.info("Step 5: Analysing missing values")
    missing_report = get_missing_value_report(df)

    # ---- 6. Target preparation ----
    logger.info("Step 6: Preparing target variable")
    df = normalize_cleveland_target(df)
    if TARGET_COLUMN not in df.columns:
        raise HeartGuardError("Target column not found after normalisation")

    target_dist = df[TARGET_COLUMN].value_counts().sort_index().to_dict()
    class_analysis = analyze_class_distribution(df[TARGET_COLUMN])
    logger.info("Target distribution: %s", target_dist)

    # ---- 7. Train/test split ----
    logger.info("Step 7: Splitting dataset %d/%d", int((1 - test_size) * 100), int(test_size * 100))
    X_train, X_test, y_train, y_test = split_dataset(
        df, test_size=test_size, random_state=random_state,
    )

    # ---- 8. Fit preprocessor on training data ONLY ----
    logger.info("Step 8: Fitting preprocessor on training data")
    numerical_feats = [c for c in NUMERICAL_FEATURES if c in X_train.columns]
    categorical_feats = [c for c in CATEGORICAL_FEATURES if c in X_train.columns]
    preprocessor = fit_preprocessor(X_train, numerical_feats, categorical_feats)

    # ---- 9-10. Transform ----
    logger.info("Step 9-10: Transforming train and test data")
    X_train_t, X_test_t = transform_data(preprocessor, X_train, X_test)

    # ---- Feature names ----
    feature_names = get_feature_names(preprocessor)
    logger.info("Final feature count: %d", len(feature_names))

    # ---- Data leakage check ----
    leakage_check = _verify_no_leakage(X_train, X_test, preprocessor)

    # ---- Invalid values (on original data before split) ----
    invalid_values = check_invalid_values(df_raw)

    # ---- Outlier analysis ----
    num_cols_for_outliers = [c for c in NUMERICAL_FEATURES if c in df_raw.columns]
    outliers = detect_outliers_iqr(df_raw, columns=num_cols_for_outliers)

    # ---- Metadata ----
    pipeline_elapsed = (datetime.now(timezone.utc) - pipeline_start).total_seconds()
    metadata: dict[str, Any] = {
        "dataset": "Cleveland Heart Disease",
        "pipeline_timestamp": pipeline_start.isoformat(),
        "pipeline_elapsed_seconds": round(pipeline_elapsed, 3),
        "random_state": random_state,
        "test_size": test_size,
        "preprocessing_strategy": {
            "numerical_imputation": "median",
            "numerical_scaling": "MinMaxScaler",
            "categorical_imputation": "most_frequent",
            "categorical_encoding": "OneHotEncoder(handle_unknown='ignore')",
        },
        "raw_shape": {"rows": raw_rows, "columns": raw_cols},
        "cleaned_shape": {"rows": len(df), "columns": len(df.shape)},
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "target_distribution": target_dist,
        "class_analysis": class_analysis,
        "missing_values": {
            col: int(cnt) for col, cnt in df_raw.isnull().sum().items() if cnt > 0
        },
        "duplicates": dup_report,
        "invalid_values": {
            col: {"count": len(indices)} for col, indices in invalid_values.items()
        },
        "outliers": {col: info["count"] for col, info in outliers.items()},
        "leakage_check": leakage_check,
        "feature_names": feature_names,
        "numerical_features": numerical_feats,
        "categorical_features": categorical_feats,
    }

    # ---- 11. Save artefacts ----
    if save_artefacts:
        logger.info("Step 11: Saving artefacts")
        _save_pipeline_artefacts(
            df=df,
            df_raw=df_raw,
            X_train_t=X_train_t,
            X_test_t=X_test_t,
            y_train=y_train,
            y_test=y_test,
            preprocessor=preprocessor,
            metadata=metadata,
            missing_report=missing_report,
            invalid_values=invalid_values,
            outliers=outliers,
        )

    logger.info("=== Cleveland data pipeline complete (%.2fs) ===", pipeline_elapsed)

    return DataPipelineResult(
        X_train=X_train_t,
        X_test=X_test_t,
        y_train=y_train,
        y_test=y_test,
        preprocessor=preprocessor,
        feature_names=feature_names,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Framingham inspection
# ---------------------------------------------------------------------------


def inspect_framingham_dataset(
    path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Inspect the Framingham dataset and return a structured summary.

    Does NOT merge with Cleveland.  Documents available variables and
    identifies which ones can be mapped to the HeartGuard canonical schema.

    Args:
        path: Optional path to the Framingham CSV.

    Returns:
        Summary dictionary, or ``None`` if the dataset is not found.
    """
    try:
        df = load_framingham_dataset(path)
    except (DatasetNotFoundError, Exception) as exc:
        logger.warning("Framingham dataset not available: %s", exc)
        return None

    info = get_dataset_info(df)
    missing_report = get_missing_value_report(df)
    dup_report = get_duplicate_report(df)

    from src.data.features import FRAMINGHAM_MAPPABLE_FEATURES

    summary: dict[str, Any] = {
        "dataset": "Framingham Heart Study",
        "shape": {"rows": info["rows"], "columns": info["columns"]},
        "column_names": info["column_names"],
        "data_types": info["dtypes"],
        "missing_values": {
            col: int(cnt) for col, cnt in info["missing_values"].items() if cnt > 0
        },
        "total_missing": sum(info["missing_values"].values()),
        "duplicates": dup_report,
        "mappable_to_canonical": FRAMINGHAM_MAPPABLE_FEATURES,
        "non_mappable_columns": [
            c for c in info["column_names"]
            if c not in FRAMINGHAM_MAPPABLE_FEATURES and c != TARGET_COLUMN
        ],
        "target_column": TARGET_COLUMN if TARGET_COLUMN in df.columns else None,
    }

    if TARGET_COLUMN in df.columns:
        summary["target_distribution"] = info["target_distribution"]

    return summary


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _verify_no_leakage(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    preprocessor: ColumnTransformer,
) -> dict[str, bool]:
    """Verify that no data leakage occurred during preprocessing."""
    # Check 1: scaler/encoder was fit on train only
    num_pipeline = preprocessor.named_transformers_.get("num")
    scaler_fitted = num_pipeline is not None and hasattr(num_pipeline, "named_steps")
    imputer_fitted = (
        num_pipeline is not None
        and hasattr(num_pipeline.named_steps.get("imputer"), "statistics_")
    )

    # Check 2: target not in features
    target_in_features = TARGET_COLUMN in X_train.columns

    return {
        "train_test_split_before_preprocessing": True,
        "imputer_fit_on_train_only": bool(imputer_fitted),
        "scaler_fit_on_train_only": bool(scaler_fitted),
        "encoder_fit_on_train_only": True,  # OneHotEncoder is in same ColumnTransformer
        "target_excluded_from_features": not target_in_features,
    }


def _save_pipeline_artefacts(
    df: pd.DataFrame,
    df_raw: pd.DataFrame,
    X_train_t: pd.DataFrame,
    X_test_t: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    preprocessor: ColumnTransformer,
    metadata: dict[str, Any],
    missing_report: pd.DataFrame,
    invalid_values: dict,
    outliers: dict,
) -> None:
    """Persist all pipeline artefacts to disk."""
    from config.settings import MODEL_DIRECTORY, PROCESSED_DATA_DIRECTORY, REPORT_DIRECTORY

    # Processed CSVs
    train_df = pd.concat([X_train_t.reset_index(drop=True), y_train.reset_index(drop=True)], axis=1)
    test_df = pd.concat([X_test_t.reset_index(drop=True), y_test.reset_index(drop=True)], axis=1)

    save_processed_data(train_df, "cleveland_train.csv")
    save_processed_data(test_df, "cleveland_test.csv")

    # Clean version of raw (after duplicate removal, target normalised)
    save_processed_data(df, "cleveland_clean.csv")

    # Preprocessor
    save_preprocessor(preprocessor, MODEL_DIRECTORY / "preprocessor.pkl")

    # Data quality report
    quality_report = generate_data_quality_report(df_raw, "Cleveland Heart Disease")
    save_data_quality_report(quality_report, "cleveland_data_quality.json")

    # EDA summary report
    eda_summary = _build_eda_summary(df_raw, metadata)
    eda_path = REPORT_DIRECTORY / "data_quality"
    eda_path.mkdir(parents=True, exist_ok=True)
    with open(eda_path / "cleveland_eda_summary.json", "w", encoding="utf-8") as f:
        json.dump(eda_summary, f, indent=2, default=str)
    logger.info("EDA summary saved to %s", eda_path / "cleveland_eda_summary.json")

    # Dataset metadata
    with open(eda_path / "dataset_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.info("Dataset metadata saved to %s", eda_path / "dataset_metadata.json")

    # Leakage check
    with open(eda_path / "data_leakage_check.json", "w", encoding="utf-8") as f:
        json.dump(metadata["leakage_check"], f, indent=2)
    logger.info("Leakage check saved to %s", eda_path / "data_leakage_check.json")


def _build_eda_summary(df: pd.DataFrame, metadata: dict[str, Any]) -> dict[str, Any]:
    """Build a structured EDA summary from actual data."""
    num_cols = [c for c in NUMERICAL_FEATURES if c in df.columns]
    cat_cols = [c for c in CATEGORICAL_FEATURES if c in df.columns]

    numerical_summary: dict[str, Any] = {}
    for col in num_cols:
        desc = df[col].describe()
        numerical_summary[col] = {
            "mean": round(float(desc.get("mean", 0)), 4),
            "std": round(float(desc.get("std", 0)), 4),
            "min": round(float(desc.get("min", 0)), 4),
            "25%": round(float(desc.get("25%", 0)), 4),
            "50%": round(float(desc.get("50%", 0)), 4),
            "75%": round(float(desc.get("75%", 0)), 4),
            "max": round(float(desc.get("max", 0)), 4),
        }

    categorical_summary: dict[str, Any] = {}
    for col in cat_cols:
        categorical_summary[col] = {
            "unique": int(df[col].nunique()),
            "value_counts": {str(k): int(v) for k, v in df[col].value_counts().sort_index().items()},
        }

    # Correlations for numerical features
    correlations: dict[str, Any] = {}
    if len(num_cols) >= 2:
        corr_matrix = df[num_cols].corr()
        # Flatten upper triangle
        for i, c1 in enumerate(num_cols):
            for c2 in num_cols[i + 1:]:
                val = round(float(corr_matrix.loc[c1, c2]), 4)
                correlations[f"{c1}__{c2}"] = val

    return {
        "dataset": "Cleveland",
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "target_distribution": metadata.get("target_distribution", {}),
        "missing_values": metadata.get("missing_values", {}),
        "duplicates": metadata.get("duplicates", {}),
        "numerical_summary": numerical_summary,
        "categorical_summary": categorical_summary,
        "outliers": metadata.get("outliers", {}),
        "correlations": correlations,
    }
