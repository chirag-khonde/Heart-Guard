"""Deterministic rule library for HeartGuard AI Recommendations (Phase 13).

Provides rule definitions that evaluate verified project data fields:
  - Lifestyle factors: smoking, physical inactivity, diet, sleep, alcohol, family history
  - Clinical data & SHAP drivers: blood pressure, cholesterol, fasting blood sugar
  - Multimodal risk tiers: CRITICAL, ELEVATED, LOW
  - Longitudinal trend deltas: INCREASING, DECREASING

SAFETY INVARIANTS:
  - All rule outputs are strictly non-diagnostic ("Consider...", "Discuss with...").
  - No drug names, dosages, or medical prescriptions are permitted.
"""

from __future__ import annotations

from typing import Any, Callable
from src.recommendations.recommendation_models import (
    PRIORITY_HIGH,
    PRIORITY_INFO,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
)

# Rule definition structure
RuleMatch = dict[str, Any]


def rule_smoking(factors: list[dict[str, Any]], clinical: dict[str, Any]) -> RuleMatch | None:
    for f in factors:
        name = str(f.get("display_name", f.get("category", ""))).lower()
        if "smoke" in name or "smoking" in name:
            return {
                "rule_id": "SMOKING_CESSATION_SUPPORT",
                "category": "Smoking",
                "title": "Consider exploring smoking cessation support",
                "description": (
                    "Smoking and tobacco use was identified as an elevated lifestyle risk factor in your "
                    "assessment. Consider speaking with a healthcare professional about evidence-based "
                    "cessation strategies and community health resources."
                ),
                "priority": PRIORITY_HIGH,
                "source": "Lifestyle Data",
            }
    return None


def rule_physical_inactivity(factors: list[dict[str, Any]], clinical: dict[str, Any]) -> RuleMatch | None:
    for f in factors:
        name = str(f.get("display_name", f.get("category", ""))).lower()
        if "inactivity" in name or "sedentary" in name or "exercise" in name:
            return {
                "rule_id": "PHYSICAL_ACTIVITY_BOOST",
                "category": "Physical Activity",
                "title": "Consider gradually increasing regular physical activity",
                "description": (
                    "Your assessment noted lower physical activity levels. Depending on your personal "
                    "circumstances and clinician guidance, consider gradually incorporating moderate "
                    "aerobic movement such as brisk walking into your weekly routine."
                ),
                "priority": PRIORITY_MEDIUM,
                "source": "Lifestyle Data",
            }
    return None


def rule_unhealthy_diet(factors: list[dict[str, Any]], clinical: dict[str, Any]) -> RuleMatch | None:
    for f in factors:
        name = str(f.get("display_name", f.get("category", ""))).lower()
        if "diet" in name or "food" in name or "junk" in name:
            return {
                "rule_id": "NUTRITION_BALANCE",
                "category": "Nutrition",
                "title": "Consider adopting heart-healthy nutritional patterns",
                "description": (
                    "Nutritional habits were flagged as a contributing factor in your lifestyle assessment. "
                    "Consider emphasizing whole grains, vegetables, and unsaturated fats while moderating "
                    "foods high in saturated fats and refined sugars."
                ),
                "priority": PRIORITY_MEDIUM,
                "source": "Lifestyle Data",
            }
    return None


def rule_poor_sleep(factors: list[dict[str, Any]], clinical: dict[str, Any]) -> RuleMatch | None:
    for f in factors:
        name = str(f.get("display_name", f.get("category", ""))).lower()
        if "sleep" in name or "insomnia" in name:
            return {
                "rule_id": "SLEEP_CONSISTENCY",
                "category": "Sleep",
                "title": "Consider improving sleep consistency and recovery",
                "description": (
                    "Insufficient or disrupted sleep was identified in your lifestyle assessment. "
                    "Consider establishing a consistent sleep schedule and discussing persistent sleep "
                    "concerns with a clinician."
                ),
                "priority": PRIORITY_MEDIUM,
                "source": "Lifestyle Data",
            }
    return None


def rule_alcohol_use(factors: list[dict[str, Any]], clinical: dict[str, Any]) -> RuleMatch | None:
    for f in factors:
        name = str(f.get("display_name", f.get("category", ""))).lower()
        if "alcohol" in name or "drink" in name:
            return {
                "rule_id": "ALCOHOL_MODERATION",
                "category": "Alcohol",
                "title": "Consider moderating alcohol consumption",
                "description": (
                    "Alcohol intake was identified in your lifestyle inputs. Moderating intake in "
                    "accordance with standard cardiovascular health guidelines supports long-term wellness."
                ),
                "priority": PRIORITY_LOW,
                "source": "Lifestyle Data",
            }
    return None


