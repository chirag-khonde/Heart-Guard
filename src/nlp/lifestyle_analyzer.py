"""Lifestyle Text Analyzer / NLP Module for HeartGuard (Phase 6).

Implements rule-based NLP extraction of cardiovascular lifestyle risk signals
from free text using NLTK tokenization, phrase matching, negation detection,
and predefined risk scoring.
"""

from __future__ import annotations

import re
from typing import Any

from src.nlp.explanation import (
    DISCLAIMER_TEXT,
    generate_lifestyle_summary,
    get_top_lifestyle_risk_factors,
)
from src.nlp.risk_lexicon import (
    HEALTHY_DIET_TERMS,
    MAX_LIFESTYLE_SCORE,
    NEGATION_TERMS,
    NON_ALCOHOLIC_DRINKS,
    POSITIVE_EXERCISE_TERMS,
    RISK_LEXICON,
)
from src.nlp.scoring import (
    calculate_lifestyle_score,
    get_risk_category,
    get_score_breakdown,
)
from src.nlp.text_preprocessor import (
    normalize_text,
    tokenize_text,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Maximum allowed character limit for patient text input
MAX_INPUT_CHARACTERS: int = 5000


class LifestyleAnalyzer:
    """Rule-based NLP analyzer for patient lifestyle cardiovascular risk."""

    def __init__(self) -> None:
        """Initialise the lifestyle analyzer with the risk lexicon."""
        self.lexicon = RISK_LEXICON

    def _is_phrase_negated(
        self,
        text: str,
        match_start: int,
        match_end: int,
        window_chars: int = 35,
    ) -> bool:
        """Check if a matched phrase is preceded by a negation word within a window.

        Args:
            text: Lowercased string where match occurred.
            match_start: Start character index of the match.
            match_end: End character index of the match.
            window_chars: Character window preceding the match to inspect.

        Returns:
            bool: True if negation is detected before the match.
        """
        start = max(0, match_start - window_chars)
        preceding_snippet = text[start:match_start].strip().lower()

        # Check for clause boundaries (periods, semicolons, but)
        # Only inspect the snippet after the last clause boundary
        clause_break = re.split(r"[,;.\n]|\bbut\b", preceding_snippet)
        immediate_clause = clause_break[-1].strip()

        words = re.findall(r"\b[\w'-]+\b", immediate_clause)
        for w in words:
            if w in NEGATION_TERMS:
                return True

        # Check for multi-word negation phrases in the preceding snippet
        for neg_phrase in ("do not", "does not", "did not", "no longer", "used to"):
            if neg_phrase in immediate_clause:
                return True

        return False

    def _detect_smoking(self, text: str) -> tuple[list[str], list[str]]:
        """Detect smoking evidence in normalized text.

        Returns:
            tuple of (matched_terms, evidence_snippets).
        """
        matched_terms: list[str] = []
        evidence_snippets: list[str] = []
        config = self.lexicon["smoking"]
        all_keywords = config["primary_keywords"] + config["variation_keywords"]

        # Sort keywords longest first for maximal phrase matching
        sorted_kw = sorted(all_keywords, key=len, reverse=True)

        for kw in sorted_kw:
            # Pattern matching word boundaries
            pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            for m in pattern.finditer(text):
                if not self._is_phrase_negated(text, m.start(), m.end()):
                    if kw not in matched_terms:
                        matched_terms.append(kw)
                    snippet = text[max(0, m.start() - 10) : min(len(text), m.end() + 10)].strip()
                    if snippet not in evidence_snippets:
                        evidence_snippets.append(snippet)

        return matched_terms, evidence_snippets

    def _detect_physical_inactivity(self, text: str) -> tuple[list[str], list[str]]:
        """Detect physical inactivity evidence in normalized text.

        Handles positive exercise context and negation.
        """
        matched_terms: list[str] = []
        evidence_snippets: list[str] = []
        config = self.lexicon["physical_inactivity"]
        all_keywords = config["primary_keywords"] + config["variation_keywords"]

        # 1. Check positive exercise counters (e.g. "exercise regularly", "work out every")
        # unless preceded by negation (e.g. "no regular exercise")
        has_unnegated_positive_exercise = False
        for pos_term in POSITIVE_EXERCISE_TERMS:
            pos_pat = re.compile(rf"\b{re.escape(pos_term)}\b", re.IGNORECASE)
            for m in pos_pat.finditer(text):
                if not self._is_phrase_negated(text, m.start(), m.end(), window_chars=20):
                    has_unnegated_positive_exercise = True
                    break
            if has_unnegated_positive_exercise:
                break

        # 2. Check direct negative exercise patterns (e.g., "don't exercise", "no regular exercise")
        neg_exercise_patterns = [
            r"\b(?:no|not|never|rarely|hardly|little|lack of|without|don't|dont|do not|doesn't|doesnt)\b\s+(?:regular\s+)?(?:exercise|physical activity|workout|workouts)\b",
            r"\b(?:don't|dont|do not|doesn't|doesnt|never|rarely|hardly)\s+exercise\b",
        ]
        for pat in neg_exercise_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                term = m.group(0)
                if term not in matched_terms:
                    matched_terms.append(term)
                snippet = text[max(0, m.start() - 5) : min(len(text), m.end() + 5)].strip()
                if snippet not in evidence_snippets:
                    evidence_snippets.append(snippet)

        # 3. Check explicit inactivity keywords (e.g., "sedentary", "desk job", "mostly sitting")
        for kw in sorted(all_keywords, key=len, reverse=True):
            pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            for m in pattern.finditer(text):
                if not self._is_phrase_negated(text, m.start(), m.end()):
                    if kw not in matched_terms:
                        matched_terms.append(kw)
                    snippet = text[max(0, m.start() - 10) : min(len(text), m.end() + 10)].strip()
                    if snippet not in evidence_snippets:
                        evidence_snippets.append(snippet)

        # If user explicitly has unnegated regular exercise and no specific inactivity triggers like desk job/sedentary
        if has_unnegated_positive_exercise and not any(
            t in ("sedentary", "desk job", "mostly sitting", "couch potato") for t in matched_terms
        ):
            return [], []

        return matched_terms, evidence_snippets

    def _detect_unhealthy_diet(self, text: str) -> tuple[list[str], list[str]]:
        """Detect unhealthy diet evidence in normalized text."""
        matched_terms: list[str] = []
        evidence_snippets: list[str] = []

        # Check for explicit healthy diet counters (e.g. "healthy diet", "avoid junk food")
        config = self.lexicon["unhealthy_diet"]
        all_keywords = config["primary_keywords"] + config["variation_keywords"]

        for kw in sorted(all_keywords, key=len, reverse=True):
            pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            for m in pattern.finditer(text):
                # Check for negation or avoid/no
                if not self._is_phrase_negated(text, m.start(), m.end(), window_chars=30):
                    if kw not in matched_terms:
                        matched_terms.append(kw)
                    snippet = text[max(0, m.start() - 10) : min(len(text), m.end() + 10)].strip()
                    if snippet not in evidence_snippets:
                        evidence_snippets.append(snippet)

        return matched_terms, evidence_snippets

    def _detect_poor_sleep(self, text: str) -> tuple[list[str], list[str]]:
        """Detect poor sleep evidence in normalized text.

        Requires numeric sleep < 6 hours or explicit symptoms (insomnia, poor sleep).
        Does NOT match bare 'sleep' alone.
        """
        matched_terms: list[str] = []
        evidence_snippets: list[str] = []

        # 1. Numeric sleep hour detection (e.g. "sleep 5 hours", "only 4.5 hours sleep")
        numeric_patterns = [
            r"\b(?:sleep|sleeping|slept|get|getting)\b\s*(?:about|around|only|just)?\s*(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr|hour)\b",
            r"\b(?:about|around|only|just)?\s*(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr|hour)\b(?:\s*of)?\s*(?:sleep|sleeping)\b",
        ]
        for pat in numeric_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                hours = float(m.group(1))
                if hours < 6.0:  # Less than 6 hours indicates poor sleep
                    matched_term = m.group(0).strip()
                    if matched_term not in matched_terms:
                        matched_terms.append(matched_term)
                    snippet = text[max(0, m.start() - 5) : min(len(text), m.end() + 5)].strip()
                    if snippet not in evidence_snippets:
                        evidence_snippets.append(snippet)

        # 2. Symptomatic sleep keywords (e.g., insomnia, poor sleep, sleep deprivation)
        config = self.lexicon["poor_sleep"]
        all_keywords = config["primary_keywords"] + config["variation_keywords"]

        for kw in sorted(all_keywords, key=len, reverse=True):
            # Avoid re-matching generic numeric patterns handled above
            if kw == "sleep 5 hours" or kw == "sleeping 5 hours" or kw == "only 5 hours sleep":
                continue
            pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            for m in pattern.finditer(text):
                if not self._is_phrase_negated(text, m.start(), m.end()):
                    if kw not in matched_terms:
                        matched_terms.append(kw)
                    snippet = text[max(0, m.start() - 10) : min(len(text), m.end() + 10)].strip()
                    if snippet not in evidence_snippets:
                        evidence_snippets.append(snippet)

        return matched_terms, evidence_snippets

    def _detect_family_history(self, text: str) -> tuple[list[str], list[str]]:
        """Detect family history of cardiovascular disease in normalized text."""
        matched_terms: list[str] = []
        evidence_snippets: list[str] = []
        config = self.lexicon["family_history"]
        all_keywords = config["primary_keywords"] + config["variation_keywords"]

        for kw in sorted(all_keywords, key=len, reverse=True):
            pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            for m in pattern.finditer(text):
                if not self._is_phrase_negated(text, m.start(), m.end()):
                    if kw not in matched_terms:
                        matched_terms.append(kw)
                    snippet = text[max(0, m.start() - 10) : min(len(text), m.end() + 10)].strip()
                    if snippet not in evidence_snippets:
                        evidence_snippets.append(snippet)

        return matched_terms, evidence_snippets

    def _detect_alcohol_use(self, text: str) -> tuple[list[str], list[str]]:
        """Detect alcohol use evidence in normalized text.

        Implements alcohol disambiguation so that non-alcoholic drinks
        (water, milk, tea, coffee, juice) are excluded.
        """
        matched_terms: list[str] = []
        evidence_snippets: list[str] = []
        config = self.lexicon["alcohol_use"]
        all_keywords = config["primary_keywords"] + config["variation_keywords"]

        # 1. Check explicit alcoholic beverages (beer, wine, whiskey, vodka, liquor, spirits)
        explicit_alcohol = [
            "alcohol",
            "beer",
            "wine",
            "liquor",
            "spirits",
            "whiskey",
            "vodka",
            "cocktails",
            "alcoholic",
            "heavy drinking",
            "binge drinking",
        ]
        for kw in explicit_alcohol:
            pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            for m in pattern.finditer(text):
                if not self._is_phrase_negated(text, m.start(), m.end()):
                    if kw not in matched_terms:
                        matched_terms.append(kw)
                    snippet = text[max(0, m.start() - 10) : min(len(text), m.end() + 10)].strip()
                    if snippet not in evidence_snippets:
                        evidence_snippets.append(snippet)

        # 2. Check contextual "drink" usages
        drink_pattern = re.compile(r"\b(?:drink|drinking|drinks|drank)\b", re.IGNORECASE)
        for m in drink_pattern.finditer(text):
            if self._is_phrase_negated(text, m.start(), m.end()):
                continue

            # Look ahead in the immediate clause after "drink" (up to 45 characters)
            following = text[m.end() : min(len(text), m.end() + 45)].lower().strip()
            immediate_clause = re.split(r"[,;.\n]|\band\b|\bbut\b", following)[0]
            following_words = set(re.findall(r"\b[\w'-]+\b", immediate_clause))

            # If followed by a known non-alcoholic drink (water, coffee, tea, milk, etc.), skip
            if following_words & NON_ALCOHOLIC_DRINKS:
                continue

            # Check if followed by alcohol or qualifiers like occasionally, heavily, daily
            snippet = text[max(0, m.start() - 10) : min(len(text), m.end() + 20)].strip()
            matched_term = "drink"
            if snippet not in evidence_snippets and "drink" not in matched_terms:
                matched_terms.append("drink")
                evidence_snippets.append(snippet)

        return matched_terms, evidence_snippets

    def analyze(self, text: str) -> dict[str, Any]:
        """Analyze free-text lifestyle input and return structured risk evaluation.

        Args:
            text: Patient lifestyle description.

        Returns:
            dict containing raw_text, normalized_text, tokens, lifestyle_score,
            risk_category, detected_risk_factors, top_risk_factors, and summary.

        Raises:
            ValueError: If input text exceeds MAX_INPUT_CHARACTERS (5000).
        """
        if text is None:
            text = ""

        if len(text) > MAX_INPUT_CHARACTERS:
            raise ValueError(
                f"Input text exceeds maximum allowed limit of {MAX_INPUT_CHARACTERS} characters "
                f"(received {len(text)} characters)."
            )

        raw_text = str(text)
        normalized = normalize_text(raw_text)
        tokens = tokenize_text(raw_text)

        # If text is empty or has no content
        if not normalized.strip():
            empty_summary = (
                "No lifestyle text provided.\n"
                "Lifestyle risk score: 0/100 (LOW).\n\n"
                f"Disclaimer: {DISCLAIMER_TEXT}"
            )
            return {
                "raw_text": raw_text,
                "normalized_text": normalized,
                "tokens": tokens,
                "lifestyle_score": 0,
                "risk_category": "LOW",
                "detected_risk_factors": [],
                "total_detected_factors": 0,
                "top_risk_factors": [],
                "score_breakdown": get_score_breakdown([]),
                "summary": empty_summary,
                "disclaimer": DISCLAIMER_TEXT,
            }

        detected_factors: list[dict[str, Any]] = []

        # Run detection across all 6 risk categories
        detectors = {
            "smoking": self._detect_smoking,
            "physical_inactivity": self._detect_physical_inactivity,
            "unhealthy_diet": self._detect_unhealthy_diet,
            "poor_sleep": self._detect_poor_sleep,
            "family_history": self._detect_family_history,
            "alcohol_use": self._detect_alcohol_use,
        }

        for cat_key, detector_fn in detectors.items():
            matched_terms, evidence = detector_fn(normalized)
            if matched_terms:
                cat_config = self.lexicon[cat_key]
                detected_factors.append(
                    {
                        "category": cat_key,
                        "display_name": cat_config["display_name"],
                        "risk_points": cat_config["risk_points"],
                        "severity": cat_config["severity"],
                        "matched_terms": matched_terms,
                        "evidence": "; ".join(evidence),
                        "direction": cat_config["direction"],
                    }
                )

        # Calculate score and category
        score = calculate_lifestyle_score(detected_factors)
        category = get_risk_category(score)
        top_factors = get_top_lifestyle_risk_factors(detected_factors, top_n=3)
        breakdown = get_score_breakdown(detected_factors)
        summary = generate_lifestyle_summary(detected_factors, score, category)

        result = {
            "raw_text": raw_text,
            "normalized_text": normalized,
            "tokens": tokens,
            "lifestyle_score": score,
            "risk_category": category,
            "detected_risk_factors": detected_factors,
            "total_detected_factors": len(detected_factors),
            "top_risk_factors": top_factors,
            "score_breakdown": breakdown,
            "summary": summary,
            "disclaimer": DISCLAIMER_TEXT,
        }

        logger.info(
            "Lifestyle analysis complete: score=%d/100, category=%s, factors_detected=%d",
            score,
            category,
            len(detected_factors),
        )
        return result


# ===========================================================================
# Standalone Functional API for Backward Compatibility
# ===========================================================================

_GLOBAL_ANALYZER: LifestyleAnalyzer | None = None


def _get_analyzer() -> LifestyleAnalyzer:
    """Singleton accessor for the LifestyleAnalyzer instance."""
    global _GLOBAL_ANALYZER
    if _GLOBAL_ANALYZER is None:
        _GLOBAL_ANALYZER = LifestyleAnalyzer()
    return _GLOBAL_ANALYZER


def analyze_lifestyle_text(text: str) -> dict[str, Any]:
    """Analyze lifestyle text for health risk factors.

    Args:
        text: Patient lifestyle description text.

    Returns:
        Structured analysis dictionary.
    """
    return _get_analyzer().analyze(text)


def detect_risk_factors(text: str) -> list[str]:
    """Detect lifestyle risk factor category names from text.

    Args:
        text: Patient lifestyle description text.

    Returns:
        List of detected risk factor category names (e.g. ['smoking', 'poor_sleep']).
    """
    res = analyze_lifestyle_text(text)
    return [f["category"] for f in res.get("detected_risk_factors", [])]


def calculate_lifestyle_score_from_results(analysis_results: dict[str, Any]) -> float:
    """Calculate lifestyle risk score from analysis results.

    Args:
        analysis_results: Results from analyze_lifestyle_text.

    Returns:
        float: Score between 0 and 100.
    """
    return float(analysis_results.get("lifestyle_score", 0))
