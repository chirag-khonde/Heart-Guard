"""Assessment router for HeartGuard API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.deps import CurrentUser, get_current_user, require_role
from src.alerts.alert_manager import AlertManager
from src.analytics.history_service import HistoryService
from src.risk_engine.multimodal_risk import MultimodalRiskEngine

import json
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


class AssessmentCreateRequest(BaseModel):
    clinical_data: dict[str, Any] | None = None
    lifestyle_text: str | None = None
    # Flat field support
    age: Any | None = None
    sex: Any | None = None
    chest_pain_type: Any | None = None
    resting_bp: Any | None = None
    resting_blood_pressure: Any | None = None
    cholesterol: Any | None = None
    fasting_blood_sugar: Any | None = None
    resting_ecg: Any | None = None
    max_heart_rate: Any | None = None
    exercise_angina: Any | None = None
    exercise_induced_angina: Any | None = None
    st_depression: Any | None = None
    num_major_vessels: Any | None = None


class AssessmentResponse(BaseModel):
    id: int | None = None
    assessment_id: str
    user_id: int
    created_at: str
    clinical_risk: float
    lifestyle_risk: float
    overall_risk: float
    risk_score: float | None = None
    risk_percentage: float | None = None
    risk_category: str
    recommendation: str
    recommendations: list[str] | None = None
    model_version: str
    narrative_summary: str
    alert_status: str
    shap_explanation: dict[str, float] | None = None
    clinical_data: dict[str, Any] | None = None


def _normalize_clinical_data(raw: dict[str, Any]) -> dict[str, Any]:
    norm = dict(raw)
    # Field aliases
    if "resting_blood_pressure" in norm and "resting_bp" not in norm:
        norm["resting_bp"] = norm.pop("resting_blood_pressure")
    if "exercise_induced_angina" in norm and "exercise_angina" not in norm:
        norm["exercise_angina"] = norm.pop("exercise_induced_angina")

    # Sex normalization
    if "sex" in norm:
        s = norm["sex"]
        if isinstance(s, str):
            norm["sex"] = 1 if s.lower() in ("male", "m", "1", "true") else 0
        elif isinstance(s, bool):
            norm["sex"] = 1 if s else 0
        else:
            try:
                norm["sex"] = int(s)
            except Exception:
                norm["sex"] = 0

    # Binary features normalization
    for bin_field in ("fasting_blood_sugar", "exercise_angina"):
        if bin_field in norm:
            v = norm[bin_field]
            if isinstance(v, str):
                norm[bin_field] = 1 if v.lower() in ("true", "1", "yes") else 0
            elif isinstance(v, bool):
                norm[bin_field] = 1 if v else 0
            else:
                try:
                    norm[bin_field] = int(v)
                except Exception:
                    norm[bin_field] = 0

    # Numeric conversion
    for num_field in ("age", "resting_bp", "cholesterol", "max_heart_rate", "st_depression", "num_major_vessels", "chest_pain_type", "resting_ecg"):
        if num_field in norm and norm[num_field] is not None:
            try:
                if num_field in ("chest_pain_type", "resting_ecg", "num_major_vessels"):
                    norm[num_field] = int(float(norm[num_field]))
                else:
                    norm[num_field] = float(norm[num_field])
            except Exception:
                pass

    return norm


def _assessment_to_response(asmt, extra_result: dict[str, Any] | None = None) -> AssessmentResponse:
    shap_map: dict[str, float] = {}
    if extra_result and extra_result.get("clinical_explanation"):
        top_feats = extra_result["clinical_explanation"].get("top_features", [])
        for f in top_feats:
            if isinstance(f, dict) and "feature" in f and "shap_value" in f:
                shap_map[f["feature"]] = float(f["shap_value"])

    if not shap_map and getattr(asmt, "top_clinical_factors_json", None):
        try:
            factors = json.loads(asmt.top_clinical_factors_json)
            if isinstance(factors, list):
                for f in factors:
                    if isinstance(f, dict) and "feature" in f:
                        val = f.get("shap_value", f.get("impact", 0.1))
                        shap_map[f["feature"]] = float(val)
                    elif isinstance(f, str):
                        shap_map[f] = 0.1
        except Exception:
            pass

    recs = [asmt.recommendation] if asmt.recommendation else []

    return AssessmentResponse(
        id=asmt.id,
        assessment_id=asmt.assessment_id,
        user_id=asmt.user_id,
        created_at=asmt.created_at,
        clinical_risk=asmt.clinical_risk,
        lifestyle_risk=asmt.lifestyle_risk,
        overall_risk=asmt.overall_risk,
        risk_score=asmt.overall_risk,
        risk_percentage=asmt.overall_risk,
        risk_category=asmt.risk_category,
        recommendation=asmt.recommendation,
        recommendations=recs,
        model_version=asmt.model_version,
        narrative_summary=asmt.narrative_summary,
        alert_status=asmt.alert_status,
        shap_explanation=shap_map if shap_map else None,
    )


@router.post("", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    body: AssessmentCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        raw_clinical = dict(body.clinical_data or {})
        flat_dict = body.model_dump()
        for k, v in flat_dict.items():
            if k not in ("clinical_data", "lifestyle_text") and v is not None and k not in raw_clinical:
                raw_clinical[k] = v

        norm_clinical = _normalize_clinical_data(raw_clinical)
        lifestyle_text = (body.lifestyle_text or raw_clinical.get("lifestyle_text") or "No lifestyle narrative provided.").strip()

        from src.data.features import HEARTGUARD_FEATURES
        from datetime import datetime, timezone
        import uuid

        has_clinical = any(norm_clinical.get(f) is not None for f in HEARTGUARD_FEATURES)
        if not has_clinical and lifestyle_text:
            from src.nlp.lifestyle_analyzer import LifestyleAnalyzer
            from src.recommendations.recommendation_rules import (
                rule_alcohol_use,
                rule_family_history,
                rule_physical_inactivity,
                rule_poor_sleep,
                rule_smoking,
                rule_unhealthy_diet,
            )
            analyzer = LifestyleAnalyzer()
            l_res = analyzer.analyze(lifestyle_text)
            l_score = float(l_res.get("lifestyle_score", 0.0))
            l_cat = str(l_res.get("risk_category", "LOW"))
            factors = l_res.get("detected_risk_factors", [])
            recs: list[str] = []
            for rule_fn in [
                rule_smoking,
                rule_physical_inactivity,
                rule_unhealthy_diet,
                rule_poor_sleep,
                rule_alcohol_use,
                rule_family_history,
            ]:
                match = rule_fn(factors, {})
                if match:
                    recs.append(f"{match['title']}: {match['description']}")
            if not recs:
                recs.append("Maintain healthy daily habits and schedule regular checkups.")

            return AssessmentResponse(
                id=None,
                assessment_id=uuid.uuid4().hex[:8],
                user_id=current_user.user_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                clinical_risk=0.0,
                lifestyle_risk=l_score,
                overall_risk=l_score,
                risk_score=l_score,
                risk_percentage=l_score,
                risk_category=l_cat,
                recommendation=recs[0],
                recommendations=recs,
                model_version="lifestyle-nlp (v1.0.0)",
                narrative_summary=str(l_res.get("summary", "")),
                alert_status="NOT_TRIGGERED",
            )

        engine = MultimodalRiskEngine()
        result = engine.assess(
            clinical_data=norm_clinical,
            lifestyle_text=lifestyle_text,
        )

        alert_manager = AlertManager()
        alert_result = alert_manager.process_risk_result(
            risk_result=result,
            assessment_id=None,
        )

        asmt = HistoryService.save_assessment(
            user_id=current_user.user_id,
            multimodal_result=result,
            alert_status=alert_result.get("notification_status", "NOT_TRIGGERED"),
        )

        return _assessment_to_response(asmt, extra_result=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.exception("Assessment processing error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Assessment failed: {str(e)}")


@router.get("", response_model=list[AssessmentResponse])
async def list_assessments(current_user: CurrentUser = Depends(get_current_user)):
    if current_user.role == "ADMIN":
        from src.analytics.history_service import _get_connection, _row_to_assessment
        with _get_connection() as conn:
            rows = conn.execute("SELECT * FROM assessments ORDER BY created_at DESC LIMIT 100").fetchall()
            return [_assessment_to_response(_row_to_assessment(r)) for r in rows]

    assessments = HistoryService.get_user_assessments(
        user_id=current_user.user_id,
        sort_order="desc",
        limit=50,
    )
    return [_assessment_to_response(a) for a in assessments]


@router.get("/latest", response_model=AssessmentResponse)
async def get_latest_assessment(current_user: CurrentUser = Depends(get_current_user)):
    asmt = HistoryService.get_latest_assessment(user_id=current_user.user_id)
    if asmt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assessments found")
    return _assessment_to_response(asmt)


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role in ("ADMIN", "REVIEWER"):
        asmt = HistoryService.get_assessment_by_id(assessment_id, user_id=None)
    else:
        asmt = HistoryService.get_assessment_by_id(assessment_id, user_id=current_user.user_id)

    if asmt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    if current_user.role == "PATIENT" and asmt.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return _assessment_to_response(asmt)
