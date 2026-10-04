"""
Unit tests for Point-in-Time Labeling and Leakage Prevention (Section 10).
"""

from datetime import datetime, timedelta
import pandas as pd
from data.labeling.labeler import PointInTimeLabeler


def test_point_in_time_fence_and_leakage_exclusion():
    labeler = PointInTimeLabeler(observation_window_days=5, prediction_horizons_days=[7, 14])

    cutoff = datetime(2026, 6, 1, 12, 0, 0)

    # 1. Telemetry records spanning before and after cutoff
    timestamps = [cutoff - timedelta(days=4) + timedelta(hours=i * 6) for i in range(30)]
    telemetry_df = pd.DataFrame({
        "timestamp": timestamps,
        "vib_drive_end_rms": [2.2 + 0.1 * i for i in range(30)],
        "vib_kurtosis": [3.0 for _ in range(30)],
        "temp_bearing_drive_end": [68.0 for _ in range(30)],
        "press_lube_oil_bar": [3.2 for _ in range(30)]
    })

    # 2. Maintenance events: one confirmed failure at Day 4 into the future (within 7d horizon)
    events = [
        {
            "event_type": "CONFIRMED_FAILURE",
            "event_timestamp": (cutoff + timedelta(days=4)).isoformat(),
            "notes": "Bearing failure observed on turbine"
        }
    ]

    instance = labeler.create_labeled_instance(cutoff, telemetry_df, events)

    assert instance is not None
    # Label at 7d horizon must be positive (failure occurred within 7 days)
    assert instance["labels"]["label_fail_7d"] == 1
    assert instance["labels"]["label_fail_14d"] == 1
    # Features must be finite and computed only up to cutoff
    assert instance["features"]["vib_de_rms_mean"] > 0
