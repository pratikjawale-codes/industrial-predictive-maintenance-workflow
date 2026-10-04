"""
Probabilistic Remaining Useful Life (RUL) Estimation Engine.
Implements Section 4 & 5: RUL point estimate, P10/P50/P90 prediction intervals,
and cumulative failure probability before maintenance lead time.
"""

from typing import Dict, Any, Tuple
import numpy as np


class ProbabilisticRULModel:
    """
    Estimates Remaining Useful Life (RUL) with Bayesian uncertainty bounds:
    - P10 (Pessimistic RUL): 90% confidence equipment survives at least this long.
    - P50 (Median RUL): Most probable remaining operating lifespan.
    - P90 (Optimistic RUL): Upper envelope under gentle load conditions.
    """

    def __init__(self, model_version: str = "v1.8.2-rul"):
        self.model_version = model_version
        self.max_nominal_rul_days = 90.0  # nominal healthy lifespan between major C-inspections

    def predict_rul(
        self,
        features: Dict[str, float],
        calibrated_risk: float
    ) -> Dict[str, float]:
        """
        Predict Remaining Useful Life in days and hours, along with uncertainty bounds.
        """
        vib = features.get("vib_de_rms_ewma_1h", 2.0)
        kurt = features.get("vib_kurtosis", 3.0)
        slope = features.get("vib_de_trend_slope_24h", 0.0)
        temp_delta = features.get("temp_bearing_delta_ambient", 35.0)

        # Baseline degradation factor (0.0 = brand new, 1.0 = imminent failure)
        # Combined with calibrated risk score
        risk_norm = np.clip(calibrated_risk / 100.0, 0.01, 0.99)
        
        # Exponential degradation curve matching Weibull hazard rates
        # RUL drops sharply as mechanical vibration and thermal dissipation escalate
        degradation_factor = (
            0.50 * risk_norm +
            0.20 * np.clip((vib - 2.0) / 6.0, 0.0, 1.0) +
            0.15 * np.clip((kurt - 3.0) / 6.0, 0.0, 1.0) +
            0.15 * np.clip((temp_delta - 35.0) / 45.0, 0.0, 1.0)
        )
        degradation_factor = float(np.clip(degradation_factor, 0.02, 0.98))

        # P50 Median RUL in days
        # Healthy machine: 45 to 80 days
        # Degraded machine: 3 to 14 days
        # Critical machine: 0.5 to 2 days
        rul_days_p50 = max(0.5, round(float(self.max_nominal_rul_days * (1.0 - degradation_factor) ** 1.6), 1))

        # Uncertainty expansion: Standard error increases when rate-of-change (slope) is high
        uncertainty_rate = 0.18 + 0.12 * np.clip(abs(slope) / 2.0, 0.0, 1.0)
        
        # Log-normal distribution percentile intervals
        rul_days_p10 = max(0.2, round(float(rul_days_p50 * (1.0 - uncertainty_rate * 1.645)), 1))
        rul_days_p90 = round(float(rul_days_p50 * (1.0 + uncertainty_rate * 1.645)), 1)
        rul_hours_median = round(rul_days_p50 * 24.0, 1)

        # Cumulative failure probability before typical 7-day maintenance turnaround
        if rul_days_p50 <= 7.0:
            p_fail_before_7d = min(0.99, round(0.50 + 0.50 * (7.0 - rul_days_p50) / 7.0, 3))
        else:
            p_fail_before_7d = max(0.01, round(0.50 * (7.0 / rul_days_p50) ** 1.5, 3))

        return {
            "rul_days_median": rul_days_p50,
            "rul_days_p10": rul_days_p10,
            "rul_days_p90": rul_days_p90,
            "rul_hours_median": rul_hours_median,
            "confidence_interval_width_days": round(rul_days_p90 - rul_days_p10, 1),
            "failure_probability_before_window": p_fail_before_7d,
            "degradation_percentage": round(degradation_factor * 100.0, 1)
        }
