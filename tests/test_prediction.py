"""Tests for prediction module."""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock


def test_prediction_module_importable():
    """Test that prediction module can be imported."""
    from src.ml import predict

    assert hasattr(predict, "predict_with_model")
    assert hasattr(predict, "predict_batch")
    assert hasattr(predict, "predict_probability")


def test_predict_with_model_signature():
    """Test that predict_with_model accepts model + patient_data."""
    from src.ml.predict import predict_with_model

    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([0])
    mock_model.predict_proba.return_value = np.array([[0.9, 0.1]])

    result = predict_with_model(mock_model, pd.DataFrame({"a": [1]}))
    assert "prediction" in result
    assert "probability" in result


def test_predict_batch_signature():
    """Test that predict_batch accepts model + X."""
    from src.ml.predict import predict_batch

    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([0, 1, 0])

    result = predict_batch(mock_model, pd.DataFrame({"a": [1, 2, 3]}))
    assert isinstance(result, np.ndarray)
    assert len(result) == 3


def test_predict_probability_signature():
    """Test that predict_probability accepts model + patient_data."""
    from src.ml.predict import predict_probability

    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.9, 0.1], [0.3, 0.7]])

    result = predict_probability(mock_model, pd.DataFrame({"a": [1, 2]}))
    assert isinstance(result, np.ndarray)
    assert len(result) == 2