def rule_family_history(factors: list[dict[str, Any]], clinical: dict[str, Any]) -> RuleMatch | None:
    for f in factors:
        name = str(f.get("display_name", f.get("category", ""))).lower()
        if "family" in name or "hereditary" in name:
            return {
                "rule_id": "FAMILY_HISTORY_AWARENESS",
                "category": "Follow-up",
                "title": "Discuss family cardiovascular history with your doctor",
                "description": (
                    "A family history of cardiovascular conditions was noted in your inputs. "
                    "Sharing this background with your doctor can help tailor personal preventive checkup schedules."
                ),
                "priority": PRIORITY_MEDIUM,
                "source": "Lifestyle Data",
            }
    return None


def rule_blood_pressure(
    factors: list[dict[str, Any]],
    clinical: dict[str, Any],
    top_shap: list[dict[str, Any]],
) -> RuleMatch | None:
    trestbps = clinical.get("trestbps")
    has_shap_bp = any("trestbps" in str(s.get("feature", "")).lower() or "blood pressure" in str(s.get("clinical_label", "")).lower() for s in top_shap[:3])

    if (trestbps is not None and float(trestbps) >= 130) or has_shap_bp:
        source = "SHAP" if has_shap_bp else "Clinical Data"
        return {
            "rule_id": "CLINICAL_BP_MONITORING",
            "category": "Clinical Factors",
            "title": "Consider routine resting blood pressure monitoring",
            "description": (
                "Resting blood pressure was identified as an elevated factor in your assessment. "
                "Consider monitoring your blood pressure periodically and sharing home readings with your physician."
            ),
            "priority": PRIORITY_HIGH,
            "source": source,
        }
    return None


def rule_cholesterol(
    factors: list[dict[str, Any]],
    clinical: dict[str, Any],
    top_shap: list[dict[str, Any]],
) -> RuleMatch | None:
    chol = clinical.get("chol")
    has_shap_chol = any("chol" in str(s.get("feature", "")).lower() or "cholesterol" in str(s.get("clinical_label", "")).lower() for s in top_shap[:3])

    if (chol is not None and float(chol) >= 240) or has_shap_chol:
        source = "SHAP" if has_shap_chol else "Clinical Data"
        return {
            "rule_id": "CLINICAL_CHOL_CHECK",
            "category": "Clinical Factors",
            "title": "Consider reviewing cholesterol levels with your physician",
            "description": (
                "Serum cholesterol was identified as a contributing parameter in your evaluation. "
                "Consider scheduling a periodic lipid panel discussion with your healthcare provider."
            ),
            "priority": PRIORITY_MEDIUM,
            "source": source,
        }
    return None


def rule_fasting_blood_sugar(
    factors: list[dict[str, Any]],
    clinical: dict[str, Any],
    top_shap: list[dict[str, Any]],
) -> RuleMatch | None:
    fbs = clinical.get("fbs")
    if fbs is not None and int(fbs) == 1:
        return {
            "rule_id": "CLINICAL_GLUCOSE_MONITORING",
            "category": "Clinical Factors",
            "title": "Consider discussing fasting blood glucose levels",
            "description": (
                "Fasting blood sugar was noted above the standard reference cutoff (120 mg/dl). "
                "Consider consulting your clinician for a routine metabolic evaluation."
            ),
            "priority": PRIORITY_MEDIUM,
            "source": "Clinical Data",
        }
    return None


def rule_risk_category(category: str, overall_risk: float) -> RuleMatch:
    norm_cat = category.strip().upper()
    if "CRITICAL" in norm_cat or "HIGH" in norm_cat or overall_risk >= 85.0:
        return {
            "rule_id": "RISK_TIER_CRITICAL_FOLLOWUP",
            "category": "Follow-up",
            "title": "Promptly consult a qualified healthcare professional",
            "description": (
                "Your HeartGuard model-based assessment is in the critical risk category. "
                "Consider sharing this assessment summary with a qualified healthcare professional promptly. "
                "If you or anyone experiences urgent symptoms (e.g. chest discomfort, shortness of breath), "
                "seek emergency medical attention immediately."
            ),
            "priority": PRIORITY_HIGH,
            "source": "Risk Category",
        }
    elif "ELEVATED" in norm_cat or overall_risk >= 60.0:
        return {
            "rule_id": "RISK_TIER_ELEVATED_FOLLOWUP",
            "category": "Follow-up",
            "title": "Schedule a routine cardiovascular prevention review",
            "description": (
                "Your assessment indicates elevated model-based risk parameters. "
                "Consider bringing this assessment report to your next routine appointment to discuss preventive care."
            ),
            "priority": PRIORITY_MEDIUM,
            "source": "Risk Category",
        }
    else:
        return {
            "rule_id": "ROUTINE_PREVENTION_MAINTENANCE",
            "category": "Assessment Monitoring",
            "title": "Maintain current healthy preventive routines",
            "description": (
                "Your assessment falls within the lower baseline risk tier. "
                "Continue maintaining balanced daily physical activity, nutritious eating, and regular routine wellness visits."
            ),
            "priority": PRIORITY_LOW,
            "source": "Risk Category",
        }


