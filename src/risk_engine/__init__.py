"""HeartGuard Multimodal Risk Engine Package (Phase 7).

Combines Clinical ML Risk (70%) and Lifestyle NLP Risk (30%) into a unified
cardiovascular risk assessment.
"""

from src.risk_engine.multimodal_risk import (
    MultimodalRiskEngine,
    calculate_multimodal_risk,
)
from src.risk_engine.risk_categories import (
    ACTION_APPOINTMENT,
    ACTION_CRITICAL,
    ACTION_MONITORING,
    APPOINTMENT_THRESHOLD,
    CATEGORY_APPOINTMENT,
    CATEGORY_CRITICAL,
    CATEGORY_DISPLAY_LABELS,
    CATEGORY_MONITORING,
    CLINICAL_WEIGHT,
    CRITICAL_THRESHOLD,
    LIFESTYLE_WEIGHT,
    get_alert_level,
    get_overall_risk_category,
    get_recommended_action,
)
from src.risk_engine.risk_explanation import (
    DISCLAIMER_TEXT,
    format_multimodal_breakdown,
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

__all__ = [
    "ACTION_APPOINTMENT",
    "ACTION_CRITICAL",
    "ACTION_MONITORING",
    "APPOINTMENT_THRESHOLD",
    "CATEGORY_APPOINTMENT",
    "CATEGORY_CRITICAL",
    "CATEGORY_DISPLAY_LABELS",
    "CATEGORY_MONITORING",
    "CLINICAL_WEIGHT",
    "CRITICAL_THRESHOLD",
    "DISCLAIMER_TEXT",
    "LIFESTYLE_WEIGHT",
    "MultimodalRiskEngine",
    "calculate_multimodal_risk",
    "format_multimodal_breakdown",
    "generate_overall_explanation",
    "get_alert_level",
    "get_overall_risk_category",
    "get_recommended_action",
    "validate_clinical_input",
    "validate_clinical_risk",
    "validate_lifestyle_input",
    "validate_lifestyle_risk",
    "validate_overall_risk",
    "validate_weights",
]
