"""Extended cross-validation for HeartGuard model evaluation (Phase 14).

Wraps the existing StratifiedKFold strategy with extended metrics including
specificity, balanced accuracy, and PR-AUC per fold.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from config.settings import EVALUATION_CV_FOLDS, EVALUATION_RANDOM_STATE
from src.evaluation.classification_metrics import (
    calculate_brier_score,
    calculate_pr_metrics,
    calculate_specificity,
)
from src.ml.cross_validation import create_cv_strategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_stratified_cv(
    pipeline: Pipeline | Any,
    X: pd.DataFrame | np.ndarray,
    y: pd.Series | np.ndarray,
    n_splits: int = EVALUATION_CV_FOLDS,
    random_state: int = EVALUATION_RANDOM_STATE,
) -> dict[str, Any]:
    """Run stratified k-fold cross-validation with extended classification metrics.

    Uses the same StratifiedKFold strategy as model training to ensure
    consistency. Preprocessing is done inside the pipeline per fold.

    Args:
        pipeline: Fitted or unfitted sklearn Pipeline (or compatible estimator).
        X: Raw feature DataFrame or array.
        y: Target series or array.
        n_splits: Number of folds (default: 5 per config).
        random_state: Random seed (default: 42 per config).

    Returns:
        Dict with per-metric mean/std and per-fold scores.
    """
    from sklearn.metrics import (
        accuracy_score, f1_score, precision_score, recall_score,
        roc_auc_score, balanced_accuracy_score,
    )

    cv = create_cv_strategy(n_splits=n_splits, random_state=random_state)
    fold_scores: list[dict[str, float]] = []

    X = pd.DataFrame(X) if not isinstance(X, (pd.DataFrame, np.ndarray)) else X
    y = np.asarray(y)

    # Deep-clone pipeline for CV to avoid fitting on full data
    import copy

    for fold_idx, (train_idx, val_idx) in enumerate(cv.split(X, y)):
        X_tr = X.iloc[train_idx] if isinstance(X, pd.DataFrame) else X[train_idx]
        y_tr = y[train_idx]
        X_val = X.iloc[val_idx] if isinstance(X, pd.DataFrame) else X[val_idx]
        y_val = y[val_idx]

        fold_pipeline = copy.deepcopy(pipeline)
        fold_pipeline.fit(X_tr, y_tr)

        y_pred = fold_pipeline.predict(X_val)
        y_prob = None
        if hasattr(fold_pipeline, "predict_proba"):
            y_prob = fold_pipeline.predict_proba(X_val)[:, 1]

        scores: dict[str, float] = {
            "accuracy": round(float(accuracy_score(y_val, y_pred)), 4),
            "precision": round(float(precision_score(y_val, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_val, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_val, y_pred, zero_division=0)), 4),
            "specificity": calculate_specificity(y_val, y_pred),
            "balanced_accuracy": round(float(balanced_accuracy_score(y_val, y_pred)), 4),
        }

        if y_prob is not None:
            try:
                scores["roc_auc"] = round(float(roc_auc_score(y_val, y_prob)), 4)
            except ValueError:
                scores["roc_auc"] = 0.0
            try:
                pr = calculate_pr_metrics(y_val, y_prob)
                scores["pr_auc"] = pr["pr_auc"]
            except ValueError:
                scores["pr_auc"] = 0.0
            scores["brier_score"] = calculate_brier_score(y_val, y_prob)

        fold_scores.append(scores)
        logger.info("Fold %d/%d complete: F1=%.4f", fold_idx + 1, n_splits, scores["f1"])

    # Aggregate
    metric_keys = list(fold_scores[0].keys())
    aggregated: dict[str, Any] = {
        "n_splits": n_splits,
        "random_state": random_state,
        "folds": fold_scores,
    }
    for metric in metric_keys:
        values = [f[metric] for f in fold_scores if metric in f]
        aggregated[f"{metric}_mean"] = round(float(np.mean(values)), 4)
        aggregated[f"{metric}_std"] = round(float(np.std(values)), 4)

    return aggregated
