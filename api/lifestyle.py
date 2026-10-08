"""Lifestyle analysis router for HeartGuard API."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.deps import CurrentUser, get_current_user
from src.nlp.lifestyle_analyzer import LifestyleAnalyzer
from src.recommendations.recommendation_rules import (
    rule_alcohol_use,
    rule_family_history,
    rule_physical_inactivity,
    rule_poor_sleep,
    rule_smoking,
    rule_unhealthy_diet,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/lifestyle", tags=["lifestyle"])


class LifestyleAnalyzeRequest(BaseModel):
    text: str | None = None
    lifestyle_text: str | None = None


class LifestyleAnalyzeResponse(BaseModel):
    risk_score: float
    lifestyle_score: float
    risk_category: str
    detected_risk_factors: list[Any] = []
    top_risk_factors: list[Any] = []
    recommendations: list[str] = []
    summary: str = ""
    disclaimer: str = ""


@router.post("/analyze", response_model=LifestyleAnalyzeResponse)
async def analyze_lifestyle(
    body: LifestyleAnalyzeRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    raw_text = body.text or body.lifestyle_text or ""
    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lifestyle description cannot be empty.",
        )

    try:
        analyzer = LifestyleAnalyzer()
        res = analyzer.analyze(raw_text)

        score = float(res.get("lifestyle_score", 0.0))
        cat = str(res.get("risk_category", "LOW"))
        factors = res.get("detected_risk_factors", [])
        top_factors = res.get("top_risk_factors", [])
        summary = str(res.get("summary", ""))
        disclaimer = str(res.get("disclaimer", ""))

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
            recs.append("Maintain your positive lifestyle habits, stay active, and consult your physician for regular health screenings.")

        return LifestyleAnalyzeResponse(
            risk_score=score,
            lifestyle_score=score,
            risk_category=cat,
            detected_risk_factors=factors,
            top_risk_factors=top_factors,
            recommendations=recs,
            summary=summary,
            disclaimer=disclaimer,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Lifestyle analysis error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lifestyle analysis failed: {str(e)}",
        )
