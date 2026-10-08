"""Confusion matrix computation and plotting for HeartGuard evaluation (Phase 14)."""

from __future__ import annotations

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix


def compute_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, int | float]:
    """Compute a binary confusion matrix with derived rates.

    Args:
        y_true: Ground-truth binary labels (0/1).
        y_pred: Predicted binary labels (0/1).

    Returns:
        Dict with TP, TN, FP, FN, FPR, FNR, TPR, TNR.
    """
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])
    total = tn + fp + fn + tp

    fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
    fnr = round(fn / (fn + tp), 4) if (fn + tp) > 0 else 0.0
    tpr = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0  # sensitivity / recall
    tnr = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0  # specificity

    return {
        "TP": tp, "TN": tn, "FP": fp, "FN": fn,
        "total": total,
        "fpr": fpr,
        "fnr": fnr,
        "tpr": tpr,
        "tnr": tnr,
    }


def plot_confusion_matrix_figure(
    cm_dict: dict[str, int | float],
    model_name: str,
) -> io.BytesIO:
    """Plot a confusion matrix heatmap and return as PNG byte buffer.

    Args:
        cm_dict: Dict from :func:`compute_confusion_matrix`.
        model_name: Model name for the plot title.

    Returns:
        In-memory PNG byte buffer.
    """
    tn = cm_dict["TN"]
    fp = cm_dict["FP"]
    fn = cm_dict["FN"]
    tp = cm_dict["TP"]
    cm_arr = np.array([[tn, fp], [fn, tp]])

    labels = ["Absence\n(No Disease)", "Presence\n(Disease)"]

    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_facecolor("#f8fafc")
    im = ax.imshow(cm_arr, interpolation="nearest", cmap=plt.cm.Blues)
    fig.colorbar(im, ax=ax)

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Predicted Label", fontsize=9)
    ax.set_ylabel("True Label", fontsize=9)
    ax.set_title(f"Confusion Matrix — {model_name.replace('_', ' ').title()}", fontsize=10, fontweight="bold")

    threshold = cm_arr.max() / 2.0
    for i in range(2):
        for j in range(2):
            cell_label = ["TN", "FP", "FN", "TP"][i * 2 + j]
            ax.text(
                j, i,
                f"{cell_label}\n{cm_arr[i, j]}",
                ha="center", va="center", fontsize=11,
                color="white" if cm_arr[i, j] > threshold else "black",
            )

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf
