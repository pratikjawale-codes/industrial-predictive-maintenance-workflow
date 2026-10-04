"""
Multi-Horizon Failure Prediction Model.
Implements Section 4 & 8: Calibrated failure risk across 24h, 72h, 7d, and 14d horizons.
"""

from typing import Dict, Any, Tuple
import numpy as np
from models.calibration.calibrator import ProbabilityCalibrator


class MultiHorizonFailureModel:
    """
    Predicts equipment failure probabilities across 4 operational horizons:
    - 24 Hours: Immediate critical breakdown (Emergency Action)
    - 72 Hours: Urgent degradation (Hot inspection / load reduction)
    - 7 Days:   Target maintenance planning horizon (Primary GE Objective)
    - 14 Days:  Strategic turnaround planning window
    """

    def __init__(self, model_version: str = "v2.4.1-champion"):
        self.model_version = model_version
        self.calibrator = ProbabilityCalibrator()

        # Feature weights for multi-horizon failure risk
        self.feature_weights = {
            "vib_de_rms_ewma_1h": 0.22,
            "vib_kurtosis": 0.18,
            "vib_de_trend_slope_24h": 0.16,
            "temp_bearing_delta_ambient": 0.14,
            "press_lube_oil_bar": -0.12,  # lower lube pressure increases risk
            "vib_harmonic_ratio_2x_1x": 0.10,
            "temp_lube_delta_supply_return": 0.08
        }

    def predict_horizons(
        self,
        features: Dict[str, float]
    ) -> Tuple[Dict[str, float], float, str]:
        """
        Calculate calibrated failure probabilities for 24h, 72h, 7d, 14d horizons,
        overall risk score [0-100], and severity category.
        """
        # 1. Base degradation score calculated from physics & features
        score = 0.0
        vib = features.get("vib_de_rms_ewma_1h", 2.0)
        kurt = features.get("vib_kurtosis", 3.0)
        slope = features.get("vib_de_trend_slope_24h", 0.0)
        temp_delta = features.get("temp_bearing_delta_ambient", 35.0)
        p_lube = features.get("press_lube_oil_bar", 3.2)
        harm_2x = features.get("vib_harmonic_ratio_2x_1x", 0.3)

        # Baseline normalized score (0.0 to 1.0)
        norm_vib = np.clip((vib - 1.5) / 6.0, 0.0, 2.0)
        norm_kurt = np.clip((kurt - 2.8) / 5.0, 0.0, 2.0)
        norm_slope = np.clip(slope / 2.0, -0.5, 2.0)
        norm_temp = np.clip((temp_delta - 30.0) / 40.0, 0.0, 2.0)
        norm_p_loss = np.clip((3.0 - p_lube) / 2.0, 0.0, 2.0)
        norm_harm = np.clip((harm_2x - 0.4) / 1.0, 0.0, 2.0)

        raw_degradation = (
            0.26 * norm_vib +
            0.22 * norm_kurt +
            0.18 * norm_slope +
            0.14 * norm_temp +
            0.12 * norm_p_loss +
            0.08 * norm_harm
        )

        # Cumulative probability accumulation over time horizons
        # 14-day horizon sees the degradation earliest
        p_14d_raw = np.clip(raw_degradation * 0.95, 0.01, 0.98)
        p_7d_raw = np.clip(p_14d_raw * (0.80 + 0.15 * norm_slope), 0.005, 0.96)
        p_72h_raw = np.clip(p_7d_raw * (0.60 + 0.25 * norm_vib), 0.002, 0.93)
        p_24h_raw = np.clip(p_72h_raw * (0.45 + 0.35 * norm_slope), 0.001, 0.90)

        # Apply Platt calibration
        p_14d = self.calibrator.calibrate(float(p_14d_raw))
        p_7d = self.calibrator.calibrate(float(p_7d_raw))
        p_72h = self.calibrator.calibrate(float(p_72h_raw))
        p_24h = self.calibrator.calibrate(float(p_24h_raw))

        # Enforce physical monotonicity: P(24h) <= P(72h) <= P(7d) <= P(14d)
        p_72h = max(p_24h, p_72h)
        p_7d = max(p_72h, p_7d)
        p_14d = max(p_7d, p_14d)

        horizon_probs = {
            "24h": round(p_24h, 4),
            "72h": round(p_72h, 4),
            "7d": round(p_7d, 4),
            "14d": round(p_14d, 4)
        }

        # Weighted risk score
        risk_score = round(float((p_24h * 0.40 + p_72h * 0.30 + p_7d * 0.20 + p_14d * 0.10) * 100.0), 1)

        # Operational severity rating
        if risk_score >= 70.0 or p_24h > 0.45:
            severity = "CRITICAL"
        elif risk_score >= 45.0 or p_7d > 0.40:
            severity = "ELEVATED"
        elif risk_score >= 20.0 or p_14d > 0.30:
            severity = "WATCHLIST"
        else:
            severity = "NORMAL"

        return horizon_probs, risk_score, severity
