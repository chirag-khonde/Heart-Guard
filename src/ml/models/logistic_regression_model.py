"""Logistic Regression model for HeartGuard.

Baseline clinical classification model using scikit-learn LogisticRegression.
Configuration derived from the HeartGuard project specification.
"""

from sklearn.linear_model import LogisticRegression

from src.utils.logger import get_logger

logger = get_logger(__name__)

RANDOM_STATE: int = 42


def create_logistic_regression(
    C: float = 1.0,
    solver: str = "lbfgs",
    max_iter: int = 500,
    random_state: int = RANDOM_STATE,
) -> LogisticRegression:
    """Create a configured Logistic Regression model.

    Args:
        C: Inverse of regularisation strength (default 1.0).
        solver: Optimisation algorithm (default 'lbfgs').
        max_iter: Maximum iterations (default 500).
        random_state: Random seed (default 42).

    Returns:
        Unfitted LogisticRegression instance.
    """
    model = LogisticRegression(
        C=C,
        solver=solver,
        max_iter=max_iter,
        random_state=random_state,
    )
    logger.info(
        "Logistic Regression created: C=%s, solver=%s, max_iter=%d",
        C, solver, max_iter,
    )
    return model
