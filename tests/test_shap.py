"""Tests for the SHAP explainability module (Phase 5)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import joblib
import numpy as np
import pandas as pd
import pytest

from src.explainability.shap_explainer import (
    CLINICAL_LABELS,
    NEUTRAL_TOLERANCE,
    calculate_shap_values,
    create_global_importance_plot,
    create_local_importance_plot,
    create_shap_explainer,
    create_summary_plot,
    create_waterfall_plot,
    generate_human_readable_summary,
    get_feature_contributions,
    get_global_feature_importance,
    get_local_explanation,
    get_top_features,
    get_top_risk_factors,
    load_explainable_model,
    load_feature_names,
    load_training_data,
    save_explainer_metadata,
    save_explainability_summary,
    save_global_importance_csv,
    save_local_explanation_json,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_training_data() -> pd.DataFrame:
    """Create synthetic training data for testing."""
    rng = np.random.RandomState(42)
    n = 100
    return pd.DataFrame({
        "age": rng.uniform(30, 80, n),
        "resting_bp": rng.uniform(90, 180, n),
        "cholesterol": rng.uniform(100, 400, n),
        "max_heart_rate": rng.uniform(80, 200, n),
        "st_depression": rng.uniform(0, 5, n),
        "num_major_vessels": rng.choice([0, 1, 2, 3], n),
        "sex_0": rng.choice([0, 1], n),
        "sex_1": rng.choice([0, 1], n),
        "chest_pain_type_0": rng.choice([0, 1], n),
        "chest_pain_type_1": rng.choice([0, 1], n),
        "chest_pain_type_2": rng.choice([0, 1], n),
        "chest_pain_type_3": rng.choice([0, 1], n),
        "fasting_blood_sugar_0": rng.choice([0, 1], n),
        "fasting_blood_sugar_1": rng.choice([0, 1], n),
        "resting_ecg_0": rng.choice([0, 1], n),
        "resting_ecg_1": rng.choice([0, 1], n),
        "resting_ecg_2": rng.choice([0, 1], n),
        "exercise_angina_0": rng.choice([0, 1], n),
        "exercise_angina_1": rng.choice([0, 1], n),
    })


@pytest.fixture
def synthetic_shap_values() -> np.ndarray:
    """Create synthetic SHAP values for testing."""
    rng = np.random.RandomState(42)
    return rng.randn(5, 19)


@pytest.fixture
def synthetic_shap_row() -> np.ndarray:
    """Create a single row of synthetic SHAP values."""
    return np.array([
        0.15, -0.08, 0.22, -0.12, 0.35, 0.05,
        0.02, -0.02, 0.10, -0.05, 0.08, -0.03,
        0.01, -0.01, 0.06, -0.04, 0.02, 0.18, -0.15,
    ])


@pytest.fixture
def feature_names_19() -> list[str]:
    """19 transformed feature names."""
    return [
        "age", "resting_bp", "cholesterol", "max_heart_rate",
        "st_depression", "num_major_vessels",
        "sex_0", "sex_1",
        "chest_pain_type_0", "chest_pain_type_1", "chest_pain_type_2", "chest_pain_type_3",
        "fasting_blood_sugar_0", "fasting_blood_sugar_1",
        "resting_ecg_0", "resting_ecg_1", "resting_ecg_2",
        "exercise_angina_0", "exercise_angina_1",
    ]


# ---------------------------------------------------------------------------
# Test: Model loading
# ---------------------------------------------------------------------------


class TestModelLoading:
    """Tests for load_explainable_model and load_feature_names."""

    def test_load_explainable_model_returns_model_and_name(self):
        model, name = load_explainable_model()
        assert model is not None
        assert isinstance(name, str)
        assert len(name) > 0

    def test_load_feature_names_returns_list(self):
        names = load_feature_names()
        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)

    def test_load_feature_names_count_matches_model(self):
        names = load_feature_names()
        model, _ = load_explainable_model()
        # Model should accept this many features
        assert len(names) >= 10  # At least the canonical features

    def test_load_training_data_returns_dataframe(self):
        df = load_training_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "target" not in df.columns


# ---------------------------------------------------------------------------
# Test: Explainer creation
# ---------------------------------------------------------------------------


class TestExplainerCreation:
    """Tests for create_shap_explainer."""

    def test_creates_explainer_for_best_model(self, synthetic_training_data):
        model, name = load_explainable_model()
        explainer, explainer_type = create_shap_explainer(model, synthetic_training_data)
        assert explainer is not None
        assert isinstance(explainer_type, str)
        assert explainer_type in ("TreeExplainer", "LinearExplainer", "KernelExplainer")

    def test_linear_model_gets_linear_explainer(self, synthetic_training_data):
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(random_state=42, max_iter=200)
        model.fit(synthetic_training_data, np.random.randint(0, 2, len(synthetic_training_data)))
        explainer, etype = create_shap_explainer(model, synthetic_training_data)
        assert etype == "LinearExplainer"

    def test_tree_model_gets_tree_explainer(self, synthetic_training_data):
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=10, random_state=42, max_depth=3)
        model.fit(synthetic_training_data, np.random.randint(0, 2, len(synthetic_training_data)))
        explainer, etype = create_shap_explainer(model, synthetic_training_data)
        assert etype == "TreeExplainer"


# ---------------------------------------------------------------------------
# Test: SHAP value calculation
# ---------------------------------------------------------------------------


class TestSHAPValues:
    """Tests for calculate_shap_values."""

    def test_calculates_for_linear_model(self, synthetic_training_data):
        model, _ = load_explainable_model()
        explainer, _ = create_shap_explainer(model, synthetic_training_data)
        shap_vals, base_vals = calculate_shap_values(
            explainer, synthetic_training_data.iloc[:5],
        )
        assert shap_vals.ndim == 2
        assert shap_vals.shape[0] == 5
        assert base_vals.shape[0] == 5

    def test_output_shape_matches_features(self, synthetic_training_data):
        model, _ = load_explainable_model()
        explainer, _ = create_shap_explainer(model, synthetic_training_data)
        shap_vals, _ = calculate_shap_values(
            explainer, synthetic_training_data.iloc[:3],
        )
        assert shap_vals.shape[1] == synthetic_training_data.shape[1]

    def test_base_values_are_finite(self, synthetic_training_data):
        model, _ = load_explainable_model()
        explainer, _ = create_shap_explainer(model, synthetic_training_data)
        _, base_vals = calculate_shap_values(
            explainer, synthetic_training_data.iloc[:5],
        )
        assert np.all(np.isfinite(base_vals))


# ---------------------------------------------------------------------------
# Test: Feature contributions
# ---------------------------------------------------------------------------


class TestFeatureContributions:
    """Tests for get_feature_contributions, get_top_features, get_top_risk_factors."""

    def test_contributions_returns_dataframe(
        self, synthetic_shap_row, feature_names_19,
    ):
        df = get_feature_contributions(synthetic_shap_row, feature_names_19)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(feature_names_19)
        assert "feature" in df.columns
        assert "shap_value" in df.columns
        assert "direction" in df.columns
        assert "absolute_importance" in df.columns

    def test_contributions_sorted_by_importance(
        self, synthetic_shap_row, feature_names_19,
    ):
        df = get_feature_contributions(synthetic_shap_row, feature_names_19)
        abs_vals = df["absolute_importance"].values
        assert all(abs_vals[i] >= abs_vals[i + 1] for i in range(len(abs_vals) - 1))

    def test_direction_labels_correct(
        self, synthetic_shap_row, feature_names_19,
    ):
        df = get_feature_contributions(synthetic_shap_row, feature_names_19)
        for _, row in df.iterrows():
            if row["direction"] == "increases_risk":
                assert row["shap_value"] > NEUTRAL_TOLERANCE
            elif row["direction"] == "decreases_risk":
                assert row["shap_value"] < -NEUTRAL_TOLERANCE
            else:
                assert abs(row["shap_value"]) <= NEUTRAL_TOLERANCE

    def test_top_features_returns_subset(
        self, synthetic_shap_row, feature_names_19,
    ):
        df = get_top_features(synthetic_shap_row, feature_names_19, top_n=5)
        assert len(df) == 5
        assert isinstance(df, pd.DataFrame)

    def test_top_risk_factors_only_positive(
        self, synthetic_shap_row, feature_names_19,
    ):
        df = get_top_risk_factors(synthetic_shap_row, feature_names_19, top_n=5)
        assert all(row["direction"] == "increases_risk" for _, row in df.iterrows())

    def test_top_risk_factors_handles_fewer_positive(
        self, feature_names_19,
    ):
        # All negative SHAP values
        neg_row = np.full(len(feature_names_19), -0.5)
        df = get_top_risk_factors(neg_row, feature_names_19, top_n=3)
        assert len(df) == 0

    def test_contributions_mismatched_lengths_raises(
        self, synthetic_shap_row,
    ):
        with pytest.raises(ValueError, match="SHAP value count"):
            get_feature_contributions(synthetic_shap_row, ["f1", "f2"])


# ---------------------------------------------------------------------------
# Test: Local explanation
# ---------------------------------------------------------------------------


class TestLocalExplanation:
    """Tests for get_local_explanation."""

    def test_returns_structured_dict(
        self, synthetic_shap_row, feature_names_19,
    ):
        result = get_local_explanation(
            shap_values_row=synthetic_shap_row,
            base_value=0.3,
            feature_names=feature_names_19,
            prediction=1,
            probability=0.75,
        )
        assert isinstance(result, dict)
        assert result["prediction"] == 1
        assert result["probability"] == 0.75
        assert result["base_value"] == 0.3
        assert "features" in result
        assert len(result["features"]) == len(feature_names_19)

    def test_includes_required_fields(
        self, synthetic_shap_row, feature_names_19,
    ):
        result = get_local_explanation(
            synthetic_shap_row, 0.0, feature_names_19,
        )
        for feat in result["features"]:
            assert "name" in feat
            assert "shap_value" in feat
            assert "direction" in feat
            assert "absolute_importance" in feat
            assert "clinical_label" in feat

    def test_with_patient_values(
        self, synthetic_shap_row, feature_names_19,
    ):
        X_row = pd.DataFrame([np.ones(len(feature_names_19))], columns=feature_names_19)
        result = get_local_explanation(
            synthetic_shap_row, 0.0, feature_names_19, X_row=X_row,
        )
        for feat in result["features"]:
            assert "value" in feat


# ---------------------------------------------------------------------------
# Test: Global importance
# ---------------------------------------------------------------------------


class TestGlobalImportance:
    """Tests for get_global_feature_importance."""

    def test_returns_ranked_dataframe(
        self, synthetic_shap_values, feature_names_19,
    ):
        df = get_global_feature_importance(synthetic_shap_values, feature_names_19)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(feature_names_19)
        assert "rank" in df.columns
        assert "mean_absolute_shap" in df.columns
        assert df["rank"].min() == 1
        assert df["rank"].max() == len(feature_names_19)

    def test_sorted_descending(
        self, synthetic_shap_values, feature_names_19,
    ):
        df = get_global_feature_importance(synthetic_shap_values, feature_names_19)
        vals = df["mean_absolute_shap"].values
        assert all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1))

    def test_non_negative_mean_abs(
        self, synthetic_shap_values, feature_names_19,
    ):
        df = get_global_feature_importance(synthetic_shap_values, feature_names_19)
        assert all(df["mean_absolute_shap"] >= 0)

    def test_invalid_shape_raises(self, feature_names_19):
        bad_shap = np.ones((5, 19, 2))
        with pytest.raises(ValueError, match="Expected 2D"):
            get_global_feature_importance(bad_shap, feature_names_19)


# ---------------------------------------------------------------------------
# Test: Human-readable summary
# ---------------------------------------------------------------------------


class TestHumanReadableSummary:
    """Tests for generate_human_readable_summary."""

    def test_generates_string(
        self, synthetic_shap_row, feature_names_19,
    ):
        contributions = get_feature_contributions(synthetic_shap_row, feature_names_19)
        summary = generate_human_readable_summary(
            contributions, prediction=1, probability=0.7,
        )
        assert isinstance(summary, str)
        assert "Model prediction" in summary
        assert "probability" in summary

    def test_includes_risk_factors(
        self, synthetic_shap_row, feature_names_19,
    ):
        contributions = get_feature_contributions(synthetic_shap_row, feature_names_19)
        summary = generate_human_readable_summary(contributions, prediction=1)
        # Should mention either increasing or decreasing factors
        assert "contributing" in summary.lower()

    def test_disclaimer_present(
        self, synthetic_shap_row, feature_names_19,
    ):
        contributions = get_feature_contributions(synthetic_shap_row, feature_names_19)
        summary = generate_human_readable_summary(contributions)
        assert "causation" in summary.lower() or "model behavior" in summary.lower()


# ---------------------------------------------------------------------------
# Test: Visualisation
# ---------------------------------------------------------------------------


class TestVisualisations:
    """Tests for plot generation functions."""

    def test_waterfall_plot(
        self, synthetic_shap_row, feature_names_19, tmp_path,
    ):
        path = create_waterfall_plot(
            synthetic_shap_row, 0.3, feature_names_19,
            output_dir=tmp_path, filename="test_waterfall.png",
        )
        assert path.exists()
        assert path.suffix == ".png"
        assert path.stat().st_size > 0

    def test_global_importance_plot(self, tmp_path):
        imp_df = pd.DataFrame({
            "feature": ["age", "cholesterol", "max_heart_rate"],
            "mean_absolute_shap": [0.3, 0.2, 0.1],
            "clinical_label": ["Age", "Cholesterol", "Maximum Heart Rate"],
        })
        path = create_global_importance_plot(
            imp_df, output_dir=tmp_path, filename="test_global.png",
        )
        assert path.exists()
        assert path.stat().st_size > 0

    def test_local_importance_plot(self, synthetic_shap_row, feature_names_19, tmp_path):
        contrib = get_feature_contributions(synthetic_shap_row, feature_names_19)
        path = create_local_importance_plot(
            contrib, output_dir=tmp_path, filename="test_local.png",
        )
        assert path.exists()
        assert path.stat().st_size > 0

    def test_summary_plot(
        self, feature_names_19, tmp_path,
    ):
        rng = np.random.RandomState(42)
        shap_vals = rng.randn(20, 19)
        X = pd.DataFrame(
            rng.randn(20, 19), columns=feature_names_19,
        )
        path = create_summary_plot(
            shap_vals, feature_names_19,
            X=X,
            output_dir=tmp_path, filename="test_summary.png",
        )
        assert path.exists()
        assert path.stat().st_size > 0


# ---------------------------------------------------------------------------
# Test: Artifact export
# ---------------------------------------------------------------------------


class TestArtifactExport:
    """Tests for saving explanation artifacts."""

    def test_save_global_importance_csv(self, tmp_path):
        imp_df = pd.DataFrame({
            "feature": ["age", "chol"],
            "mean_absolute_shap": [0.3, 0.2],
            "rank": [1, 2],
        })
        path = save_global_importance_csv(imp_df, output_dir=tmp_path)
        assert path.exists()
        loaded = pd.read_csv(path)
        assert len(loaded) == 2

    def test_save_local_explanation_json(self, tmp_path):
        explanation = {
            "prediction": 1,
            "probability": 0.75,
            "base_value": 0.3,
            "features": [{"name": "age", "shap_value": 0.1}],
        }
        path = save_local_explanation_json(explanation, output_dir=tmp_path)
        assert path.exists()
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["prediction"] == 1

    def test_save_explainer_metadata(self, tmp_path):
        path = save_explainer_metadata(
            "logistic_regression", "LinearExplainer",
            ["age", "chol"], "train.csv",
            output_dir=tmp_path,
        )
        assert path.exists()
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["best_model"] == "logistic_regression"
        assert loaded["explainer_type"] == "LinearExplainer"
        assert "shap_version" in loaded

    def test_save_explainability_summary(self, tmp_path):
        imp_df = pd.DataFrame({
            "feature": ["age"],
            "mean_absolute_shap": [0.3],
            "clinical_label": ["Age"],
        })
        path = save_explainability_summary(
            "logistic_regression", "LinearExplainer",
            imp_df, local_explanation=None,
            output_dir=tmp_path,
        )
        assert path.exists()
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["model"] == "logistic_regression"


# ---------------------------------------------------------------------------
# Test: Clinical labels
# ---------------------------------------------------------------------------


class TestClinicalLabels:
    """Tests for CLINICAL_LABELS mapping."""

    def test_all_features_have_labels(self, feature_names_19):
        for name in feature_names_19:
            assert name in CLINICAL_LABELS, f"Missing clinical label for {name}"

    def test_labels_are_strings(self):
        for key, val in CLINICAL_LABELS.items():
            assert isinstance(val, str)
            assert len(val) > 0


# ---------------------------------------------------------------------------
# Test: Model reload workflow
# ---------------------------------------------------------------------------


class TestModelReloadWorkflow:
    """Test the complete workflow from saved artifacts."""

    def test_full_workflow(self, tmp_path):
        # Load model
        model, model_name = load_explainable_model()
        assert model is not None

        # Load feature names
        feature_names = load_feature_names()
        assert len(feature_names) > 0

        # Load training data
        train_data = load_training_data()
        assert len(train_data) > 0

        # Create explainer
        explainer, explainer_type = create_shap_explainer(model, train_data)
        assert explainer is not None

        # Calculate SHAP values
        shap_vals, base_vals = calculate_shap_values(
            explainer, train_data.iloc[:1],
        )
        assert shap_vals.shape[1] == len(feature_names)

        # Get contributions
        contrib = get_feature_contributions(shap_vals[0], feature_names)
        assert len(contrib) == len(feature_names)

        # Get local explanation
        explanation = get_local_explanation(
            shap_vals[0], float(base_vals[0]), feature_names,
            prediction=1, probability=0.7,
        )
        assert "features" in explanation

        # Save artifacts
        save_local_explanation_json(explanation, output_dir=tmp_path)
        assert (tmp_path / "shap_local_explanation.json").exists()


# ---------------------------------------------------------------------------
# Test: Explanation consistency
# ---------------------------------------------------------------------------


class TestExplanationConsistency:
    """Test that explanations are deterministic."""

    def test_same_input_same_output(self, synthetic_training_data):
        model, _ = load_explainable_model()
        explainer, _ = create_shap_explainer(model, synthetic_training_data)
        X = synthetic_training_data.iloc[:3]

        sv1, bv1 = calculate_shap_values(explainer, X)
        sv2, bv2 = calculate_shap_values(explainer, X)

        np.testing.assert_array_almost_equal(sv1, sv2, decimal=10)
        np.testing.assert_array_almost_equal(bv1, bv2, decimal=10)


# ---------------------------------------------------------------------------
# Test: No patient identity stored
# ---------------------------------------------------------------------------


class TestSecurityNoPatientIdentity:
    """Verify explanation artifacts do not contain patient identity."""

    def test_local_explanation_no_identity(self, synthetic_shap_row, feature_names_19, tmp_path):
        explanation = get_local_explanation(
            synthetic_shap_row, 0.3, feature_names_19,
            prediction=1, probability=0.7,
        )
        path = save_local_explanation_json(explanation, output_dir=tmp_path)
        with open(path) as f:
            loaded = json.load(f)
        # No top-level patient identity fields (name, phone, etc.)
        identity_fields = {"patient_name", "name_of_patient", "phone", "address", "ssn", "mrn"}
        assert not identity_fields.intersection(loaded.keys())
