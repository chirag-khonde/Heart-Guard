"""Tests for configuration and utilities."""

import pytest

from config.settings import (
    CLINICAL_WEIGHT,
    LIFESTYLE_WEIGHT,
    PROJECT_NAME,
    PROJECT_VERSION,
    RISK_THRESHOLD_CRITICAL,
    RISK_THRESHOLD_HIGH,
    RISK_THRESHOLD_LOW,
    RISK_THRESHOLD_MODERATE,
)


def test_project_name():
    """Test project name constant."""
    assert PROJECT_NAME == "HeartGuard"


def test_project_version():
    """Test project version constant."""
    assert PROJECT_VERSION == "1.0.0"


def test_clinical_weight():
    """Test clinical weight constant."""
    assert CLINICAL_WEIGHT == 0.70


def test_lifestyle_weight():
    """Test lifestyle weight constant."""
    assert LIFESTYLE_WEIGHT == 0.30


def test_risk_thresholds():
    """Test risk threshold constants."""
    assert RISK_THRESHOLD_LOW == 60
    assert RISK_THRESHOLD_MODERATE == 75
    assert RISK_THRESHOLD_HIGH == 85
    assert RISK_THRESHOLD_CRITICAL == 85


def test_validate_age_valid():
    """Test validate_age with valid age."""
    from src.utils.validators import validate_age

    assert validate_age(25) == 25
    assert validate_age("30") == 30
    assert validate_age(0) == 0
    assert validate_age(150) == 150


def test_validate_age_invalid():
    """Test validate_age with invalid age."""
    from src.utils.validators import validate_age

    with pytest.raises(ValueError, match="must be a number"):
        validate_age("abc")

    with pytest.raises(ValueError, match="must be between 0 and 150"):
        validate_age(-1)

    with pytest.raises(ValueError, match="must be between 0 and 150"):
        validate_age(151)


def test_validate_positive_number_valid():
    """Test validate_positive_number with valid values."""
    from src.utils.validators import validate_positive_number

    assert validate_positive_number(10, "test") == 10.0
    assert validate_positive_number("5.5", "test") == 5.5
    assert validate_positive_number(0, "test") == 0.0


def test_validate_positive_number_invalid():
    """Test validate_positive_number with invalid values."""
    from src.utils.validators import validate_positive_number

    with pytest.raises(ValueError, match="must be a number"):
        validate_positive_number("abc", "test")

    with pytest.raises(ValueError, match="must be positive"):
        validate_positive_number(-1, "test")


def test_validate_required_text_valid():
    """Test validate_required_text with valid text."""
    from src.utils.validators import validate_required_text

    assert validate_required_text("hello", "test") == "hello"
    assert validate_required_text("  hello  ", "test") == "hello"


def test_validate_required_text_invalid():
    """Test validate_required_text with invalid text."""
    from src.utils.validators import validate_required_text

    with pytest.raises(ValueError, match="is required"):
        validate_required_text(None, "test")

    with pytest.raises(ValueError, match="cannot be empty"):
        validate_required_text("", "test")

    with pytest.raises(ValueError, match="cannot be empty"):
        validate_required_text("   ", "test")


def test_logger_importable():
    """Test that logger module can be imported."""
    from src.utils.logger import get_logger, log_error, log_info, log_warning

    logger = get_logger("test")
    assert logger is not None
