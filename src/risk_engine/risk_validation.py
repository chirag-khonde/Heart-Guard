"""Validation Utilities for HeartGuard Multimodal Risk Engine.

Validates clinical input attributes, lifestyle narratives, risk probabilities,
and multimodal weight allocations.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from src.data.features import (
    BINARY_FEATURES,
    HEARTGUARD_FEATURES,
    VALIDATION_BOUNDS,
)
from src.nlp.lifestyle_analyzer import MAX_INPUT_CHARACTERS


def validate_clinical_risk(risk: float) -> float:
    """Ensure clinical risk score is a finite number between 0 and 100.

    Args:
        risk: Numerical clinical risk percentage.

    Returns:
        float: Validated risk score.

    Raises:
        ValueError: If risk is NaN, infinite, or outside [0, 100].
    """
    if risk is None or not isinstance(risk, (int, float)) or math.isnan(risk) or math.isinf(risk):
        raise ValueError(f"Clinical risk must be a valid finite number, got {risk}")
    if risk < 0.0 or risk > 100.0:
        raise ValueError(f"Clinical risk must be between 0 and 100, got {risk}")
    return float(risk)


def validate_lifestyle_risk(risk: float) -> float:
    """Ensure lifestyle risk score is a finite number between 0 and 100.

    Args:
        risk: Numerical lifestyle risk score.

    Returns:
        float: Validated risk score.

    Raises:
        ValueError: If risk is NaN, infinite, or outside [0, 100].
    """
    if risk is None or not isinstance(risk, (int, float)) or math.isnan(risk) or math.isinf(risk):
        raise ValueError(f"Lifestyle risk must be a valid finite number, got {risk}")
    if risk < 0.0 or risk > 100.0:
        raise ValueError(f"Lifestyle risk must be between 0 and 100, got {risk}")
    return float(risk)


def validate_overall_risk(risk: float) -> float:
    """Ensure calculated overall multimodal risk score is between 0 and 100.

    Args:
        risk: Numerical overall risk percentage.

    Returns:
        float: Validated risk score.

    Raises:
        ValueError: If risk is NaN, infinite, or outside [0, 100].
    """
    if risk is None or not isinstance(risk, (int, float)) or math.isnan(risk) or math.isinf(risk):
        raise ValueError(f"Overall risk must be a valid finite number, got {risk}")
    if risk < 0.0 or risk > 100.0:
        raise ValueError(f"Overall risk must be between 0 and 100, got {risk}")
    return float(risk)


def validate_weights(
    clinical_weight: float = 0.70,
    lifestyle_weight: float = 0.30,
) -> None:
    """Ensure multimodal weights are valid, non-negative, and sum to 1.0.

    Args:
        clinical_weight: Weight for clinical ML risk (default: 0.70).
        lifestyle_weight: Weight for lifestyle risk (default: 0.30).

    Raises:
        ValueError: If either weight is < 0 or > 1, or their sum != 1.0.
    """
    if not (0.0 <= clinical_weight <= 1.0):
        raise ValueError(f"Clinical weight must be between 0 and 1, got {clinical_weight}")
    if not (0.0 <= lifestyle_weight <= 1.0):
        raise ValueError(f"Lifestyle weight must be between 0 and 1, got {lifestyle_weight}")

    weight_sum = clinical_weight + lifestyle_weight
    if not math.isclose(weight_sum, 1.0, rel_tol=1e-5, abs_tol=1e-5):
        raise ValueError(
            f"Multimodal weights must sum to 1.0, got {weight_sum} "
            f"(clinical={clinical_weight}, lifestyle={lifestyle_weight})"
        )


def validate_clinical_input(
    clinical_data: dict[str, Any] | pd.DataFrame,
) -> dict[str, Any]:
    """Validate structured patient clinical features against the canonical schema.

    Args:
        clinical_data: Dictionary or single-row DataFrame of patient features.

    Returns:
        dict[str, Any]: Cleaned canonical dictionary of clinical features.

    Raises:
        ValueError: If required fields are missing, non-numeric, or outside valid ranges.
    """
    if clinical_data is None:
        raise ValueError("Complete the required clinical information before performing the multimodal assessment.")

    if isinstance(clinical_data, pd.DataFrame):
        if len(clinical_data) == 0:
            raise ValueError("Complete the required clinical information before performing the multimodal assessment.")
        data_dict = clinical_data.iloc[0].to_dict()
    elif isinstance(clinical_data, dict):
        data_dict = dict(clinical_data)
    else:
        raise ValueError(f"Clinical data must be a dict or DataFrame, got {type(clinical_data)}")

    # Check for missing required features
    missing_fields = [f for f in HEARTGUARD_FEATURES if f not in data_dict or data_dict[f] is None]
    if missing_fields:
        raise ValueError(
            f"Complete the required clinical information before performing the multimodal assessment. "
            f"Missing fields: {', '.join(missing_fields)}"
        )

    validated_dict: dict[str, Any] = {}
    for feat in HEARTGUARD_FEATURES:
        val = data_dict[feat]
        try:
            num_val = float(val)
        except (ValueError, TypeError):
            raise ValueError(f"Clinical feature '{feat}' must be a numerical value, got '{val}'")

        if math.isnan(num_val) or math.isinf(num_val):
            raise ValueError(f"Clinical feature '{feat}' cannot be NaN or infinite")

        # Range bounds validation
        if feat in VALIDATION_BOUNDS:
            min_val, max_val = VALIDATION_BOUNDS[feat]
            if num_val < min_val or num_val > max_val:
                raise ValueError(
                    f"Clinical feature '{feat}' value {num_val} is outside physiological range "
                    f"[{min_val}, {max_val}]"
                )

        # Binary features validation
        if feat in BINARY_FEATURES:
            if num_val not in (0.0, 1.0):
                raise ValueError(f"Binary clinical feature '{feat}' must be 0 or 1, got {num_val}")

        validated_dict[feat] = num_val

    return validated_dict


def validate_lifestyle_input(lifestyle_text: str | None) -> str:
    """Validate patient free-text lifestyle narrative.

    Args:
        lifestyle_text: Free-text string describing daily habits.

    Returns:
        str: Cleaned stripped string.

    Raises:
        ValueError: If input is None, empty, or exceeds character limit.
    """
    if lifestyle_text is None or not str(lifestyle_text).strip():
        raise ValueError("Lifestyle description is required for multimodal assessment.")

    cleaned = str(lifestyle_text).strip()
    if len(cleaned) > MAX_INPUT_CHARACTERS:
        raise ValueError(
            f"Lifestyle description exceeds maximum allowed limit of {MAX_INPUT_CHARACTERS:,} characters "
            f"(received {len(cleaned):,} characters)."
        )

    return cleaned
