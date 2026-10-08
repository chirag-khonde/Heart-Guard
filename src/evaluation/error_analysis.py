"""Error analysis for HeartGuard model evaluation (Phase 14).

Provides aggregate FP/FN analysis. Uses anonymized sample indices only.
No patient names, emails, account IDs, or personal information are included.
"""

from __future__ import annotations

import numpy as np


def analyse_errors(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    sample_ids: list[int] | np.ndarray | None = None,
) -> dict[str, object]:
    """Analyse false positives and false negatives in aggregate.

    Identifies the indices of FP and FN samples using anonymized integer IDs only.
    No patient identity information is included in the output.

    Args:
        y_true: Ground-truth binary labels.
        y_pred: Predicted binary labels.
        sample_ids: Optional list of integer sample indices. Defaults to 0..N-1.

    Returns:
        Dict with FP/FN counts, rates, and anonymized sample index lists.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    n = len(y_true)

    if sample_ids is None:
        sample_ids = list(range(n))

    sample_ids = np.asarray(sample_ids)

    tp_mask = (y_true == 1) & (y_pred == 1)
    tn_mask = (y_true == 0) & (y_pred == 0)
    fp_mask = (y_true == 0) & (y_pred == 1)
    fn_mask = (y_true == 1) & (y_pred == 0)

    tp_count = int(tp_mask.sum())
    tn_count = int(tn_mask.sum())
    fp_count = int(fp_mask.sum())
    fn_count = int(fn_mask.sum())

    fp_rate = round(fp_count / (fp_count + tn_count), 4) if (fp_count + tn_count) > 0 else 0.0
    fn_rate = round(fn_count / (fn_count + tp_count), 4) if (fn_count + tp_count) > 0 else 0.0

    fp_indices = sample_ids[fp_mask].tolist()[:20]  # cap at 20 for display
    fn_indices = sample_ids[fn_mask].tolist()[:20]

    return {
        "total_samples": n,
        "tp": tp_count,
        "tn": tn_count,
        "fp": fp_count,
        "fn": fn_count,
        "fp_rate": fp_rate,
        "fn_rate": fn_rate,
        "fp_sample_indices": fp_indices,
        "fn_sample_indices": fn_indices,
        "note": (
            "Sample indices are zero-based integer positions in the evaluation dataset. "
            "No patient personal information is included."
        ),
        "fn_disclaimer": (
            "False negatives represent instances where the model predicted absence of the "
            "positive class but the true label was positive. This does NOT directly imply "
            "missed real-world disease cases unless the dataset is clinically validated."
        ),
        "fp_disclaimer": (
            "False positives are instances where the model predicted presence of the positive "
            "class but the true label was absent. FP and FN rates are properties of this "
            "evaluation dataset and this model configuration."
        ),
    }
