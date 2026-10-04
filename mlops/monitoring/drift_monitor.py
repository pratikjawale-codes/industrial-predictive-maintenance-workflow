"""
Data and Feature Drift Observability Engine.
Implements Section 5, 12, 13 & 23: Population Stability Index (PSI) and
distribution shift monitoring on live industrial telemetry.
"""

from typing import Dict, List, Any
import numpy as np


class DriftMonitor:
    """
    Computes statistical drift scores (PSI) on streaming features against
    historical training baselines. Triggers automated retraining alerts.
    """

    def __init__(self):
        # Reference distributions (mean, std) for PSI calculation
        self.feature_baselines: Dict[str, Dict[str, float]] = {
            "vib_de_rms_ewma_1h": {"mean": 2.2, "std": 0.6},
            "vib_kurtosis": {"mean": 3.0, "std": 0.4},
            "temp_bearing_delta_ambient": {"mean": 35.0, "std": 8.0},
            "press_lube_oil_bar": {"mean": 3.2, "std": 0.4},
            "motor_current_unbalance_pct": {"mean": 0.9, "std": 0.3}
        }

    def compute_psi(self, current_features: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluate drift metric for key features:
        - PSI < 0.10: No significant drift (Green)
        - 0.10 <= PSI < 0.25: Moderate drift, investigate (Yellow)
        - PSI >= 0.25: Critical drift, trigger automated retraining gate (Red)
        """
        drift_results = {}
        max_psi = 0.0

        for feat, baseline in self.feature_baselines.items():
            curr_val = current_features.get(feat, baseline["mean"])
            z = abs(curr_val - baseline["mean"]) / max(baseline["std"], 0.01)

            # Empirical PSI approximation from standardized shift
            # delta_mean^2 / (2 * variance)
            psi = float(round((z ** 2) * 0.06, 3))
            max_psi = max(max_psi, psi)

            if psi >= 0.25:
                status = "CRITICAL_DRIFT"
            elif psi >= 0.10:
                status = "MODERATE_DRIFT"
            else:
                status = "STABLE"

            drift_results[feat] = {
                "current_value": round(float(curr_val), 3),
                "baseline_mean": baseline["mean"],
                "psi_score": psi,
                "status": status
            }

        overall_status = "STABLE"
        if max_psi >= 0.25:
            overall_status = "ACTION_REQUIRED_RETRAIN"
        elif max_psi >= 0.10:
            overall_status = "WARNING_MONITOR"

        return {
            "overall_drift_status": overall_status,
            "max_psi": round(max_psi, 3),
            "features": drift_results,
            "retraining_recommended": max_psi >= 0.25
        }
