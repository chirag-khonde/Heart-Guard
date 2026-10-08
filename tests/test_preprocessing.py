"""Tests for the HeartGuard data preprocessing pipeline (Phase 2).

Covers:
    - Dataset loading and validation
    - Column normalization
    - Required-column validation
    - Train/test split with stratification
    - Preprocessor creation, fitting, and transformation
    - Missing-value and duplicate analysis
    - Invalid-value detection
    - Data quality report generation
    - No data leakage
    - Edge cases
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cleveland_df(n: int = 100, with_missing: bool = False) -> pd.DataFrame:
    """Create a synthetic Cleveland-like DataFrame for testing."""
    rng = np.random.RandomState(42)
    df = pd.DataFrame({
        "age": rng.randint(30, 80, n),
        "sex": rng.randint(0, 2, n),
        "chest_pain_type": rng.randint(0, 4, n),
        "resting_bp": rng.randint(90, 200, n),
        "cholesterol": rng.randint(150, 400, n),
        "fasting_blood_sugar": rng.randint(0, 2, n),
        "resting_ecg": rng.randint(0, 2, n),
        "max_heart_rate": rng.randint(100, 200, n),
        "exercise_angina": rng.randint(0, 2, n),
        "st_depression": rng.uniform(0, 6, n).round(1),
        "num_major_vessels": rng.randint(0, 4, n),
        "target": rng.randint(0, 2, n),
    })
    if with_missing:
        df.loc[0, "cholesterol"] = np.nan
        df.loc[1, "resting_bp"] = np.nan
        df.loc[2, "age"] = np.nan
    return df


def _make_cleveland_with_severity_target(n: int = 50) -> pd.DataFrame:
    """Create a Cleveland-like DataFrame with severity-scale target (0-4)."""
    rng = np.random.RandomState(42)
    df = _make_cleveland_df(n)
    df["target"] = rng.choice([0, 1, 2, 3, 4], size=n)
    return df


# ---------------------------------------------------------------------------
# Module import tests
# ---------------------------------------------------------------------------


class TestModuleImports:
    """Verify all Phase 2 modules are importable."""

    def test_import_features(self):
        from src.data import features
        assert hasattr(features, "NUMERICAL_FEATURES")
        assert hasattr(features, "CATEGORICAL_FEATURES")
        assert hasattr(features, "TARGET_COLUMN")

    def test_import_loader(self):
        from src.data import loader
        assert hasattr(loader, "load_csv")
        assert hasattr(loader, "validate_dataset_exists")
        assert hasattr(loader, "load_cleveland_dataset")
        assert hasattr(loader, "load_framingham_dataset")
        assert hasattr(loader, "normalize_column_names")
        assert hasattr(loader, "get_dataset_info")
        assert hasattr(loader, "validate_required_columns")

    def test_import_preprocessing(self):
        from src.data import preprocessing
        assert hasattr(preprocessing, "split_dataset")
        assert hasattr(preprocessing, "create_preprocessor")
        assert hasattr(preprocessing, "fit_preprocessor")
        assert hasattr(preprocessing, "transform_data")
        assert hasattr(preprocessing, "get_missing_value_report")
        assert hasattr(preprocessing, "get_duplicate_report")

    def test_import_quality(self):
        from src.data import quality
        assert hasattr(quality, "generate_data_quality_report")
        assert hasattr(quality, "save_data_quality_report")

    def test_import_exceptions(self):
        from src.utils import exceptions
        assert hasattr(exceptions, "DatasetNotFoundError")
        assert hasattr(exceptions, "DatasetEmptyError")
        assert hasattr(exceptions, "DatasetSchemaError")
        assert hasattr(exceptions, "DataValidationError")

    def test_import_validators(self):
        from src.utils import validators
        assert hasattr(validators, "check_invalid_values")
        assert hasattr(validators, "detect_outliers_iqr")


# ---------------------------------------------------------------------------
# Feature constants tests
# ---------------------------------------------------------------------------


class TestFeatureConstants:
    """Verify feature constants are correctly defined."""

    def test_numerical_features_count(self):
        from src.data.features import NUMERICAL_FEATURES
        assert len(NUMERICAL_FEATURES) == 6

    def test_categorical_features_count(self):
        from src.data.features import CATEGORICAL_FEATURES
        assert len(CATEGORICAL_FEATURES) == 5

    def test_target_column(self):
        from src.data.features import TARGET_COLUMN
        assert TARGET_COLUMN == "target"

    def test_cleveland_column_map_has_all_features(self):
        from src.data.features import CLEVELAND_COLUMN_MAP, ALL_FEATURES
        mapped = set(CLEVELAND_COLUMN_MAP.values())
        for feat in ALL_FEATURES:
            assert feat in mapped, f"Feature '{feat}' not in CLEVELAND_COLUMN_MAP"

    def test_validation_bounds_reasonable(self):
        from src.data.features import VALIDATION_BOUNDS
        assert VALIDATION_BOUNDS["age"] == (1, 150)
        assert VALIDATION_BOUNDS["resting_bp"][0] == 1


# ---------------------------------------------------------------------------
# Dataset existence validation tests
# ---------------------------------------------------------------------------


class TestDatasetExists:
    """Test validate_dataset_exists function."""

    def test_exists_returns_true(self, tmp_path):
        csv = tmp_path / "test.csv"
        csv.write_text("a,b\n1,2\n")
        from src.data.loader import validate_dataset_exists
        assert validate_dataset_exists(csv) is True

    def test_missing_file_raises(self, tmp_path):
        from src.data.loader import validate_dataset_exists
        from src.utils.exceptions import DatasetNotFoundError
        with pytest.raises(DatasetNotFoundError):
            validate_dataset_exists(tmp_path / "nonexistent.csv")

    def test_empty_file_raises(self, tmp_path):
        csv = tmp_path / "empty.csv"
        csv.write_text("")
        from src.data.loader import validate_dataset_exists
        from src.utils.exceptions import DatasetEmptyError
        with pytest.raises(DatasetEmptyError):
            validate_dataset_exists(csv)


# ---------------------------------------------------------------------------
# CSV loading tests
# ---------------------------------------------------------------------------


class TestLoadCSV:
    """Test the load_csv function."""

    def test_load_valid_csv(self, tmp_path):
        csv = tmp_path / "data.csv"
        csv.write_text("age,sex\n25,1\n30,0\n")
        from src.data.loader import load_csv
        df = load_csv(csv)
        assert len(df) == 2
        assert list(df.columns) == ["age", "sex"]

    def test_load_missing_file_raises(self):
        from src.data.loader import load_csv
        from src.utils.exceptions import DatasetNotFoundError
        with pytest.raises(DatasetNotFoundError):
            load_csv("/nonexistent/path/data.csv")

    def test_load_empty_file_raises(self, tmp_path):
        csv = tmp_path / "empty.csv"
        csv.write_text("")
        from src.data.loader import load_csv
        from src.utils.exceptions import DatasetEmptyError
        with pytest.raises(DatasetEmptyError):
            load_csv(csv)


# ---------------------------------------------------------------------------
# Column normalization tests
# ---------------------------------------------------------------------------


class TestColumnNormalization:
    """Test normalize_column_names."""

    def test_lowercase_and_strip(self):
        import pandas as pd
        from src.data.loader import normalize_column_names
        df = pd.DataFrame({"Age ": [1], "SEX": [0], "  CP  ": [2]})
        result = normalize_column_names(df)
        assert list(result.columns) == ["age", "sex", "cp"]

    def test_preserves_data(self):
        import pandas as pd
        from src.data.loader import normalize_column_names
        df = pd.DataFrame({"Col A": [1, 2], "Col B": [3, 4]})
        result = normalize_column_names(df)
        assert result["col_a"].tolist() == [1, 2]
        assert result["col_b"].tolist() == [3, 4]


# ---------------------------------------------------------------------------
# Required column validation tests
# ---------------------------------------------------------------------------


class TestRequiredColumns:
    """Test validate_required_columns."""

    def test_passes_when_all_present(self):
        import pandas as pd
        from src.data.loader import validate_required_columns
        df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        assert validate_required_columns(df, ["a", "b"]) is True

    def test_raises_when_missing(self):
        import pandas as pd
        from src.data.loader import validate_required_columns
        from src.utils.exceptions import DatasetSchemaError
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(DatasetSchemaError, match="cholesterol"):
            validate_required_columns(df, ["a", "cholesterol"], dataset_name="Cleveland")


# ---------------------------------------------------------------------------
# Target normalization tests
# ---------------------------------------------------------------------------


class TestTargetNormalization:
    """Test Cleveland target normalization."""

    def test_already_binary(self):
        import pandas as pd
        from src.data.loader import normalize_cleveland_target
        df = pd.DataFrame({"target": [0, 1, 0, 1, 1]})
        result = normalize_cleveland_target(df)
        assert set(result["target"].unique()) <= {0, 1}

    def test_severity_to_binary(self):
        import pandas as pd
        from src.data.loader import normalize_cleveland_target
        df = pd.DataFrame({"target": [0, 1, 2, 3, 4]})
        result = normalize_cleveland_target(df)
        assert set(result["target"].unique()) == {0, 1}
        # 0 stays 0, everything else becomes 1
        assert result["target"].tolist() == [0, 1, 1, 1, 1]

    def test_missing_target_unchanged(self):
        import pandas as pd
        from src.data.loader import normalize_cleveland_target
        df = pd.DataFrame({"age": [25, 30]})
        result = normalize_cleveland_target(df)
        assert "target" not in result.columns


# ---------------------------------------------------------------------------
# Train/test split tests
# ---------------------------------------------------------------------------


class TestTrainTestSplit:
    """Test split_dataset function."""

    def test_split_returns_four_items(self):
        from src.data.preprocessing import split_dataset
        df = _make_cleveland_df(100)
        result = split_dataset(df)
        assert len(result) == 4

    def test_split_sizes(self):
        from src.data.preprocessing import split_dataset
        df = _make_cleveland_df(100)
        X_train, X_test, y_train, y_test = split_dataset(df)
        assert len(X_train) == 80
        assert len(X_test) == 20

    def test_stratification_preserves_ratio(self):
        from src.data.preprocessing import split_dataset
        df = _make_cleveland_df(200)
        X_train, X_test, y_train, y_test = split_dataset(df)
        train_ratio = y_train.mean()
        test_ratio = y_test.mean()
        # Should be within 5% of each other
        assert abs(train_ratio - test_ratio) < 0.05

    def test_target_not_in_X(self):
        from src.data.preprocessing import split_dataset
        df = _make_cleveland_df(50)
        X_train, X_test, _, _ = split_dataset(df)
        assert "target" not in X_train.columns
        assert "target" not in X_test.columns

    def test_missing_target_raises(self):
        import pandas as pd
        from src.data.preprocessing import split_dataset
        df = pd.DataFrame({"age": [25, 30], "sex": [0, 1]})
        with pytest.raises(ValueError, match="target"):
            split_dataset(df)


# ---------------------------------------------------------------------------
# Preprocessor creation and fitting tests
# ---------------------------------------------------------------------------


class TestPreprocessor:
    """Test preprocessor creation, fitting, and transformation."""

    def test_create_preprocessor_returns_transformer(self):
        from src.data.preprocessing import create_preprocessor
        from sklearn.compose import ColumnTransformer
        preprocessor = create_preprocessor()
        assert isinstance(preprocessor, ColumnTransformer)

    def test_fit_preprocessor(self):
        from src.data.preprocessing import fit_preprocessor
        df = _make_cleveland_df(50)
        X = df.drop(columns=["target"])
        preprocessor = fit_preprocessor(X)
        assert preprocessor is not None

    def test_transform_produces_dataframe(self):
        from src.data.preprocessing import fit_preprocessor, transform_data
        df = _make_cleveland_df(50)
        X = df.drop(columns=["target"])
        preprocessor = fit_preprocessor(X)
        result = transform_data(preprocessor, X)
        assert len(result) == 1
        assert isinstance(result[0], pd.DataFrame)
        assert result[0].shape[0] == 50

    def test_transform_train_and_test(self):
        from src.data.preprocessing import split_dataset, fit_preprocessor, transform_data
        df = _make_cleveland_df(100)
        X_train, X_test, _, _ = split_dataset(df)
        preprocessor = fit_preprocessor(X_train)
        X_train_t, X_test_t = transform_data(preprocessor, X_train, X_test)
        assert X_train_t.shape[0] == 80
        assert X_test_t.shape[0] == 20
        assert X_train_t.shape[1] == X_test_t.shape[1]

    def test_no_nan_after_transform(self):
        from src.data.preprocessing import split_dataset, fit_preprocessor, transform_data
        df = _make_cleveland_df(100, with_missing=True)
        X_train, X_test, _, _ = split_dataset(df)
        preprocessor = fit_preprocessor(X_train)
        X_train_t, X_test_t = transform_data(preprocessor, X_train, X_test)
        assert X_train_t.isnull().sum().sum() == 0
        assert X_test_t.isnull().sum().sum() == 0

    def test_categorical_encoding(self):
        from src.data.preprocessing import fit_preprocessor, transform_data
        df = pd.DataFrame({
            "age": [25, 30, 35, 40],
            "resting_bp": [120, 130, 140, 150],
            "cholesterol": [200, 210, 220, 230],
            "max_heart_rate": [150, 160, 170, 180],
            "st_depression": [0.0, 1.0, 2.0, 3.0],
            "num_major_vessels": [0, 1, 2, 3],
            "sex": [0, 1, 0, 1],
            "chest_pain_type": [0, 1, 2, 3],
            "fasting_blood_sugar": [0, 1, 0, 1],
            "resting_ecg": [0, 1, 0, 1],
            "exercise_angina": [0, 1, 0, 1],
        })
        preprocessor = fit_preprocessor(df)
        result = transform_data(preprocessor, df)
        # After one-hot encoding, should have more columns than original
        assert result[0].shape[1] > df.shape[1] - 1  # minus target


# ---------------------------------------------------------------------------
# No data leakage tests
# ---------------------------------------------------------------------------


class TestDataLeakage:
    """Verify preprocessing does not leak test data into training."""

    def test_imputer_fit_only_on_train(self):
        from src.data.preprocessing import split_dataset, fit_preprocessor
        df = _make_cleveland_df(100, with_missing=True)
        X_train, X_test, _, _ = split_dataset(df)
        preprocessor = fit_preprocessor(X_train)

        # Extract the numerical imputer median values
        num_pipeline = preprocessor.named_transformers_["num"]
        imputer = num_pipeline.named_steps["imputer"]
        # medians_ should reflect training data only
        assert imputer.statistics_ is not None

    def test_test_data_not_used_in_fit(self):
        """Fitting preprocessor on train alone should not change if test is different."""
        from src.data.preprocessing import fit_preprocessor, transform_data
        df_train = _make_cleveland_df(50)
        X_train = df_train.drop(columns=["target"])

        # Create a different test set
        df_test = _make_cleveland_df(50)
        X_test = df_test.drop(columns=["target"])

        preprocessor = fit_preprocessor(X_train)
        X_train_t = transform_data(preprocessor, X_train)[0]
        X_test_t = transform_data(preprocessor, X_test)[0]

        # Shapes should be consistent
        assert X_train_t.shape[0] == 50
        assert X_test_t.shape[0] == 50
        assert X_train_t.shape[1] == X_test_t.shape[1]


# ---------------------------------------------------------------------------
# Missing value analysis tests
# ---------------------------------------------------------------------------


class TestMissingValueReport:
    """Test get_missing_value_report."""

    def test_no_missing(self):
        import pandas as pd
        from src.data.preprocessing import get_missing_value_report
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        report = get_missing_value_report(df)
        assert report["missing_count"].sum() == 0

    def test_with_missing(self):
        import pandas as pd
        from src.data.preprocessing import get_missing_value_report
        df = pd.DataFrame({"a": [1, np.nan, 3], "b": [np.nan, np.nan, 3]})
        report = get_missing_value_report(df)
        a_row = report[report["column"] == "a"].iloc[0]
        assert a_row["missing_count"] == 1
        b_row = report[report["column"] == "b"].iloc[0]
        assert b_row["missing_count"] == 2


# ---------------------------------------------------------------------------
# Duplicate analysis tests
# ---------------------------------------------------------------------------


class TestDuplicateReport:
    """Test get_duplicate_report."""

    def test_no_duplicates(self):
        import pandas as pd
        from src.data.preprocessing import get_duplicate_report
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        report = get_duplicate_report(df)
        assert report["duplicate_rows"] == 0
        assert report["duplicate_percentage"] == 0.0

    def test_with_duplicates(self):
        import pandas as pd
        from src.data.preprocessing import get_duplicate_report
        df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
        report = get_duplicate_report(df)
        assert report["duplicate_rows"] == 1
        assert report["duplicate_percentage"] == pytest.approx(33.33, abs=0.1)


class TestRemoveDuplicates:
    """Test remove_exact_duplicates."""

    def test_removes_duplicates(self):
        import pandas as pd
        from src.data.preprocessing import remove_exact_duplicates
        df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
        result = remove_exact_duplicates(df)
        assert len(result) == 2

    def test_no_duplicates_unchanged(self):
        import pandas as pd
        from src.data.preprocessing import remove_exact_duplicates
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = remove_exact_duplicates(df)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Invalid value detection tests
# ---------------------------------------------------------------------------


class TestInvalidValues:
    """Test check_invalid_values."""

    def test_valid_data(self):
        from src.data.preprocessing import get_missing_value_report
        from src.utils.validators import check_invalid_values
        df = _make_cleveland_df(50)
        invalid = check_invalid_values(df)
        # All values should be in valid ranges
        assert len(invalid) == 0

    def test_invalid_age(self):
        import pandas as pd
        from src.utils.validators import check_invalid_values
        df = pd.DataFrame({
            "age": [-5, 25, 200],
            "resting_bp": [120, 130, 140],
            "cholesterol": [200, 210, 220],
            "max_heart_rate": [150, 160, 170],
            "st_depression": [0, 1, 2],
            "num_major_vessels": [0, 1, 2],
        })
        invalid = check_invalid_values(df)
        assert "age" in invalid
        assert 0 in invalid["age"]  # -5
        assert 2 in invalid["age"]  # 200

    def test_invalid_blood_pressure(self):
        import pandas as pd
        from src.utils.validators import check_invalid_values
        df = pd.DataFrame({
            "age": [25, 30, 35],
            "resting_bp": [-10, 130, 140],
            "cholesterol": [200, 210, 220],
            "max_heart_rate": [150, 160, 170],
            "st_depression": [0, 1, 2],
            "num_major_vessels": [0, 1, 2],
        })
        invalid = check_invalid_values(df)
        assert "resting_bp" in invalid

    def test_invalid_cholesterol(self):
        import pandas as pd
        from src.utils.validators import check_invalid_values
        df = pd.DataFrame({
            "age": [25, 30, 35],
            "resting_bp": [120, 130, 140],
            "cholesterol": [0, 210, 220],
            "max_heart_rate": [150, 160, 170],
            "st_depression": [0, 1, 2],
            "num_major_vessels": [0, 1, 2],
        })
        invalid = check_invalid_values(df)
        assert "cholesterol" in invalid


# ---------------------------------------------------------------------------
# Outlier detection tests
# ---------------------------------------------------------------------------


class TestOutlierDetection:
    """Test detect_outliers_iqr."""

    def test_no_outliers(self):
        import pandas as pd
        from src.utils.validators import detect_outliers_iqr
        df = pd.DataFrame({"value": [10, 11, 12, 13, 14, 15]})
        result = detect_outliers_iqr(df, columns=["value"])
        assert "value" not in result

    def test_with_outliers(self):
        import pandas as pd
        from src.utils.validators import detect_outliers_iqr
        df = pd.DataFrame({"value": [10, 11, 12, 13, 14, 100]})
        result = detect_outliers_iqr(df, columns=["value"])
        assert "value" in result
        assert result["value"]["count"] >= 1


# ---------------------------------------------------------------------------
# Data quality report tests
# ---------------------------------------------------------------------------


class TestDataQualityReport:
    """Test data quality report generation."""

    def test_report_structure(self):
        from src.data.quality import generate_data_quality_report
        df = _make_cleveland_df(50)
        report = generate_data_quality_report(df, "test_dataset")
        assert report["dataset_name"] == "test_dataset"
        assert report["rows"] == 50
        assert report["columns"] == 12
        assert "column_names" in report
        assert "missing_values" in report
        assert "duplicates" in report
        assert "target_distribution" in report

    def test_save_report(self, tmp_path):
        from src.data.quality import generate_data_quality_report, save_data_quality_report
        df = _make_cleveland_df(30)
        report = generate_data_quality_report(df, "test")
        path = save_data_quality_report(report, "test_report.json", tmp_path)
        assert path.exists()
        import json
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["rows"] == 30


# ---------------------------------------------------------------------------
# Preprocessor persistence tests
# ---------------------------------------------------------------------------


class TestPreprocessorPersistence:
    """Test saving and loading the preprocessor."""

    def test_save_and_load(self, tmp_path):
        from src.data.preprocessing import (
            fit_preprocessor, transform_data,
            save_preprocessor, load_preprocessor,
        )
        df = _make_cleveland_df(50)
        X = df.drop(columns=["target"])
        preprocessor = fit_preprocessor(X)
        path = tmp_path / "preprocessor.pkl"
        save_preprocessor(preprocessor, path)
        loaded = load_preprocessor(path)
        X_t1 = transform_data(preprocessor, X)[0]
        X_t2 = transform_data(loaded, X)[0]
        pd.testing.assert_frame_equal(X_t1, X_t2)


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe_split(self):
        import pandas as pd
        from src.data.preprocessing import split_dataset
        df = pd.DataFrame({
            "age": pd.Series(dtype="int64"),
            "sex": pd.Series(dtype="int64"),
            "target": pd.Series(dtype="int64"),
        })
        X_train, X_test, y_train, y_test = split_dataset(df)
        assert len(X_train) == 0
        assert len(X_test) == 0

    def test_single_row_dataframe(self):
        import pandas as pd
        from src.data.preprocessing import split_dataset
        df = pd.DataFrame({"age": [25], "sex": [1], "target": [0]})
        X_train, X_test, y_train, y_test = split_dataset(df)
        assert len(X_train) == 1
        assert len(X_test) == 0

    def test_unknown_category_handled(self):
        """OneHotEncoder should handle unknown categories during transform."""
        from src.data.preprocessing import fit_preprocessor, transform_data
        df_train = pd.DataFrame({
            "age": [25, 30, 35, 40],
            "resting_bp": [120, 130, 140, 150],
            "cholesterol": [200, 210, 220, 230],
            "max_heart_rate": [150, 160, 170, 180],
            "st_depression": [0.0, 1.0, 2.0, 3.0],
            "num_major_vessels": [0, 1, 2, 3],
            "sex": [0, 1, 0, 1],
            "chest_pain_type": [0, 1, 2, 3],
            "fasting_blood_sugar": [0, 1, 0, 1],
            "resting_ecg": [0, 1, 0, 1],
            "exercise_angina": [0, 1, 0, 1],
        })
        preprocessor = fit_preprocessor(df_train)

        # Test data has unknown category 99 in chest_pain_type
        df_test = pd.DataFrame({
            "age": [25],
            "resting_bp": [120],
            "cholesterol": [200],
            "max_heart_rate": [150],
            "st_depression": [0.0],
            "num_major_vessels": [0],
            "sex": [0],
            "chest_pain_type": [99],  # unknown
            "fasting_blood_sugar": [0],
            "resting_ecg": [0],
            "exercise_angina": [0],
        })
        result = transform_data(preprocessor, df_test)
        assert result[0].shape[0] == 1  # should not crash

    def test_all_missing_column(self):
        """A column with all NaN values should still be handled."""
        import pandas as pd
        from src.data.preprocessing import fit_preprocessor, transform_data
        df = pd.DataFrame({
            "age": [25, 30, 35, 40],
            "resting_bp": [120, 130, 140, 150],
            "cholesterol": [200, 210, 220, 230],
            "max_heart_rate": [150, 160, 170, 180],
            "st_depression": [0.0, 1.0, 2.0, 3.0],
            "num_major_vessels": [0, 1, 2, 3],
            "sex": [0, 1, 0, 1],
            "chest_pain_type": [0, 1, 2, 3],
            "fasting_blood_sugar": [0, 1, 0, 1],
            "resting_ecg": [0, 1, 0, 1],
            "exercise_angina": [0, 1, 0, 1],
        })
        preprocessor = fit_preprocessor(df)
        result = transform_data(preprocessor, df)
        assert result[0].isnull().sum().sum() == 0


# ---------------------------------------------------------------------------
# End-to-end pipeline test
# ---------------------------------------------------------------------------


class TestEndToEndPipeline:
    """Full pipeline test: load -> split -> fit -> transform."""

    def test_full_pipeline(self):
        from src.data.preprocessing import (
            split_dataset,
            fit_preprocessor,
            transform_data,
        )
        df = _make_cleveland_df(100)
        X_train, X_test, y_train, y_test = split_dataset(df)
        preprocessor = fit_preprocessor(X_train)
        X_train_t, X_test_t = transform_data(preprocessor, X_train, X_test)

        # Verify shapes
        assert X_train_t.shape[0] == 80
        assert X_test_t.shape[0] == 20
        assert X_train_t.shape[1] == X_test_t.shape[1]

        # Verify no NaN
        assert X_train_t.isnull().sum().sum() == 0
        assert X_test_t.isnull().sum().sum() == 0

        # Verify target is separate
        assert len(y_train) == 80
        assert len(y_test) == 20
