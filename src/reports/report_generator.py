"""Report generator for HeartGuard AI Risk Assessment reports (Phase 10).

Builds professional multi-page PDF documents using ReportLab.
Enforces patient data isolation before generation, formats multimodal risk components,
embeds historical trend charts, and incorporates standard medical disclaimers.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.analytics.history_service import HistoryService
from src.analytics.models import Assessment
from src.analytics.trend_service import TrendService
from src.recommendations.recommendation_service import RecommendationService
from src.reports.report_templates import (
    APPOINT_COLOR,
    BG_LIGHT,
    BORDER_COLOR,
    CRITICAL_COLOR,
    CRITICAL_WARNING,
    MONITOR_COLOR,
    NumberedCanvas,
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    STANDARD_DISCLAIMER,
    TEXT_DARK,
    TEXT_MUTED,
    get_report_styles,
)


def _render_trend_chart_to_image(trends: list[dict[str, Any]]) -> io.BytesIO | None:
    """Render a risk trend chart using matplotlib and return as in-memory PNG."""
    if len(trends) < 2:
        return None

    dates = [t["date"] for t in trends]
    overall = [t["overall_risk"] for t in trends]
    clinical = [t["clinical_risk"] for t in trends]
    lifestyle = [t["lifestyle_risk"] for t in trends]

    fig, ax = plt.subplots(figsize=(6.2, 2.4), dpi=150)
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#ffffff")

    ax.plot(dates, overall, marker="o", color="#1e3a8a", linewidth=2.2, label="Overall Risk (70/30)")
    ax.plot(dates, clinical, marker="s", color="#0284c7", linewidth=1.5, linestyle="--", label="Clinical Risk (70%)")
    ax.plot(dates, lifestyle, marker="^", color="#d97706", linewidth=1.5, linestyle=":", label="Lifestyle Risk (30%)")

    ax.set_title("Cardiovascular Risk Trajectory Over Time", fontsize=10, fontweight="bold", color="#1e293b", pad=8)
    ax.set_xlabel("Assessment Date", fontsize=8, color="#64748b")
    ax.set_ylabel("Risk Score (%)", fontsize=8, color="#64748b")
    ax.set_ylim(0, 105)
    ax.grid(True, linestyle="--", alpha=0.4, color="#cbd5e1")
    ax.tick_params(axis="both", labelsize=7, colors="#475569")
    ax.legend(loc="upper left", fontsize=7, framealpha=0.9)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


class ReportGenerator:
    """Generates structured PDF assessment reports for authenticated patients."""

    @staticmethod
    def generate_assessment_report(
        assessment_id: str,
        user_id: int,
        db_path: Path | None = None,
    ) -> bytes:
        """Generate a complete PDF report for a patient assessment.

        Args:
            assessment_id: Assessment unique identifier.
            user_id: Authenticated user ID (must own the assessment).
            db_path: SQLite DB path override.

        Returns:
            bytes: Compiled PDF data.

        Raises:
            PermissionError: If the assessment does not belong to the user.
            ValueError: If the assessment cannot be found.
        """
        # 1. Authorization check at the service boundary
        if not HistoryService.user_owns_assessment(user_id, assessment_id, db_path=db_path):
            raise PermissionError("Access denied: You do not own this assessment record.")

        assessment = HistoryService.get_assessment_by_id(assessment_id, user_id=user_id, db_path=db_path)
        if assessment is None:
            raise ValueError(f"Assessment '{assessment_id}' not found.")

        # Historical context
        all_user_assessments = HistoryService.get_user_assessments(
            user_id=user_id, sort_order="desc", limit=None, db_path=db_path
        )
        previous_assessment = None
        for idx, a in enumerate(all_user_assessments):
            if a.assessment_id == assessment_id and idx + 1 < len(all_user_assessments):
                previous_assessment = all_user_assessments[idx + 1]
                break

        trends = TrendService.get_risk_trends(user_id=user_id, db_path=db_path)
        comparison = TrendService.compare_assessments(assessment, previous_assessment)

        # 2. Build Document
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = get_report_styles()
        story: list[Any] = []

        # ===================================================================
        # PAGE 1: Executive Summary & Overview
        # ===================================================================
        story.append(Paragraph("HEARTGUARD", styles["Title"]))
        story.append(Paragraph("AI-Based Heart Disease Risk Assessment Report · Academic / Research Prototype", styles["Subtitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceAfter=14))

        # Metadata Table
        meta_data = [
            [
                Paragraph("Assessment ID", styles["MetaLabel"]),
                Paragraph(f"<code>{assessment.assessment_id}</code>", styles["MetaValue"]),
                Paragraph("Assessment Date", styles["MetaLabel"]),
                Paragraph(assessment.created_at[:19].replace("T", " "), styles["MetaValue"]),
            ],
            [
                Paragraph("Patient ID", styles["MetaLabel"]),
                Paragraph(f"UID-{assessment.user_id:04d}", styles["MetaValue"]),
                Paragraph("Model Version", styles["MetaLabel"]),
                Paragraph(assessment.model_version, styles["MetaValue"]),
            ],
            [
                Paragraph("Alert Status", styles["MetaLabel"]),
                Paragraph(assessment.alert_status, styles["MetaValue"]),
                Paragraph("Evaluation Type", styles["MetaLabel"]),
                Paragraph("Multimodal (70% ML + 30% NLP)", styles["MetaValue"]),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[1.3 * inch, 1.7 * inch, 1.3 * inch, 2.2 * inch])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # Overall Risk Callout
        is_crit = "CRITICAL" in assessment.risk_category.upper()
        is_appoint = "APPOINTMENT" in assessment.risk_category.upper() or "ELEVATED" in assessment.risk_category.upper()
        cat_color = CRITICAL_COLOR if is_crit else (APPOINT_COLOR if is_appoint else MONITOR_COLOR)

        risk_callout_data = [
            [
                Paragraph(
                    f"<font size='26' color='{cat_color.hexval()}'><b>{assessment.overall_risk:.1f}%</b></font><br/>"
                    f"<font size='9' color='{TEXT_MUTED.hexval()}'>OVERALL MULTIMODAL RISK SCORE</font>",
                    styles["BodyBold"],
                ),
                Paragraph(
                    f"<font size='13' color='{cat_color.hexval()}'><b>{assessment.risk_category}</b></font><br/><br/>"
                    f"<b>Recommended Action:</b><br/>{assessment.recommendation}",
                    styles["Body"],
                ),
            ]
        ]
        risk_table = Table(risk_callout_data, colWidths=[2.5 * inch, 4.0 * inch])
        risk_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 1.5, cat_color),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.append(risk_table)
        story.append(Spacer(1, 14))

        # Narrative Summary
        if assessment.narrative_summary:
            story.append(Paragraph("Assessment Narrative", styles["Heading2"]))
            story.append(Paragraph(assessment.narrative_summary, styles["Body"]))

        story.append(PageBreak())

        # ===================================================================
        # PAGE 2: Component Breakdown & Explainability
        # ===================================================================
        story.append(Paragraph("Risk Components & Explainability", styles["Heading1"]))
        story.append(Paragraph("HeartGuard decomposes cardiovascular risk into objective clinical measurements and qualitative lifestyle habits.", styles["Body"]))
        story.append(Spacer(1, 8))

        # Breakdown Table
        clin_contrib = round(assessment.clinical_risk * 0.70, 2)
        life_contrib = round(assessment.lifestyle_risk * 0.30, 2)
        comp_data = [
            ["Modality", "Raw Score", "Weight", "Weighted Contribution"],
            ["Clinical ML (Physiological Metrics)", f"{assessment.clinical_risk:.1f}%", "70%", f"+{clin_contrib:.2f} pts"],
            ["Lifestyle NLP (Habits & Narratives)", f"{assessment.lifestyle_risk:.1f}%", "30%", f"+{life_contrib:.2f} pts"],
            ["Overall Combined Risk", f"{assessment.overall_risk:.1f}%", "100%", f"{assessment.overall_risk:.2f} pts"],
        ]
        comp_table = Table(comp_data, colWidths=[2.8 * inch, 1.2 * inch, 1.0 * inch, 1.5 * inch])
        comp_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("BACKGROUND", (0, 1), (-1, -1), BG_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(comp_table)
        story.append(Spacer(1, 14))

        # Top Clinical Risk Drivers (SHAP)
        story.append(Paragraph("Top Clinical Risk Drivers (SHAP Analysis)", styles["Heading2"]))
        top_factors = assessment.get_top_clinical_factors()
        if top_factors:
            shap_data = [["Rank", "Clinical Parameter", "SHAP Impact Score"]]
            for rk, tf in enumerate(top_factors[:5], 1):
                label = tf.get("clinical_label") or tf.get("feature", "Clinical Feature")
                val = tf.get("shap_value", 0.0)
                shap_data.append([str(rk), str(label), f"+{val:.4f}"])

            shap_table = Table(shap_data, colWidths=[0.8 * inch, 3.7 * inch, 2.0 * inch])
            shap_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY_COLOR),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                        ("BACKGROUND", (0, 1), (-1, -1), BG_LIGHT),
                        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(shap_table)
        else:
            story.append(Paragraph("<i>Explainability details are available only for assessments where SHAP results were stored.</i>", styles["Disclaimer"]))

        story.append(Spacer(1, 12))

        # Detected Lifestyle Signals
        story.append(Paragraph("Detected Lifestyle Signals", styles["Heading2"]))
        life_factors = assessment.get_lifestyle_factors()
        if life_factors:
            lf_data = [["Factor", "Severity", "Risk Impact"]]
            for lf in life_factors[:5]:
                lf_data.append([
                    str(lf.get("display_name", "Factor")),
                    str(lf.get("severity", "MODERATE")).upper(),
                    f"+{lf.get('risk_points', 0)} pts",
                ])
            lf_table = Table(lf_data, colWidths=[3.5 * inch, 1.5 * inch, 1.5 * inch])
            lf_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY_COLOR),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                        ("BACKGROUND", (0, 1), (-1, -1), BG_LIGHT),
                        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(lf_table)
        else:
            story.append(Paragraph("<i>No specific predefined lifestyle risk factors were flagged in this assessment.</i>", styles["Disclaimer"]))

        story.append(PageBreak())

        # ===================================================================
        # PAGE 3: Historical Context & Trend Trajectory
        # ===================================================================
        story.append(Paragraph("Historical Context & Risk Trajectory", styles["Heading1"]))
        story.append(Paragraph("Evaluation of how model predictions compare against prior assessments.", styles["Body"]))
        story.append(Spacer(1, 8))

        if comparison:
            story.append(Paragraph("Latest vs Previous Assessment Comparison", styles["Heading2"]))
            comp_metrics = [
                ["Metric", "Previous Assessment", "Current Assessment", "Change"],
                [
                    "Overall Risk",
                    f"{comparison['overall_risk']['previous']:.1f}%",
                    f"{comparison['overall_risk']['latest']:.1f}%",
                    comparison['overall_risk']['delta_str'],
                ],
                [
                    "Clinical Risk (70%)",
                    f"{comparison['clinical_risk']['previous']:.1f}%",
                    f"{comparison['clinical_risk']['latest']:.1f}%",
                    comparison['clinical_risk']['delta_str'],
                ],
                [
                    "Lifestyle Risk (30%)",
                    f"{comparison['lifestyle_risk']['previous']:.1f}%",
                    f"{comparison['lifestyle_risk']['latest']:.1f}%",
                    comparison['lifestyle_risk']['delta_str'],
                ],
                [
                    "Risk Category",
                    comparison['category']['previous'],
                    comparison['category']['latest'],
                    "Changed" if comparison['category']['changed'] else "Unchanged",
                ],
            ]
            c_table = Table(comp_metrics, colWidths=[2.2 * inch, 1.4 * inch, 1.4 * inch, 1.5 * inch])
            c_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                        ("BACKGROUND", (0, 1), (-1, -1), BG_LIGHT),
                        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(c_table)
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"<b>Trend Interpretation:</b> {comparison['interpretation']}", styles["Body"]))
            story.append(Paragraph(comparison["disclaimer"], styles["Disclaimer"]))
            story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("<i>Single assessment record available — comparative change metrics require at least two historical assessments.</i>", styles["Disclaimer"]))
            story.append(Spacer(1, 10))

        # Trajectory Plot
        chart_buf = _render_trend_chart_to_image(trends)
        if chart_buf is not None:
            story.append(Paragraph("Risk Trend Trajectory", styles["Heading2"]))
            story.append(Image(chart_buf, width=6.2 * inch, height=2.4 * inch))
        else:
            story.append(Paragraph("<b>Risk Trend Trajectory:</b> Insufficient historical data for trend analysis. (Minimum 2 assessments required).", styles["Body"]))

        story.append(PageBreak())

        # ===================================================================
        # PAGE 4: AI Insights & Personalized Recommendations (Phase 13)
        # ===================================================================
        story.append(Paragraph("AI Insights & Personalized Recommendations", styles["Heading1"]))
        story.append(Paragraph("Explainable, action-oriented guidance derived deterministically from your multimodal assessment data.", styles["Body"]))
        story.append(Spacer(1, 8))

        # Retrieve or compute assessment insights
        try:
            insights = RecommendationService.get_or_create_insights(assessment_id, user_id=user_id)
        except Exception:
            insights = None

        if insights:
            # Assessment Summary Box
            story.append(Paragraph("Personalized Assessment Summary", styles["Heading2"]))
            story.append(Paragraph(f"<i>{insights.summary_text}</i>", styles["Body"]))
            story.append(Spacer(1, 6))

            # Top Model Factors
            if insights.top_factors:
                story.append(Paragraph("Top Model Contributors (Explainability)", styles["Heading2"]))
                factor_items = "<br/>".join([f"• <b>{f['feature']}:</b> {f['description']}" for f in insights.top_factors[:4]])
                story.append(Paragraph(factor_items, styles["Body"]))
                story.append(Spacer(1, 8))

            # Actionable Recommendations Table
            if insights.recommendations:
                story.append(Paragraph("Personalized Recommendations", styles["Heading2"]))
                rec_rows = [["Priority", "Category", "Recommended Guidance"]]
                for rec in insights.recommendations[:6]:
                    guidance_p = Paragraph(f"<b>{rec.title}</b><br/>{rec.description}", styles["Body"])
                    rec_rows.append([rec.priority, rec.category, guidance_p])

                rec_table = Table(rec_rows, colWidths=[1.1 * inch, 1.8 * inch, 3.6 * inch])
                rec_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                            ("BACKGROUND", (0, 1), (-1, -1), BG_LIGHT),
                            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                story.append(rec_table)
            else:
                story.append(Paragraph("<i>No personalized recommendations are available for this assessment.</i>", styles["Disclaimer"]))
        else:
            story.append(Paragraph("<i>Insights are currently unavailable for this assessment.</i>", styles["Disclaimer"]))

        story.append(Spacer(1, 8))
        story.append(Paragraph("<b>Notice:</b> These AI-generated insights are informational and are not a medical diagnosis or treatment plan.", styles["Disclaimer"]))

        story.append(PageBreak())

        # ===================================================================
        # PAGE 5: Alert Information & Medical Disclaimers
        # ===================================================================
        story.append(Paragraph("Alert Information & Disclaimers", styles["Heading1"]))
        story.append(Spacer(1, 8))

        # Alert Box
        alert_info_data = [
            [
                Paragraph("Alert Dispatch Status", styles["MetaLabel"]),
                Paragraph(f"<b>{assessment.alert_status}</b>", styles["Body"]),
            ],
            [
                Paragraph("Privacy Protection", styles["MetaLabel"]),
                Paragraph("Recipient phone numbers are masked in all audit trails and reports (e.g. +1*****4567) to ensure patient confidentiality.", styles["Body"]),
            ],
            [
                Paragraph("Notification Note", styles["MetaLabel"]),
                Paragraph("Emergency alerts are triggered strictly when overall risk exceeds the critical threshold (> 85%).", styles["Body"]),
            ],
        ]
        alert_table = Table(alert_info_data, colWidths=[2.0 * inch, 4.5 * inch])
        alert_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(alert_table)
        story.append(Spacer(1, 16))

        # Emergency Banner if Critical
        if is_crit:
            story.append(Paragraph("CRITICAL CARDIOVASCULAR RISK DETECTED", styles["CriticalAlert"]))
            story.append(Paragraph(CRITICAL_WARNING, styles["CriticalAlert"]))
            story.append(Spacer(1, 10))

        # Standard Medical Disclaimer Box
        story.append(Paragraph("Medical & Research Disclaimers", styles["Heading2"]))
        disc_text = (
            f"<b>Academic & Research Prototype Notice:</b><br/>"
            f"{STANDARD_DISCLAIMER}<br/><br/>"
            f"<b>Risk Score Interpretation:</b><br/>"
            f"Changes in HeartGuard risk scores represent changes in the model's assessment "
            f"inputs and outputs. They do not by themselves establish a medical diagnosis or disease progression. "
            f"HeartGuard does not make clinical diagnoses, prescribe medication, or formulate treatment plans. "
            f"Always seek the counsel of a physician or other qualified health provider with any questions "
            f"regarding a medical condition."
        )
        disc_box = Table([[Paragraph(disc_text, styles["Body"])]], colWidths=[6.5 * inch])
        disc_box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.append(disc_box)

        # Build document with NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer.getvalue()
