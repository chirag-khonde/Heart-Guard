"""Utility functions for report generation and safe data export (Phase 10).

Includes safe filename generation to prevent path traversal, temporary file management,
and CSV export with formula injection mitigation.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
import re

from src.analytics.history_service import HistoryService


def sanitize_report_filename(assessment_id: str) -> str:
    """Generate a safe, path-traversal-free filename for a PDF report.

    Args:
        assessment_id: Raw assessment identifier.

    Returns:
        Safe filename string (e.g. 'HeartGuard_Assessment_a1b2c3d4.pdf').
    """
    cleaned_id = re.sub(r"[^a-zA-Z0-9_\-]", "", str(assessment_id).strip())
    if not cleaned_id:
        cleaned_id = "unknown"
    return f"HeartGuard_Assessment_{cleaned_id}.pdf"


def _sanitize_csv_cell(value: str) -> str:
    """Sanitize a cell value to prevent CSV formula injection in spreadsheet applications.

    If a string starts with '=', '+', '-', or '@', prepend a single quote to force text rendering.
    """
    val_str = str(value)
    if val_str and val_str[0] in ("=", "+", "-", "@"):
        return f"'{val_str}"
    return val_str


def export_assessments_to_csv(
    user_id: int,
    db_path: Path | None = None,
) -> str:
    """Export the authenticated patient's assessment history to CSV.

    Guarantees:
      - Strictly includes records belonging to user_id.
      - Never includes passwords, tokens, Twilio credentials, or raw lifestyle text.
      - Neutralizes potential spreadsheet formula injection vectors.

    Args:
        user_id: Authenticated user ID.
        db_path: SQLite DB path override.

    Returns:
        CSV content as string.
    """
    assessments = HistoryService.get_user_assessments(
        user_id=user_id, sort_order="desc", limit=None, db_path=db_path
    )

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header row
    headers = [
        "Assessment Date",
        "Assessment ID",
        "Clinical Risk (%)",
        "Lifestyle Risk (%)",
        "Overall Risk (%)",
        "Risk Category",
        "Recommendation",
        "Alert Status",
    ]
    writer.writerow(headers)

    for a in assessments:
        row = [
            _sanitize_csv_cell(a.created_at[:10]),
            _sanitize_csv_cell(a.assessment_id),
            _sanitize_csv_cell(f"{a.clinical_risk:.1f}"),
            _sanitize_csv_cell(f"{a.lifestyle_risk:.1f}"),
            _sanitize_csv_cell(f"{a.overall_risk:.1f}"),
            _sanitize_csv_cell(a.risk_category),
            _sanitize_csv_cell(a.recommendation),
            _sanitize_csv_cell(a.alert_status),
        ]
        writer.writerow(row)

    return output.getvalue()