def rule_trend_comparison(comparison: dict[str, Any] | None) -> RuleMatch | None:
    if not comparison:
        return None

    direction = comparison.get("trend_direction", "UNCHANGED")
    overall_info = comparison.get("overall_risk", {})
    delta = overall_info.get("delta", 0.0)

    if direction == "INCREASED" or delta > 2.0:
        return {
            "rule_id": "TREND_INCREASED_ATTENTION",
            "category": "Assessment Monitoring",
            "title": "Reflect on lifestyle changes since your previous assessment",
            "description": (
                f"Your model-based score increased by {overall_info.get('delta_str', 'several points')} "
                "compared with your previous evaluation. Consider reviewing recent lifestyle patterns or "
                "discussing changes with your healthcare provider."
            ),
            "priority": PRIORITY_MEDIUM,
            "source": "Assessment Trend",
        }
    elif direction in ("DECREASED", "DECREASING") or delta < -2.0:
        return {
            "rule_id": "TREND_DECREASING_REINFORCE",
            "category": "Assessment Monitoring",
            "title": "Continue maintaining positive habit adjustments",
            "description": (
                f"Your model-based score decreased by {overall_info.get('delta_str', 'several points')} "
                "compared with your prior assessment. Continue maintaining the beneficial routines that "
                "contributed to this favorable change."
            ),
            "priority": PRIORITY_LOW,
            "source": "Assessment Trend",
        }
    return None


rule_risk_tier = rule_risk_category


def evaluate_lifestyle_rules(
    assessment_id: str,
    lifestyle_factors: list[dict[str, Any]],
) -> list[Any]:
    """Evaluate lifestyle rules against patient lifestyle factors."""
    from src.recommendations.recommendation_models import Recommendation
    recs: list[Recommendation] = []
    clinical: dict[str, Any] = {}
    lifestyle_rules = [
        rule_smoking,
        rule_physical_inactivity,
        rule_unhealthy_diet,
        rule_poor_sleep,
        rule_alcohol_use,
        rule_family_history,
    ]
    for r in lifestyle_rules:
        match = r(lifestyle_factors, clinical)
        if match:
            recs.append(
                Recommendation(
                    assessment_id=assessment_id,
                    category=match["category"],
                    title=match["title"],
                    description=match["description"],
                    priority=match["priority"],
                    source=match["source"],
                    rule_id=match["rule_id"],
                )
            )
    return recs


def evaluate_clinical_rules(
    assessment_id: str,
    clinical_data: dict[str, Any],
) -> list[Any]:
    """Evaluate clinical rules against clinical measurements."""
    from src.recommendations.recommendation_models import Recommendation
    recs: list[Recommendation] = []
    factors: list[dict[str, Any]] = []
    clinical_rules = [
        rule_blood_pressure,
        rule_fasting_blood_sugar,
        rule_cholesterol,
    ]
    for r in clinical_rules:
        match = r(factors, clinical_data, [])
        if match:
            recs.append(
                Recommendation(
                    assessment_id=assessment_id,
                    category=match["category"],
                    title=match["title"],
                    description=match["description"],
                    priority=match["priority"],
                    source=match["source"],
                    rule_id=match["rule_id"],
                )
            )
    return recs


def evaluate_risk_tier_rules(
    assessment_id: str,
    risk_category: str,
    overall_risk: float,
) -> list[Any]:
    """Evaluate risk tier rules."""
    from src.recommendations.recommendation_models import Recommendation
    match = rule_risk_tier(risk_category, overall_risk)
    if match:
        return [
            Recommendation(
                assessment_id=assessment_id,
                category=match["category"],
                title=match["title"],
                description=match["description"],
                priority=match["priority"],
                source=match["source"],
                rule_id=match["rule_id"],
            )
        ]
    return []


def evaluate_trend_rules(
    assessment_id: str,
    trend_direction: str,
    delta: float,
) -> list[Any]:
    """Evaluate trend rules."""
    from src.recommendations.recommendation_models import Recommendation
    comparison = {
        "trend_direction": trend_direction,
        "overall_risk": {
            "delta": delta,
            "delta_str": f"{abs(delta):.1f}%",
        },
    }
    match = rule_trend_comparison(comparison)
    if match:
        return [
            Recommendation(
                assessment_id=assessment_id,
                category=match["category"],
                title=match["title"],
                description=match["description"],
                priority=match["priority"],
                source=match["source"],
                rule_id=match["rule_id"],
            )
        ]
    return []

