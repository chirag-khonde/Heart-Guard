"""Validation utilities for HeartGuard.

Provides reusable validation functions for input data, including
dataset-level validators for clinical values.
"""

from typing import Any

import pandas as pd

from src.data.features import BINARY_FEATURES, VALIDATION_BOUNDS
from src.utils.logger import get_logger

logger = get_logger(__name__)


def validate_age(age: Any) -> int:
    """Validate that age is a reasonable integer.

    Args:
        age: Value to validate.

    Returns:
        Validated age as integer.

    Raises:
        ValueError: If age is not a valid number or outside range.
    """
    try:
        age_int = int(age)
    except (TypeError, ValueError):
        raise ValueError(f"Age must be a number, got {type(age).__name__}")

    if age_int < 0 or age_int > 150:
        raise ValueError(f"Age must be between 0 and 150, got {age_int}")

    return age_int


def validate_positive_number(value: Any, field_name: str) -> float:
    """Validate that a value is a positive number.

    Args:
        value: Value to validate.
        field_name: Name of the field for error messages.

    Returns:
        Validated value as float.

    Raises:
        ValueError: If value is not a positive number.
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number, got {type(value).__name__}")

    if num < 0:
        raise ValueError(f"{field_name} must be positive, got {num}")

    return num


def validate_required_text(value: Any, field_name: str) -> str:
    """Validate that a text field is not empty.

    Args:
        value: Value to validate.
        field_name: Name of the field for error messages.

    Returns:
        Validated text as string.

    Raises:
        ValueError: If value is empty or None.
    """
    if value is None:
        raise ValueError(f"{field_name} is required")

    text = str(value).strip()

    if not text:
        raise ValueError(f"{field_name} cannot be empty")

    return text


# ---------------------------------------------------------------------------
# Dataset-level validators
# ---------------------------------------------------------------------------


def check_invalid_values(df: pd.DataFrame) -> dict[str, list[int]]:
    """Detect invalid values in clinical columns.

    Returns a dictionary mapping column names to lists of row indices
    where invalid values were found.

    Args:
        df: DataFrame to validate.

    Returns:
        Dict mapping column name to list of invalid row indices.
    """
    invalid: dict[str, list[int]] = {}

    for col, (lo, hi) in VALIDATION_BOUNDS.items():
        if col not in df.columns:
            continue
        mask = df[col].notna() & ((df[col] < lo) | (df[col] > hi))
        indices = df.index[mask].tolist()
        if indices:
            invalid[col] = indices
            logger.warning(
                "Column '%s': %d invalid values detected (expected %.1f–%.1f)",
                col, len(indices), lo, hi,
            )

    for col in BINARY_FEATURES:
        if col not in df.columns:
            continue
        valid_binary = {0, 1, 0.0, 1.0}
        mask = df[col].notna() & (~df[col].isin(valid_binary))
        indices = df.index[mask].tolist()
        if indices:
            invalid[col] = indices
            logger.warning(
                "Column '%s': %d non-binary values detected", col, len(indices)
            )

    return invalid


def detect_outliers_iqr(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    factor: float = 1.5,
) -> dict[str, dict[str, Any]]:
    """Detect potential outliers using the IQR method.

    Reports outliers but does NOT remove them.

    Args:
        df: DataFrame to inspect.
        columns: Columns to check. If None, checks all numeric columns.
        factor: IQR multiplier (default 1.5).

    Returns:
        Dict mapping column name to outlier metadata.
    """
    if columns is None:
        columns = df.select_dtypes(include="number").columns.tolist()

    results: dict[str, dict[str, Any]] = {}

    for col in columns:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr
        outlier_mask = (series < lower) | (series > upper)
        count = int(outlier_mask.sum())
        if count > 0:
            results[col] = {
                "count": count,
                "lower_bound": float(lower),
                "upper_bound": float(upper),
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
            }
            logger.info(
                "Outliers in '%s': %d (IQR bounds [%.2f, %.2f])",
                col, count, lower, upper,
            )

    return results
