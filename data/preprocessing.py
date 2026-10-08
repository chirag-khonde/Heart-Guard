"""Data preprocessing pipeline for HeartGuard.

Implements a scikit-learn-based preprocessing pipeline that handles
missing values, categorical encoding, and feature scaling. Designed
to prevent data leakage by fitting only on training data.

Usage::

    from src.data.loader import load_cleveland_dataset
    from src.data.preprocessing import (
        split_dataset,
        create_preprocessor,
        fit_preprocessor,
        transform_data,
    )

    df = load_cleveland_dataset()
    X_train, X_test, y_train, y_test = split_dataset(df)
    preprocessor = fit_preprocessor(X_train)
    X_train_t, X_test_t = transform_data(preprocessor, X_train, X_test)
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

from src.data.features import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Dataset splitting
# ---------------------------------------------------------------------------


def split_dataset(
    df: pd.DataFrame,
    test_size: float = 0.20,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split a DataFrame into train/test sets with stratification.

    The split is performed BEFORE any preprocessing to prevent data leakage.

    Args:
        df: DataFrame containing features and the target column.
        test_size: Fraction of data for testing (default 0.20).
        random_state: Random seed for reproducibility (default 42).

    Returns:
        Tuple of (X_train, X_test, y_train, y_test).

    Raises:
        ValueError: If target column is not present in df.
    """
    if TARGET_COLUMN not in df.columns:
        raise ValueError(
            f"Target column '{TARGET_COLUMN}' not found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    # Handle edge cases where sklearn's train_test_split fails
    if len(df) == 0:
        logger.warning("Empty DataFrame provided to split_dataset.")
        return X, X, y, y

    if len(df) == 1:
        logger.warning("Single-row DataFrame: returning full data as train, empty test.")
        return X, X.iloc[:0], y, y.iloc[:0]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    logger.info(
        "Train/test split: train=%d, test=%d (test_size=%.0f%%)",
        len(X_train), len(X_test), test_size * 100,
    )
    logger.info("Target distribution — train: %s, test: %s",
                y_train.value_counts().to_dict(),
                y_test.value_counts().to_dict())

    return X_train, X_test, y_train, y_test


# ---------------------------------------------------------------------------
# Preprocessing pipeline
# ---------------------------------------------------------------------------


def create_preprocessor(
    numerical_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
) -> ColumnTransformer:
    """Create an unfitted preprocessing ColumnTransformer.

    Numerical features: median imputation + min-max scaling.
    Categorical features: most-frequent imputation + one-hot encoding.

    Args:
        numerical_features: List of numerical column names. Defaults to
            the canonical NUMERICAL_FEATURES.
        categorical_features: List of categorical column names. Defaults to
            the canonical CATEGORICAL_FEATURES.

    Returns:
        Unfitted ColumnTransformer.
    """
    if numerical_features is None:
        numerical_features = list(NUMERICAL_FEATURES)
    if categorical_features is None:
        categorical_features = list(CATEGORICAL_FEATURES)

    # Filter to columns that actually exist in the data (checked at fit time)
    numerical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", MinMaxScaler()),
    ])

    categorical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    # Use 'passthrough' for columns not in either list — ColumnTransformer
    # will raise if columns are not covered; we handle that in fit_preprocessor.
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numerical_pipeline, numerical_features),
            ("cat", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

    logger.info(
        "Preprocessor created: %d numerical, %d categorical",
        len(numerical_features), len(categorical_features),
    )
    return preprocessor


def fit_preprocessor(
    X_train: pd.DataFrame,
    numerical_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
) -> ColumnTransformer:
    """Fit a preprocessing pipeline on training data only.

    This is the critical function that enforces no data leakage:
    the imputer and scaler are fit exclusively on X_train.

    Args:
        X_train: Training features.
        numerical_features: Optional override for numerical columns.
        categorical_features: Optional override for categorical columns.

    Returns:
        Fitted ColumnTransformer ready for transform_data().
    """
    if numerical_features is None:
        numerical_features = [c for c in NUMERICAL_FEATURES if c in X_train.columns]
    if categorical_features is None:
        categorical_features = [c for c in CATEGORICAL_FEATURES if c in X_train.columns]

    preprocessor = create_preprocessor(numerical_features, categorical_features)
    preprocessor.fit(X_train)

    logger.info("Preprocessor fitted on %d training samples", len(X_train))
    return preprocessor


def transform_data(
    preprocessor: ColumnTransformer,
    *dataframes: pd.DataFrame,
) -> list[pd.DataFrame]:
    """Transform one or more DataFrames using a fitted preprocessor.

    Args:
        preprocessor: Fitted ColumnTransformer.
        *dataframes: One or more DataFrames to transform.

    Returns:
        List of transformed DataFrames (same order as input).
    """
    results: list[pd.DataFrame] = []

    # Get feature names after transformation
    feature_names = preprocessor.get_feature_names_out()

    for i, df in enumerate(dataframes):
        transformed = preprocessor.transform(df)
        out_df = pd.DataFrame(transformed, columns=feature_names, index=df.index)
        results.append(out_df)
        logger.info("Transformed DataFrame %d: %d rows x %d cols", i, *out_df.shape)

    return results


# ---------------------------------------------------------------------------
# Feature name recovery
# ---------------------------------------------------------------------------


def get_feature_names(preprocessor: ColumnTransformer) -> list[str]:
    """Recover meaningful feature names from a fitted preprocessor.

    Returns the output feature names after one-hot encoding so that
    downstream modules (model analysis, SHAP, visualisations) can use
    human-readable names instead of generic ``feature_0``, ``feature_1``.

    Args:
        preprocessor: A fitted ColumnTransformer.

    Returns:
        List of output feature name strings.
    """
    names = preprocessor.get_feature_names_out()
    return list(names)


# ---------------------------------------------------------------------------
# Missing-value and duplicate analysis
# ---------------------------------------------------------------------------


def get_missing_value_report(df: pd.DataFrame) -> pd.DataFrame:
    """Generate a missing-value report for a DataFrame.

    Returns a DataFrame with columns: column, missing_count, missing_percentage.

    Args:
        df: DataFrame to analyse.

    Returns:
        DataFrame with one row per column (sorted by missing percentage desc).
    """
    total = len(df)
    missing = df.isnull().sum()
    report = pd.DataFrame({
        "column": missing.index,
        "missing_count": missing.values,
        "missing_percentage": (missing.values / total * 100).round(2),
    })
    report = report.sort_values("missing_percentage", ascending=False).reset_index(drop=True)
    return report


def get_duplicate_report(df: pd.DataFrame) -> dict:
    """Analyse duplicate rows in a DataFrame.

    Args:
        df: DataFrame to inspect.

    Returns:
        Dict with total_rows, duplicate_rows, duplicate_percentage.
    """
    total = len(df)
    dup_count = int(df.duplicated().sum())
    return {
        "total_rows": total,
        "duplicate_rows": dup_count,
        "duplicate_percentage": round(dup_count / total * 100, 2) if total > 0 else 0.0,
    }


def remove_exact_duplicates(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
    """Remove exact duplicate rows and log the action.

    Args:
        df: DataFrame to deduplicate.
        inplace: If True, modify df in place.

    Returns:
        DataFrame without exact duplicate rows.
    """
    before = len(df)
    if inplace:
        df.drop_duplicates(inplace=True)
        after = len(df)
    else:
        df = df.drop_duplicates()
        after = len(df)
    removed = before - after
    if removed > 0:
        logger.info("Removed %d exact duplicate rows (%d -> %d)", removed, before, after)
    return df


# ---------------------------------------------------------------------------
# Save processed data
# ---------------------------------------------------------------------------


def save_processed_data(
    df: pd.DataFrame,
    filename: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Save a processed DataFrame to the data/processed directory.

    Args:
        df: DataFrame to save.
        filename: Name of the output CSV file.
        output_dir: Override output directory. Defaults to data/processed/.

    Returns:
        Path to the saved file.
    """
    from config.settings import PROCESSED_DATA_DIRECTORY

    if output_dir is None:
        output_dir = PROCESSED_DATA_DIRECTORY
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    df.to_csv(path, index=False)
    logger.info("Saved processed data to %s (%d rows x %d cols)", path, len(df), len(df.columns))
    return path


def save_preprocessor(preprocessor: ColumnTransformer, path: str | Path | None = None) -> Path:
    """Persist a fitted preprocessor to disk.

    Args:
        preprocessor: Fitted ColumnTransformer.
        path: File path. Defaults to models/preprocessor.pkl.

    Returns:
        Path to the saved file.
    """
    from config.settings import MODEL_DIRECTORY

    if path is None:
        path = MODEL_DIRECTORY / "preprocessor.pkl"
    else:
        path = Path(path)

    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, path)
    logger.info("Preprocessor saved to %s", path)
    return path


def load_preprocessor(path: str | Path) -> ColumnTransformer:
    """Load a previously saved preprocessor.

    Args:
        path: File path to the pickled preprocessor.

    Returns:
        Loaded ColumnTransformer.
    """
    path = Path(path)
    preprocessor = joblib.load(path)
    logger.info("Preprocessor loaded from %s", path)
    return preprocessor
