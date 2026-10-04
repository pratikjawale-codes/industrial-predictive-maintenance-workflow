"""
Maintenance Recommendation and Cost-Sensitive Decision Engine.
Implements Section 5 & 15: Separation of risk from action, hysteresis,
alert deduplication, and financial cost-optimization.
"""

from typing import Dict, Any


class MaintenanceDecisionEngine:
    """
    Translates calibrated probabilities and degradation metrics into
    governed industrial maintenance decisions and SAP PM work orders.
    """

    def __init__(self):
        # In-memory hysteresis tracking: asset_id -> { "consecutive_alerts": int, "last_alert_time": str }
        self.hysteresis_state: Dict[str, Dict[str, Any]] = {}

        # Standard action catalog mapped to failure modes
        self.action_catalog = {
            "BEARING_SPALLING_FATIGUE": {
                "action": "Perform High-Frequency Ultrasonic Scan & Schedule Bearing Replacement",
                "sop_code": "GE-SOP-BRG-402",
                "recommended_window_hours": 72,
                "parts_required": ["Spherical Roller Bearing SKF 23152", "High-Temp Synthetic Grease Mobil SHC 220"]
            },
            "THERMAL_OVERHEATING": {
                "action": "Inspect Lube Cooler Thermostatic Valve & Flush Bearing Oil Cavity",
                "sop_code": "GE-SOP-LUB-118",
                "recommended_window_hours": 48,
                "parts_required": ["Thermostatic Element 65C", "Oil Sampling Kit"]
            },
            "LUBRICATION_STARVATION": {
                "action": "Emergency Lube Header Flow Check & Replace In-Line Filter Cartridge",
                "sop_code": "GE-SOP-FLTR-091",
                "recommended_window_hours": 24,
                "parts_required": ["Duplex Filter Cartridge 10-Micron", "Filter Differential Indicator"]
            },
            "ROTOR_IMBALANCE_MISALIGNMENT": {
                "action": "Perform Dynamic Multi-Plane Laser Alignment & Check Coupling Shim Packs",
                "sop_code": "GE-SOP-ALIGN-205",
                "recommended_window_hours": 96,
                "parts_required": ["Precision Stainless Shims Kit", "Coupling Disc Pack"]
            },
            "SEAL_LEAKAGE_PRESSURE_LOSS": {
                "action": "Inspect Dry Gas Seal Buffer Gas Pressure & Replace Labyrinth Seals",
                "sop_code": "GE-SOP-SEAL-312",
                "recommended_window_hours": 48,
                "parts_required": ["Labyrinth Seal Ring Kit", "O-Ring Viton Set"]
            },
            "STATOR_WINDING_INSULATION_FAULT": {
                "action": "Perform Megger Insulation Resistance Test & Stator Surge Comparison",
                "sop_code": "GE-SOP-ELEC-501",
                "recommended_window_hours": 36,
                "parts_required": ["Class H Insulation Resins", "RTD Terminal Block"]
            }
        }

    def evaluate_decision(
        self,
        asset_id: str,
        asset_metadata: Dict[str, Any],
        horizon_probs: Dict[str, float],
        risk_score: float,
        rul_info: Dict[str, float],
        failure_mode: str,
        is_anomaly: bool,
        track_hysteresis: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate cost-sensitive decision logic, apply alert hysteresis,
        and generate recommended maintenance action with ROI impact.
        """
        criticality = asset_metadata.get("criticality", "Tier 2 (Essential)")
        
        # Financial cost parameters by criticality
        if "Tier 1" in criticality:
            unplanned_downtime_hourly_cost = 15000.0  # $15,000/hr for major Gas Turbine
            typical_breakdown_hours = 36.0           # 36 hours repair time
            planned_inspection_cost = 4500.0
        elif "Tier 2" in criticality:
            unplanned_downtime_hourly_cost = 6500.0
            typical_breakdown_hours = 24.0
            planned_inspection_cost = 2500.0
        else:
            unplanned_downtime_hourly_cost = 2000.0
            typical_breakdown_hours = 12.0
            planned_inspection_cost = 1000.0

        p_fail_24h = horizon_probs.get("24h", 0.0)
        p_fail_7d = horizon_probs.get("7d", 0.0)
        rul_days = rul_info.get("rul_days_median", 30.0)

        # Hysteresis update: check consecutive alerts
        if track_hysteresis and asset_id not in self.hysteresis_state:
            self.hysteresis_state[asset_id] = {"consecutive_alerts": 0, "last_timestamp": None}

        is_elevated = (risk_score >= 40.0) or (p_fail_7d > 0.35) or is_anomaly
        if track_hysteresis:
            if is_elevated:
                self.hysteresis_state[asset_id]["consecutive_alerts"] += 1
            else:
                self.hysteresis_state[asset_id]["consecutive_alerts"] = max(
                    0, self.hysteresis_state[asset_id]["consecutive_alerts"] - 1
                )

        consecutive = self.hysteresis_state.get(asset_id, {}).get("consecutive_alerts", 0)

        # Alert Suppression / Hysteresis Policy:
        # Require at least 2 consecutive cycles for P2 Warning, 3 for P1 Emergency
        # unless risk_score >= 80% (imminent catastrophic failure)
        alert_triggered = False
        alert_level = "NORMAL"

        if risk_score >= 75.0 or (p_fail_24h >= 0.50 and consecutive >= 2):
            alert_triggered = True
            alert_level = "CRITICAL_P1"
        elif (risk_score >= 45.0 or p_fail_7d >= 0.40) and consecutive >= 2:
            alert_triggered = True
            alert_level = "WARNING_P2"
        elif (risk_score >= 25.0 or is_anomaly) and consecutive >= 1:
            alert_triggered = True
            alert_level = "ADVISORY_P3"

        # Action lookup
        action_details = self.action_catalog.get(failure_mode, self.action_catalog["BEARING_SPALLING_FATIGUE"])
        
        # Dynamic window calculation based on RUL
        recommended_window = min(
            action_details["recommended_window_hours"],
            int(max(12, rul_days * 24.0 * 0.5))
        )

        # Cost-benefit analysis
        potential_loss = unplanned_downtime_hourly_cost * typical_breakdown_hours
        expected_unmitigated_cost = potential_loss * p_fail_7d
        avoided_cost_net = max(0.0, expected_unmitigated_cost - planned_inspection_cost)

        return {
            "alert_triggered": alert_triggered,
            "alert_level": alert_level,
            "consecutive_cycles": consecutive,
            "recommended_action": action_details["action"],
            "sop_code": action_details["sop_code"],
            "maintenance_window_hours": recommended_window,
            "required_parts": action_details["parts_required"],
            "human_in_loop_required": (alert_level in ["CRITICAL_P1", "WARNING_P2"]),
            "financial_impact": {
                "unplanned_downtime_hourly_rate_usd": unplanned_downtime_hourly_cost,
                "potential_unplanned_loss_usd": potential_loss,
                "planned_intervention_cost_usd": planned_inspection_cost,
                "projected_cost_avoidance_usd": round(avoided_cost_net, 2)
            }
        }
