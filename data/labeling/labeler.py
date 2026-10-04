"""
Point-in-Time Labeling and Temporal Data Leakage Prevention Engine.
Implements Section 10 (Labeling & Leakage Prevention):
- Observation window vs Prediction horizon
- Positive / Negative label definitions
- Right-censoring handling
- Exclusion of post-prediction maintenance records
"""

from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


class PointInTimeLabeler:
    """
    Constructs training instances from raw telemetry and maintenance logs
    with strict temporal fences to prevent lookahead data leakage.
    """

    def __init__(
        self,
        observation_window_days: int = 7,
        prediction_horizons_days: List[int] = [1, 3, 7, 14]
    ):
        self.obs_days = observation_window_days
        self.horizons = prediction_horizons_days

    def create_labeled_instance(
        self,
        prediction_cutoff: datetime,
        asset_telemetry: pd.DataFrame,
        maintenance_events: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract features strictly prior to prediction_cutoff.
        Assign failure labels strictly within [prediction_cutoff, prediction_cutoff + horizon].
        Disregard maintenance events generated after the cutoff when building feature sets.
        """
        obs_start = prediction_cutoff - timedelta(days=self.obs_days)

        # 1. Temporal feature fence (MUST be strictly <= prediction_cutoff)
        telemetry_window = asset_telemetry[
            (asset_telemetry["timestamp"] >= obs_start) &
            (asset_telemetry["timestamp"] <= prediction_cutoff)
        ]

        if len(telemetry_window) < 10:
            # Insufficient historical observation depth
            return None

        # 2. Extract strictly retrospective features
        features = {
            "vib_de_rms_mean": float(telemetry_window["vib_drive_end_rms"].mean()),
            "vib_de_rms_max": float(telemetry_window["vib_drive_end_rms"].max()),
            "vib_kurtosis_mean": float(telemetry_window["vib_kurtosis"].mean()),
            "temp_bearing_mean": float(telemetry_window["temp_bearing_drive_end"].mean()),
            "press_lube_mean": float(telemetry_window["press_lube_oil_bar"].mean())
        }

        # 3. Label generation over multiple prospective horizons
        labels = {}
        for h in self.horizons:
            horizon_end = prediction_cutoff + timedelta(days=h)
            
            # Check for confirmed failure in this horizon
            failure_in_horizon = False
            censored = False

            for event in maintenance_events:
                event_time = datetime.fromisoformat(event["event_timestamp"])
                
                # Exclude events that happened BEFORE cutoff (already part of history)
                if event_time <= prediction_cutoff:
                    continue
                
                # If equipment was decommissioned or data stream stopped early (Censoring)
                if event.get("event_type") == "ASSET_DECOMMISSIONED" and event_time <= horizon_end:
                    censored = True
                    break

                if event.get("event_type") == "CONFIRMED_FAILURE" and prediction_cutoff < event_time <= horizon_end:
                    failure_in_horizon = True
                    break

            if censored:
                labels[f"label_fail_{h}d"] = np.nan  # Exclude censored from supervised loss
            else:
                labels[f"label_fail_{h}d"] = 1 if failure_in_horizon else 0

        return {
            "prediction_cutoff": prediction_cutoff.isoformat(),
            "features": features,
            "labels": labels
        }
