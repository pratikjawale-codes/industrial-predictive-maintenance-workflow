"""
Integration tests for FastAPI endpoints matching Section 17 of the GE Project Plan.
"""

from copy import deepcopy

from fastapi.testclient import TestClient
from apps.inference_api.main import app
from apps.inference_api.main import decision_engine

client = TestClient(app)


def test_liveness_and_readiness_probes():
    r_live = client.get("/health/live")
    assert r_live.status_code == 200
    assert r_live.json()["status"] == "UP"

    r_ready = client.get("/health/ready")
    assert r_ready.status_code == 200
    assert r_ready.json()["status"] == "READY"


def test_dashboard_serves_current_operations_view():
    response = client.get("/")
    assert response.status_code == 200
    assert "Keep critical assets" in response.text
    assert "Find asset or site" in response.text
    assert "DEMO v2.4" in response.text


def test_predict_multi_horizon_endpoint():
    payload = {
        "asset_id": "GE-GT-0104",
        "sensors": {
            "vib_drive_end_rms": 4.5,
            "vib_non_drive_end_rms": 2.2,
            "vib_kurtosis": 5.8,
            "vib_crest_factor": 3.9,
            "vib_spectral_1x": 1.8,
            "vib_spectral_2x": 1.2,
            "temp_bearing_drive_end": 82.0,
            "temp_ambient": 24.0,
            "press_lube_oil_bar": 2.9
        }
    }
    res = client.post("/v1/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "horizon_probabilities" in data
    assert "24h" in data["horizon_probabilities"]
    assert "7d" in data["horizon_probabilities"]
    assert "predicted_failure_mode" in data
    assert "calibrated_risk_score" in data


def test_predict_rejects_invalid_telemetry():
    res = client.post(
        "/v1/predict",
        json={
            "asset_id": "GE-TEST-INVALID",
            "sensors": {
                "vib_drive_end_rms": 99.5,
                "temp_bearing_drive_end": 68.0
            }
        }
    )
    assert res.status_code == 422
    assert res.json()["detail"]["message"] == "Telemetry failed data-quality validation"


def test_rul_endpoint():
    payload = {
        "asset_id": "GE-GT-0104",
        "sensors": {
            "vib_drive_end_rms": 4.2,
            "temp_bearing_drive_end": 78.0
        }
    }
    res = client.post("/v1/rul", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["rul_days_median"] > 0
    assert data["rul_days_p10"] <= data["rul_days_median"]
    assert "failure_probability_before_window" in data


def test_anomaly_endpoint():
    payload = {
        "asset_id": "GE-GT-0104",
        "sensors": {
            "vib_drive_end_rms": 7.8,
            "vib_kurtosis": 8.1
        }
    }
    res = client.post("/v1/anomaly", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "is_anomaly" in data
    assert "contributing_signals" in data


def test_rul_endpoint_rejects_out_of_range_telemetry():
    response = client.post(
        "/v1/rul",
        json={
            "asset_id": "GE-GT-INVALID-RUL",
            "sensors": {
                "vib_drive_end_rms": 100.0,
                "temp_bearing_drive_end": 68.0
            }
        }
    )
    assert response.status_code == 422


def test_asset_health_and_explanation():
    history_before = deepcopy(decision_engine.hysteresis_state)
    r_health = client.get("/v1/assets/GE-GT-0104/health")
    assert r_health.status_code == 200
    h_data = r_health.json()
    assert h_data["asset_id"] == "GE-GT-0104"
    assert "health_score" in h_data
    assert "recommended_action" in h_data
    assert h_data["horizon_probabilities"]["24h"] <= h_data["horizon_probabilities"]["7d"]
    assert h_data["rul_days_p10"] <= h_data["rul_days_p50"] <= h_data["rul_days_p90"]
    assert decision_engine.hysteresis_state == history_before

    r_explain = client.get("/v1/assets/GE-GT-0104/explanation")
    assert r_explain.status_code == 200
    e_data = r_explain.json()
    assert "feature_attributions" in e_data
    assert "evidence_window" in e_data


def test_work_order_workflow_and_feedback():
    # 1. Create work order
    wo_req = {
        "asset_id": "GE-GT-0104",
        "failure_mode": "BEARING_SPALLING_FATIGUE",
        "priority": "HIGH",
        "recommended_action": "Borescope Inspection & Ultrasonic Bearing Scan",
        "maintenance_window_hours": 48,
        "assigned_work_center": "WC-MECH-TURBO-01"
    }
    res = client.post("/v1/work-orders", json=wo_req)
    assert res.status_code == 200
    wo = res.json()
    assert wo["work_order_id"].startswith("WO-SAP-")
    assert wo["sap_notification_id"].startswith("NOTIF-")

    # 2. Submit verified feedback into label store
    fb_req = {
        "asset_id": "GE-GT-0104",
        "actual_outcome": "TRUE_POSITIVE_FAILURE",
        "confirmed_failure_mode": "BEARING_SPALLING_FATIGUE",
        "technician_findings": "Confirmed outer race spalling. Bearing replaced.",
        "parts_replaced": ["Bearing SKF 23152"]
    }
    fb_res = client.post(f"/v1/work-orders/{wo['work_order_id']}/feedback", json=fb_req)
    assert fb_res.status_code == 200
    assert fb_res.json()["status"] == "SUCCESS"
    duplicate_res = client.post(f"/v1/work-orders/{wo['work_order_id']}/feedback", json=fb_req)
    assert duplicate_res.status_code == 409


def test_feedback_and_fault_simulation_reject_unknown_records():
    feedback = {
        "asset_id": "GE-GT-0104",
        "actual_outcome": "TRUE_POSITIVE_FAILURE",
        "confirmed_failure_mode": "BEARING_SPALLING_FATIGUE",
        "technician_findings": "Verified during inspection.",
        "parts_replaced": []
    }
    response = client.post("/v1/work-orders/WO-DOES-NOT-EXIST/feedback", json=feedback)
    assert response.status_code == 404

    response = client.post(
        "/v1/simulate/fault",
        json={"asset_id": "GE-DOES-NOT-EXIST", "fault_type": "BEARING_DAMAGE"}
    )
    assert response.status_code == 404

    response = client.post(
        "/v1/simulate/fault",
        json={"asset_id": "GE-GT-0104", "fault_type": "UNKNOWN"}
    )
    assert response.status_code == 422


def test_alert_acknowledgement_uses_path_identifier():
    response = client.post(
        "/v1/alerts/ALT-2026-0891/ack",
        json={"engineer_id": "ENG-TEST-01", "notes": "Reviewed"}
    )
    assert response.status_code == 200
    assert response.json()["alert"]["alert_id"] == "ALT-2026-0891"


def test_work_order_requires_known_asset():
    response = client.post(
        "/v1/work-orders",
        json={
            "asset_id": "GE-NOT-REAL",
            "failure_mode": "BEARING_SPALLING_FATIGUE",
            "priority": "HIGH",
            "recommended_action": "Inspect bearing",
            "maintenance_window_hours": 48,
            "assigned_work_center": "WC-MECH-TURBO-01"
        }
    )
    assert response.status_code == 404


def test_feedback_must_match_work_order_asset():
    response = client.post(
        "/v1/work-orders/WO-SAP-89201/feedback",
        json={
            "asset_id": "GE-GT-0104",
            "actual_outcome": "TRUE_POSITIVE_FAILURE",
            "confirmed_failure_mode": "BEARING_SPALLING_FATIGUE",
            "technician_findings": "Verified finding.",
            "parts_replaced": []
        }
    )
    assert response.status_code == 404


def test_model_version_registry():
    res = client.get("/v1/models/failure-multi-horizon/version")
    assert res.status_code == 200
    data = res.json()
    assert data["active_version"] == "v2.4.1-champion"
    assert data["details"]["median_lead_time_days"] == 11.2


def test_copilot_chat():
    res = client.post("/v1/copilot/chat", json={"query": "How to inspect bearing clearances on Frame 7HA turbine?"})
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert len(data["citations"]) > 0
    assert "GEK-10998" in data["citations"][0]["citation"]
