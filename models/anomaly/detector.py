"""
Multivariate Anomaly Detection and Signal Attribution Engine.
Implements Section 4 & 8: Unsupervised anomaly scoring for unknown degradation signatures,
with sensor-level contribution decomposition.
"""

from typing import Dict, List, Any, Tuple
import numpy as np


class MultivariateAnomalyDetector:
    """
    Detects multivariate sensor anomalies and decomposes the anomaly score
    into sensor-level contributions to guide troubleshooting.
    """

    def __init__(self, baseline_threshold: float = 65.0):
        self.threshold = baseline_threshold

        # Normal operating baselines (mean, std) for key normalized sensors
        self.sensor_baselines: Dict[str, Dict[str, float]] = {
            "vib_drive_end_rms": {"mean": 2.2, "std": 0.6},
            "vib_non_drive_end_rms": {"mean": 1.8, "std": 0.5},
            "vib_peak_to_peak": {"mean": 45.0, "std": 12.0},
            "vib_kurtosis": {"mean": 3.0, "std": 0.4},
            "temp_bearing_drive_end": {"mean": 68.0, "std": 8.0},
            "temp_bearing_non_drive": {"mean": 64.0, "std": 7.0},
            "temp_lube_oil_supply": {"mean": 44.0, "std": 4.0},
            "press_lube_oil_bar": {"mean": 3.2, "std": 0.4},
            "press_discharge_bar": {"mean": 20.0, "std": 3.0},
            "motor_current_amps": {"mean": 180.0, "std": 25.0},
            "acoustic_emission_db": {"mean": 45.0, "std": 8.0}
        }

    def detect_anomalies(
        self,
        sensors: Dict[str, float]
    ) -> Tuple[bool, float, List[Dict[str, Any]]]:
        """
        Calculates multivariate Mahalanobis / Z-score composite distance,
        normalizes into [0.0 - 100.0] score, and returns top contributing sensors.
        """
        contributions = []
        squared_distances = []

        for sensor_id, stats in self.sensor_baselines.items():
            val = sensors.get(sensor_id, stats["mean"])
            z_score = abs(val - stats["mean"]) / stats["std"]
            sq_dist = z_score ** 2
            squared_distances.append(sq_dist)

            contributions.append({
                "sensor_id": sensor_id,
                "current_value": round(float(val), 2),
                "baseline_mean": stats["mean"],
                "deviation_z": round(float(z_score), 2),
                "severity_contribution": round(float(min(100.0, z_score * 25.0)), 1)
            })

        # Multivariate composite chi-squared like metric
        mean_sq_dist = float(np.mean(squared_distances)) if squared_distances else 0.0
        
        # Sigmoid compression into 0-100 scale
        # 1 standard deviation ~ 15-25 score, 3 standard deviations ~ 80+ score
        raw_anomaly_metric = np.sqrt(mean_sq_dist)
        normalized_score = float(np.clip((raw_anomaly_metric / 3.5) * 100.0, 0.0, 100.0))

        # Sort contributions descending
        contributions.sort(key=lambda x: x["deviation_z"], reverse=True)

        is_anomaly = normalized_score >= self.threshold

        return is_anomaly, round(normalized_score, 1), contributions[:5]
