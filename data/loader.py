"""Data loading utilities for HeartGuard.

Provides functions for loading, validating, and inspecting the Cleveland
and Framingham datasets. Handles column normalization, schema validation,
and dataset metadata.
"""

from pathlib import Path

import pandas as pd

from src.data.features import (
    CLEVELAND_ALT_NAMES,
    CLEVELAND_COLUMN_MAP,
    CLEVELAND_STANDARD_COLUMNS,
    CLEVELAND_14_COLUMNS,
    TARGET_COLUMN,
)
from src.utils.exceptions import (
    DatasetEmptyError,
    DatasetFormatError,
    DatasetNotFoundError,
    DatasetSchemaError,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def validate_dataset_exists(path: str | Path) -> bool:
    """Check if a dataset file exists and is non-empty.

    Args:
        path: Path to the dataset file.

    Returns:
        True if file exists and has content.

    Raises:
        DatasetNotFoundError: If file does not exist.
        DatasetEmptyError: If file is empty.
    """
    path = Path(path)

    if not path.exists():
        raise DatasetNotFoundError(str(path))

    if path.stat().st_size == 0:
        raise DatasetEmptyError(str(path))

    return True


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV file into a DataFrame.

    Args:
        path: Path to the CSV file.

    Returns:
        Loaded DataFrame.

    Raises:
        DatasetNotFoundError: If file does not exist.
        DatasetEmptyError: If file is empty.
        DatasetFormatError: If file cannot be parsed as CSV.
    """
    path = Path(path)
    validate_dataset_exists(path)

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise DatasetFormatError(str(path), reason=str(exc)) from exc

    if df.empty:
        raise DatasetEmptyError(str(path))

    logger.info("Loaded %s: %d rows x %d columns", path.name, len(df), len(df.columns))
    return df


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame column names to lowercase and strip whitespace.

    Args:
        df: DataFrame whose columns to normalize.

    Returns:
        DataFrame with normalized column names (new copy).
    """
    df = df.copy()
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    logger.info("Normalized column names: %s", list(df.columns))
    return df


def get_dataset_info(df: pd.DataFrame) -> dict:
    """Get structured information about a DataFrame.

    Args:
        df: DataFrame to inspect.

    Returns:
        Dictionary with rows, columns, column_names, missing_values,
        duplicates, dtypes, and target_distribution.
    """
    target_dist: dict = {}
    if TARGET_COLUMN in df.columns:
        target_dist = df[TARGET_COLUMN].value_counts().to_dict()

    info: dict = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict(),
        "duplicates": int(df.duplicated().sum()),
        "target_distribution": target_dist,
    }

    logger.info("Dataset info: %d rows x %d columns", info["rows"], info["columns"])
    return info


# ---------------------------------------------------------------------------
# Column mapping
# ---------------------------------------------------------------------------


