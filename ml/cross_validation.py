"""Cross-validation utilities for HeartGuard.

Provides a reusable five-fold stratified cross-validation strategy
that Phase 4 model training will consume.  No model training occurs
in this module -- only the CV splitter is created.
"""

from __future__ import annotations

from typing import Iterator

import numpy as np
from sklearn.model_selection import StratifiedKFold

from src.utils.logger import get_logger

logger = get_logger(__name__)

RANDOM_STATE: int = 42
N_SPLITS: int = 5


def create_cv_strategy(
    n_splits: int = N_SPLITS,
    shuffle: bool = True,
    random_state: int = RANDOM_STATE,
) -> StratifiedKFold:
    """Create a stratified k-fold cross-validation splitter.

    The splitter preserves class proportions in each fold, which is
    critical for the potentially imbalanced Cleveland dataset.

    Args:
        number of folds (default 5).
        shuffle: Whether to shuffle before splitting (default True).
        random_state: Random seed for reproducibility (default 42).

    Returns:
        Configured :class:`StratifiedKFold` instance.
    """
    cv = StratifiedKFold(
        n_splits=n_splits,
        shuffle=shuffle,
        random_state=random_state,
    )
    logger.info(
        "CV strategy created: StratifiedKFold(n_splits=%d, shuffle=%s, random_state=%d)",
        n_splits, shuffle, random_state,
    )
    return cv


def get_cv_splits(
    cv: StratifiedKFold,
    X: np.ndarray | list,
    y: np.ndarray | list,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Materialise the cross-validation splits as lists of index arrays.

    Useful when callers need to iterate over folds explicitly.

    Args:
        cv: A configured :class:`StratifiedKFold` instance.
        X: Feature matrix (used only for length).
        y: Target vector.

    Returns:
        List of (train_indices, validation_indices) tuples.
    """
    splits = list(cv.split(X, y))
    logger.info("Generated %d CV splits", len(splits))
    for i, (train_idx, val_idx) in enumerate(splits):
        logger.info("  Fold %d: train=%d, val=%d", i + 1, len(train_idx), len(val_idx))
    return splits
