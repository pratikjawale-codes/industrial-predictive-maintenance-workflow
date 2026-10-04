"""
Unit tests for Automated Model Quality Gates and Canary Criteria (Section 12).
"""

from mlops.monitoring.model_gates import ModelQualityGates


def test_model_quality_gate_approval():
    champion = {
        "pr_auc": 0.940,
        "recall": 0.930,
        "brier_score": 0.042,
        "median_lead_time_days": 11.2,
        "false_alerts_per_100_machines_month": 1.4
    }

    # Better candidate
    candidate_pass = {
        "pr_auc": 0.952,
        "recall": 0.945,
        "brier_score": 0.038,
        "median_lead_time_days": 12.0,
        "false_alerts_per_100_machines_month": 1.1
    }

    passed, report = ModelQualityGates.evaluate_candidate(champion, candidate_pass)
    assert passed is True
    assert report["decision"] == "APPROVED_FOR_CANARY"
    assert report["canary_traffic_percent"] == 10


def test_model_quality_gate_rejection_on_recall_regression():
    champion = {"pr_auc": 0.940, "recall": 0.930, "brier_score": 0.042, "median_lead_time_days": 11.2, "false_alerts_per_100_machines_month": 1.4}
    
    # Degraded candidate missing dangerous failures (recall < 0.90)
    candidate_fail = {
        "pr_auc": 0.945,
        "recall": 0.840,  # Below 0.90 threshold
        "brier_score": 0.040,
        "median_lead_time_days": 11.0,
        "false_alerts_per_100_machines_month": 1.2
    }

    passed, report = ModelQualityGates.evaluate_candidate(champion, candidate_fail)
    assert passed is False
    assert report["decision"] == "REJECTED_QUALITY_FAILURE"
    assert report["gate_results"]["recall_gate"]["passed"] is False
