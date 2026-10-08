"""Classification metrics for HeartGuard model evaluation (Phase 14).

All metrics are computed from actual predictions — no fabricated values.
Handles zero-division safely.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def calculate_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    """Compute accuracy, precision, recall, F1, specificity, and balanced accuracy.

    Args:
        y_true: Ground-truth binary labels.
        y_pred: Predicted binary labels.

    Returns:
        Dictionary of metric name -> rounded float value.
    """
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    spec = calculate_specificity(y_true, y_pred)
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "specificity": round(spec, 4),
        "balanced_accuracy": round(bal_acc, 4),
    }


def calculate_specificity(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute specificity = TN / (TN + FP).

    Handles zero denominator safely (returns 0.0).

    Args:
        y_true: Ground-truth binary labels.
        y_pred: Predicted binary labels.

    Returns:
        Specificity score in [0, 1].
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    denom = tn + fp
    return round(tn / denom, 4) if denom > 0 else 0.0


def calculate_roc_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> dict[str, object]:
    """Compute ROC curve data and AUC.

    Args:
        y_true: Ground-truth binary labels.
        y_prob: Predicted probabilities for the positive class.

    Returns:
        Dictionary with 'auc', 'fpr', 'tpr', 'thresholds' (all as lists).
    """
    auc = round(float(roc_auc_score(y_true, y_prob)), 4)
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    return {
        "auc": auc,
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist(),
    }


def calculate_pr_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> dict[str, object]:
    """Compute Precision-Recall curve data and average precision (PR-AUC).

    Args:
        y_true: Ground-truth binary labels.
        y_prob: Predicted probabilities for the positive class.

    Returns:
        Dictionary with 'pr_auc', 'precision', 'recall', 'thresholds'.
    """
    pr_auc = round(float(average_precision_score(y_true, y_prob)), 4)
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    return {
        "pr_auc": pr_auc,
        "precision": precision.tolist(),
        "recall": recall.tolist(),
        "thresholds": thresholds.tolist(),
    }


def calculate_brier_score(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> float:
    """Compute Brier score for calibration evaluation.

    Args:
        y_true: Ground-truth binary labels.
        y_prob: Predicted probabilities for the positive class.

    Returns:
        Brier score rounded to 4 decimal places.
    """
    return round(float(brier_score_loss(y_true, y_prob)), 4)


def calculate_per_class_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_labels: list[str] | None = None,
) -> list[dict[str, object]]:
    """Compute per-class precision, recall, F1, and support.

    Args:
        y_true: Ground-truth binary labels.
        y_pred: Predicted binary labels.
        class_labels: Optional list of class names for labels 0 and 1.

    Returns:
        List of dicts with 'class', 'precision', 'recall', 'f1', 'support'.
    """
    classes = class_labels or ["Absence (0)", "Presence (1)"]
    results = []
    for i, label in enumerate(classes):
        mask_true = np.asarray(y_true) == i
        mask_pred = np.asarray(y_pred) == i
        support = int(mask_true.sum())
        if support == 0:
            results.append({"class": label, "precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0})
            continue
        prec = float(precision_score(y_true, y_pred, pos_label=i, zero_division=0))
        rec = float(recall_score(y_true, y_pred, pos_label=i, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, pos_label=i, zero_division=0))
        results.append({
            "class": label,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": support,
        })
    return results
