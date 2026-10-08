"""Random Forest model for HeartGuard.

Bagging ensemble classification model using scikit-learn RandomForestClassifier.
Configuration derived from the HeartGuard project specification.
"""

from sklearn.ensemble import RandomForestClassifier

from src.utils.logger import get_logger

logger = get_logger(__name__)

RANDOM_STATE: int = 42


def create_random_forest(
    n_estimators: int = 200,
    max_depth: int = 8,
    min_samples_split: int = 5,
    random_state: int = RANDOM_STATE,
    n_jobs: int = -1,
) -> RandomForestClassifier:
    """Create a configured Random Forest model.

    Args:
        n_estimators: Number of trees (default 200).
        max_depth: Maximum tree depth (default 8).
        min_samples_split: Minimum samples to split a node (default 5).
        random_state: Random seed (default 42).
        n_jobs: Parallel jobs (default -1, all cores).

    Returns:
        Unfitted RandomForestClassifier instance.
    """
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        random_state=random_state,
        n_jobs=n_jobs,
    )
    logger.info(
        "Random Forest created: n_estimators=%d, max_depth=%d, min_samples_split=%d",
        n_estimators, max_depth, min_samples_split,
    )
    return model
