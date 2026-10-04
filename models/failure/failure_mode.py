"""
Failure-Mode Taxonomy Classifier.
Implements Section 4 & 5: Multiclass categorization of industrial degradation modes.
"""

from typing import Dict, Tuple
import numpy as np


FAILURE_MODES = [
    "BEARING_SPALLING_FATIGUE",
    "THERMAL_OVERHEATING",
    "LUBRICATION_STARVATION",
    "ROTOR_IMBALANCE_MISALIGNMENT",
    "SEAL_LEAKAGE_PRESSURE_LOSS",
    "STATOR_WINDING_INSULATION_FAULT"
]


class FailureModeClassifier:
    """
    Diagnoses the underlying physical failure mode:
    1. BEARING_SPALLING_FATIGUE: High Kurtosis, Crest Factor, High Acoustic Emission
    2. THERMAL_OVERHEATING: Bearing delta T > 45°C, Lube oil return overheating
    3. LUBRICATION_STARVATION: Lube pressure drop < 2.0 bar, friction acoustic rise
    4. ROTOR_IMBALANCE_MISALIGNMENT: 1X/2X rotational harmonics elevation, nde vibration
    5. SEAL_LEAKAGE_PRESSURE_LOSS: Discharge pressure drop, differential pressure rise
    6. STATOR_WINDING_INSULATION_FAULT: Phase current unbalance > 3%, thermal hotspots
    """

    def predict_mode(self, features: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
        """
        Evaluate physical indicators and return softmax-like probability
        distribution across failure modes.
        """
        # Feature extraction
        kurtosis = features.get("vib_kurtosis", 3.0)
        crest = features.get("vib_crest_factor", 2.5)
        harm_2x = features.get("vib_harmonic_ratio_2x_1x", 0.3)
        temp_delta = features.get("temp_bearing_delta_ambient", 35.0)
        p_lube = features.get("press_lube_oil_bar", 3.2)
        press_diff = features.get("press_diff_filter_normalized", 0.4)
        curr_unbal = features.get("motor_current_unbalance_pct", 0.8)
        acoustic = features.get("acoustic_high_freq_db", 42.0)

        # Raw evidence scores for each mode
        scores = {
            "BEARING_SPALLING_FATIGUE": (
                max(0.0, kurtosis - 3.0) * 1.8 +
                max(0.0, crest - 2.5) * 1.5 +
                max(0.0, acoustic - 50.0) * 0.08
            ),
            "THERMAL_OVERHEATING": (
                max(0.0, temp_delta - 40.0) * 0.12 +
                max(0.0, acoustic - 45.0) * 0.03
            ),
            "LUBRICATION_STARVATION": (
                max(0.0, 2.8 - p_lube) * 2.2 +
                max(0.0, temp_delta - 42.0) * 0.08
            ),
            "ROTOR_IMBALANCE_MISALIGNMENT": (
                max(0.0, harm_2x - 0.45) * 4.0 +
                max(0.0, features.get("vib_de_rms_ewma_1h", 2.0) - 3.0) * 0.8
            ),
            "SEAL_LEAKAGE_PRESSURE_LOSS": (
                max(0.0, press_diff - 0.6) * 3.5 +
                max(0.0, features.get("temp_exhaust_spread_max", 14.0) - 22.0) * 0.1
            ),
            "STATOR_WINDING_INSULATION_FAULT": (
                max(0.0, curr_unbal - 1.5) * 3.0 +
                max(0.0, temp_delta - 48.0) * 0.06
            )
        }

        # Temperature baseline fallback
        raw_vals = np.array(list(scores.values()))
        if np.max(raw_vals) <= 0.05:
            # Baseline normal state: distributed evenly
            probs = {k: 0.166 for k in FAILURE_MODES}
            top_mode = "BEARING_SPALLING_FATIGUE"
        else:
            # Softmax calculation
            exp_vals = np.exp(raw_vals - np.max(raw_vals))
            softmax = exp_vals / np.sum(exp_vals)
            probs = {k: round(float(p), 3) for k, p in zip(scores.keys(), softmax)}
            top_mode = max(probs, key=probs.get)

        return top_mode, probs
