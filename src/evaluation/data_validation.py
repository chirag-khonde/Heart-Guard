"""Dataset validation for HeartGuard model evaluation (Phase 14).

Validates the evaluation dataset for schema correctness, missing values,
duplicates, class distribution, data types, and range violations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.data.features import (
    ALL_FEATURES,
    BINARY_FEATURES,
    TARGET_COLUMN,
    VALIDATION_BOUNDS,
)


STATUS_PASS = "PASS"
STATUS_WARNING = "WARNING"
STATUS_FAIL = "FAIL"


@dataclass
class ValidationCheck:
    name: str
    status: str
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class ValidationResult:
    overall_status: str
    checks: list[ValidationCheck] = field(default_factory=list)
    summary: str = ""

    @property
    def passed(self) -> bool:
        return self.overall_status == STATUS_PASS


def validate_evaluation_dataset(
    df: pd.DataFrame,
    feature_cols: list[str] | None = None,
    target_col: str = TARGET_COLUMN,
) -> ValidationResult:
    """Validate a DataFrame for use in model evaluation.

    Checks:
      1. Not empty
      2. Target column exists
      3. Expected features present
      4. Missing values
      5. Duplicate rows
      6. Class distribution (imbalance detection)
      7. Data types (numeric features)
      8. Range violations
      9. Binary feature validity

    Args:
        df: DataFrame to validate.
        feature_cols: Expected feature column names.
        target_col: Name of the target column.

    Returns:
        :class:`ValidationResult` with per-check status.
    """
    if feature_cols is None:
        feature_cols = ALL_FEATURES

    checks: list[ValidationCheck] = []
    overall = STATUS_PASS

    # 1. Empty dataset
    if len(df) == 0:
        checks.append(ValidationCheck(
            "empty_dataset", STATUS_FAIL, "Dataset has 0 rows.", {}
        ))
        return ValidationResult(STATUS_FAIL, checks, "Dataset is empty.")

    checks.append(ValidationCheck("empty_dataset", STATUS_PASS, f"{len(df)} rows found."))

    # 2. Target column
    if target_col not in df.columns:
        checks.append(ValidationCheck(
            "target_column", STATUS_FAIL,
            f"Target column '{target_col}' not found. Found: {list(df.columns)}", {}
        ))
        overall = STATUS_FAIL
    else:
        checks.append(ValidationCheck("target_column", STATUS_PASS, f"Target '{target_col}' present."))

    # 3. Expected features
    missing_features = [f for f in feature_cols if f not in df.columns]
    if missing_features:
        checks.append(ValidationCheck(
            "expected_features", STATUS_WARNING,
            f"{len(missing_features)} expected feature(s) missing.",
            {"missing": missing_features},
        ))
        if overall == STATUS_PASS:
            overall = STATUS_WARNING
    else:
        checks.append(ValidationCheck("expected_features", STATUS_PASS, "All expected features present."))

    # 4. Missing values
    total_missing = int(df.isnull().sum().sum())
    if total_missing > 0:
        missing_cols = {col: int(cnt) for col, cnt in df.isnull().sum().items() if cnt > 0}
        checks.append(ValidationCheck(
            "missing_values", STATUS_WARNING,
            f"{total_missing} total missing values detected.",
            {"columns": missing_cols},
        ))
        if overall == STATUS_PASS:
            overall = STATUS_WARNING
    else:
        checks.append(ValidationCheck("missing_values", STATUS_PASS, "No missing values."))

    # 5. Duplicate rows
    n_dups = int(df.duplicated().sum())
    if n_dups > 0:
        dup_pct = round(n_dups / len(df) * 100, 2)
        status = STATUS_WARNING if dup_pct < 10.0 else STATUS_FAIL
        checks.append(ValidationCheck(
            "duplicate_rows", status,
            f"{n_dups} duplicate rows ({dup_pct}%).",
            {"count": n_dups, "pct": dup_pct},
        ))
        if status == STATUS_FAIL:
            overall = STATUS_FAIL
        elif overall == STATUS_PASS:
            overall = STATUS_WARNING
    else:
        checks.append(ValidationCheck("duplicate_rows", STATUS_PASS, "No duplicate rows."))

    # 6. Class distribution
    if target_col in df.columns:
        dist = df[target_col].value_counts().to_dict()
        counts = list(dist.values())
        if len(counts) >= 2:
            imbalance_ratio = max(counts) / min(counts)
            if imbalance_ratio > 5.0:
                status = STATUS_WARNING
                msg = f"Class imbalance ratio {imbalance_ratio:.2f} — consider this when interpreting metrics."
                if overall == STATUS_PASS:
                    overall = STATUS_WARNING
            else:
                status = STATUS_PASS
                msg = f"Class distribution: {dist} — imbalance ratio {imbalance_ratio:.2f}."
        else:
            status = STATUS_WARNING
            msg = f"Only {len(counts)} unique target value(s) found — binary classification requires 2."
        checks.append(ValidationCheck("class_distribution", status, msg, {"distribution": {str(k): v for k, v in dist.items()}}))

    # 7. Data types for numerical features
    bad_dtypes = []
    for col in [f for f in VALIDATION_BOUNDS if f in df.columns]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            bad_dtypes.append(col)
    if bad_dtypes:
        checks.append(ValidationCheck(
            "data_types", STATUS_FAIL,
            f"Non-numeric dtype in numerical features: {bad_dtypes}",
            {"columns": bad_dtypes},
        ))
        overall = STATUS_FAIL
    else:
        checks.append(ValidationCheck("data_types", STATUS_PASS, "All numerical feature dtypes are numeric."))

    # 8. Range violations
    range_issues: dict[str, dict] = {}
    for col, (lo, hi) in VALIDATION_BOUNDS.items():
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            out_of_range = int(((df[col] < lo) | (df[col] > hi)).sum())
            if out_of_range > 0:
                range_issues[col] = {"count": out_of_range, "valid_range": f"[{lo}, {hi}]"}
    if range_issues:
        checks.append(ValidationCheck(
            "range_violations", STATUS_WARNING,
            f"{len(range_issues)} feature(s) have out-of-range values.",
            range_issues,
        ))
        if overall == STATUS_PASS:
            overall = STATUS_WARNING
    else:
        checks.append(ValidationCheck("range_violations", STATUS_PASS, "All numerical values within expected bounds."))

    # 9. Binary feature validity
    binary_issues: dict[str, list] = {}
    for col in BINARY_FEATURES:
        if col in df.columns:
            unexpected = [v for v in df[col].dropna().unique() if v not in (0, 1)]
            if unexpected:
                binary_issues[col] = [str(v) for v in unexpected]
    if binary_issues:
        checks.append(ValidationCheck(
            "binary_feature_values", STATUS_WARNING,
            "Some binary features contain unexpected values (not 0 or 1).",
            binary_issues,
        ))
        if overall == STATUS_PASS:
            overall = STATUS_WARNING
    else:
        checks.append(ValidationCheck("binary_feature_values", STATUS_PASS, "All binary features contain only 0/1 values."))

    failed = sum(1 for c in checks if c.status == STATUS_FAIL)
    warned = sum(1 for c in checks if c.status == STATUS_WARNING)
    summary = f"{len(checks)} checks: {len(checks)-failed-warned} passed, {warned} warnings, {failed} failed."

    return ValidationResult(overall_status=overall, checks=checks, summary=summary)
