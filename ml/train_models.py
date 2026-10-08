"""Centralized model training engine for HeartGuard.

Implements a unified training loop for all four models (Logistic Regression,
Random Forest, XGBoost, Neural Network) using sklearn Pipelines to ensure
zero data leakage during cross-validation.

Usage::

    from src.ml.train_models import train_all_models
    result = train_all_models()
    print(result.best_model_name)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from config.settings import MODEL_DIRECTORY, REPORT_DIRECTORY
from src.data.features import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
)
from src.data.loader import load_cleveland_dataset, normalize_cleveland_target
from src.data.pipeline import prepare_cleveland_pipeline
from src.data.preprocessing import (
    create_preprocessor,
    get_feature_names,
    save_preprocessor,
    split_dataset,
)
from src.ml.cross_validation import create_cv_strategy
from src.ml.evaluate import (
    evaluate_all_models,
    plot_confusion_matrix,
    plot_metrics_comparison,
    plot_roc_comparison,
)
from src.ml.model_registry import (
    register_model,
    save_model,
)
from src.ml.models.logistic_regression_model import create_logistic_regression
from src.ml.models.random_forest_model import create_random_forest
from src.ml.models.xgboost_model import create_xgboost
from src.ml.models.neural_network_model import (
    create_neural_network,
    train_neural_network,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

RANDOM_STATE: int = 42
N_SPLITS: int = 5


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class TrainingResult:
    """Structured result returned by the centralized training engine."""

    models: dict[str, Any] = field(default_factory=dict)
    cv_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    test_results: dict[str, dict[str, float]] = field(default_factory=dict)
    best_model_name: str = ""
    best_model: Any = None
    feature_names: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Classical model CV helpers (sklearn Pipeline approach)
# ---------------------------------------------------------------------------


def _build_pipeline(
    model: Any,
    preprocessor: ColumnTransformer,
) -> Pipeline:
    """Wrap a model and preprocessor into a single sklearn Pipeline.

    This guarantees that within each CV fold, the preprocessor is fit only
    on the training portion and applied to the validation portion.

    Args:
        model: Unfitted classifier.
        preprocessor: Unfitted ColumnTransformer.

    Returns:
        sklearn Pipeline with 'preprocessor' and 'classifier' steps.
    """
    return Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", model),
    ])


def _cross_validate_classical(
    pipeline: Pipeline,
    X: pd.DataFrame,
    y: pd.Series,
    cv: StratifiedKFold,
    model_name: str,
) -> dict[str, Any]:
    """Run stratified cross-validation on a classical sklearn Pipeline.

    Args:
        pipeline: Unfitted Pipeline (preprocessor + classifier).
        X: Raw (unpreprocessed) training features.
        y: Training labels.
        cv: StratifiedKFold splitter.
        model_name: Name for logging.

    Returns:
        Dict with mean and per-fold metric lists.
    """
    fold_scores: list[dict[str, float]] = []

    for fold_idx, (train_idx, val_idx) in enumerate(cv.split(X, y)):
        X_fold_train = X.iloc[train_idx]
        y_fold_train = y.iloc[train_idx]
        X_fold_val = X.iloc[val_idx]
        y_fold_val = y.iloc[val_idx]

        pipeline.fit(X_fold_train, y_fold_train)
        y_pred = pipeline.predict(X_fold_val)
        y_prob = pipeline.predict_proba(X_fold_val)[:, 1]

        fold_scores.append({
            "accuracy": round(float(accuracy_score(y_fold_val, y_pred)), 4),
            "precision": round(float(precision_score(y_fold_val, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_fold_val, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_fold_val, y_pred, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_fold_val, y_prob)), 4),
        })

    means: dict[str, Any] = {}
    for metric in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
        values = [f[metric] for f in fold_scores]
        means[f"{metric}_mean"] = round(float(np.mean(values)), 4)
        means[f"{metric}_std"] = round(float(np.std(values)), 4)

    means["folds"] = fold_scores
    logger.info(
        "%s CV: roc_auc=%.4f (+/- %.4f), f1=%.4f (+/- %.4f)",
        model_name, means["roc_auc_mean"], means["roc_auc_std"],
        means["f1_mean"], means["f1_std"],
    )
    return means


# ---------------------------------------------------------------------------
# Main training entry point
# ---------------------------------------------------------------------------


def train_all_models(
    save_artefacts: bool = True,
    verbose: int = 0,
) -> TrainingResult:
    """Run the full Phase 4 training pipeline for all four models.

    Steps:
        1. Run the Phase 3 Cleveland data pipeline.
        2. Cross-validate all four models with data-leakage-free Pipelines.
        3. Train the best four models on the full training set.
        4. Evaluate all trained models on the held-out test set.
        5. Select the best model by ROC-AUC (primary) / F1 (secondary).
        6. Save all models, preprocessor, visualisation, and JSON reports.
        7. Return the TrainingResult with all metadata.

    Returns:
        TrainingResult with all trained models and results.
    """
    result = TrainingResult()
    pipeline_start = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info("HeartGuard Phase 4 — Centralized Model Training")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: Run the data pipeline
    # ------------------------------------------------------------------
    logger.info("Step 1: Running Cleveland data pipeline")
    try:
        pipeline_result = prepare_cleveland_pipeline(save_artefacts=True)
    except Exception as exc:
        logger.error("Data pipeline failed: %s", exc)
        raise

    X_train_t = pipeline_result.X_train
    X_test_t = pipeline_result.X_test
    y_train = pipeline_result.y_train
    y_test = pipeline_result.y_test
    preprocessor = pipeline_result.preprocessor
    feature_names = pipeline_result.feature_names

    result.feature_names = feature_names

    logger.info(
        "Pipeline complete: train=%d rows, test=%d rows, %d features",
        len(X_train_t), len(X_test_t), len(feature_names),
    )

    # ------------------------------------------------------------------
    # Step 2: Cross-validation
    # ------------------------------------------------------------------
    logger.info("Step 2: Cross-validation for all models")
    cv = create_cv_strategy(n_splits=N_SPLITS)

    # Re-load raw data and re-split to get unprocessed features for
    # Pipeline-based CV (preprocessor is fit inside each fold).
    logger.info("Re-loading raw training data for CV (leakage-free Pipelines)")
    raw_df = load_cleveland_dataset()
    raw_df = normalize_cleveland_target(raw_df)
    X_train_raw, X_test_raw, y_train_raw, y_test_raw = split_dataset(
        raw_df, test_size=0.20, random_state=RANDOM_STATE,
    )

    assert len(X_train_raw) == len(X_train_t), (
        f"Raw train rows ({len(X_train_raw)}) != transformed train rows ({len(X_train_t)})"
    )

    # All four models use sklearn Pipelines for uniform CV
    models_to_cv = {
        "logistic_regression": create_logistic_regression(),
        "random_forest": create_random_forest(),
        "xgboost": create_xgboost(),
        "neural_network": create_neural_network(),
    }

    cv_results: dict[str, dict[str, Any]] = {}
    for name, model in models_to_cv.items():
        pipeline = _build_pipeline(model, create_preprocessor())
        cv_results[name] = _cross_validate_classical(
            pipeline, X_train_raw, y_train_raw, cv, name,
        )

    result.cv_results = cv_results

    # ------------------------------------------------------------------
    # Step 3: Select best model and train on full training set
    # ------------------------------------------------------------------
    logger.info("Step 3: Training final models on full training set")

    # Select best by CV ROC-AUC (primary), F1 (secondary)
    best_name = ""
    best_auc = -1.0
    best_f1 = -1.0
    for name, cv_data in cv_results.items():
        auc = cv_data["roc_auc_mean"]
        f1 = cv_data["f1_mean"]
        if (auc > best_auc) or (auc == best_auc and f1 > best_f1):
            best_name = name
            best_auc = auc
            best_f1 = f1
    logger.info("Best CV model: %s (AUC=%.4f, F1=%.4f)", best_name, best_auc, best_f1)

    # Train final models on full preprocessed training data
    trained_models: dict[str, Any] = {}

    lr_final = create_logistic_regression()
    lr_final.fit(X_train_t, y_train)
    trained_models["logistic_regression"] = lr_final

    rf_final = create_random_forest()
    rf_final.fit(X_train_t, y_train)
    trained_models["random_forest"] = rf_final

    xgb_final = create_xgboost()
    xgb_final.fit(X_train_t, y_train)
    trained_models["xgboost"] = xgb_final

    nn_model = create_neural_network()
    nn_history = train_neural_network(
        nn_model, X_train_t.values, y_train.values, max_iter=50,
    )
    trained_models["neural_network"] = nn_model

    result.models = trained_models
    result.best_model_name = best_name
    result.best_model = trained_models[best_name]

    # ------------------------------------------------------------------
    # Step 4: Test set evaluation
    # ------------------------------------------------------------------
    logger.info("Step 4: Evaluating all models on the test set")
    test_results = evaluate_all_models(trained_models, X_test_t, y_test)
    result.test_results = test_results

    # ------------------------------------------------------------------
    # Step 5: Save artefacts
    # ------------------------------------------------------------------
    if save_artefacts:
        logger.info("Step 5: Saving all artefacts")
        _save_training_artefacts(
            trained_models=trained_models,
            cv_results=cv_results,
            test_results=test_results,
            best_name=best_name,
            best_auc=best_auc,
            best_f1=best_f1,
            preprocessor=preprocessor,
            feature_names=feature_names,
            nn_history=nn_history,
            pipeline_metadata=pipeline_result.metadata,
            X_test_t=X_test_t,
            y_test=y_test,
        )

    elapsed = (datetime.now(timezone.utc) - pipeline_start).total_seconds()
    result.metadata = {
        "training_timestamp": pipeline_start.isoformat(),
        "training_elapsed_seconds": round(elapsed, 3),
        "n_models": len(trained_models),
        "best_model_name": best_name,
        "cv_n_splits": N_SPLITS,
        "random_state": RANDOM_STATE,
        "test_size": 0.20,
    }

    logger.info("Phase 4 training complete in %.2fs — best model: %s", elapsed, best_name)
    return result


# ---------------------------------------------------------------------------
# Artefact persistence
# ---------------------------------------------------------------------------


def _save_training_artefacts(
    trained_models: dict[str, Any],
    cv_results: dict[str, dict[str, Any]],
    test_results: dict[str, dict[str, float]],
    best_name: str,
    best_auc: float,
    best_f1: float,
    preprocessor: ColumnTransformer,
    feature_names: list[str],
    nn_history: dict[str, Any],
    pipeline_metadata: dict[str, Any],
    X_test_t: Any = None,
    y_test: Any = None,
) -> None:
    """Save all models, reports, and figures after training."""
    figures_dir = REPORT_DIRECTORY / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    training_dir = REPORT_DIRECTORY / "training"
    training_dir.mkdir(parents=True, exist_ok=True)

    # Save models
    for name, model in trained_models.items():
        save_model(model, name)

    # Save preprocessor
    save_preprocessor(preprocessor)

    # Save feature names
    feature_names_path = MODEL_DIRECTORY / "feature_names.json"
    with open(feature_names_path, "w", encoding="utf-8") as f:
        json.dump(feature_names, f, indent=2)
    logger.info("Feature names saved to %s", feature_names_path)

    # Save model_results.json (CV + test metrics + best model)
    model_results = {
        "best_model": {
            "model_name": best_name,
            "cv_roc_auc_mean": best_auc,
            "cv_f1_mean": best_f1,
        },
        "cv_results": {
            name: {k: v for k, v in data.items() if k != "folds"}
            for name, data in cv_results.items()
        },
        "test_results": test_results,
    }
    results_path = REPORT_DIRECTORY / "model_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(model_results, f, indent=2, default=str)
    logger.info("Model results saved to %s", results_path)

    # Save best_model.json
    best_model_info = {
        "model_name": best_name,
        "cv_roc_auc_mean": best_auc,
        "cv_f1_mean": best_f1,
        "test_metrics": test_results.get(best_name, {}),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    best_path = REPORT_DIRECTORY / "best_model.json"
    with open(best_path, "w", encoding="utf-8") as f:
        json.dump(best_model_info, f, indent=2)
    logger.info("Best model info saved to %s", best_path)

    # Save model_comparison.csv
    comparison_rows = []
    for name in trained_models.keys():
        row: dict[str, Any] = {"model": name}
        row.update(cv_results.get(name, {}))
        row.update({f"test_{k}": v for k, v in test_results.get(name, {}).items()})
        row.pop("folds", None)
        comparison_rows.append(row)
    comparison_df = pd.DataFrame(comparison_rows).set_index("model")
    comparison_path = REPORT_DIRECTORY / "model_comparison.csv"
    comparison_df.to_csv(comparison_path, float_format="%.4f")
    logger.info("Model comparison CSV saved to %s", comparison_path)

    # Save training_summary.json
    training_summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models_trained": list(trained_models.keys()),
        "best_model_name": best_name,
        "cv_results_summary": {
            name: {
                "roc_auc_mean": cv_results[name]["roc_auc_mean"],
                "roc_auc_std": cv_results[name]["roc_auc_std"],
                "f1_mean": cv_results[name]["f1_mean"],
                "f1_std": cv_results[name]["f1_std"],
            }
            for name in trained_models.keys()
        },
        "test_results_summary": {
            name: test_results[name] for name in trained_models.keys()
        },
        "feature_names": feature_names,
        "pipeline_metadata": pipeline_metadata,
    }
    summary_path = training_dir / "training_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(training_summary, f, indent=2, default=str)
    logger.info("Training summary saved to %s", summary_path)

    # Save neural network training history
    nn_history_data = {
        "model_name": "neural_network",
        "epochs": nn_history.get("n_iter", 0),
        "final_loss": nn_history.get("final_loss"),
        "loss_curve": nn_history.get("loss_curve", []),
    }
    nn_history_path = training_dir / "neural_network_history.json"
    with open(nn_history_path, "w", encoding="utf-8") as f:
        json.dump(nn_history_data, f, indent=2)
    logger.info("Neural network history saved to %s", nn_history_path)

    # Save model metadata
    for name, model in trained_models.items():
        meta = {
            "model_type": name,
            "feature_names": feature_names,
            "training_timestamp": datetime.now(timezone.utc).isoformat(),
            "cv_roc_auc_mean": cv_results[name]["roc_auc_mean"],
            "cv_f1_mean": cv_results[name]["f1_mean"],
            "test_metrics": test_results.get(name, {}),
        }
        register_model(name, meta)

    # Generate visualisations
    logger.info("Generating confusion matrices...")
    if X_test_t is not None and y_test is not None:
        for name, model in trained_models.items():
            y_pred = model.predict(X_test_t)
            plot_confusion_matrix(
                y_test.values if hasattr(y_test, "values") else y_test,
                y_pred, name, figures_dir,
            )

        logger.info("Generating ROC comparison...")
        plot_roc_comparison(trained_models, X_test_t, y_test, figures_dir)
        plot_metrics_comparison(test_results, figures_dir)

    # Neural network training curves
    _plot_nn_training_curves(nn_history, figures_dir)

    # Feature importance for tree-based models
    _plot_feature_importance(trained_models, feature_names, figures_dir)

    logger.info("All artefacts saved successfully")


def _plot_nn_training_curves(history: dict[str, Any], output_dir: Path) -> Path:
    """Plot and save neural network training loss curve."""
    loss_curve = history.get("loss_curve", [])
    if not loss_curve:
        logger.warning("No loss curve data for NN training curves plot")
        return output_dir / "neural_network_training_curves.png"

    fig, ax = plt.subplots(figsize=(8, 4))
    epochs = range(1, len(loss_curve) + 1)
    ax.plot(epochs, loss_curve, color="#3498db", linewidth=2, label="Training Loss")
    ax.set_title("Neural Network — Training Loss")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.legend()
    fig.tight_layout()
    path = output_dir / "neural_network_training_curves.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("NN training curves saved to %s", path)
    return path


def _plot_feature_importance(
    trained_models: dict[str, Any],
    feature_names: list[str],
    output_dir: Path,
) -> Path | None:
    """Plot feature importance for Random Forest and XGBoost."""
    importance_data: dict[str, np.ndarray] = {}
    if "random_forest" in trained_models:
        importance_data["Random Forest"] = trained_models["random_forest"].feature_importances_
    if "xgboost" in trained_models:
        importance_data["XGBoost"] = trained_models["xgboost"].feature_importances_

    if not importance_data:
        return None

    fig, axes = plt.subplots(1, len(importance_data), figsize=(8 * len(importance_data), 6))
    if len(importance_data) == 1:
        axes = [axes]

    colors = ["#3498db", "#2ecc71", "#e74c3c", "#9b59b6", "#f39c12",
              "#1abc9c", "#e67e22", "#34495e", "#d35400", "#27ae60"]

    for ax, (name, importances) in zip(axes, importance_data.items()):
        sorted_idx = np.argsort(importances)[::-1][:10]
        top_names = [feature_names[i] for i in sorted_idx]
        top_vals = importances[sorted_idx]

        ax.barh(range(len(top_names)), top_vals, color=colors[:len(top_names)], edgecolor="black")
        ax.set_yticks(range(len(top_names)))
        ax.set_yticklabels(top_names)
        ax.set_title(f"{name} — Top 10 Features")
        ax.set_xlabel("Importance")
        ax.invert_yaxis()

    fig.tight_layout()
    path = output_dir / "feature_importance.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Feature importance saved to %s", path)
    return path
