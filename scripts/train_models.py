"""HeartGuard model training CLI script.

Runs the centralized training engine and saves all artefacts.
No arguments required — uses default configuration.

Usage::

    python scripts/train_models.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    """Entry point for the training CLI."""
    try:
        from src.ml.train_models import train_all_models
        from src.utils.logger import get_logger

        logger = get_logger("train_models")
        logger.info("HeartGuard training CLI started")
        logger.info("Project root: %s", PROJECT_ROOT)

        result = train_all_models(save_artefacts=True, verbose=0)

        logger.info("=" * 60)
        logger.info("Training complete!")
        logger.info("Best model: %s", result.best_model_name)
        logger.info("=" * 60)

        # Print summary table
        print("\n" + "=" * 60)
        print("HeartGuard Model Training Summary")
        print("=" * 60)
        print(f"Best model: {result.best_model_name}")
        print(f"Models trained: {list(result.models.keys())}")
        print("\nCV ROC-AUC (mean +/- std):")
        for name, cv in result.cv_results.items():
            print(f"  {name:25s}: {cv['roc_auc_mean']:.4f} +/- {cv['roc_auc_std']:.4f}")
        print("\nTest Metrics:")
        for name, metrics in result.test_results.items():
            print(f"  {name:25s}: acc={metrics['accuracy']:.4f}, f1={metrics['f1']:.4f}, auc={metrics['roc_auc']:.4f}")
        print("=" * 60)

        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
