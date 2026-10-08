"""Precision-Recall analysis for HeartGuard model evaluation (Phase 14)."""

from __future__ import annotations

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.evaluation.classification_metrics import calculate_pr_metrics


def compute_pr_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> dict[str, object]:
    """Compute Precision-Recall curve data and PR-AUC.

    Args:
        y_true: Ground-truth binary labels.
        y_prob: Predicted probabilities for positive class.

    Returns:
        Dict with 'pr_auc', 'precision', 'recall', 'thresholds'.
    """
    return calculate_pr_metrics(y_true, y_prob)


def plot_pr_figure(
    precision: list[float],
    recall: list[float],
    pr_auc: float,
    model_name: str,
    baseline_positive_rate: float | None = None,
) -> io.BytesIO:
    """Plot a Precision-Recall curve.

    Args:
        precision: Precision values.
        recall: Recall values.
        pr_auc: Average precision (PR-AUC).
        model_name: Model name for plot title.
        baseline_positive_rate: Class positive rate baseline (no-skill line).

    Returns:
        In-memory PNG byte buffer.
    """
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#ffffff")

    ax.plot(recall, precision, color="#d97706", linewidth=2.5,
            label=f"{model_name.replace('_', ' ').title()} (AP = {pr_auc:.3f})")
    ax.fill_between(recall, precision, alpha=0.08, color="#d97706")

    if baseline_positive_rate is not None:
        ax.axhline(y=baseline_positive_rate, color="#6b7280", linestyle="--",
                   linewidth=1.2, label=f"No-Skill ({baseline_positive_rate:.2f})")

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("Recall", fontsize=10)
    ax.set_ylabel("Precision", fontsize=10)
    ax.set_title(f"Precision-Recall Curve — {model_name.replace('_', ' ').title()}", fontsize=11, fontweight="bold")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf
