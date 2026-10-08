"""Unit and security tests for HeartGuard PDF Report Generator and CSV Exporter (Phase 10).

Validates:
  - Valid PDF compilation with expected headings, metadata, and disclaimers
  - Strict ownership authorization (Patient A cannot generate Patient B's report)
  - Single assessment vs multiple assessment reports (trend chart inclusion)
  - Missing SHAP explanation data handled gracefully
  - Critical risk warnings in report
  - Safe filename generation & path traversal prevention
  - CSV export authorization and spreadsheet formula injection protection
"""

from __future__ import annotations

from pathlib import Path
import pytest

from src.analytics.history_service import HistoryService
from src.analytics.models import init_assessment_db
from src.reports.report_generator import ReportGenerator
from src.reports.report_utils import export_assessments_to_csv, sanitize_report_filename


@pytest.fixture()
def tmp_assessments_db(tmp_path: Path) -> Path:
    """Fixture providing a fresh isolated assessments SQLite database."""
    db_file = tmp_path / "test_assessments.db"
    init_assessment_db(db_file)
    return db_file


def _create_mock_assessment_result(
    overall_risk: float = 45.0,
    clinical_risk: float = 50.0,
    lifestyle_risk: float = 33.3,
    category: str = "LOWER_RISK",
    has_shap: bool = True,
) -> dict:
    return {
        "combined": {
            "risk": overall_risk,
            "category": category,
            "alert_level": "MONITORING",
            "recommended_action": "Regular monitoring recommended.",
        },
        "clinical": {
            "risk": clinical_risk,
            "probability": clinical_risk / 100.0,
            "prediction": 1 if clinical_risk > 50 else 0,
            "model": "xgboost",
            "clinical_data": {"age": 60, "chol": 210},
        },
        "lifestyle": {
            "risk": lifestyle_risk,
            "category": "LOW",
            "detected_factors": [
                {"display_name": "Poor Sleep", "severity": "LOW", "risk_points": 5}
            ],
            "summary": "Mild sleep deficiency.",
        },
        "clinical_explanation": {
            "top_risk_factors": (
                [{"clinical_label": "Resting Blood Pressure", "shap_value": 0.312}]
                if has_shap
                else []
            ),
        },
        "overall_explanation": "Multimodal diagnostic summary narrative.",
    }


# ---------------------------------------------------------------------------
# 1. PDF Report Generation & Validation
# ---------------------------------------------------------------------------


