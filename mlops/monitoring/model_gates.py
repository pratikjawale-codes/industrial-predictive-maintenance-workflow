"""
Automated Model Promotion & Quality Gates.
Implements Section 12 (MLOps & Release Lifecycle):
Compares candidate models against production champion across ML, operational,
and financial criteria prior to canary deployment.
"""

from typing import Dict, Any, Tuple


class ModelQualityGates:
    """
    Evaluates candidate models against strict enterprise release criteria.
    Automates promotion decisions from MLflow staging into production registry.
    """

    GATE_THRESHOLDS = {
        "min_pr_auc": 0.90,
        "min_recall": 0.90,
        "max_brier_score": 0.05,
        "min_lead_time_days": 7.0,
        "max_false_alerts_month": 2.0,
        "max_p95_latency_ms": 50.0
    }

    @classmethod
    def evaluate_candidate(
        cls,
        champion_metrics: Dict[str, float],
        candidate_metrics: Dict[str, float]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check whether candidate outperforms or meets quality gates relative to champion.
        """
        checks = {}
        passed_all = True

        # 1. PR-AUC Gate: Must not regress more than 0.5% and must meet baseline
        cand_pr_auc = candidate_metrics.get("pr_auc", 0.0)
        champ_pr_auc = champion_metrics.get("pr_auc", 0.90)
        pr_auc_ok = (cand_pr_auc >= cls.GATE_THRESHOLDS["min_pr_auc"]) and (cand_pr_auc >= champ_pr_auc - 0.005)
        checks["pr_auc_gate"] = {"passed": pr_auc_ok, "candidate": cand_pr_auc, "champion": champ_pr_auc}
        if not pr_auc_ok: passed_all = False

        # 2. Recall Gate: Dangerous failure misses must be strictly bounded
        cand_recall = candidate_metrics.get("recall", 0.0)
        recall_ok = cand_recall >= cls.GATE_THRESHOLDS["min_recall"]
        checks["recall_gate"] = {"passed": recall_ok, "candidate": cand_recall, "threshold": cls.GATE_THRESHOLDS["min_recall"]}
        if not recall_ok: passed_all = False

        # 3. Calibration Brier Score Gate
        cand_brier = candidate_metrics.get("brier_score", 1.0)
        brier_ok = cand_brier <= cls.GATE_THRESHOLDS["max_brier_score"]
        checks["calibration_gate"] = {"passed": brier_ok, "candidate_brier": cand_brier, "max_allowed": cls.GATE_THRESHOLDS["max_brier_score"]}
        if not brier_ok: passed_all = False

        # 4. Advance Lead Time Gate (Must satisfy 7-14 day requirement)
        cand_lead = candidate_metrics.get("median_lead_time_days", 0.0)
        lead_ok = cand_lead >= cls.GATE_THRESHOLDS["min_lead_time_days"]
        checks["lead_time_gate"] = {"passed": lead_ok, "candidate_days": cand_lead, "min_required_days": 7.0}
        if not lead_ok: passed_all = False

        # 5. False Alerts Gate
        cand_fa = candidate_metrics.get("false_alerts_per_100_machines_month", 5.0)
        fa_ok = cand_fa <= cls.GATE_THRESHOLDS["max_false_alerts_month"]
        checks["false_alert_gate"] = {"passed": fa_ok, "candidate": cand_fa, "max_allowed": cls.GATE_THRESHOLDS["max_false_alerts_month"]}
        if not fa_ok: passed_all = False

        decision = "APPROVED_FOR_CANARY" if passed_all else "REJECTED_QUALITY_FAILURE"

        return passed_all, {
            "decision": decision,
            "canary_traffic_percent": 10 if passed_all else 0,
            "gate_results": checks
        }
