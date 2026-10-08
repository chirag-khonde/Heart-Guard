"""Core Recommendation Engine for HeartGuard (Phase 13).

Transforms multimodal assessment data into prioritized, personalized,
non-diagnostic recommendations and AI insight summaries.
"""

from __future__ import annotations

import datetime
from typing import Any, Optional
import uuid

from config.settings import RECOMMENDATION_ENGINE_VERSION
from src.analytics.models import Assessment
from src.analytics.trend_service import TrendService
from src.recommendations.recommendation_models import (
    AssessmentInsights,
    PRIORITY_ORDER,
    RECOMMENDATION_DISCLAIMER,
    Recommendation,
)
from src.recommendations.recommendation_rules import (
    rule_alcohol_use,
    rule_blood_pressure,
    rule_cholesterol,
    rule_family_history,
    rule_fasting_blood_sugar,
    rule_physical_inactivity,
    rule_poor_sleep,
    rule_risk_category,
    rule_smoking,
    rule_trend_comparison,
    rule_unhealthy_diet,
)
from src.recommendations.recommendation_validator import validate_recommendation
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RecommendationEngine:
    """Consumes assessment records and produces personalized, non-diagnostic guidance."""

    @staticmethod
    def generate_insights(
        assessment: Assessment,
        previous_assessment: Optional[Assessment] = None,
    ) -> AssessmentInsights:
        """Generate consolidated AI insights and personalized recommendations for an assessment.

        Args:
            assessment: Current Assessment domain instance.
            previous_assessment: Optional prior Assessment instance for trend deltas.

        Returns:
            AssessmentInsights containing personalized summary, top factors,
            trend comparison, and deduplicated prioritized recommendations.
        """
        user_id = assessment.user_id
        aid = assessment.assessment_id
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        lifestyle_factors = assessment.get_lifestyle_factors()
        clinical_data = assessment.get_clinical_data()
        top_shap = assessment.get_top_clinical_factors()

        comparison = TrendService.compare_assessments(assessment, previous_assessment)

        # 1. Execute deterministic rules
        raw_matches: list[dict[str, Any]] = []

        # Lifestyle rules
        for fn in [
            rule_smoking,
            rule_physical_inactivity,
            rule_unhealthy_diet,
            rule_poor_sleep,
            rule_alcohol_use,
            rule_family_history,
        ]:
            res = fn(lifestyle_factors, clinical_data)
            if res:
                raw_matches.append(res)

        # Clinical & SHAP rules
        for fn in [rule_blood_pressure, rule_cholesterol, rule_fasting_blood_sugar]:
            res = fn(lifestyle_factors, clinical_data, top_shap)
            if res:
                raw_matches.append(res)

        # Risk tier rule (always fires one recommendation)
        raw_matches.append(rule_risk_category(assessment.risk_category, assessment.overall_risk))

        # Trend rule
        if comparison:
            trend_res = rule_trend_comparison(comparison)
            if trend_res:
                raw_matches.append(trend_res)

        # 2. Validate safety and deduplicate
        seen_rules: set[str] = set()
        seen_categories: set[str] = set()
        valid_recs: list[Recommendation] = []

        for m in raw_matches:
            rule_id = m["rule_id"]
            cat = m["category"]

            # Deduplication check: do not emit duplicate rule_ids
            if rule_id in seen_rules:
                continue

            try:
                is_valid, reason = validate_recommendation(m)
                if not is_valid:
                    logger.warning("Rejected unsafe recommendation '%s': %s", rule_id, reason)
                    continue
            except Exception as exc:
                logger.warning("Rejected unsafe recommendation '%s': %s", rule_id, exc)
                continue

            seen_rules.add(rule_id)
            seen_categories.add(cat)

            rec_obj = Recommendation(
                id=None,
                recommendation_id=uuid.uuid4().hex[:12],
                assessment_id=aid,
                user_id=user_id,
                category=cat,
                title=m["title"],
                description=m["description"],
                priority=m["priority"],
                source=m["source"],
                rule_id=rule_id,
                version=RECOMMENDATION_ENGINE_VERSION,
                created_at=now_iso,
            )
            valid_recs.append(rec_obj)

        # 3. Sort by priority (HIGH > MEDIUM > LOW > INFO)
        valid_recs.sort(key=lambda r: PRIORITY_ORDER.get(r.priority, 99))

        # 4. Generate summary text
        FRIENDLY_NAMES = {
            "trestbps": "Resting Blood Pressure",
            "chol": "Serum Cholesterol",
            "thalach": "Max Heart Rate",
            "fbs": "Fasting Blood Sugar",
            "cp": "Chest Pain Type",
            "oldpeak": "ST Depression (Oldpeak)",
            "age": "Age",
            "sex": "Sex",
            "ca": "Major Vessels (Fluoroscopy)",
            "thal": "Thalassemia Indicator",
            "exang": "Exercise-Induced Angina",
            "restecg": "Resting ECG",
            "slope": "ST Slope",
        }

        top_factor_names = []
        for tf in top_shap[:3]:
            raw_feat = str(tf.get("feature", "")).lower()
            label = tf.get("clinical_label") or FRIENDLY_NAMES.get(raw_feat) or raw_feat.replace("_", " ").title()
            if label:
                top_factor_names.append(label)

        summary_parts = [
            f"Your latest HeartGuard assessment indicates a model-based risk score of "
            f"{assessment.overall_risk:.1f}% ({assessment.risk_category.replace('_', ' ').title()})."
        ]
        if top_factor_names:
            factors_str = ", ".join(top_factor_names[:-1]) + (" and " if len(top_factor_names) > 1 else "") + top_factor_names[-1]
            summary_parts.append(
                f"Features with the highest statistical influence on this output included {factors_str}."
            )
        summary_text = " ".join(summary_parts)

        # 5. Format comparison summary
        if comparison:
            comp_summary = comparison.get("interpretation") or comparison.get("summary")
        elif previous_assessment is None:
            comp_summary = "This is your first HeartGuard assessment, so there is no previous assessment available for comparison."
        else:
            comp_summary = None

        # 6. Format top factors with clear lay explanations
        top_factors_formatted: list[dict[str, Any]] = []
        for tf in top_shap[:5]:
            raw_feat = str(tf.get("feature", "Clinical Feature")).lower()
            clean_name = tf.get("clinical_label") or FRIENDLY_NAMES.get(raw_feat) or raw_feat.replace("_", " ").title()
            val = tf.get("shap_value", tf.get("importance", 0.0))
            direction = "positive contributor (increased model risk)" if val >= 0 else "protective factor (reduced model risk)"
            top_factors_formatted.append(
                {
                    "feature": clean_name,
                    "shap_value": val,
                    "direction": direction,
                    "description": f"{clean_name} contributed to this model-based assessment score based on statistical feature importance.",
                    "explanation": f"{clean_name} was one of the stronger {direction}s for this model output.",
                }
            )

        return AssessmentInsights(
            assessment_id=aid,
            summary_text=summary_text,
            top_factors=top_factors_formatted,
            comparison_summary=comp_summary,
            recommendations=valid_recs,
            disclaimer=RECOMMENDATION_DISCLAIMER,
            version=RECOMMENDATION_ENGINE_VERSION,
            comparison=comparison,
        )
