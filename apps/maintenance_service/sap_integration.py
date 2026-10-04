"""
SAP PM Work-Order Integration and Closed-Loop Maintenance Feedback Service.
Implements Section 2, 4, 15 & 17: Work-order routing, engineer acknowledgements,
and verified label feedback for continuous learning.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid


class MaintenanceWorkOrderService:
    """
    Simulates enterprise SAP Plant Maintenance (SAP PM) integration,
    manages alert queues, generates maintenance work orders, and collects
    closed-loop ground-truth labels from completed inspections.
    """

    def __init__(self):
        # In-memory stores
        self.alerts: List[Dict[str, Any]] = []
        self.work_orders: List[Dict[str, Any]] = []
        self.feedback_labels: List[Dict[str, Any]] = []

        # Populate realistic initial seed work orders & alerts
        self._seed_initial_records()

    def _seed_initial_records(self):
        """Pre-populate sample enterprise state for demonstration."""
        sample_alerts = [
            {
                "alert_id": "ALT-2026-0891",
                "asset_id": "GE-GT-0104",
                "asset_name": "Gas Turbine Frame 7HA.03 (Unit 1)",
                "plant_name": "Greenville Gas Plant, SC",
                "severity": "CRITICAL_P1",
                "failure_mode": "BEARING_SPALLING_FATIGUE",
                "risk_score": 88.4,
                "p_fail_7d": 0.82,
                "rul_days": 4.2,
                "status": "OPEN",
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "recommended_action": "Perform High-Frequency Ultrasonic Scan & Schedule Bearing Replacement",
                "notes": "Spike in Kurtosis (8.4) and 2X rotational harmonic. Emergency inspection required."
            },
            {
                "alert_id": "ALT-2026-0892",
                "asset_id": "GE-CP-0201",
                "asset_name": "Centrifugal Gas Compressor B-4",
                "plant_name": "Atlanta Power Station, GA",
                "severity": "WARNING_P2",
                "failure_mode": "THERMAL_OVERHEATING",
                "risk_score": 58.2,
                "p_fail_7d": 0.48,
                "rul_days": 11.5,
                "status": "ACKNOWLEDGED",
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "recommended_action": "Inspect Lube Cooler Thermostatic Valve & Flush Bearing Oil Cavity",
                "notes": "Bearing temperature elevated +18°C above normal thermal baseline."
            }
        ]
        self.alerts.extend(sample_alerts)

        sample_wo = [
            {
                "work_order_id": "WO-SAP-89201",
                "sap_notification_id": "NOTIF-1004829",
                "asset_id": "GE-BFP-0302",
                "asset_name": "Boiler Feed Pump Stage 4",
                "plant_name": "Schenectady Turbine Works, NY",
                "priority": "HIGH",
                "status": "RELEASED",
                "failure_mode": "ROTOR_IMBALANCE_MISALIGNMENT",
                "recommended_action": "Dynamic Multi-Plane Laser Alignment",
                "assigned_work_center": "WC-MECH-TURBO-01",
                "maintenance_window_hours": 48,
                "estimated_downtime_hours": 8.0,
                "estimated_cost_usd": 6800.0,
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "notes": "Laser alignment tools reserved in tool crib."
            }
        ]
        self.work_orders.extend(sample_wo)

    def record_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record or update an alert from the decision engine."""
        alert_id = f"ALT-2026-{len(self.alerts) + 890:04d}"
        alert_record = {
            "alert_id": alert_id,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "OPEN",
            **alert_data
        }
        self.alerts.insert(0, alert_record)
        return alert_record

    def acknowledge_alert(self, alert_id: str, engineer_id: str, notes: str = "") -> Optional[Dict[str, Any]]:
        """Engineer acknowledgement of alert."""
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                alert["status"] = "ACKNOWLEDGED"
                alert["acknowledged_by"] = engineer_id
                alert["acknowledged_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                if notes:
                    alert["notes"] = f"{alert.get('notes', '')} | {notes}"
                return alert
        return None

    def create_work_order(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new maintenance work order routed to SAP PM.
        Generates SAP Notification ID and reserves scheduled maintenance window.
        """
        wo_counter = len(self.work_orders) + 89202
        wo_id = f"WO-SAP-{wo_counter}"
        notif_id = f"NOTIF-{uuid.uuid4().hex[:8].upper()}"

        priority = request_data.get("priority", "HIGH")
        downtime_map = {"EMERGENCY": 16.0, "HIGH": 8.0, "MEDIUM": 4.0, "LOW": 2.0}
        cost_map = {"EMERGENCY": 18500.0, "HIGH": 7500.0, "MEDIUM": 3200.0, "LOW": 1200.0}

        wo_record = {
            "work_order_id": wo_id,
            "sap_notification_id": notif_id,
            "asset_id": request_data["asset_id"],
            "alert_id": request_data.get("alert_id"),
            "failure_mode": request_data.get("failure_mode", "BEARING_SPALLING_FATIGUE"),
            "priority": priority,
            "status": "RELEASED",
            "recommended_action": request_data.get("recommended_action", "Inspect and Replace Component"),
            "assigned_work_center": request_data.get("assigned_work_center", "WC-MAIN-PLANT"),
            "maintenance_window_hours": request_data.get("maintenance_window_hours", 48),
            "estimated_downtime_hours": downtime_map.get(priority, 6.0),
            "estimated_cost_usd": cost_map.get(priority, 5000.0),
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "notes": request_data.get("notes", "")
        }

        self.work_orders.insert(0, wo_record)

        # Update associated alert if provided
        if request_data.get("alert_id"):
            for alt in self.alerts:
                if alt["alert_id"] == request_data["alert_id"]:
                    alt["status"] = "WORK_ORDER_DISPATCHED"
                    alt["work_order_id"] = wo_id

        return wo_record

    def submit_maintenance_feedback(
        self,
        work_order_id: str,
        asset_id: str,
        actual_outcome: str,          # TRUE_POSITIVE_FAILURE, PREVENTED_DEGRADATION, FALSE_ALERT_NO_DEFECT
        confirmed_failure_mode: str,
        technician_findings: str,
        parts_replaced: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Closed-loop outcome capture: Record verified inspection results.
        Feeds directly into the label store for continuous model retraining.
        """
        work_order = next(
            (wo for wo in self.work_orders if wo["work_order_id"] == work_order_id),
            None
        )
        if work_order is None:
            return None
        if work_order["asset_id"] != asset_id:
            raise ValueError(
                f"Work order {work_order_id} belongs to asset {work_order['asset_id']}"
            )
        if work_order["status"] == "COMPLETED":
            raise ValueError(f"Work order {work_order_id} is already completed")

        feedback_record = {
            "feedback_id": f"FBK-{uuid.uuid4().hex[:6].upper()}",
            "work_order_id": work_order_id,
            "asset_id": asset_id,
            "outcome": actual_outcome,
            "confirmed_failure_mode": confirmed_failure_mode,
            "technician_findings": technician_findings,
            "parts_replaced": parts_replaced,
            "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "retraining_eligible": True
        }

        self.feedback_labels.append(feedback_record)

        # Update work order status
        work_order["status"] = "COMPLETED"
        work_order["actual_outcome"] = actual_outcome
        work_order["findings"] = technician_findings

        return feedback_record

    def get_all_alerts(self) -> List[Dict[str, Any]]:
        return self.alerts

    def get_all_work_orders(self) -> List[Dict[str, Any]]:
        return self.work_orders

    def get_label_store(self) -> List[Dict[str, Any]]:
        return self.feedback_labels
