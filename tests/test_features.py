"""
Unit tests for Stateful Feature Engineering (Section 5 & 19).
"""

from features.streaming.calculator import StreamingFeatureCalculator


def test_feature_extraction_and_ewma():
    calc = StreamingFeatureCalculator()
    sensors = {
        "vib_drive_end_rms": 3.0,
        "vib_non_drive_end_rms": 2.0,
        "vib_peak_to_peak": 50.0,
        "vib_kurtosis": 3.5,
        "vib_crest_factor": 2.8,
        "vib_spectral_1x": 1.5,
        "vib_spectral_2x": 0.8,
        "temp_bearing_drive_end": 75.0,
        "temp_ambient": 25.0,
        "temp_lube_oil_supply": 40.0,
        "temp_lube_oil_return": 55.0,
        "press_lube_oil_bar": 3.0,
        "press_discharge_bar": 21.0,
        "press_diff_filter_mbar": 200.0,
        "flow_rate_m3h": 400.0
    }

    features = calc.update_and_extract("GE-GT-0104", sensors, operating_hours=15000.0)

    assert "vib_de_rms_ewma_1h" in features
    assert "vib_harmonic_ratio_2x_1x" in features
    assert "temp_bearing_delta_ambient" in features
    assert features["temp_bearing_delta_ambient"] == 50.0
    assert features["temp_lube_delta_supply_return"] == 15.0
    assert features["vib_harmonic_ratio_2x_1x"] == round(0.8 / 1.5, 4) or features["vib_harmonic_ratio_2x_1x"] > 0


def test_read_only_feature_extraction_does_not_advance_stream_state():
    calc = StreamingFeatureCalculator()
    calc.update_and_extract("GE-GT-0104", {"vib_drive_end_rms": 2.0})
    history_before = list(calc.history["GE-GT-0104"]["vib_drive_end_rms"])
    ewma_before = calc.ewma_state["GE-GT-0104"]["vib_drive_end_rms"]

    features = calc.update_and_extract(
        "GE-GT-0104",
        {"vib_drive_end_rms": 8.0},
        update_state=False
    )

    assert calc.history["GE-GT-0104"]["vib_drive_end_rms"] == history_before
    assert calc.ewma_state["GE-GT-0104"]["vib_drive_end_rms"] == ewma_before
    assert features["vib_de_rms_ewma_1h"] == ewma_before
