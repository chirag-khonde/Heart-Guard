"""HeartGuard NLP Lifestyle Text Analyzer Module (Phase 6)."""

from src.nlp.explanation import (
    DISCLAIMER_TEXT,
    generate_lifestyle_summary,
    generate_risk_factor_explanation,
    get_top_lifestyle_risk_factors,
)
from src.nlp.lifestyle_analyzer import (
    LifestyleAnalyzer,
    analyze_lifestyle_text,
    calculate_lifestyle_score_from_results,
    detect_risk_factors,
)
from src.nlp.risk_lexicon import (
    MAX_LIFESTYLE_SCORE,
    RISK_LEXICON,
)
from src.nlp.scoring import (
    calculate_category_contribution,
    calculate_lifestyle_score,
    get_risk_category,
    get_score_breakdown,
)
from src.nlp.text_preprocessor import (
    ensure_nltk_resources,
    normalize_text,
    normalize_whitespace,
    remove_unnecessary_punctuation,
    tokenize_text,
)

__all__ = [
    "DISCLAIMER_TEXT",
    "LifestyleAnalyzer",
    "MAX_LIFESTYLE_SCORE",
    "RISK_LEXICON",
    "analyze_lifestyle_text",
    "calculate_category_contribution",
    "calculate_lifestyle_score",
    "calculate_lifestyle_score_from_results",
    "detect_risk_factors",
    "ensure_nltk_resources",
    "generate_lifestyle_summary",
    "generate_risk_factor_explanation",
    "get_risk_category",
    "get_score_breakdown",
    "get_top_lifestyle_risk_factors",
    "normalize_text",
    "normalize_whitespace",
    "remove_unnecessary_punctuation",
    "tokenize_text",
]
