"""XGBoost model for HeartGuard.

Boosting ensemble classification model using xgboost.XGBClassifier.
Configuration derived from the HeartGuard project specification.
"""

from xgboost import XGBClassifier

from src.utils.logger import get_logger

logger = get_logger(__name__)

RANDOM_STATE: int = 42


def create_xgboost(
    n_estimators: int = 300,
    max_depth: int = 4,
    learning_rate: float = 0.05,
    subsample: float = 0.8,
    random_state: int = RANDOM_STATE,
    eval_metric: str = "logloss",
    use_label_encoder: bool = False,
) -> XGBClassifier:
    """Create a configured XGBoost model.

    Args:
        n_estimators: Number of boosting rounds (default 300).
        max_depth: Maximum tree depth (default 4).
        learning_rate: Boosting learning rate (default 0.05).
        subsample: Subsample ratio of training instances (default 0.8).
        random_state: Random seed (default 42).
        eval_metric: Evaluation metric (default 'logloss').
        use_label_encoder: Disable label encoder warning (default False).

    Returns:
        Unfitted XGBClassifier instance.
    """
    model = XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=subsample,
        random_state=random_state,
        eval_metric=eval_metric,
        use_label_encoder=use_label_encoder,
    )
    logger.info(
        "XGBoost created: n_estimators=%d, max_depth=%d, lr=%s, subsample=%s",
        n_estimators, max_depth, learning_rate, subsample,
    )
    return model
