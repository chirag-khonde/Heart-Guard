"""Predefined Cardiovascular Lifestyle Risk Lexicon for HeartGuard.

Defines the centralized risk categories, point weights, severity levels,
primary documented triggers, and contextual variations based on the
HeartGuard project specification.
"""

from __future__ import annotations

from typing import Any, TypedDict


class RiskCategoryDefinition(TypedDict):
    """Schema for a risk category in the lexicon."""

    display_name: str
    risk_points: int
    severity: str
    primary_keywords: list[str]
    variation_keywords: list[str]
    direction: str


# ===========================================================================
# Centralized Risk Lexicon
# ===========================================================================

RISK_LEXICON: dict[str, RiskCategoryDefinition] = {
    "smoking": {
        "display_name": "Smoking",
        "risk_points": 25,
        "severity": "High",
        "primary_keywords": [
            "smoke",
            "smoking",
            "cigarette",
            "cigarettes",
            "tobacco",
            "nicotine",
        ],
        "variation_keywords": [
            "cigar",
            "cigars",
            "vape",
            "vaping",
            "vapes",
            "chain smoker",
            "chain smoking",
        ],
        "direction": "increases_lifestyle_risk",
    },
    "physical_inactivity": {
        "display_name": "Physical Inactivity",
        "risk_points": 15,
        "severity": "High",
        "primary_keywords": [
            "no exercise",
            "sedentary",
            "desk job",
        ],
        "variation_keywords": [
            "inactive",
            "inactivity",
            "little exercise",
            "no physical activity",
            "rarely exercise",
            "never exercise",
            "mostly sitting",
            "not exercising",
            "no regular exercise",
            "lack of exercise",
            "no workout",
            "couch potato",
            "barely exercise",
            "hardly exercise",
        ],
        "direction": "increases_lifestyle_risk",
    },
    "unhealthy_diet": {
        "display_name": "Unhealthy Diet",
        "risk_points": 18,
        "severity": "Moderate",
        "primary_keywords": [
            "oily food",
            "junk",
            "fast food",
            "fried",
        ],
        "variation_keywords": [
            "fried food",
            "unhealthy food",
            "processed food",
            "high fat food",
            "too much junk food",
            "junk food",
            "fatty food",
            "sugary food",
            "deep fried",
            "oily foods",
            "fast foods",
            "fried foods",
        ],
        "direction": "increases_lifestyle_risk",
    },
    "poor_sleep": {
        "display_name": "Poor Sleep",
        "risk_points": 12,
        "severity": "Moderate",
        "primary_keywords": [
            "sleep 5 hours",
            "insomnia",
            "poor sleep",
        ],
        "variation_keywords": [
            "sleeping 5 hours",
            "only 5 hours sleep",
            "less sleep",
            "lack of sleep",
            "sleep deprivation",
            "sleepless",
            "broken sleep",
            "trouble sleeping",
            "cannot sleep",
            "cant sleep",
            "sleep disorder",
            "poor quality sleep",
            "disturbed sleep",
        ],
        "direction": "increases_lifestyle_risk",
    },
    "family_history": {
        "display_name": "Family History",
        "risk_points": 20,
        "severity": "High",
        "primary_keywords": [
            "family history",
            "heart attack",
            "cardiac",
        ],
        "variation_keywords": [
            "family history of heart disease",
            "family history of heart attack",
            "father had heart attack",
            "mother had heart attack",
            "parent had cardiac disease",
            "parents had heart disease",
            "history of heart disease",
            "family history of cardiac",
            "dad had heart attack",
            "mom had heart attack",
            "cardiac history",
        ],
        "direction": "increases_lifestyle_risk",
    },
    "alcohol_use": {
        "display_name": "Alcohol Use",
        "risk_points": 10,
        "severity": "Low",
        "primary_keywords": [
            "drink",
            "alcohol",
            "beer",
            "wine",
        ],
        "variation_keywords": [
            "liquor",
            "spirits",
            "whiskey",
            "vodka",
            "cocktails",
            "alcoholic",
            "heavy drinking",
            "binge drinking",
            "drink alcohol",
            "drink beer",
            "drink wine",
            "drink heavily",
            "drink occasionally",
        ],
        "direction": "increases_lifestyle_risk",
    },
}

# Maximum score threshold
MAX_LIFESTYLE_SCORE: int = 100

# Negation terms used by the rule-based negation detector
NEGATION_TERMS: set[str] = {
    "no",
    "not",
    "never",
    "don't",
    "dont",
    "doesn't",
    "doesnt",
    "didn't",
    "didnt",
    "without",
    "do not",
    "does not",
    "did not",
    "quit",
    "stopped",
    "avoid",
    "avoids",
    "avoiding",
    "neither",
    "nor",
    "hardly",
    "barely",
}

# Non-alcoholic substances for alcohol disambiguation
NON_ALCOHOLIC_DRINKS: set[str] = {
    "water",
    "milk",
    "tea",
    "coffee",
    "juice",
    "soda",
    "lemonade",
    "smoothie",
    "protein shake",
    "energy drink",
    "electrolyte",
    "chai",
}

# Positive exercise indicators that counter physical inactivity
POSITIVE_EXERCISE_TERMS: list[str] = [
    "exercise regularly",
    "regular exercise",
    "exercise daily",
    "daily exercise",
    "exercise every",
    "work out every",
    "work out regularly",
    "regular workouts",
    "exercise 5",
    "exercise 4",
    "exercise 3",
    "exercise 6",
    "exercise five",
    "exercise four",
    "exercise three",
    "gym regularly",
    "go to the gym",
    "active lifestyle",
    "physically active",
    "run every",
    "jog every",
    "swimming regularly",
]

# Healthy diet indicators that counter unhealthy diet
HEALTHY_DIET_TERMS: list[str] = [
    "healthy food",
    "healthy diet",
    "eat healthy",
    "clean eating",
    "balanced diet",
    "nutritious food",
    "avoid junk",
    "avoid fast food",
    "avoid oily",
    "avoid fried",
    "no junk",
    "no fast food",
    "no oily",
    "no fried",
]
