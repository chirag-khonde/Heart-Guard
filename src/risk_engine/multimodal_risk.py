"""Multimodal Risk Assessment Engine for HeartGuard (Phase 7).

Integrates clinical machine learning predictions (70%) and lifestyle NLP
risk scoring (30%) into a unified, explainable cardiovascular risk assessment.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from config.settings import MODEL_DIRECTORY, REPORT_DIRECTORY
from src.data.features import HEARTGUARD_FEATURES
from src.data.preprocessing import load_preprocessor
from src.ml.model_registry import load_model
from src.nlp.explanation import DISCLAIMER_TEXT as LIFESTYLE_DISCLAIMER
from src.nlp.lifestyle_analyzer import LifestyleAnalyzer
from src.risk_engine.risk_categories import (
    CLINICAL_WEIGHT,
    LIFESTYLE_WEIGHT,
    get_alert_level,
    get_overall_risk_category,
    get_recommended_action,
)
from src.risk_engine.risk_explanation import (
    DISCLAIMER_TEXT,
    generate_overall_explanation,
)
from src.risk_engine.risk_validation import (
    validate_clinical_input,
    validate_clinical_risk,
    validate_lifestyle_input,
    validate_lifestyle_risk,
    validate_overall_risk,
    validate_weights,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_multimodal_risk(
    clinical_risk: float,
    lifestyle_risk: float,
    clinical_weight: float = CLINICAL_WEIGHT,
    lifestyle_weight: float = LIFESTYLE_WEIGHT,
) -> float:
    """Calculate the 70/30 weighted multimodal cardiovascular risk percentage.

    Formula:
        Overall Risk = (Clinical Risk * 0.70) + (Lifestyle Risk * 0.30)

    Args:
        clinical_risk: Clinical model risk percentage (0 - 100).
        lifestyle_risk: Lifestyle risk score (0 - 100).
        clinical_weight: Clinical weight fraction (default: 0.70).
        lifestyle_weight: Lifestyle weight fraction (default: 0.30).

    Returns:
        float: Bounded overall risk percentage between 0 and 100.
    """
    validate_weights(clinical_weight, lifestyle_weight)
    c_risk = validate_clinical_risk(clinical_risk)
    l_risk = validate_lifestyle_risk(lifestyle_risk)

    overall = (c_risk * clinical_weight) + (l_risk * lifestyle_weight)
    return validate_overall_risk(overall)


class MultimodalRiskEngine:
    """Unified Multimodal Risk Engine combining Clinical ML and Lifestyle NLP."""

    def __init__(self, model_name: str | None = None) -> None:
        """Initialise the Multimodal Risk Engine.

        Args:
            model_name: Optional model name to override the best model.
        """
        self._model_name = model_name or self._resolve_best_model_name()
        self._model: Any = None
        self._preprocessor: Any = None
        self._feature_names: list[str] = []
        self._lifestyle_analyzer: LifestyleAnalyzer | None = None
        self._shap_service: Any = None
        self._loaded: bool = False

    def _resolve_best_model_name(self) -> str:
        """Dynamically resolve the best clinical model from report artifacts."""
        best_report = REPORT_DIRECTORY / "best_model.json"
        if best_report.exists():
            try:
                with open(best_report, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("model_name", "logistic_regression")
            except Exception as exc:
                logger.warning("Could not read best_model.json (%s), falling back to logistic_regression", exc)
        return "logistic_regression"

    def _ensure_loaded(self) -> None:
        """Lazy-load clinical model, preprocessor, feature names, and services."""
        if self._loaded:
            return

        # Load clinical model
        self._model = load_model(self._model_name)

        # Load fitted preprocessor
        prep_path = MODEL_DIRECTORY / "preprocessor.pkl"
        if not prep_path.exists():
            raise FileNotFoundError(f"Preprocessor artifact not found at {prep_path}")
        self._preprocessor = load_preprocessor(prep_path)

        # Load expected model feature names
        fn_path = MODEL_DIRECTORY / "feature_names.json"
        if fn_path.exists():
            with open(fn_path, "r", encoding="utf-8") as f:
                self._feature_names = json.load(f)
        else:
            self._feature_names = list(HEARTGUARD_FEATURES)

        # Initialize LifestyleAnalyzer
        self._lifestyle_analyzer = LifestyleAnalyzer()

        self._loaded = True
        logger.info(
            "MultimodalRiskEngine loaded: model=%s, features=%d",
            self._model_name,
            len(self._feature_names),
        )

    @property
    def model_name(self) -> str:
        """Canonical name of the active clinical model."""
        return self._model_name

    def _preprocess_clinical_data(self, clinical_dict: dict[str, Any]) -> pd.DataFrame:
        """Transform canonical clinical features into aligned model feature space."""
        df_row = pd.DataFrame([clinical_dict])

        # Apply scikit-learn preprocessor pipeline
        raw_transformed = self._preprocessor.transform(df_row)

        if hasattr(self._preprocessor, "get_feature_names_out"):
            p_cols = list(self._preprocessor.get_feature_names_out())
        else:
            p_cols = self._feature_names[: raw_transformed.shape[1]]

        X_df = pd.DataFrame(raw_transformed, columns=p_cols, index=df_row.index)

        # Ensure all expected model columns are present (fill missing dummy cols with 0)
        for col in self._feature_names:
            if col not in X_df.columns:
                X_df[col] = 0.0

        return X_df[self._feature_names]

    def assess(
        self,
        clinical_data: dict[str, Any] | pd.DataFrame,
        lifestyle_text: str,
        include_shap: bool = True,
    ) -> dict[str, Any]:
        """Perform a complete multimodal cardiovascular risk assessment.

        Args:
            clinical_data: Dictionary or single-row DataFrame of clinical metrics.
            lifestyle_text: Free-text narrative describing daily habits.
            include_shap: Whether to incorporate SHAP clinical explanations.

        Returns:
            dict[str, Any]: Structured, JSON-serializable assessment result.
        """
        logger.info("Multimodal assessment started using model '%s'", self._model_name)

        # 1. Validate inputs
        validated_clinical = validate_clinical_input(clinical_data)
        validated_lifestyle = validate_lifestyle_input(lifestyle_text)

        self._ensure_loaded()

        # 2. Run Clinical ML Model
        X_transformed = self._preprocess_clinical_data(validated_clinical)
        y_pred = int(self._model.predict(X_transformed)[0])

        if hasattr(self._model, "predict_proba"):
            proba_arr = self._model.predict_proba(X_transformed)
            clinical_probability = float(proba_arr[0, 1])
        else:
            clinical_probability = 1.0 if y_pred == 1 else 0.0

        # Clinical Risk: 0 - 100%
        clinical_risk = clinical_probability * 100.0
        clinical_risk = validate_clinical_risk(clinical_risk)

        # 3. Run Lifestyle NLP Analyzer
        assert self._lifestyle_analyzer is not None
        lifestyle_result = self._lifestyle_analyzer.analyze(validated_lifestyle)
        lifestyle_risk = float(lifestyle_result.get("lifestyle_score", 0.0))
        lifestyle_risk = validate_lifestyle_risk(lifestyle_risk)

        # 4. Calculate 70/30 Multimodal Risk
        clinical_contrib = clinical_risk * CLINICAL_WEIGHT
        lifestyle_contrib = lifestyle_risk * LIFESTYLE_WEIGHT
        overall_risk = calculate_multimodal_risk(clinical_risk, lifestyle_risk)

        # 5. Determine Qualitative Categories and Guidance
        category = get_overall_risk_category(overall_risk)
        recommended_action = get_recommended_action(overall_risk)
        alert_level = get_alert_level(overall_risk)

        # 6. Clinical SHAP Explanation (Optional)
        clinical_explanation: dict[str, Any] | None = None
        clinical_explanation_available = False

        if include_shap:
            try:
                from src.explainability.service import SHAPExplainerService

                if self._shap_service is None:
                    self._shap_service = SHAPExplainerService()

                # Generate explanation for the patient
                exp_result = self._shap_service.explain_patient(
                    validated_clinical, save_artifacts=False
                )
                clinical_explanation = {
                    "base_value": float(exp_result.get("base_value", 0.0)),
                    "top_features": exp_result.get("features", [])[:5],
                    "top_risk_factors": exp_result.get("top_risk_factors", []),
                    "human_readable_summary": exp_result.get("human_readable_summary", ""),
                    "waterfall_plot": exp_result.get("waterfall_plot"),
                }
                clinical_explanation_available = True
            except Exception as exc:
                logger.warning("SHAP explanation generation failed (%s); proceeding without SHAP", exc)
                clinical_explanation_available = False

        # 7. Assemble Structured Result
        result: dict[str, Any] = {
            "clinical": {
                "risk": round(clinical_risk, 2),
                "probability": round(clinical_probability, 4),
                "prediction": y_pred,
                "model": self._model_name,
                "clinical_data": validated_clinical,
            },
            "lifestyle": {
                "risk": round(lifestyle_risk, 2),
                "category": lifestyle_result.get("risk_category", "LOW"),
                "detected_factors": lifestyle_result.get("detected_risk_factors", []),
                "top_risk_factors": lifestyle_result.get("top_risk_factors", []),
                "total_factors": lifestyle_result.get("total_detected_factors", 0),
                "summary": lifestyle_result.get("summary", ""),
            },
            "weights": {
                "clinical": CLINICAL_WEIGHT,
                "lifestyle": LIFESTYLE_WEIGHT,
            },
            "contributions": {
                "clinical": round(clinical_contrib, 2),
                "lifestyle": round(lifestyle_contrib, 2),
            },
            "combined": {
                "risk": round(overall_risk, 2),
                "category": category,
                "alert_level": alert_level,
                "recommended_action": recommended_action,
            },
            "clinical_explanation_available": clinical_explanation_available,
            "clinical_explanation": clinical_explanation,
            "overall_explanation": "",
            "disclaimer": DISCLAIMER_TEXT,
        }

        # Generate comprehensive overall explanation
        result["overall_explanation"] = generate_overall_explanation(result)

        logger.info(
            "Multimodal assessment completed: overall_risk=%.2f%%, category=%s, alert_level=%s",
            overall_risk,
            category,
            alert_level,
        )
        return result
