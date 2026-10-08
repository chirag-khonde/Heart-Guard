"""Neural Network / MLP model for HeartGuard.

Multilayer Perceptron classification model using sklearn's MLPClassifier.
Architecture derived from the HeartGuard project specification.

Architecture:
    Input -> Dense(64, ReLU) -> Dense(32, ReLU) -> Dense(16, ReLU) -> Output

Note: TensorFlow/Keras requires a compatible backend. Since Python 3.14
does not yet have stable TensorFlow support, this implementation uses
sklearn's MLPClassifier which provides equivalent MLP functionality.
The hidden_layer_sizes=(64, 32, 16) matches the specified architecture.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.neural_network import MLPClassifier

from src.utils.logger import get_logger

logger = get_logger(__name__)

RANDOM_STATE: int = 42


def create_neural_network(
    input_dim: int | None = None,
    hidden_layer_sizes: tuple[int, ...] = (64, 32, 16),
    activation: str = "relu",
    alpha: float = 0.0001,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    max_iter: int = 50,
    random_state: int = RANDOM_STATE,
    **kwargs: Any,
) -> MLPClassifier:
    """Create a configured Neural Network (MLP) model.

    Args:
        input_dim: Not used by MLPClassifier, kept for API compatibility.
        hidden_layer_sizes: Tuple of layer sizes (default (64, 32, 16)).
        activation: Activation function (default 'relu').
        alpha: L2 regularisation strength (default 0.0001).
        batch_size: Batch size (default 32).
        learning_rate: Initial learning rate (default 0.001).
        max_iter: Maximum training epochs (default 50).
        random_state: Random seed (default 42).

    Returns:
        Unfitted MLPClassifier instance.
    """
    model = MLPClassifier(
        hidden_layer_sizes=hidden_layer_sizes,
        activation=activation,
        alpha=alpha,
        batch_size=batch_size,
        learning_rate_init=learning_rate,
        max_iter=max_iter,
        random_state=random_state,
    )
    logger.info(
        "Neural Network created: layers=%s, activation=%s, max_iter=%d",
        hidden_layer_sizes, activation, max_iter,
    )
    return model


def train_neural_network(
    model: MLPClassifier,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray | None = None,
    y_val: np.ndarray | None = None,
    max_iter: int = 50,
    batch_size: int = 32,
    random_state: int = RANDOM_STATE,
    verbose: int = 0,
) -> dict[str, Any]:
    """Train the neural network model.

    Args:
        model: MLPClassifier instance.
        X_train: Training features.
        y_train: Training labels.
        X_val: Validation features (optional, used for tracking).
        y_val: Validation labels (optional).
        max_iter: Maximum epochs.
        batch_size: Batch size.
        random_state: Random seed.
        verbose: Verbosity level (0 = silent).

    Returns:
        Dictionary with training history (loss_curve_, validation_scores_).
    """
    model.fit(X_train, y_train)

    history: dict[str, Any] = {
        "loss_curve": [round(float(v), 4) for v in model.loss_curve_],
        "n_iter": model.n_iter_,
        "final_loss": round(float(model.loss_curve_[-1]), 4) if model.loss_curve_ else None,
    }

    if hasattr(model, "validation_scores_") and model.validation_scores_:
        history["validation_scores"] = [round(float(v), 4) for v in model.validation_scores_]

    logger.info(
        "Neural Network trained for %d epochs, final loss=%.4f",
        model.n_iter_, history["final_loss"] or 0.0,
    )
    return history


def save_neural_network(model: MLPClassifier, path: str | Path) -> Path:
    """Save the neural network model to disk.

    Args:
        model: Trained MLPClassifier.
        path: File path (should end in .pkl).

    Returns:
        Path to saved model.
    """
    import joblib
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    logger.info("Neural Network saved to %s", path)
    return path


def load_neural_network(path: str | Path) -> MLPClassifier:
    """Load a neural network model from disk.

    Args:
        path: File path to saved model.

    Returns:
        Loaded MLPClassifier.
    """
    import joblib
    path = Path(path)
    model = joblib.load(path)
    logger.info("Neural Network loaded from %s", path)
    return model
