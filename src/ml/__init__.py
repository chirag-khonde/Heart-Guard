"""HeartGuard machine learning module."""

from src.ml.cross_validation import create_cv_strategy, get_cv_splits
from src.ml.evaluate import (
    evaluate_all_models,
    evaluate_model,
    calculate_classification_metrics,
    calculate_roc_auc,
    compare_models,
    plot_confusion_matrix,
    plot_metrics_comparison,
    plot_roc_comparison,
)
from src.ml.model_registry import (
    save_model,
    load_model,
    get_available_models,
    get_best_model_name,
    register_model,
    get_model_path,
)
from src.ml.predict import (
    predict_batch,
    predict_probability,
    predict_with_model,
)
from src.ml.train_models import train_all_models
