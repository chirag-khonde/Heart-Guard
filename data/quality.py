"""Data quality report generation for HeartGuard.

Generates structured JSON quality reports for the Cleveland and
Framingham datasets. All values are derived from the actual data.
"""

import json
from pathlib import Path

import pandas as pd

from src.data.features import (
    ALL_FEATURES,
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    CLEVELAND_COLUMN_MAP,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
    VALIDATION_BOUNDS,
)
from src.utils.logger import get_logger
from src.utils.validators import check_invalid_values, detect_outliers_iqr

logger = get_logger(__name__)


def _column_summary(df: pd.DataFrame) -> dict:
    """Produce per-column metadata."""
    summary: dict = {}
    for col in df.columns:
        info: dict = {
            "dtype": str(df[col].dtype),
            "missing": int(df[col].isnull().sum()),
            "unique": int(df[col].nunique()),
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            desc = df[col].describe()
            info["mean"] = round(float(desc.get("mean", 0)), 4)
            info["std"] = round(float(desc.get("std", 0)), 4)
            info["min"] = round(float(desc.get("min", 0)), 4)
            info["max"] = round(float(desc.get("max", 0)), 4)
            info["median"] = round(float(df[col].median()), 4)
        else:
            info["top_values"] = df[col].value_counts().head(5).to_dict()
        summary[col] = info
    return summary


def generate_data_quality_report(
    df: pd.DataFrame,
    dataset_name: str,
    target_col: str = TARGET_COLUMN,
) -> dict:
    """Generate a comprehensive data-quality report for a DataFrame.

    The report contains:
        - dataset name
        - row/column counts
        - column names and data types
        - missing-value counts
        - duplicate counts
        - target distribution
        - invalid-value summary
        - outlier summary
        - per-column summary statistics

    Args:
        df: DataFrame to report on.
        dataset_name: Human-readable dataset name.
        target_col: Name of the target column.

    Returns:
        Report dictionary suitable for JSON serialisation.
    """
    report: dict = {
        "dataset_name": dataset_name,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": {
            col: int(cnt) for col, cnt in df.isnull().sum().items() if cnt > 0
        },
        "total_missing": int(df.isnull().sum().sum()),
        "duplicates": {
            "total_rows": len(df),
            "duplicate_rows": int(df.duplicated().sum()),
            "duplicate_percentage": round(
                int(df.duplicated().sum()) / len(df) * 100, 2
            ) if len(df) > 0 else 0.0,
        },
        "target_distribution": {},
        "invalid_values": {},
        "outliers": {},
        "column_summary": {},
    }

    # Target distribution
    if target_col in df.columns:
        report["target_distribution"] = {
            str(k): int(v) for k, v in df[target_col].value_counts().sort_index().items()
        }

    # Invalid values
    invalid = check_invalid_values(df)
    report["invalid_values"] = {
        col: {"count": len(indices), "sample_indices": indices[:10]}
        for col, indices in invalid.items()
    }

    # Outliers
    num_cols = [c for c in NUMERICAL_FEATURES if c in df.columns]
    report["outliers"] = detect_outliers_iqr(df, columns=num_cols)

    # Per-column summary
    report["column_summary"] = _column_summary(df)

    logger.info(
        "Data quality report generated for '%s': %d rows, %d cols, %d missing, %d duplicates",
        dataset_name, report["rows"], report["columns"],
        report["total_missing"], report["duplicates"]["duplicate_rows"],
    )
    return report


def save_data_quality_report(
    report: dict,
    filename: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Save a data-quality report as JSON.

    Args:
        report: Report dictionary.
        filename: Output filename (e.g. 'cleveland_data_quality.json').
        output_dir: Override directory. Defaults to reports/data_quality/.

    Returns:
        Path to the saved file.
    """
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent.parent / "reports" / "data_quality"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info("Data quality report saved to %s", path)
    return path


def generate_and_save_report(
    df: pd.DataFrame,
    dataset_name: str,
    filename: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Convenience: generate + save a data-quality report in one call.

    Args:
        df: DataFrame to report on.
        dataset_name: Human-readable dataset name.
        filename: Output filename.
        output_dir: Optional output directory override.

    Returns:
        Path to the saved JSON file.
    """
    report = generate_data_quality_report(df, dataset_name)
    return save_data_quality_report(report, filename, output_dir)


def print_dataset_summary(df: pd.DataFrame, name: str = "Dataset") -> None:
    """Print a concise dataset summary to stdout.

    Args:
        df: DataFrame to summarise.
        name: Display name for the dataset.
    """
    print(f"\n{'=' * 60}")
    print(f"  {name} Summary")
    print(f"{'=' * 60}")
    print(f"  Rows:    {len(df)}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Missing: {int(df.isnull().sum().sum())} total values")
    print(f"  Duplicates: {int(df.duplicated().sum())} rows")

    if TARGET_COLUMN in df.columns:
        print(f"\n  Target distribution:")
        for val, count in df[TARGET_COLUMN].value_counts().sort_index().items():
            pct = count / len(df) * 100
            print(f"    {val}: {count} ({pct:.1f}%)")

    print(f"\n  Columns: {list(df.columns)}")
    print(f"{'=' * 60}\n")
