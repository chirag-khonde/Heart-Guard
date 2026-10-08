"""Tests for the HeartGuard data pipeline (Phase 3).

Covers:
    - Pipeline module import
    - DataPipelineResult structure
    - Cleveland pipeline end-to-end
    - Framingham inspection
    - Class distribution analysis
    - Feature name recovery
    - Deterministic feature ordering
    - Min-Max normalisation
    - No data leakage
    - Preprocessor persistence (save/reload)
    - Cross-validation utility
    - Edge cases
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NUMERICAL_COLS = [
    "age", "resting_bp", "cholesterol", "max_heart_rate",
    "st_depression", "num_major_vessels",
]
CATEGORICAL_COLS = [
    "sex", "chest_pain_type", "fasting_blood_sugar", "resting_ecg",
    "exercise_angina",
]
ALL_FEATURES = NUMERICAL_COLS + CATEGORICAL_COLS


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


def _make_cleveland_csv(path: Path, n: int = 303) -> Path:
    """Write a synthetic Cleveland CSV to disk and return its path."""
    df = _make_cleveland_df(n)
    csv_path = path / "heart.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------


class TestPipelineImports:
    """Verify all Phase 3 modules are importable."""

    def test_import_pipeline(self):
        from src.data import pipeline
        assert hasattr(pipeline, "prepare_cleveland_pipeline")
        assert hasattr(pipeline, "DataPipelineResult")
        assert hasattr(pipeline, "analyze_class_distribution")
        assert hasattr(pipeline, "inspect_framingham_dataset")

    def test_import_cross_validation(self):
        from src.ml import cross_validation
        assert hasattr(cross_validation, "create_cv_strategy")
        assert hasattr(cross_validation, "get_cv_splits")

    def test_import_get_feature_names(self):
        from src.data.preprocessing import get_feature_names
        assert callable(get_feature_names)

    def test_import_heartguard_features(self):
        from src.data.features import HEARTGUARD_FEATURES
        assert len(HEARTGUARD_FEATURES) == 11


# ---------------------------------------------------------------------------
# Deterministic feature ordering
# ---------------------------------------------------------------------------


class TestFeatureOrdering:
    """Verify HEARTGUARD_FEATURES is stable and deterministic."""

    def test_feature_count(self):
        from src.data.features import HEARTGUARD_FEATURES
        assert len(HEARTGUARD_FEATURES) == 11

    def test_features_match_canonical(self):
        from src.data.features import HEARTGUARD_FEATURES, ALL_FEATURES
        assert set(HEARTGUARD_FEATURES) == set(ALL_FEATURES)

    def test_order_is_deterministic(self):
        from src.data.features import HEARTGUARD_FEATURES
        first = list(HEARTGUARD_FEATURES)
        second = list(HEARTGUARD_FEATURES)
        assert first == second

    def test_first_feature_is_age(self):
        from src.data.features import HEARTGUARD_FEATURES
        assert HEARTGUARD_FEATURES[0] == "age"

    def test_last_feature_is_num_major_vessels(self):
        from src.data.features import HEARTGUARD_FEATURES
        assert HEARTGUARD_FEATURES[-1] == "num_major_vessels"


# ---------------------------------------------------------------------------
# Min-Max normalisation
# ---------------------------------------------------------------------------


class TestMinMaxNormalisation:
    """Verify the preprocessor uses MinMaxScaler (not StandardScaler)."""

    def test_scaler_is_minmax(self):
        from src.data.preprocessing import fit_preprocessor
        from sklearn.preprocessing import MinMaxScaler
        df = _make_cleveland_df(50)
        X = df.drop(columns=["target"])
        preprocessor = fit_preprocessor(X)
        num_pipeline = preprocessor.named_transformers_["num"]
        scaler = num_pipeline.named_steps["scaler"]
        assert isinstance(scaler, MinMaxScaler)

    def test_scaled_values_in_0_1_range(self):
        from src.data.preprocessing import fit_preprocessor, transform_data
        df = _make_cleveland_df(50)
        X = df.drop(columns=["target"])
        preprocessor = fit_preprocessor(X)
        X_t = transform_data(preprocessor, X)[0]
        # All numerical columns should be in [0, 1] after MinMaxScaler
        for col in X_t.columns:
            if col in [c for c in NUMERICAL_COLS if c in X_t.columns]:
                assert X_t[col].min() >= -0.01, f"{col} below 0"
                assert X_t[col].max() <= 1.01, f"{col} above 1"


# ---------------------------------------------------------------------------
# Feature name recovery
# ---------------------------------------------------------------------------


class TestFeatureNameRecovery:
    """Verify get_feature_names returns meaningful names."""

    def test_returns_list(self):
        from src.data.preprocessing import fit_preprocessor, get_feature_names
        df = _make_cleveland_df(50)
        X = df.drop(columns=["target"])
        preprocessor = fit_preprocessor(X)
        names = get_feature_names(preprocessor)
        assert isinstance(names, list)
        assert len(names) > 0

    def test_names_are_strings(self):
        from src.data.preprocessing import fit_preprocessor, get_feature_names
        df = _make_cleveland_df(50)
        X = df.drop(columns=["target"])
        preprocessor = fit_preprocessor(X)
        names = get_feature_names(preprocessor)
        for name in names:
            assert isinstance(name, str)

    def test_numerical_names_present(self):
        from src.data.preprocessing import fit_preprocessor, get_feature_names
        df = _make_cleveland_df(50)
        X = df.drop(columns=["target"])
        preprocessor = fit_preprocessor(X)
        names = get_feature_names(preprocessor)
        for col in NUMERICAL_COLS:
            if col in X.columns:
                assert col in names, f"Numerical feature '{col}' not in names"

    def test_no_generic_names(self):
        from src.data.preprocessing import fit_preprocessor, get_feature_names
        df = _make_cleveland_df(50)
        X = df.drop(columns=["target"])
        preprocessor = fit_preprocessor(X)
        names = get_feature_names(preprocessor)
        for name in names:
            assert not name.startswith("feature_"), f"Generic name found: {name}"


# ---------------------------------------------------------------------------
# Class distribution analysis
# ---------------------------------------------------------------------------


class TestClassDistribution:
    """Test analyze_class_distribution function."""

    def test_balanced_classes(self):
        from src.data.pipeline import analyze_class_distribution
        y = pd.Series([0, 0, 1, 1])
        result = analyze_class_distribution(y)
        assert result["class_counts"] == {0: 2, 1: 2}
        assert result["imbalance_ratio"] == 1.0

    def test_imbalanced_classes(self):
        from src.data.pipeline import analyze_class_distribution
        y = pd.Series([0, 0, 0, 0, 1])
        result = analyze_class_distribution(y)
        assert result["class_counts"] == {0: 4, 1: 1}
        assert result["imbalance_ratio"] == 4.0

    def test_single_class(self):
        from src.data.pipeline import analyze_class_distribution
        y = pd.Series([0, 0, 0])
        result = analyze_class_distribution(y)
        assert result["imbalance_ratio"] == 1.0


# ---------------------------------------------------------------------------
# DataPipelineResult structure
# ---------------------------------------------------------------------------


class TestDataPipelineResult:
    """Verify the DataPipelineResult dataclass."""

    def test_has_required_fields(self):
        from src.data.pipeline import DataPipelineResult
        fields = {f.name for f in DataPipelineResult.__dataclass_fields__.values()}
        assert "X_train" in fields
        assert "X_test" in fields
        assert "y_train" in fields
        assert "y_test" in fields
        assert "preprocessor" in fields
        assert "feature_names" in fields
        assert "metadata" in fields


# ---------------------------------------------------------------------------
# Cleveland pipeline (end-to-end with synthetic data)
# ---------------------------------------------------------------------------


class TestClevelandPipeline:
    """End-to-end pipeline test using synthetic Cleveland data."""

    def test_pipeline_returns_result(self, tmp_path):
        from src.data.pipeline import prepare_cleveland_pipeline, DataPipelineResult
        csv_path = _make_cleveland_csv(tmp_path, n=200)
        result = prepare_cleveland_pipeline(path=csv_path, save_artefacts=False)
        assert isinstance(result, DataPipelineResult)

    def test_pipeline_shapes(self, tmp_path):
        from src.data.pipeline import prepare_cleveland_pipeline
        csv_path = _make_cleveland_csv(tmp_path, n=200)
        result = prepare_cleveland_pipeline(path=csv_path, save_artefacts=False)
        assert result.X_train.shape[0] == 160
        assert result.X_test.shape[0] == 40
        assert result.X_train.shape[1] == result.X_test.shape[1]

    def test_pipeline_no_nan(self, tmp_path):
        from src.data.pipeline import prepare_cleveland_pipeline
        csv_path = _make_cleveland_csv(tmp_path, n=100)
        result = prepare_cleveland_pipeline(path=csv_path, save_artefacts=False)
        assert result.X_train.isnull().sum().sum() == 0
        assert result.X_test.isnull().sum().sum() == 0

    def test_pipeline_target_binary(self, tmp_path):
        from src.data.pipeline import prepare_cleveland_pipeline
        csv_path = _make_cleveland_csv(tmp_path, n=100)
        result = prepare_cleveland_pipeline(path=csv_path, save_artefacts=False)
        assert set(result.y_train.unique()) <= {0, 1}
        assert set(result.y_test.unique()) <= {0, 1}

    def test_pipeline_metadata_populated(self, tmp_path):
        from src.data.pipeline import prepare_cleveland_pipeline
        csv_path = _make_cleveland_csv(tmp_path, n=100)
        result = prepare_cleveland_pipeline(path=csv_path, save_artefacts=False)
        assert "dataset" in result.metadata
        assert "pipeline_timestamp" in result.metadata
        assert "random_state" in result.metadata
        assert "preprocessing_strategy" in result.metadata
        assert "leakage_check" in result.metadata
        assert "feature_names" in result.metadata

    def test_pipeline_feature_names_match_transform(self, tmp_path):
        from src.data.pipeline import prepare_cleveland_pipeline
        csv_path = _make_cleveland_csv(tmp_path, n=100)
        result = prepare_cleveland_pipeline(path=csv_path, save_artefacts=False)
        assert len(result.feature_names) == result.X_train.shape[1]

    def test_pipeline_stratification(self, tmp_path):
        from src.data.pipeline import prepare_cleveland_pipeline
        csv_path = _make_cleveland_csv(tmp_path, n=200)
        result = prepare_cleveland_pipeline(path=csv_path, save_artefacts=False)
        train_ratio = result.y_train.mean()
        test_ratio = result.y_test.mean()
        assert abs(train_ratio - test_ratio) < 0.05

    def test_pipeline_saves_artefacts(self, tmp_path):
        from src.data.pipeline import prepare_cleveland_pipeline
        csv_path = _make_cleveland_csv(tmp_path, n=100)
        result = prepare_cleveland_pipeline(path=csv_path, save_artefacts=True)
        from config.settings import MODEL_DIRECTORY, PROCESSED_DATA_DIRECTORY, REPORT_DIRECTORY
        assert (PROCESSED_DATA_DIRECTORY / "cleveland_train.csv").exists()
        assert (PROCESSED_DATA_DIRECTORY / "cleveland_test.csv").exists()
        assert (MODEL_DIRECTORY / "preprocessor.pkl").exists()
        assert (REPORT_DIRECTORY / "data_quality" / "cleveland_data_quality.json").exists()
        assert (REPORT_DIRECTORY / "data_quality" / "cleveland_eda_summary.json").exists()
        assert (REPORT_DIRECTORY / "data_quality" / "dataset_metadata.json").exists()
        assert (REPORT_DIRECTORY / "data_quality" / "data_leakage_check.json").exists()


# ---------------------------------------------------------------------------
# No data leakage
# ---------------------------------------------------------------------------


class TestDataLeakageAudit:
    """Verify the pipeline's leakage checks."""

    def test_leakage_check_all_true(self, tmp_path):
        from src.data.pipeline import prepare_cleveland_pipeline
        csv_path = _make_cleveland_csv(tmp_path, n=100)
        result = prepare_cleveland_pipeline(path=csv_path, save_artefacts=False)
        check = result.metadata["leakage_check"]
        assert check["train_test_split_before_preprocessing"] is True
        assert check["imputer_fit_on_train_only"] is True
        assert check["scaler_fit_on_train_only"] is True
        assert check["encoder_fit_on_train_only"] is True
        assert check["target_excluded_from_features"] is True


