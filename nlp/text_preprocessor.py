"""Text Preprocessing and NLTK Utilities for HeartGuard.

Provides normalized text cleaning, NLTK resource management, tokenization,
and whitespace management for the rule-based lifestyle analyzer.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Track NLTK availability state
_NLTK_RESOURCES_CHECKED: bool = False
_NLTK_TOKENIZER_AVAILABLE: bool = False


def ensure_nltk_resources() -> bool:
    """Safely check and ensure required NLTK resources are available.

    Safe to call multiple times; checks cache flag before performing lookups.
    Falls back gracefully if resources or network are unavailable.

    Returns:
        bool: True if NLTK tokenizers are ready, False if falling back to regex.
    """
    global _NLTK_RESOURCES_CHECKED, _NLTK_TOKENIZER_AVAILABLE

    if _NLTK_RESOURCES_CHECKED:
        return _NLTK_TOKENIZER_AVAILABLE

    try:
        import nltk

        # Check for punkt and punkt_tab
        has_punkt = False
        for pkg in ("tokenizers/punkt", "tokenizers/punkt_tab"):
            try:
                nltk.data.find(pkg)
                has_punkt = True
            except LookupError:
                try:
                    name = pkg.split("/")[-1]
                    nltk.download(name, quiet=True)
                    has_punkt = True
                except Exception as exc:
                    logger.debug("Could not download %s: %s", pkg, exc)

        _NLTK_TOKENIZER_AVAILABLE = has_punkt
    except Exception as exc:
        logger.warning("NLTK resource check encountered an issue (%s); using regex tokenizer", exc)
        _NLTK_TOKENIZER_AVAILABLE = False

    _NLTK_RESOURCES_CHECKED = True
    return _NLTK_TOKENIZER_AVAILABLE


def normalize_whitespace(text: str) -> str:
    """Collapse consecutive spaces, tabs, and newlines into a single space.

    Args:
        text: Raw or partially cleaned text string.

    Returns:
        Stripped string with uniform single spacing.
    """
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def remove_unnecessary_punctuation(text: str) -> str:
    """Remove intrusive punctuation while preserving hyphens, apostrophes, digits, and decimals.

    Args:
        text: Lowercase or raw string.

    Returns:
        Cleaned string with extraneous punctuation converted to spaces.
    """
    if not text:
        return ""
    # Preserve decimal points between digits (e.g., 5.5, 4.5)
    preserved = re.sub(r"(?<=\d)\.(?=\d)", "___DEC___", text)
    # Retain alphanumeric, spaces, hyphens, and apostrophes
    cleaned = re.sub(r"[^\w\s\'-]", " ", preserved)
    # Restore decimal points
    restored = cleaned.replace("___DEC___", ".")
    return normalize_whitespace(restored)


def normalize_text(text: str) -> str:
    """Normalize input text for NLP keyword and phrase matching.

    Converts to lowercase, normalizes unicode accents/ligatures,
    cleans punctuation, and standardizes spacing.

    Args:
        text: Raw input string.

    Returns:
        Canonical lowercase normalized string.
    """
    if not text:
        return ""

    # Normalize unicode characters
    normalized = unicodedata.normalize("NFKD", text)

    # Convert to lowercase
    lowercased = normalized.lower()

    # Normalize whitespace and unnecessary punctuation
    cleaned = remove_unnecessary_punctuation(lowercased)
    return cleaned


def tokenize_text(text: str) -> list[str]:
    """Tokenize input text using NLTK word_tokenize with a regex fallback.

    Args:
        text: String to tokenize.

    Returns:
        List of individual word and sub-token strings.
    """
    if not text or not text.strip():
        return []

    norm = normalize_text(text)
    if not norm:
        return []

    if ensure_nltk_resources():
        try:
            from nltk.tokenize import word_tokenize

            tokens = word_tokenize(norm)
            return [t for t in tokens if t.strip()]
        except Exception as exc:
            logger.debug("NLTK word_tokenize failed (%s); falling back to regex", exc)

    # Regex tokenization fallback
    return re.findall(r"\b[\w'-]+\b", norm)
