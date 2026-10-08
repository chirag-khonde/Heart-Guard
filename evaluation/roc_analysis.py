"""ROC analysis module for HeartGuard model evaluation (Phase 14)."""

from __future__ import annotations

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.evaluation.classification_metrics import calculate_roc_metrics


def compute_roc_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> dict[str, object]:
    """Compute ROC curve data. Delegates to classification_metrics.

    Args:
        y_true: Ground-truth binary labels.
        y_prob: Predicted probabilities for the positive class.

    Returns:
        Dict with 'auc', 'fpr', 'tpr', 'thresholds'.
    """
    return calculate_roc_metrics(y_true, y_prob)


def plot_roc_figure(
    fpr: list[float],
    tpr: list[float],
    auc: float,
    model_name: str,
) -> io.BytesIO:
    """Plot a single-model ROC curve and return as PNG byte buffer.

    Args:
        fpr: False positive rates.
        tpr: True positive rates.
        auc: Area under the curve.
        model_name: Model name for plot title.

    Returns:
        In-memory PNG byte buffer.
    """
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#ffffff")

    ax.plot(fpr, tpr, color="#1e3a8a", linewidth=2.5,
            label=f"{model_name.replace('_', ' ').title()} (AUC = {auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", linewidth=1.2, label="Random Classifier")

    ax.fill_between(fpr, tpr, alpha=0.08, color="#1e3a8a")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate", fontsize=10)
    ax.set_ylabel("True Positive Rate", fontsize=10)
    ax.set_title(f"ROC Curve — {model_name.replace('_', ' ').title()}", fontsize=11, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def plot_roc_comparison_figure(
    roc_data: dict[str, dict[str, object]],
) -> io.BytesIO:
    """Plot ROC curves for multiple models on a single figure.

    Args:
        roc_data: Dict mapping model_name -> roc dict (from compute_roc_curve).

    Returns:
        In-memory PNG byte buffer.
    """
    colors = ["#1e3a8a", "#0284c7", "#d97706", "#7c3aed"]
    fig, ax = plt.subplots(figsize=(7, 5))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#ffffff")

    for (name, data), color in zip(roc_data.items(), colors):
        ax.plot(data["fpr"], data["tpr"], color=color, linewidth=2,
                label=f"{name.replace('_', ' ').title()} (AUC = {data['auc']:.3f})")

    ax.plot([0, 1], [0, 1], "k--", linewidth=1.2, label="Random")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate", fontsize=10)
    ax.set_ylabel("True Positive Rate", fontsize=10)
    ax.set_title("ROC Curve Comparison — All Models", fontsize=11, fontweight="bold")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf
