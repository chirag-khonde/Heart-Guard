"""Drift Detection Framework (Phase 17).

Implements statistical drift detection for:
- Numerical feature drift (KS test, PSI)
- Categorical feature drift (Chi-square, PSI)
- Prediction distribution drift
- Confidence monitoring

Compares reference (training) data distributions against current production
assessment data. All thresholds are engineering monitoring thresholds,
NOT clinical thresholds.
"""

from __future__ import annotations

import json
import math
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

from config.monitoring import (
    DRIFT_JS_DIVERGENCE_CRITICAL,
    DRIFT_JS_DIVERGENCE_WARNING,
    DRIFT_KS_ALPHA,
    DRIFT_MIN_SAMPLE_SIZE,
    DRIFT_PSI_CRITICAL,
    DRIFT_PSI_WARNING,
    STATUS_DRIFT_DETECTED,
    STATUS_HEALTHY,
    STATUS_INSUFFICIENT_DATA,
    STATUS_WARNING,
)
from config.settings import ASSESSMENTS_DB_PATH
from src.analytics.history_service import _get_connection
from src.data.features import CATEGORICAL_FEATURES, NUMERICAL_FEATURES
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index between two distributions."""
    ref_hist, bin_edges = np.histogram(reference, bins=bins, density=True)
    cur_hist, _ = np.histogram(current, bins=bin_edges, density=True)

    ref_hist = np.clip(ref_hist, 1e-6, None)
    cur_hist = np.clip(cur_hist, 1e-6, None)

    return float(np.sum((cur_hist - ref_hist) * np.log(cur_hist / ref_hist)))


def _ks_statistic(reference: np.ndarray, current: np.ndarray) -> tuple[float, float]:
    """Two-sample KS test statistic and approximate p-value."""
    from scipy import stats
    if len(reference) < 5 or len(current) < 5:
        return 0.0, 1.0
    stat, p_value = stats.ks_2samp(reference, current)
    return float(stat), float(p_value)


def _jensen_shannon_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """Jensen-Shannon divergence between two distributions."""
    p = np.clip(p, 1e-10, None)
    q = np.clip(q, 1e-10, None)
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    return float(0.5 * (np.sum(p * np.log(p / m)) + np.sum(q * np.log(q / m))))


def _categorical_psi(reference_counts: dict[str, int], current_counts: dict[str, int]) -> float:
    """PSI for categorical distributions."""
    all_cats = set(reference_counts.keys()) | set(current_counts.keys())
    ref_total = sum(reference_counts.values()) or 1
    cur_total = sum(current_counts.values()) or 1

    psi = 0.0
    for cat in all_cats:
        ref_pct = reference_counts.get(cat, 0) / ref_total
        cur_pct = current_counts.get(cat, 0) / cur_total
        ref_pct = max(ref_pct, 1e-6)
        cur_pct = max(cur_pct, 1e-6)
        psi += (cur_pct - ref_pct) * math.log(cur_pct / ref_pct)
    return psi


def _chi_square_test(reference_counts: dict[str, int], current_counts: dict[str, int]) -> tuple[float, float]:
    """Chi-square test for categorical distributions."""
    all_cats = set(reference_counts.keys()) | set(current_counts.keys())
    ref_total = sum(reference_counts.values()) or 1
    cur_total = sum(current_counts.values()) or 1
    n_cats = len(all_cats) or 1

    chi2 = 0.0
    for cat in all_cats:
        ref_exp = ref_total * (reference_counts.get(cat, 0) + current_counts.get(cat, 0)) / (ref_total + cur_total)
        ref_exp = max(ref_exp, 1e-6)
        observed = current_counts.get(cat, 0)
        chi2 += (observed - ref_exp) ** 2 / ref_exp

    df = max(n_cats - 1, 1)
    p_value = 1.0
    try:
        from scipy import stats
        p_value = 1 - stats.chi2.cdf(chi2, df)
    except Exception:
        pass

    return chi2, p_value


class DriftDetector:
    """Detects data and prediction drift between reference and current distributions."""

    @staticmethod
    def detect_numerical_drift(
        reference_values: np.ndarray,
        current_values: np.ndarray,
        feature_name: str,
    ) -> dict[str, Any]:
        """Detect drift in a numerical feature."""
        ref = np.array(reference_values, dtype=float)
        cur = np.array(current_values, dtype=float)

        ref = ref[~np.isnan(ref)]
        cur = cur[~np.isnan(cur)]

        if len(ref) < DRIFT_MIN_SAMPLE_SIZE or len(cur) < DRIFT_MIN_SAMPLE_SIZE:
            return {
                "feature": feature_name,
                "status": STATUS_INSUFFICIENT_DATA,
                "reference_count": len(ref),
                "current_count": len(cur),
                "message": f"Insufficient data for drift analysis (need {DRIFT_MIN_SAMPLE_SIZE} samples)",
            }

        psi_value = _psi(ref, cur)
        ks_stat, ks_p = _ks_statistic(ref, cur)

        ref_hist, _ = np.histogram(ref, bins=20, density=True)
        cur_hist, _ = np.histogram(cur, bins=20, density=True)
        js_div = _jensen_shannon_divergence(ref_hist, cur_hist)

        if psi_value >= DRIFT_PSI_CRITICAL or (ks_p < DRIFT_KS_ALPHA and js_div >= DRIFT_JS_DIVERGENCE_CRITICAL):
            status = STATUS_DRIFT_DETECTED
        elif psi_value >= DRIFT_PSI_WARNING or (ks_p < DRIFT_KS_ALPHA and js_div >= DRIFT_JS_DIVERGENCE_WARNING):
            status = STATUS_WARNING
        else:
            status = STATUS_HEALTHY

        return {
            "feature": feature_name,
            "feature_type": "numerical",
            "status": status,
            "psi": round(psi_value, 4),
            "ks_statistic": round(ks_stat, 4),
            "ks_p_value": round(ks_p, 4),
            "js_divergence": round(js_div, 4),
            "reference_mean": round(float(np.mean(ref)), 4),
            "current_mean": round(float(np.mean(cur)), 4),
            "reference_std": round(float(np.std(ref)), 4),
            "current_std": round(float(np.std(cur)), 4),
            "reference_count": len(ref),
            "current_count": len(cur),
            "psi_warning_threshold": DRIFT_PSI_WARNING,
            "psi_critical_threshold": DRIFT_PSI_CRITICAL,
        }

    @staticmethod
    def detect_categorical_drift(
        reference_counts: dict[str, int],
        current_counts: dict[str, int],
        feature_name: str,
    ) -> dict[str, Any]:
        """Detect drift in a categorical feature."""
        ref_total = sum(reference_counts.values())
        cur_total = sum(current_counts.values())

        if ref_total < DRIFT_MIN_SAMPLE_SIZE or cur_total < DRIFT_MIN_SAMPLE_SIZE:
            return {
                "feature": feature_name,
                "status": STATUS_INSUFFICIENT_DATA,
                "reference_count": ref_total,
                "current_count": cur_total,
                "message": f"Insufficient data for drift analysis (need {DRIFT_MIN_SAMPLE_SIZE} samples)",
            }

        psi_value = _categorical_psi(reference_counts, current_counts)
        chi2, chi2_p = _chi_square_test(reference_counts, current_counts)

        if psi_value >= DRIFT_PSI_CRITICAL or chi2_p < 0.01:
            status = STATUS_DRIFT_DETECTED
        elif psi_value >= DRIFT_PSI_WARNING or chi2_p < 0.05:
            status = STATUS_WARNING
        else:
            status = STATUS_HEALTHY

        return {
            "feature": feature_name,
            "feature_type": "categorical",
            "status": status,
            "psi": round(psi_value, 4),
            "chi_square": round(chi2, 4),
            "chi_square_p_value": round(chi2_p, 4),
            "reference_categories": reference_counts,
            "current_categories": current_counts,
            "reference_count": ref_total,
            "current_count": cur_total,
            "psi_warning_threshold": DRIFT_PSI_WARNING,
            "psi_critical_threshold": DRIFT_PSI_CRITICAL,
        }

    @staticmethod
    def detect_prediction_drift(
        reference_predictions: list[str],
        current_predictions: list[str],
    ) -> dict[str, Any]:
        """Detect drift in prediction distributions."""
        ref_counts = dict(Counter(reference_predictions))
        cur_counts = dict(Counter(current_predictions))

        ref_total = sum(ref_counts.values())
        cur_total = sum(cur_counts.values())

        if ref_total < DRIFT_MIN_SAMPLE_SIZE or cur_total < DRIFT_MIN_SAMPLE_SIZE:
            return {
                "status": STATUS_INSUFFICIENT_DATA,
                "reference_count": ref_total,
                "current_count": cur_total,
                "message": "Insufficient data for prediction drift analysis",
            }

        all_cats = set(ref_counts.keys()) | set(cur_counts.keys())
        ref_dist = {cat: ref_counts.get(cat, 0) / ref_total for cat in all_cats}
        cur_dist = {cat: cur_counts.get(cat, 0) / cur_total for cat in all_cats}

        max_shift = max(abs(ref_dist.get(cat, 0) - cur_dist.get(cat, 0)) for cat in all_cats)

        psi_value = _categorical_psi(ref_counts, cur_counts)

        if max_shift >= 0.20 or psi_value >= DRIFT_PSI_CRITICAL:
            status = STATUS_DRIFT_DETECTED
        elif max_shift >= 0.10 or psi_value >= DRIFT_PSI_WARNING:
            status = STATUS_WARNING
        else:
            status = STATUS_HEALTHY

        return {
            "status": status,
            "max_distribution_shift": round(max_shift, 4),
            "psi": round(psi_value, 4),
            "reference_distribution": {k: round(v, 4) for k, v in ref_dist.items()},
            "current_distribution": {k: round(v, 4) for k, v in cur_dist.items()},
            "reference_count": ref_total,
            "current_count": cur_total,
        }

    @staticmethod
    def run_full_drift_analysis(
        reference_data: dict[str, Any],
        current_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Run comprehensive drift analysis across all features.

        Args:
            reference_data: Dict with 'numerical' (feature -> values) and
                          'categorical' (feature -> {category: count}) keys.
            current_data: Same structure for current data.
        """
        results = {
            "overall_status": STATUS_HEALTHY,
            "numerical_features": {},
            "categorical_features": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        any_drift = False
        any_warning = False

        for feature in NUMERICAL_FEATURES:
            ref_vals = reference_data.get("numerical", {}).get(feature)
            cur_vals = current_data.get("numerical", {}).get(feature)
            if ref_vals is not None and cur_vals is not None:
                result = DriftDetector.detect_numerical_drift(
                    np.array(ref_vals), np.array(cur_vals), feature
                )
                results["numerical_features"][feature] = result
                if result["status"] == STATUS_DRIFT_DETECTED:
                    any_drift = True
                elif result["status"] == STATUS_WARNING:
                    any_warning = True

        for feature in CATEGORICAL_FEATURES:
            ref_cats = reference_data.get("categorical", {}).get(feature)
            cur_cats = current_data.get("categorical", {}).get(feature)
            if ref_cats is not None and cur_cats is not None:
                result = DriftDetector.detect_categorical_drift(ref_cats, cur_cats, feature)
                results["categorical_features"][feature] = result
                if result["status"] == STATUS_DRIFT_DETECTED:
                    any_drift = True
                elif result["status"] == STATUS_WARNING:
                    any_warning = True

        if any_drift:
            results["overall_status"] = STATUS_DRIFT_DETECTED
        elif any_warning:
            results["overall_status"] = STATUS_WARNING

        return results

    @staticmethod
    def get_drift_summary_from_assessments(
        date_range: str | None = None,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Extract current clinical data distribution from assessment records
        for drift comparison against training data."""
        conditions = []
        params: list[Any] = []

        if date_range in ("7d", "30d", "90d"):
            days = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with _get_connection(db_path) as conn:
            rows = conn.execute(
                f"SELECT clinical_data_json FROM assessments {where_clause} AND clinical_data_json IS NOT NULL",
                tuple(params),
            ).fetchall()

        if not rows:
            return {"status": STATUS_INSUFFICIENT_DATA, "message": "No assessment data available"}

        numerical_data: dict[str, list[float]] = {f: [] for f in NUMERICAL_FEATURES}
        categorical_data: dict[str, dict[str, int]] = {f: {} for f in CATEGORICAL_FEATURES}

        for row in rows:
            try:
                data = json.loads(row["clinical_data_json"])
                if not isinstance(data, dict):
                    continue
                for feat in NUMERICAL_FEATURES:
                    val = data.get(feat)
                    if val is not None:
                        try:
                            numerical_data[feat].append(float(val))
                        except (ValueError, TypeError):
                            pass
                for feat in CATEGORICAL_FEATURES:
                    val = data.get(feat)
                    if val is not None:
                        cat_str = str(val)
                        categorical_data[feat][cat_str] = categorical_data[feat].get(cat_str, 0) + 1
            except Exception:
                continue

        return {
            "status": STATUS_HEALTHY,
            "sample_size": len(rows),
            "numerical": numerical_data,
            "categorical": categorical_data,
        }