# ---------------------------------------------------------------------------
# Preprocessor persistence
# ---------------------------------------------------------------------------


class TestPreprocessorReload:
    """Test that a saved+loaded preprocessor produces identical results."""

    def test_reload_consistency(self, tmp_path):
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
# Cross-validation utility
# ---------------------------------------------------------------------------


class TestCrossValidation:
    """Test create_cv_strategy and get_cv_splits."""

    def test_create_cv_returns_skf(self):
        from src.ml.cross_validation import create_cv_strategy
        from sklearn.model_selection import StratifiedKFold
        cv = create_cv_strategy()
        assert isinstance(cv, StratifiedKFold)

    def test_default_5_folds(self):
        from src.ml.cross_validation import create_cv_strategy
        cv = create_cv_strategy()
        assert cv.n_splits == 5

    def test_get_cv_splits(self):
        from src.ml.cross_validation import create_cv_strategy, get_cv_splits
        cv = create_cv_strategy()
        rng = np.random.RandomState(42)
        X = rng.rand(100, 5)
        y = rng.randint(0, 2, 100)
        splits = get_cv_splits(cv, X, y)
        assert len(splits) == 5
        for train_idx, val_idx in splits:
            assert len(train_idx) > 0
            assert len(val_idx) > 0
            # No overlap
            assert len(set(train_idx) & set(val_idx)) == 0


# ---------------------------------------------------------------------------
# Framingham inspection
# ---------------------------------------------------------------------------


class TestFraminghamInspection:
    """Test inspect_framingham_dataset."""

    def test_returns_none_when_not_found(self):
        from src.data.pipeline import inspect_framingham_dataset
        result = inspect_framingham_dataset(path="/nonexistent/framingham.csv")
        assert result is None


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases for the pipeline."""

    def test_small_dataset(self, tmp_path):
        from src.data.pipeline import prepare_cleveland_pipeline
        csv_path = _make_cleveland_csv(tmp_path, n=20)
        result = prepare_cleveland_pipeline(path=csv_path, save_artefacts=False)
        assert result.X_train.shape[0] == 16
        assert result.X_test.shape[0] == 4

    def test_custom_test_size(self, tmp_path):
        from src.data.pipeline import prepare_cleveland_pipeline
        csv_path = _make_cleveland_csv(tmp_path, n=100)
        result = prepare_cleveland_pipeline(
            path=csv_path, test_size=0.30, save_artefacts=False,
        )
        assert result.X_train.shape[0] == 70
        assert result.X_test.shape[0] == 30
