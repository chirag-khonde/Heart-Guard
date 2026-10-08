"""Unit tests for HeartGuard model creation and training utilities.

Tests model factory functions, evaluate functions, predict functions,
and model registry without requiring real data.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from src.ml.evaluate import (
    calculate_classification_metrics,
    calculate_confusion_matrix,
    calculate_roc_auc,
    compare_models,
    evaluate_model,
)
from src.ml.model_registry import (
    get_available_models,
    get_best_model_name,
    get_model_path,
    load_model,
    register_model,
    save_model,
)
from src.ml.predict import (
    predict_batch,
    predict_probability,
    predict_with_model,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_classification_data():
    """Generate reproducible synthetic classification data."""
    rng = np.random.RandomState(42)
    n = 100
    X = pd.DataFrame({
        "feature_0": rng.randn(n),
        "feature_1": rng.randn(n),
        "feature_2": rng.randint(0, 3, n),
    })
    y = pd.Series(rng.randint(0, 2, n), name="target")
    return X, y


@pytest.fixture
def fitted_logistic_regression(synthetic_classification_data):
    """Return a fitted LogisticRegression model."""
    X, y = synthetic_classification_data
    model = LogisticRegression(random_state=42, max_iter=200)
    model.fit(X, y)
    return model


@pytest.fixture
def fitted_random_forest(synthetic_classification_data):
    """Return a fitted RandomForestClassifier model."""
    X, y = synthetic_classification_data
    model = RandomForestClassifier(n_estimators=10, random_state=42, max_depth=3)
    model.fit(X, y)
    return model


@pytest.fixture
def mock_model():
    """Return a mock model with predict and predict_proba methods."""
    model = MagicMock()
    model.predict.return_value = np.array([0, 1, 1, 0, 1])
    model.predict_proba.return_value = np.array([
        [0.8, 0.2], [0.3, 0.7], [0.1, 0.9], [0.6, 0.4], [0.2, 0.8],
    ])
    return model


@pytest.fixture
def y_true_binary():
    """Ground-truth labels for testing."""
    return np.array([0, 1, 1, 0, 1])


@pytest.fixture
def y_pred_binary():
    """Predicted labels for testing."""
    return np.array([0, 1, 1, 0, 1])


@pytest.fixture
def y_prob_binary():
    """Predicted probabilities for testing."""
    return np.array([0.2, 0.8, 0.9, 0.4, 0.7])


# ---------------------------------------------------------------------------
# Model factory tests
# ---------------------------------------------------------------------------


class TestLogisticRegressionModel:
    """Tests for create_logistic_regression factory."""

    def test_returns_correct_type(self):
        from src.ml.models.logistic_regression_model import create_logistic_regression
        model = create_logistic_regression()
        assert isinstance(model, LogisticRegression)

    def test_default_hyperparameters(self):
        from src.ml.models.logistic_regression_model import create_logistic_regression
        model = create_logistic_regression()
        assert model.C == 1.0
        assert model.solver == "lbfgs"
        assert model.max_iter == 500
        assert model.random_state == 42

    def test_custom_hyperparameters(self):
        from src.ml.models.logistic_regression_model import create_logistic_regression
        model = create_logistic_regression(C=0.5, solver="liblinear", max_iter=300)
        assert model.C == 0.5
        assert model.solver == "liblinear"
        assert model.max_iter == 300

    def test_fits_and_predicts(self, synthetic_classification_data):
        from src.ml.models.logistic_regression_model import create_logistic_regression
        X, y = synthetic_classification_data
        model = create_logistic_regression()
        model.fit(X, y)
        preds = model.predict(X)
        assert len(preds) == len(y)
        assert set(np.unique(preds)).issubset({0, 1})


class TestRandomForestModel:
    """Tests for create_random_forest factory."""

    def test_returns_correct_type(self):
        from src.ml.models.random_forest_model import create_random_forest
        model = create_random_forest()
        assert isinstance(model, RandomForestClassifier)

    def test_default_hyperparameters(self):
        from src.ml.models.random_forest_model import create_random_forest
        model = create_random_forest()
        assert model.n_estimators == 200
        assert model.max_depth == 8
        assert model.min_samples_split == 5
        assert model.random_state == 42

    def test_custom_hyperparameters(self):
        from src.ml.models.random_forest_model import create_random_forest
        model = create_random_forest(n_estimators=50, max_depth=4)
        assert model.n_estimators == 50
        assert model.max_depth == 4

    def test_fits_and_predicts(self, synthetic_classification_data):
        from src.ml.models.random_forest_model import create_random_forest
        X, y = synthetic_classification_data
        model = create_random_forest(n_estimators=10, max_depth=3)
        model.fit(X, y)
        preds = model.predict(X)
        proba = model.predict_proba(X)
        assert len(preds) == len(y)
        assert proba.shape == (len(y), 2)


class TestXGBoostModel:
    """Tests for create_xgboost factory."""

    def test_returns_correct_type(self):
        from src.ml.models.xgboost_model import create_xgboost
        model = create_xgboost()
        assert type(model).__name__ == "XGBClassifier"

    def test_default_hyperparameters(self):
        from src.ml.models.xgboost_model import create_xgboost
        model = create_xgboost()
        assert model.n_estimators == 300
        assert model.max_depth == 4
        assert model.learning_rate == 0.05
        assert model.subsample == 0.8
        assert model.random_state == 42

    def test_custom_hyperparameters(self):
        from src.ml.models.xgboost_model import create_xgboost
        model = create_xgboost(n_estimators=100, max_depth=6, learning_rate=0.1)
        assert model.n_estimators == 100
        assert model.max_depth == 6
        assert model.learning_rate == 0.1

    def test_fits_and_predicts(self, synthetic_classification_data):
        from src.ml.models.xgboost_model import create_xgboost
        X, y = synthetic_classification_data
        model = create_xgboost(n_estimators=20, max_depth=3)
        model.fit(X, y)
        preds = model.predict(X)
        proba = model.predict_proba(X)
        assert len(preds) == len(y)
        assert proba.shape == (len(y), 2)


class TestNeuralNetworkModel:
    """Tests for create_neural_network factory (sklearn MLPClassifier)."""

    def test_returns_correct_type(self):
        from sklearn.neural_network import MLPClassifier
        from src.ml.models.neural_network_model import create_neural_network
        model = create_neural_network()
        assert isinstance(model, MLPClassifier)

    def test_default_architecture(self):
        from src.ml.models.neural_network_model import create_neural_network
        model = create_neural_network()
        assert model.hidden_layer_sizes == (64, 32, 16)
        assert model.activation == "relu"
        assert model.max_iter == 50

    def test_custom_architecture(self):
        from src.ml.models.neural_network_model import create_neural_network
        model = create_neural_network(hidden_layer_sizes=(128, 64), max_iter=100)
        assert model.hidden_layer_sizes == (128, 64)
        assert model.max_iter == 100

    def test_fits_and_predicts(self, synthetic_classification_data):
        from src.ml.models.neural_network_model import create_neural_network
        X, y = synthetic_classification_data
        model = create_neural_network(max_iter=20)
        model.fit(X.values, y.values)
        preds = model.predict(X.values)
        proba = model.predict_proba(X.values)
        assert len(preds) == len(y)
        assert proba.shape == (len(y), 2)

    def test_reproducible_with_same_seed(self, synthetic_classification_data):
        from src.ml.models.neural_network_model import create_neural_network
        X, y = synthetic_classification_data
        m1 = create_neural_network(random_state=42, max_iter=10)
        m1.fit(X.values, y.values)

        m2 = create_neural_network(random_state=42, max_iter=10)
        m2.fit(X.values, y.values)

        # Same seed should produce same predictions
        np.testing.assert_array_equal(m1.predict(X.values), m2.predict(X.values))

    def test_loss_curve_populated(self, synthetic_classification_data):
        from src.ml.models.neural_network_model import create_neural_network
        X, y = synthetic_classification_data
        model = create_neural_network(max_iter=10)
        model.fit(X.values, y.values)
        assert hasattr(model, "loss_curve_")
        assert len(model.loss_curve_) > 0


# ---------------------------------------------------------------------------
# Evaluate tests
# ---------------------------------------------------------------------------


class TestCalculateClassificationMetrics:
    """Tests for calculate_classification_metrics."""

    def test_perfect_predictions(self, y_true_binary, y_pred_binary):
        # y_pred_binary matches y_true_binary exactly
        metrics = calculate_classification_metrics(y_true_binary, y_pred_binary)
        assert metrics["accuracy"] == 1.0
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1"] == 1.0

    def test_all_wrong(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([1, 1, 0, 0])
        metrics = calculate_classification_metrics(y_true, y_pred)
        assert metrics["accuracy"] == 0.0

    def test_known_values(self):
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 0, 1])
        metrics = calculate_classification_metrics(y_true, y_pred)
        assert metrics["accuracy"] == 0.8
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == round(2 / 3, 4)

    def test_returns_all_keys(self, y_true_binary, y_pred_binary):
        metrics = calculate_classification_metrics(y_true_binary, y_pred_binary)
        assert set(metrics.keys()) == {"accuracy", "precision", "recall", "f1"}


class TestCalculateRocAuc:
    """Tests for calculate_roc_auc."""

    def test_perfect_separation(self):
        y_true = np.array([0, 0, 1, 1])
        y_prob = np.array([0.1, 0.2, 0.9, 0.95])
        auc = calculate_roc_auc(y_true, y_prob)
        assert auc == 1.0

    def test_random_performance(self):
        rng = np.random.RandomState(42)
        y_true = rng.randint(0, 2, 200)
        y_prob = rng.rand(200)
        auc = calculate_roc_auc(y_true, y_prob)
        assert 0.3 < auc < 0.7  # ~0.5 for random

    def test_returns_float(self, y_true_binary, y_prob_binary):
        auc = calculate_roc_auc(y_true_binary, y_prob_binary)
        assert isinstance(auc, float)


class TestEvaluateModel:
    """Tests for evaluate_model."""

    def test_returns_all_metrics(
        self, fitted_logistic_regression, synthetic_classification_data
    ):
        X, y = synthetic_classification_data
        metrics = evaluate_model(fitted_logistic_regression, X, y, "test_lr")
        assert set(metrics.keys()) == {"accuracy", "precision", "recall", "f1", "roc_auc"}

    def test_metric_bounds(self, fitted_logistic_regression, synthetic_classification_data):
        X, y = synthetic_classification_data
        metrics = evaluate_model(fitted_logistic_regression, X, y, "test_lr")
        for key in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
            assert 0.0 <= metrics[key] <= 1.0


class TestEvaluateAllModels:
    """Tests for evaluate_all_models."""

    def test_returns_all_model_results(
        self, fitted_logistic_regression, fitted_random_forest, synthetic_classification_data
    ):
        from src.ml.evaluate import evaluate_all_models
        X, y = synthetic_classification_data
        models = {"lr": fitted_logistic_regression, "rf": fitted_random_forest}
        results = evaluate_all_models(models, X, y)
        assert set(results.keys()) == {"lr", "rf"}
        for name in results:
            assert "roc_auc" in results[name]


class TestCompareModels:
    """Tests for compare_models."""

    def test_returns_dataframe(self):
        results = {
            "lr": {"accuracy": 0.85, "roc_auc": 0.90},
            "rf": {"accuracy": 0.88, "roc_auc": 0.92},
        }
        df = compare_models(results)
        assert isinstance(df, pd.DataFrame)
        assert "accuracy" in df.columns
        assert df.index.name == "model"


class TestConfusionMatrix:
    """Tests for calculate_confusion_matrix."""

    def test_shape(self, y_true_binary, y_pred_binary):
        cm = calculate_confusion_matrix(y_true_binary, y_pred_binary)
        assert cm.shape == (2, 2)

    def test_perfect(self):
        y = np.array([0, 0, 1, 1])
        cm = calculate_confusion_matrix(y, y)
        assert cm[0, 0] == 2  # TN
        assert cm[1, 1] == 2  # TP
        assert cm[0, 1] == 0
        assert cm[1, 0] == 0


# ---------------------------------------------------------------------------
# Predict tests
# ---------------------------------------------------------------------------


class TestPredictWithModel:
    """Tests for predict_with_model."""

    def test_returns_expected_keys(self, mock_model):
        X = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        result = predict_with_model(mock_model, X, "test")
        assert "prediction" in result
        assert "probability" in result
        assert "model_name" in result
        assert result["model_name"] == "test"

    def test_single_row_returns_scalar(self):
        mock = MagicMock()
        mock.predict.return_value = np.array([1])
        mock.predict_proba.return_value = np.array([[0.3, 0.7]])
        X = pd.DataFrame({"a": [1]})
        result = predict_with_model(mock, X)
        assert isinstance(result["prediction"], int)
        assert isinstance(result["probability"], float)

    def test_multi_row_returns_list(self, mock_model):
        X = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        result = predict_with_model(mock_model, X)
        assert isinstance(result["prediction"], list)
        assert isinstance(result["probability"], list)


class TestPredictBatch:
    """Tests for predict_batch."""

    def test_returns_array(self, mock_model):
        X = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        preds = predict_batch(mock_model, X)
        assert isinstance(preds, np.ndarray)
        assert len(preds) == 5


class TestPredictProbability:
    """Tests for predict_probability."""

    def test_returns_array(self, mock_model):
        X = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        probs = predict_probability(mock_model, X)
        assert isinstance(probs, np.ndarray)
        assert len(probs) == 5
        assert all(0 <= p <= 1 for p in probs)


# ---------------------------------------------------------------------------
# Model registry tests
# ---------------------------------------------------------------------------


class TestModelRegistry:
    """Tests for model registry functions."""

    def test_get_model_path(self):
        path = get_model_path("logistic_regression")
        assert path.name == "logistic_regression.pkl"

    def test_get_model_path_neural_network(self):
        path = get_model_path("neural_network")
        assert path.name == "neural_network.pkl"

    def test_save_and_load_sklearn_model(self, fitted_logistic_regression, tmp_path):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            original_model_dir = Path("config/settings.py").resolve().parent.parent / "models"

            test_path = Path(td) / "logistic_regression.pkl"
            joblib.dump(fitted_logistic_regression, test_path)
            loaded = joblib.load(test_path)
            assert isinstance(loaded, LogisticRegression)

            # Verify predictions match
            X = np.random.RandomState(42).randn(5, 3)
            orig_pred = fitted_logistic_regression.predict(X)
            load_pred = loaded.predict(X)
            np.testing.assert_array_equal(orig_pred, load_pred)

    def test_get_available_models_returns_dict(self, tmp_path):
        # get_available_models returns a dict mapping name → availability
        models = get_available_models()
        assert isinstance(models, dict)

    def test_register_model(self, tmp_path):
        from src.ml.model_registry import ModelRegistry
        ModelRegistry.reset()
        import numpy as np

        dummy_artifact = np.array([1, 2, 3])
        path = tmp_path / "test_model.pkl"
        register_model("test_model", path, dummy_artifact, version="test-v1")
        assert ModelRegistry.get().is_available("test_model")
