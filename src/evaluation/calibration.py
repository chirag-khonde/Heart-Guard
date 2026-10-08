"""Calibration analysis for HeartGuard model evaluation (Phase 14).

Evaluates how well a model's predicted probabilities reflect actual outcome frequencies.

IMPORTANT: Output labels use "Model predicted probability" — NOT "true probability of disease."
Uncalibrated models may output probabilities that do not reflect real-world frequencies.
"""

from __future__ import annotations

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import calibration_curve

from src.evaluation.classification_metrics import calculate_brier_score

CALIBRATION_DISCLAIMER = (
    "Calibration curves show how well model-predicted probabilities align with observed "
    "outcome frequencies in the evaluation dataset. A perfectly calibrated model's curve "
    "follows the diagonal. Probabilities are model outputs — they are NOT validated "
    "estimates of individual disease probability."
)


def compute_calibration(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> dict[str, object]:
    """Compute calibration curve data and Brier score.

    Args:
        y_true: Ground-truth binary labels.
        y_prob: Predicted probabilities for the positive class.
        n_bins: Number of bins for the calibration curve.

    Returns:
        Dict with 'brier_score', 'mean_predicted_prob', 'fraction_of_positives', 'disclaimer'.
    """
    brier = calculate_brier_score(y_true, y_prob)
    fraction_of_positives, mean_predicted_prob = calibration_curve(
        y_true, y_prob, n_bins=n_bins, strategy="uniform"
    )
    return {
        "brier_score": brier,
        "mean_predicted_prob": mean_predicted_prob.tolist(),
        "fraction_of_positives": fraction_of_positives.tolist(),
        "disclaimer": CALIBRATION_DISCLAIMER,
    }


def plot_calibration_figure(
    calibration_data: dict[str, object],
    model_name: str,
) -> io.BytesIO:
    """Plot a reliability diagram (calibration curve).

    Args:
        calibration_data: Dict from :func:`compute_calibration`.
        model_name: Model name for the plot title.

    Returns:
        In-memory PNG byte buffer.
    """
    mean_pred = calibration_data["mean_predicted_prob"]
    frac_pos = calibration_data["fraction_of_positives"]
    brier = calibration_data["brier_score"]

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#ffffff")

    ax.plot(mean_pred, frac_pos, "s-", color="#7c3aed", linewidth=2,
            label=f"{model_name.replace('_', ' ').title()} (Brier = {brier:.4f})")
    ax.plot([0, 1], [0, 1], "k--", linewidth=1.2, label="Perfect Calibration")

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("Mean Predicted Probability", fontsize=10)
    ax.set_ylabel("Fraction of Positives", fontsize=10)
    ax.set_title(f"Calibration Curve — {model_name.replace('_', ' ').title()}", fontsize=11, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf
