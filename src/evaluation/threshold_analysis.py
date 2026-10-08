"""Threshold analysis for HeartGuard model evaluation (Phase 14).

Evaluates binary classification performance across a range of probability
thresholds to show FP/FN trade-offs.

IMPORTANT: Changing the classification threshold changes the trade-off between
false positives and false negatives. No experimental threshold is presented
as clinically optimal. The production threshold is identified separately.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.evaluation.classification_metrics import calculate_specificity

THRESHOLD_DISCLAIMER = (
    "Changing the classification threshold changes the trade-off between false positives "
    "and false negatives. Lower thresholds increase recall (sensitivity) at the cost of "
    "higher false-positive rates. Higher thresholds reduce false positives but may miss "
    "more positive cases. No experimental threshold is presented as clinically optimal."
)

DEFAULT_THRESHOLDS = np.round(np.arange(0.10, 0.91, 0.05), 2).tolist()


def analyse_thresholds(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    thresholds: list[float] | None = None,
    production_threshold: float = 0.50,
) -> dict[str, object]:
    """Evaluate classification performance across probability thresholds.

    Args:
        y_true: Ground-truth binary labels.
        y_prob: Predicted probabilities for the positive class.
        thresholds: List of threshold values to evaluate (default: 0.10–0.90 in 0.05 steps).
        production_threshold: The current production threshold (default 0.50).

    Returns:
        Dict with 'disclaimer', 'production_threshold', 'results' (list of per-threshold dicts).
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    results = []
    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        tp = int(((y_true == 1) & (y_pred == 1)).sum())
        tn = int(((y_true == 0) & (y_pred == 0)).sum())
        fp = int(((y_true == 0) & (y_pred == 1)).sum())
        fn = int(((y_true == 1) & (y_pred == 0)).sum())

        prec = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        spec = calculate_specificity(y_true, y_pred)
        f1 = round(2 * prec * recall / (prec + recall), 4) if (prec + recall) > 0 else 0.0

        results.append({
            "threshold": round(float(t), 2),
            "precision": prec,
            "recall": recall,
            "specificity": spec,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "is_production": abs(float(t) - production_threshold) < 1e-6,
        })

    return {
        "disclaimer": THRESHOLD_DISCLAIMER,
        "production_threshold": production_threshold,
        "results": results,
    }
