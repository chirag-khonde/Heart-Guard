"""Model evaluation module for HeartGuard.

Provides reusable functions for evaluating classification models.
All metrics are calculated from actual predictions -- no fabricated values.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Single-model metrics
# ---------------------------------------------------------------------------


def calculate_classification_metrics(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
) -> dict[str, float]:
    """Calculate accuracy, precision, recall, and F1 for binary classification.

    Args:
        y_true: Ground-truth labels.
        y_pred: Predicted labels.

    Returns:
        Dictionary with accuracy, precision, recall, f1.
    """
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
    }


def calculate_roc_auc(
    y_true: np.ndarray | pd.Series,
    y_prob: np.ndarray | pd.Series,
) -> float:
    """Calculate ROC-AUC from probability estimates.

    Args:
        y_true: Ground-truth labels.
        y_prob: Predicted probabilities for the positive class.

    Returns:
        ROC-AUC score rounded to 4 decimal places.
    """
    return round(float(roc_auc_score(y_true, y_prob)), 4)


def calculate_confusion_matrix(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
) -> np.ndarray:
    """Calculate a confusion matrix.

    Args:
        y_true: Ground-truth labels.
        y_pred: Predicted labels.

    Returns:
        2x2 confusion matrix as numpy array.
    """
    return confusion_matrix(y_true, y_pred)


def evaluate_model(
    model: Any,
    X_test: np.ndarray | pd.DataFrame,
    y_test: np.ndarray | pd.Series,
    model_name: str = "model",
) -> dict[str, Any]:
    """Evaluate a trained model on the test set.

    Returns classification metrics and the ROC-AUC score.

    Args:
        model: Trained classifier with predict() and predict_proba().
        X_test: Test features.
        y_test: Test labels.
        model_name: Name for logging.

    Returns:
        Dictionary with accuracy, precision, recall, f1, roc_auc.
    """
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = calculate_classification_metrics(y_test, y_pred)
    roc_auc = calculate_roc_auc(y_test, y_prob)
    metrics["roc_auc"] = roc_auc

    logger.info(
        "%s test metrics: acc=%.4f, prec=%.4f, rec=%.4f, f1=%.4f, auc=%.4f",
        model_name, metrics["accuracy"], metrics["precision"],
        metrics["recall"], metrics["f1"], roc_auc,
    )
    return metrics


# ---------------------------------------------------------------------------
# Multi-model comparison
# ---------------------------------------------------------------------------


def evaluate_all_models(
    models: dict[str, Any],
    X_test: np.ndarray | pd.DataFrame,
    y_test: np.ndarray | pd.Series,
) -> dict[str, dict[str, float]]:
    """Evaluate multiple models on the same test set.

    Args:
        models: Dict mapping model_name -> fitted model.
        X_test: Test features.
        y_test: Test labels.

    Returns:
        Dict mapping model_name -> metrics dict.
    """
    results: dict[str, dict[str, float]] = {}
    for name, model in models.items():
        results[name] = evaluate_model(model, X_test, y_test, model_name=name)
    return results


def compare_models(results: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Create a comparison DataFrame from evaluation results.

    Args:
        results: Dict mapping model_name -> metrics dict.

    Returns:
        DataFrame with models as rows and metrics as columns.
    """
    df = pd.DataFrame(results).T
    df.index.name = "model"
    return df.round(4)


# ---------------------------------------------------------------------------
# Visualisation
# ---------------------------------------------------------------------------


def plot_confusion_matrix(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
    model_name: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Plot and save a confusion matrix figure.

    Args:
        y_true: Ground-truth labels.
        y_pred: Predicted labels.
        model_name: Model name for the title and filename.
        output_dir: Directory for the saved figure.

    Returns:
        Path to saved figure.
    """
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent.parent / "reports" / "figures"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=[0, 1], yticks=[0, 1],
        xticklabels=["Absence", "Presence"],
        yticklabels=["Absence", "Presence"],
        ylabel="True Label", xlabel="Predicted Label",
        title=f"Confusion Matrix — {model_name}",
    )
    for i in range(2):
        for j in range(2):
            ax.text(j, i, format(cm[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.tight_layout()
    path = output_dir / f"{model_name}_confusion_matrix.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Confusion matrix saved to %s", path)
    return path


def plot_roc_comparison(
    models: dict[str, Any],
    X_test: np.ndarray | pd.DataFrame,
    y_test: np.ndarray | pd.Series,
    output_dir: str | Path | None = None,
) -> Path:
    """Plot ROC curves for all models on one figure.

    Args:
        models: Dict mapping model_name -> fitted model.
        X_test: Test features.
        y_test: Test labels.
        output_dir: Directory for the saved figure.

    Returns:
        Path to saved figure.
    """
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent.parent / "reports" / "figures"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#3498db", "#2ecc71", "#e74c3c", "#9b59b6"]

    for (name, model), color in zip(models.items(), colors):
        y_prob = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        auc = roc_auc_score(y_test, y_prob)
        ax.plot(fpr, tpr, color=color, label=f"{name} (AUC = {auc:.3f})", linewidth=2)

    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Random")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve Comparison — All Models")
    ax.legend(loc="lower right")
    fig.tight_layout()
    path = output_dir / "model_roc_comparison.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("ROC comparison saved to %s", path)
    return path


def plot_metrics_comparison(
    results: dict[str, dict[str, float]],
    output_dir: str | Path | None = None,
) -> Path:
    """Plot a grouped bar chart comparing model metrics.

    Args:
        results: Dict mapping model_name -> metrics dict.
        output_dir: Directory for the saved figure.

    Returns:
        Path to saved figure.
    """
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent.parent / "reports" / "figures"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_to_plot = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    model_names = list(results.keys())
    n_models = len(model_names)
    n_metrics = len(metrics_to_plot)

    x = np.arange(n_metrics)
    width = 0.8 / n_models
    colors = ["#3498db", "#2ecc71", "#e74c3c", "#9b59b6"]

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (name, color) in enumerate(zip(model_names, colors)):
        values = [results[name].get(m, 0) for m in metrics_to_plot]
        ax.bar(x + i * width, values, width, label=name, color=color, edgecolor="black")

    ax.set_ylabel("Score")
    ax.set_title("Model Metrics Comparison")
    ax.set_xticks(x + width * (n_models - 1) / 2)
    ax.set_xticklabels([m.replace("_", " ").title() for m in metrics_to_plot])
    ax.set_ylim([0, 1.05])
    ax.legend()
    fig.tight_layout()
    path = output_dir / "model_metrics_comparison.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Metrics comparison saved to %s", path)
    return path