def _apply_column_mapping(
    df: pd.DataFrame,
    mapping: dict[str, str],
    alt_names: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Apply an explicit column-name mapping to a DataFrame.

    Only renames columns that are actually present in the DataFrame.

    Args:
        df: DataFrame to rename.
        mapping: Primary mapping {source: canonical}.
        alt_names: Alternative source names that also map to canonical.

    Returns:
        DataFrame with mapped column names (new copy).
    """
    df = df.copy()
    rename_plan: dict[str, str] = {}

    for src, canonical in mapping.items():
        if src in df.columns and src != canonical:
            rename_plan[src] = canonical

    if alt_names:
        for src, canonical in alt_names.items():
            if src in df.columns and src != canonical and src not in rename_plan:
                rename_plan[src] = canonical

    if rename_plan:
        df = df.rename(columns=rename_plan)
        logger.info("Column mapping applied: %s", rename_plan)

    return df


# ---------------------------------------------------------------------------
# Cleveland dataset
# ---------------------------------------------------------------------------


def load_cleveland_dataset(
    path: str | Path | None = None,
) -> pd.DataFrame:
    """Load and prepare the Cleveland Heart Disease dataset.

    Steps:
        1. Load CSV.
        2. Normalize column names.
        3. Apply canonical column mapping.
        4. Validate required columns are present.

    Args:
        path: Path to the Cleveland CSV. If None, uses the default
              location ``data/raw/heart.csv``.

    Returns:
        Prepared DataFrame with canonical column names.

    Raises:
        DatasetNotFoundError: If file does not exist.
        DatasetSchemaError: If required columns are missing after mapping.
    """
    from config.settings import RAW_DATA_DIRECTORY

    if path is None:
        candidates = ["heart.csv", "heart_disease.csv", "cleveland.csv"]
        for name in candidates:
            candidate = RAW_DATA_DIRECTORY / name
            if candidate.exists():
                path = candidate
                break
        if path is None:
            path = RAW_DATA_DIRECTORY / "heart.csv"

    df = load_csv(path)
    df = normalize_column_names(df)

    # Detect whether we have standard 13/14-column Cleveland format
    standard_cols = CLEVELAND_STANDARD_COLUMNS & set(df.columns)
    has_14 = bool(CLEVELAND_14_COLUMNS & set(df.columns))

    if len(standard_cols) >= 10 or has_14:
        df = _apply_column_mapping(df, CLEVELAND_COLUMN_MAP, CLEVELAND_ALT_NAMES)
    else:
        logger.warning(
            "Cleveland CSV has non-standard columns (%s). "
            "Applying mapping anyway.",
            list(df.columns),
        )
        df = _apply_column_mapping(df, CLEVELAND_COLUMN_MAP, CLEVELAND_ALT_NAMES)

    # Validate required canonical columns
    required = list(CLEVELAND_COLUMN_MAP.values())
    validate_required_columns(df, required, dataset_name="Cleveland")

    return df


def prepare_cleveland_dataset(
    path: str | Path | None = None,
) -> pd.DataFrame:
    """Load, map, and normalize the Cleveland target variable.

    This is the main entry point for obtaining a clean Cleveland DataFrame.

    Args:
        path: Optional path override.

    Returns:
        DataFrame with canonical columns and binary target (0/1).
    """
    df = load_cleveland_dataset(path)
    df = normalize_cleveland_target(df)
    return df


def normalize_cleveland_target(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize the Cleveland target to binary 0/1.

    Many Cleveland CSV exports use a severity scale (0-4) where:
        0 = absence
        1-4 = presence of heart disease

    Args:
        df: DataFrame with a 'target' column.

    Returns:
        DataFrame with binary target.
    """
    df = df.copy()
    if TARGET_COLUMN not in df.columns:
        logger.warning("No target column found — returning DataFrame unchanged.")
        return df

    unique_vals = sorted(df[TARGET_COLUMN].dropna().unique())
    logger.info("Cleveland target unique values before normalization: %s", unique_vals)

    if set(unique_vals).issubset({0, 1}):
        logger.info("Target is already binary (0/1).")
        return df

    # Map any non-zero value to 1 (presence)
    df[TARGET_COLUMN] = (df[TARGET_COLUMN] > 0).astype(int)
    new_dist = df[TARGET_COLUMN].value_counts().to_dict()
    logger.info("Target normalized to binary. Distribution: %s", new_dist)
    return df


# ---------------------------------------------------------------------------
# Framingham dataset
# ---------------------------------------------------------------------------


def load_framingham_dataset(
    path: str | Path | None = None,
) -> pd.DataFrame:
    """Load the Framingham Heart Study dataset.

    The Framingham dataset is loaded and column names are normalized,
    but no automatic feature mapping to the Cleveland canonical schema
    is applied. Feature-level integration decisions are deferred to
    later phases.

    Args:
        path: Path to the Framingham CSV. If None, uses the default
              location ``data/raw/framingham.csv``.

    Returns:
        DataFrame with normalized column names.

    Raises:
        DatasetNotFoundError: If file does not exist.
        DatasetEmptyError: If file is empty.
    """
    from config.settings import RAW_DATA_DIRECTORY

    if path is None:
        candidates = ["framingham.csv", " Framingham.csv"]
        for name in candidates:
            candidate = RAW_DATA_DIRECTORY / name.strip()
            if candidate.exists():
                path = candidate
                break
        if path is None:
            path = RAW_DATA_DIRECTORY / "framingham.csv"

    df = load_csv(path)
    df = normalize_column_names(df)
    logger.info("Framingham dataset loaded: %d rows x %d columns", len(df), len(df.columns))
    return df


def prepare_framingham_dataset(
    path: str | Path | None = None,
) -> pd.DataFrame:
    """Load and basic-prepare the Framingham dataset.

    Returns a DataFrame with normalized column names. No feature mapping
    to the Cleveland schema is forced.

    Args:
        path: Optional path override.

    Returns:
        DataFrame with normalized column names.
    """
    return load_framingham_dataset(path)


# ---------------------------------------------------------------------------
# Column validation
# ---------------------------------------------------------------------------


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str = "dataset",
) -> bool:
    """Validate that a DataFrame contains all required columns.

    Args:
        df: DataFrame to validate.
        required_columns: List of column names that must exist.
        dataset_name: Name of the dataset for error messages.

    Returns:
        True if all required columns exist.

    Raises:
        DatasetSchemaError: If required columns are missing.
    """
    missing = sorted(set(required_columns) - set(df.columns))
    if missing:
        raise DatasetSchemaError(missing, dataset_name=dataset_name)
    return True
