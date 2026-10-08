"""Generate global SHAP explainability reports and visualizations for HeartGuard."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.explainability.service import SHAPExplainerService
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Compute and save global SHAP importance artifacts."""
    print("=" * 60)
    print("HeartGuard - Generating SHAP Explainability Reports")
    print("=" * 60)

    service = SHAPExplainerService()
    print(f"Loaded Model: {service.model_name}")
    print(f"Explainer Type: {service.explainer_type}")
    print(f"Features: {len(service.feature_names)}")

    print("\nComputing global SHAP feature importance...")
    global_df = service.global_importance(save_artifacts=True)

    print("\nTop 10 Global Features by Mean |SHAP|:")
    print("-" * 50)
    for idx, row in global_df.head(10).iterrows():
        print(f"  {row['rank']:2d}. {row['clinical_label']:<28} {row['mean_absolute_shap']:.4f}")

    print("\nExplainability artifacts saved to:")
    print("  - reports/explainability/shap_global_importance.csv")
    print("  - reports/explainability/explainer_metadata.json")
    print("  - reports/figures/shap_global_importance.png")
    print("  - reports/figures/shap_summary.png")
    print("\nSHAP generation completed successfully!")


if __name__ == "__main__":
    main()
