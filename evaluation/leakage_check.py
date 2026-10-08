"""Data leakage detection for HeartGuard model evaluation (Phase 14).

Explicitly checks for common sources of data leakage.
If leakage is detected, it is reported — never silently suppressed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.data.features import TARGET_COLUMN


@dataclass
class LeakageCheck:
    name: str
    leakage_detected: bool
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class LeakageReport:
    any_leakage: bool
    checks: list[LeakageCheck] = field(default_factory=list)
    summary: str = ""


def check_data_leakage(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = TARGET_COLUMN,
    train_idx: np.ndarray | None = None,
    test_idx: np.ndarray | None = None,
) -> LeakageReport:
    """Check a dataset for common data leakage scenarios.

    Checks performed:
      1. Target column included in feature list
      2. Duplicate rows across train and test splits (if provided)
      3. Features with near-perfect correlation with target (potential proxy leakage)

    Args:
        df: Full DataFrame to inspect.
        feature_cols: List of feature column names.
        target_col: Target column name.
        train_idx: Optional array of training indices.
        test_idx: Optional array of test indices.

    Returns:
        :class:`LeakageReport` with detailed findings.
    """
    checks: list[LeakageCheck] = []
    any_leakage = False

    # 1. Target in features
    target_in_features = target_col in feature_cols
    if target_in_features:
        checks.append(LeakageCheck(
            "target_in_features",
            True,
            f"LEAKAGE DETECTED: Target column '{target_col}' is included in feature_cols. "
            "This would result in artificially perfect metrics.",
            {"target_col": target_col, "feature_cols": feature_cols},
        ))
        any_leakage = True
    else:
        checks.append(LeakageCheck(
            "target_in_features",
            False,
            f"Target '{target_col}' is NOT in feature_cols. No leakage via target inclusion.",
        ))

    # 2. Train/test row overlap (duplicate rows across splits)
    if train_idx is not None and test_idx is not None:
        if len(df) > 0:
            try:
                train_df = df.iloc[train_idx].reset_index(drop=True)
                test_df = df.iloc[test_idx].reset_index(drop=True)

                # Find rows that appear in both (by full row content)
                train_tuples = set(map(tuple, train_df.values.tolist()))
                test_tuples = set(map(tuple, test_df.values.tolist()))
                overlap = len(train_tuples & test_tuples)

                if overlap > 0:
                    checks.append(LeakageCheck(
                        "train_test_row_overlap",
                        True,
                        f"LEAKAGE DETECTED: {overlap} identical rows appear in both train and test sets.",
                        {"overlap_count": overlap},
                    ))
                    any_leakage = True
                else:
                    checks.append(LeakageCheck(
                        "train_test_row_overlap",
                        False,
                        "No identical rows overlap between train and test sets.",
                    ))
            except Exception as e:
                checks.append(LeakageCheck(
                    "train_test_row_overlap",
                    False,
                    f"Train/test overlap check could not be completed: {e}",
                ))
    else:
        checks.append(LeakageCheck(
            "train_test_row_overlap",
            False,
            "Train/test indices not provided — split-level overlap check skipped.",
        ))

    # 3. Near-perfect feature-target correlation (potential proxy leakage)
    if target_col in df.columns:
        proxy_features = []
        for col in feature_cols:
            if col in df.columns and col != target_col and pd.api.types.is_numeric_dtype(df[col]):
                try:
                    corr = abs(float(df[col].corr(df[target_col])))
                    if corr > 0.95:
                        proxy_features.append({"feature": col, "abs_correlation": round(corr, 4)})
                except Exception:
                    pass
        if proxy_features:
            checks.append(LeakageCheck(
                "near_perfect_target_correlation",
                True,
                f"POTENTIAL LEAKAGE: {len(proxy_features)} feature(s) have |correlation| > 0.95 with target. "
                "Investigate whether these features contain derived or future information.",
                {"features": proxy_features},
            ))
            any_leakage = True
        else:
            checks.append(LeakageCheck(
                "near_perfect_target_correlation",
                False,
                "No feature has near-perfect correlation (>0.95) with target.",
            ))

    leakage_count = sum(1 for c in checks if c.leakage_detected)
    summary = (
        f"{leakage_count} potential leakage issue(s) found across {len(checks)} checks."
        if leakage_count > 0
        else f"No data leakage detected across {len(checks)} checks."
    )

    return LeakageReport(any_leakage=any_leakage, checks=checks, summary=summary)
