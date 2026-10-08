"""HeartGuard AI Recommendations & Insights Module (Phase 13).

Provides non-diagnostic, personalized recommendations and AI insights.
"""

from src.recommendations.recommendation_engine import RecommendationEngine
from src.recommendations.recommendation_models import (
    AssessmentInsights,
    PRIORITIES,
    PRIORITY_HIGH,
    PRIORITY_INFO,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    RECOMMENDATION_DISCLAIMER,
    Recommendation,
    init_recommendation_db,
)
from src.recommendations.recommendation_rules import (
    evaluate_clinical_rules,
    evaluate_lifestyle_rules,
    evaluate_risk_tier_rules,
    evaluate_trend_rules,
)
from src.recommendations.recommendation_service import RecommendationService
from src.recommendations.recommendation_validator import (
    PRESCRIPTION_TERMS,
    SafetyValidationError,
    validate_recommendation,
)

__all__ = [
    "AssessmentInsights",
    "PRESCRIPTION_TERMS",
    "PRIORITIES",
    "PRIORITY_HIGH",
    "PRIORITY_INFO",
    "PRIORITY_LOW",
    "PRIORITY_MEDIUM",
    "RECOMMENDATION_DISCLAIMER",
    "Recommendation",
    "RecommendationEngine",
    "RecommendationService",
    "SafetyValidationError",
    "evaluate_clinical_rules",
    "evaluate_lifestyle_rules",
    "evaluate_risk_tier_rules",
    "evaluate_trend_rules",
    "init_recommendation_db",
    "validate_recommendation",
]
