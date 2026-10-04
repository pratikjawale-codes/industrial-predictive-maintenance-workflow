"""
Unit tests for Predictive Models: Multi-Horizon Risk, RUL, Anomaly Detection, and Failure Mode.
"""

from models.failure.multi_horizon import MultiHorizonFailureModel
from models.rul.probabilistic_rul import ProbabilisticRULModel
from models.anomaly.detector import MultivariateAnomalyDetector
from models.failure.failure_mode import FailureModeClassifier


def test_multi_horizon_monotonicity():
    model = MultiHorizonFailureModel()
    features = {
        "vib_de_rms_ewma_1h": 4.5,
        "vib_kurtosis": 5.2,
        "vib_de_trend_slope_24h": 0.4,
        "temp_bearing_delta_ambient": 48.0,
        "press_lube_oil_bar": 2.2,
        "vib_harmonic_ratio_2x_1x": 0.5
    }

    probs, risk_score, severity = model.predict_horizons(features)

    # Physical monotonicity check: P(24h) <= P(72h) <= P(7d) <= P(14d)
    assert probs["24h"] <= probs["72h"]
    assert probs["72h"] <= probs["7d"]
    assert probs["7d"] <= probs["14d"]
    assert 0.0 <= risk_score <= 100.0
    assert severity in ["NORMAL", "WATCHLIST", "ELEVATED", "CRITICAL"]


def test_probabilistic_rul_intervals():
    rul_model = ProbabilisticRULModel()
    features = {
        "vib_de_rms_ewma_1h": 3.8,
        "vib_kurtosis": 4.5,
        "vib_de_trend_slope_24h": 0.2,
        "temp_bearing_delta_ambient": 42.0
    }
    rul_info = rul_model.predict_rul(features, calibrated_risk=65.0)

    # Prediction interval check: P10 <= P50 <= P90
    assert rul_info["rul_days_p10"] <= rul_info["rul_days_median"]
    assert rul_info["rul_days_median"] <= rul_info["rul_days_p90"]
    assert 0.0 <= rul_info["failure_probability_before_window"] <= 1.0


def test_multivariate_anomaly_attribution():
    detector = MultivariateAnomalyDetector()
    sensors = {
        "vib_drive_end_rms": 8.5,  # extreme spike
        "temp_bearing_drive_end": 105.0,
        "vib_kurtosis": 8.0
    }
    is_anom, score, top_signals = detector.detect_anomalies(sensors)
    assert is_anom is True
    assert score > 60.0
    assert len(top_signals) > 0
    assert top_signals[0]["sensor_id"] in ["vib_drive_end_rms", "vib_kurtosis", "temp_bearing_drive_end"]
