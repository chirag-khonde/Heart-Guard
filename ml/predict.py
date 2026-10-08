"""Prediction module for HeartGuard.

Provides functions for making predictions using trained models.
All predictions are experimental model estimates, not clinical diagnoses.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def predict_with_model(
    model: Any,
    patient_data: pd.DataFrame | np.ndarray,
    model_name: str = "model",
) -> dict[str, Any]:
    """Generate a binary prediction for patient data.

    Args:
        model: Trained classifier with predict() and predict_proba().
        patient_data: Patient features (single row or batch).
        model_name: Name for logging.

    Returns:
        Dictionary with 'prediction' (0/1) and 'probability' (float).
    """
    y_pred = model.predict(patient_data)
    y_prob = model.predict_proba(patient_data)[:, 1]

    prediction = int(y_pred[0]) if len(y_pred) == 1 else y_pred.tolist()
    probability = float(y_prob[0]) if len(y_prob) == 1 else y_prob.tolist()

    logger.info(
        "%s prediction: class=%s, prob=%.4f",
        model_name, prediction, probability if isinstance(probability, float) else probability[0],
    )
    return {
        "prediction": prediction,
        "probability": probability,
        "model_name": model_name,
    }


def predict_batch(
    model: Any,
    X: pd.DataFrame | np.ndarray,
) -> np.ndarray:
    """Generate predictions for multiple patients.

    Args:
        model: Trained classifier.
        X: Feature matrix.

    Returns:
        Array of predicted class labels.
    """
    return model.predict(X)


def predict_probability(
    model: Any,
    patient_data: pd.DataFrame | np.ndarray,
) -> np.ndarray:
    """Generate probability estimates for the positive class.

    Args:
        model: Trained classifier with predict_proba().
        patient_data: Patient features.

    Returns:
        Array of probabilities for class 1.
    """
    return model.predict_proba(patient_data)[:, 1]
