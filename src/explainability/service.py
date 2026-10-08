"""SHAP Explainer Service for HeartGuard.

Reusable service class that wraps the SHAP explainability functions
into a clean, high-level API for the Streamlit UI and testing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from config.settings import MODEL_DIRECTORY, PROCESSED_DATA_DIRECTORY, REPORT_DIRECTORY
from src.explainability.shap_explainer import (
    CLINICAL_LABELS,
    calculate_shap_values,
    create_global_importance_plot,
    create_local_importance_plot,
    create_shap_explainer,
    create_summary_plot,
    create_waterfall_plot,
    generate_human_readable_summary,
    get_feature_contributions,
    get_global_feature_importance,
    get_local_explanation,
    get_top_features,
    get_top_risk_factors,
    load_explainable_model,
    load_feature_names,
    load_training_data,
    save_explainer_metadata,
    save_explainability_summary,
    save_global_importance_csv,
    save_local_explanation_json,
)
from src.data.preprocessing import load_preprocessor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SHAPExplainerService:
    """High-level SHAP explanation service for HeartGuard.

    Usage::

        service = SHAPExplainerService()
        result = service.explain_patient(patient_data)
        global_imp = service.global_importance()
    """

    def __init__(self) -> None:
        """Initialise the service by loading model, preprocessor, and explainer."""
        self._model: Any = None
        self._model_name: str = ""
        self._explainer: Any = None
        self._explainer_type: str = ""
        self._feature_names: list[str] = []
        self._training_data: pd.DataFrame | None = None
        self._global_shap_values: np.ndarray | None = None
        self._global_importance: pd.DataFrame | None = None
        self._loaded: bool = False

    def _ensure_loaded(self) -> None:
        """Lazy-load model, explainer, and feature names on first use."""
        if self._loaded:
            return

        self._model, self._model_name = load_explainable_model()
        self._feature_names = load_feature_names()
        self._training_data = load_training_data()
        self._explainer, self._explainer_type = create_shap_explainer(
            self._model, self._training_data,
        )

        # Save explainer metadata
        save_explainer_metadata(
            model_name=self._model_name,
            explainer_type=self._explainer_type,
            feature_names=self._feature_names,
            background_source="cleveland_train.csv (242 samples)",
        )

        self._loaded = True
        logger.info(
            "SHAPExplainerService loaded: model=%s, explainer=%s, features=%d",
            self._model_name, self._explainer_type, len(self._feature_names),
        )

    @property
    def model_name(self) -> str:
        """Name of the loaded model."""
        self._ensure_loaded()
        return self._model_name

    @property
    def explainer_type(self) -> str:
        """Type of SHAP explainer in use."""
        self._ensure_loaded()
        return self._explainer_type

    @property
    def feature_names(self) -> list[str]:
        """Feature names used by the model."""
        self._ensure_loaded()
        return list(self._feature_names)

    def _preprocess_input(self, X_row: pd.DataFrame) -> pd.DataFrame:
        """Preprocess raw patient input and align to expected model features."""
        preprocessor = load_preprocessor(MODEL_DIRECTORY / "preprocessor.pkl")
        raw_transformed = preprocessor.transform(X_row)
        if hasattr(preprocessor, "get_feature_names_out"):
            p_cols = list(preprocessor.get_feature_names_out())
        else:
            p_cols = self._feature_names[: raw_transformed.shape[1]]

        X_df = pd.DataFrame(raw_transformed, columns=p_cols, index=X_row.index)
        for col in self._feature_names:
            if col not in X_df.columns:
                X_df[col] = 0.0
        return X_df[self._feature_names]

    def explain_patient(
        self,
        patient_data: dict[str, Any] | pd.DataFrame,
        save_artifacts: bool = True,
    ) -> dict[str, Any]:
        """Generate a full explanation for a single patient.

        Args:
            patient_data: Dict or single-row DataFrame with canonical features.
            save_artifacts: Whether to save plots and JSON to reports/.

        Returns:
            Structured explanation with prediction, SHAP values, and plots.
        """
        self._ensure_loaded()

        # Normalise input to DataFrame
        if isinstance(patient_data, dict):
            X_row = pd.DataFrame([patient_data])
        else:
            X_row = patient_data.copy()

        # Preprocess and align to model's feature set
        X_transformed = self._preprocess_input(X_row)

        # Predict
        prediction = int(self._model.predict(X_transformed)[0])
        probability = None
        if hasattr(self._model, "predict_proba"):
            proba = self._model.predict_proba(X_transformed)
            probability = float(proba[0, 1])

        # Calculate SHAP values
        shap_vals, base_values = calculate_shap_values(
            self._explainer, X_transformed,
        )
        shap_row = shap_vals[0]
        base_val = float(base_values[0])

        # Build contributions
        contributions = get_feature_contributions(shap_row, self._feature_names)

        # Build local explanation
        explanation = get_local_explanation(
            shap_values_row=shap_row,
            base_value=base_val,
            feature_names=self._feature_names,
            X_row=X_transformed,
            prediction=prediction,
            probability=probability,
        )

        # Human-readable summary
        summary = generate_human_readable_summary(
            contributions=contributions,
            patient_values=X_row.iloc[0] if len(X_row) > 0 else None,
            prediction=prediction,
            probability=probability,
        )
        explanation["human_readable_summary"] = summary

        # Top risk factors
        top_risk = get_top_risk_factors(shap_row, self._feature_names, top_n=3)
        explanation["top_risk_factors"] = top_risk.to_dict("records")

        # Save artifacts if requested
        if save_artifacts:
            figures_dir = REPORT_DIRECTORY / "figures"

            # Waterfall plot
            waterfall_path = create_waterfall_plot(
                shap_row, base_val, self._feature_names, X_transformed,
                output_dir=figures_dir,
                filename="shap_waterfall.png",
            )
            explanation["waterfall_plot"] = str(waterfall_path)

            # Local importance plot
            local_path = create_local_importance_plot(
                contributions, output_dir=figures_dir,
                filename="shap_local_importance.png",
            )
            explanation["local_importance_plot"] = str(local_path)

            # Save local explanation JSON
            save_local_explanation_json(explanation)

        logger.info(
            "Patient explained: prediction=%d, probability=%.4f",
            prediction, probability or 0.0,
        )
        return explanation

    def global_importance(
        self,
        save_artifacts: bool = True,
    ) -> pd.DataFrame:
        """Compute global feature importance across the training dataset.

        Args:
            save_artifacts: Whether to save plots and CSV to reports/.

        Returns:
            DataFrame with feature, mean_absolute_shap, rank.
        """
        self._ensure_loaded()

        if self._global_importance is not None and not save_artifacts:
            return self._global_importance

        # Compute SHAP values for the full training data
        logger.info("Computing global SHAP values on training data...")
        shap_vals, _ = calculate_shap_values(
            self._explainer, self._training_data,
        )
        self._global_shap_values = shap_vals

        # Compute global importance
        self._global_importance = get_global_feature_importance(
            shap_vals, self._feature_names,
        )

        if save_artifacts:
            figures_dir = REPORT_DIRECTORY / "figures"

            # Save CSV
            save_global_importance_csv(self._global_importance)

            # Save global importance plot
            create_global_importance_plot(
                self._global_importance,
                output_dir=figures_dir,
                filename="shap_global_importance.png",
            )

            # Save summary plot
            create_summary_plot(
                shap_vals,
                self._feature_names,
                X=self._training_data,
                output_dir=figures_dir,
                filename="shap_summary.png",
            )

        logger.info("Global importance computed for %d features", len(self._feature_names))
        return self._global_importance

    def get_top_risk_factors(
        self,
        patient_data: dict[str, Any] | pd.DataFrame,
        top_n: int = 3,
    ) -> pd.DataFrame:
        """Get top risk factors for a patient without full explanation.

        Args:
            patient_data: Patient features.
            top_n: Number of risk factors.

        Returns:
            DataFrame of top positive contributors.
        """
        self._ensure_loaded()

        if isinstance(patient_data, dict):
            X_row = pd.DataFrame([patient_data])
        else:
            X_row = patient_data.copy()

        X_transformed = self._preprocess_input(X_row)
        shap_vals, _ = calculate_shap_values(self._explainer, X_transformed)
        return get_top_risk_factors(shap_vals[0], self._feature_names, top_n=top_n)
