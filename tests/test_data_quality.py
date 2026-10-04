"""
Unit tests for Sensor Data Quality and Ingestion Validation (Section 9 & 19).
"""

import pytest
from data.quality.validator import DataQualityValidator


def test_valid_telemetry_snapshot():
    validator = DataQualityValidator()
    valid_sensors = {
        "vib_drive_end_rms": 2.2,
        "vib_non_drive_end_rms": 1.8,
        "vib_peak_to_peak": 45.0,
        "vib_kurtosis": 3.0,
        "temp_bearing_drive_end": 68.0,
        "temp_bearing_non_drive": 64.0,
        "temp_lube_oil_supply": 42.0,
        "press_lube_oil_bar": 3.2,
        "press_discharge_bar": 20.0,
        "motor_current_amps": 180.0,
        "acoustic_emission_db": 42.0
    }
    is_valid, report = validator.validate_snapshot("GE-GT-0104", valid_sensors)
    assert is_valid is True
    assert len(report["violations"]) == 0
    assert report["missingness"]["vib_drive_end_rms_missing"] == 0


def test_range_violation_quarantined_to_dlq():
    validator = DataQualityValidator()
    corrupt_sensors = {
        "vib_drive_end_rms": 99.5,  # Max allowed is 25.0 mm/s
        "temp_bearing_drive_end": 68.0
    }
    is_valid, report = validator.validate_snapshot("GE-GT-0104", corrupt_sensors)
    assert is_valid is False
    assert any(v["type"] == "RANGE_VIOLATION" for v in report["violations"])

    dlq = validator.get_dlq_metrics()
    assert dlq["quarantined_count"] == 1
    assert dlq["recent_quarantines"][0]["asset_id"] == "GE-GT-0104"


def test_rate_of_change_spike_detection():
    validator = DataQualityValidator()
    sensors_initial = {
        "vib_drive_end_rms": 2.2,
        "temp_bearing_drive_end": 68.0
    }
    validator.validate_snapshot("GE-GT-0104", sensors_initial)

    # Spike from 2.2 to 14.5 instantly (max rate is 5.0)
    sensors_spike = {"vib_drive_end_rms": 14.5}
    is_valid, report = validator.validate_snapshot("GE-GT-0104", sensors_spike)
    assert is_valid is False
    assert any(v["type"] == "SPIKE_DETECTED" for v in report["violations"])


def test_rejected_snapshot_does_not_replace_last_valid_baseline():
    validator = DataQualityValidator()
    validator.validate_snapshot("GE-GT-0104", {"vib_drive_end_rms": 2.2})

    valid, _ = validator.validate_snapshot(
        "GE-GT-0104",
        {"vib_drive_end_rms": 99.5, "temp_bearing_drive_end": 68.0}
    )
    assert valid is False

    valid, _ = validator.validate_snapshot(
        "GE-GT-0104",
        {"vib_drive_end_rms": 7.2, "temp_bearing_drive_end": 68.0}
    )
    assert valid is True


def test_non_finite_sensor_value_is_quarantined():
    validator = DataQualityValidator()
    valid, report = validator.validate_snapshot(
        "GE-GT-0104",
        {"vib_drive_end_rms": float("nan"), "temp_bearing_drive_end": 68.0}
    )
    assert valid is False
    assert any(item["type"] == "RANGE_VIOLATION" for item in report["violations"])