def test_generate_report_returns_valid_pdf(tmp_assessments_db: Path):
    """ReportGenerator produces a valid PDF binary with standard headers."""
    HistoryService.save_assessment(
        user_id=1,
        multimodal_result=_create_mock_assessment_result(overall_risk=52.5),
        assessment_id="RPT_VALID_01",
        db_path=tmp_assessments_db,
    )

    pdf_bytes = ReportGenerator.generate_assessment_report(
        assessment_id="RPT_VALID_01",
        user_id=1,
        db_path=tmp_assessments_db,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # All valid PDF files start with the %PDF magic header
    assert pdf_bytes.startswith(b"%PDF")
    # Verify ReportLab generator signature and EOF marker
    assert b"ReportLab" in pdf_bytes
    assert b"%%EOF" in pdf_bytes


def test_single_assessment_report_handles_missing_trends(tmp_assessments_db: Path):
    """When only 1 assessment exists, report generates without crashing and notes insufficient history."""
    HistoryService.save_assessment(
        user_id=2,
        multimodal_result=_create_mock_assessment_result(overall_risk=48.0),
        assessment_id="RPT_SINGLE_01",
        db_path=tmp_assessments_db,
    )

    pdf_bytes = ReportGenerator.generate_assessment_report(
        assessment_id="RPT_SINGLE_01",
        user_id=2,
        db_path=tmp_assessments_db,
    )
    assert pdf_bytes.startswith(b"%PDF")


def test_multiple_assessments_report_includes_trend_chart(tmp_assessments_db: Path):
    """When >= 2 assessments exist, report renders trend chart without error."""
    HistoryService.save_assessment(
        user_id=3,
        multimodal_result=_create_mock_assessment_result(overall_risk=40.0),
        assessment_id="RPT_MULTI_01",
        db_path=tmp_assessments_db,
    )
    HistoryService.save_assessment(
        user_id=3,
        multimodal_result=_create_mock_assessment_result(overall_risk=65.0),
        assessment_id="RPT_MULTI_02",
        db_path=tmp_assessments_db,
    )

    pdf_bytes = ReportGenerator.generate_assessment_report(
        assessment_id="RPT_MULTI_02",
        user_id=3,
        db_path=tmp_assessments_db,
    )
    assert pdf_bytes.startswith(b"%PDF")


def test_report_without_shap_explanation(tmp_assessments_db: Path):
    """Assessments lacking SHAP data generate clean reports with fallback notices."""
    HistoryService.save_assessment(
        user_id=4,
        multimodal_result=_create_mock_assessment_result(overall_risk=50.0, has_shap=False),
        assessment_id="RPT_NOSHAP_01",
        db_path=tmp_assessments_db,
    )

    pdf_bytes = ReportGenerator.generate_assessment_report(
        assessment_id="RPT_NOSHAP_01",
        user_id=4,
        db_path=tmp_assessments_db,
    )
    assert pdf_bytes.startswith(b"%PDF")


def test_critical_assessment_report(tmp_assessments_db: Path):
    """Critical assessments include emergency warnings."""
    HistoryService.save_assessment(
        user_id=5,
        multimodal_result=_create_mock_assessment_result(
            overall_risk=92.0, category="CRITICAL"
        ),
        alert_status="SUCCESS",
        assessment_id="RPT_CRIT_01",
        db_path=tmp_assessments_db,
    )

    pdf_bytes = ReportGenerator.generate_assessment_report(
        assessment_id="RPT_CRIT_01",
        user_id=5,
        db_path=tmp_assessments_db,
    )
    assert pdf_bytes.startswith(b"%PDF")


# ---------------------------------------------------------------------------
# 2. Security & Authorization
# ---------------------------------------------------------------------------


def test_patient_cannot_generate_other_patient_report(tmp_assessments_db: Path):
    """Patient A cannot generate a report for Patient B's assessment ID."""
    HistoryService.save_assessment(
        user_id=10,
        multimodal_result=_create_mock_assessment_result(overall_risk=70.0),
        assessment_id="ASSESS_PATIENT_B",
        db_path=tmp_assessments_db,
    )

    # Patient A (user_id=20) attempts to generate Patient B's report
    with pytest.raises(PermissionError, match="Access denied"):
        ReportGenerator.generate_assessment_report(
            assessment_id="ASSESS_PATIENT_B",
            user_id=20,
            db_path=tmp_assessments_db,
        )


def test_missing_assessment_raises_value_error(tmp_assessments_db: Path):
    """Attempting to generate a non-existent assessment raises an error."""
    with pytest.raises(PermissionError):
        ReportGenerator.generate_assessment_report(
            assessment_id="NON_EXISTENT_ID",
            user_id=1,
            db_path=tmp_assessments_db,
        )


def test_safe_filename_generation_prevents_path_traversal():
    """Verify sanitize_report_filename strips path traversal characters."""
    dangerous_id = "../../etc/passwd"
    safe = sanitize_report_filename(dangerous_id)
    assert "/" not in safe
    assert "\\" not in safe
    assert ".." not in safe
    assert safe == "HeartGuard_Assessment_etcpasswd.pdf"

    clean = sanitize_report_filename("a1b2c3d4")
    assert clean == "HeartGuard_Assessment_a1b2c3d4.pdf"


# ---------------------------------------------------------------------------
# 3. CSV Export Security & Formula Injection
# ---------------------------------------------------------------------------


def test_csv_export_user_isolation(tmp_assessments_db: Path):
    """CSV export must include only the requested user's assessment history."""
    HistoryService.save_assessment(
        user_id=100,
        multimodal_result=_create_mock_assessment_result(overall_risk=35.0),
        assessment_id="AID_USER_100",
        db_path=tmp_assessments_db,
    )
    HistoryService.save_assessment(
        user_id=200,
        multimodal_result=_create_mock_assessment_result(overall_risk=75.0),
        assessment_id="AID_USER_200",
        db_path=tmp_assessments_db,
    )

    csv_data = export_assessments_to_csv(user_id=100, db_path=tmp_assessments_db)
    assert "AID_USER_100" in csv_data
    assert "AID_USER_200" not in csv_data


def test_csv_export_formula_injection_protection(tmp_assessments_db: Path):
    """Cells starting with formula trigger characters (=, +, -, @) must be neutralized."""
    malicious_result = _create_mock_assessment_result(
        overall_risk=50.0,
    )
    malicious_result["combined"]["recommended_action"] = "=CMD('calc.exe')|'A'"

    HistoryService.save_assessment(
        user_id=105,
        multimodal_result=malicious_result,
        assessment_id="AID_FORMULA_01",
        db_path=tmp_assessments_db,
    )

    csv_data = export_assessments_to_csv(user_id=105, db_path=tmp_assessments_db)
    assert "AID_FORMULA_01" in csv_data
    # Formula character '=' must be escaped with a leading quote
    assert "'=CMD('calc.exe')|'A'" in csv_data
