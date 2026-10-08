"""Model comparison for HeartGuard evaluation (Phase 14).

Compares metrics across multiple model evaluation runs.
Production vs experimental models are clearly labeled.

IMPORTANT: A model should NOT be selected solely because it has the highest
accuracy. For imbalanced classification tasks, consider Recall, Precision,
F1, Specificity, ROC-AUC, and PR-AUC in context of the project's objectives.
"""

from __future__ import annotations

import pandas as pd

MODEL_COMPARISON_DISCLAIMER = (
    "Model comparison is based on evaluation dataset metrics only. Higher accuracy alone "
    "does not indicate a superior model — especially for imbalanced datasets. "
    "Consider Recall, Precision, F1, Specificity, ROC-AUC, and PR-AUC together. "
    "No model is promoted to production automatically."
)


def compare_model_evaluations(
    eval_results: list[dict],
    production_model_name: str | None = None,
) -> dict[str, object]:
    """Build a comparison table from multiple model evaluation result dicts.

    Args:
        eval_results: List of evaluation result dicts, each with 'model_name' and 'metrics'.
        production_model_name: Name of the current production model (for labeling).

    Returns:
        Dict with comparison DataFrame (as records) and disclaimer.
    """
    rows = []
    metric_keys = ["accuracy", "precision", "recall", "f1", "specificity",
                   "balanced_accuracy", "roc_auc", "pr_auc"]

    for result in eval_results:
        model_name = result.get("model_name", "Unknown")
        metrics = result.get("metrics", {})
        is_prod = (model_name == production_model_name)

        row = {
            "model_name": model_name,
            "model_status": "PRODUCTION" if is_prod else "EXPERIMENTAL",
        }
        for key in metric_keys:
            row[key] = metrics.get(key, "N/A")
        rows.append(row)

    return {
        "comparison_rows": rows,
        "production_model": production_model_name,
        "disclaimer": MODEL_COMPARISON_DISCLAIMER,
        "metric_keys": metric_keys,
    }


def get_best_model_by_metric(
    comparison_data: dict,
    metric: str = "roc_auc",
) -> str | None:
    """Identify the best-performing model by a given metric (informational only).

    Args:
        comparison_data: Result from :func:`compare_model_evaluations`.
        metric: Metric name to compare.

    Returns:
        Model name with the highest metric value, or None if unavailable.

    Note:
        This is informational only. No automatic production promotion occurs.
    """
    rows = comparison_data.get("comparison_rows", [])
    best_name = None
    best_val = -1.0
    for row in rows:
        val = row.get(metric, None)
        if isinstance(val, float) and val > best_val:
            best_val = val
            best_name = row["model_name"]
    return best_name
