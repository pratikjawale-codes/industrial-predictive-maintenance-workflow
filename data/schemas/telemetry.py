"""
Data contracts and Pydantic schemas for the GE AI Predictive Maintenance Platform.
Implements Section 9 and Section 17 specifications.
"""

from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    """Raw sensor telemetry event matching Section 9."""
    asset_id: str = Field(..., description="Unique asset identifier, e.g., GE-GT-0104")
    sensor_id: str = Field(..., description="Sensor tag, e.g., VIB_BRG_DE_RMS")
    event_timestamp: datetime = Field(..., description="Sensor event timestamp (event-time semantics)")
    ingestion_timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Platform ingestion timestamp"
    )
    value: float = Field(..., description="Sensor reading value")
    unit: str = Field(..., description="Engineering unit, e.g., mm/s, degC, bar, A")
    quality_code: int = Field(default=192, description="OPC quality code (192 = Good, 0 = Bad, 64 = Uncertain)")
    source_system: str = Field(default="SCADA_MODBUS", description="Ingestion source (SCADA, PLC, IoT_EDGE, MES)")


class AssetMetadata(BaseModel):
    """Digital twin asset metadata."""
    asset_id: str
    asset_name: str
    plant_id: str
    plant_name: str
    asset_family: str  # Gas Turbine, Centrifugal Compressor, Feed Pump, Wind Turbine, Motor
    criticality: str   # Tier 1 (Critical), Tier 2 (Essential), Tier 3 (Balance of Plant)
    operating_hours: float
    last_maintenance_date: str
    status: str        # OPERATIONAL, WARNING, CRITICAL, UNDER_MAINTENANCE
    latitude: float
    longitude: float


class MultiHorizonPredictionRequest(BaseModel):
    """Prediction request for multi-horizon risk and degradation assessment."""
    asset_id: str
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    sensors: Dict[str, float] = Field(
        ...,
        description="Sensor snapshot dictionary containing vibration, temperature, pressure, motor electrical features"
    )
    operating_hours: Optional[float] = 12500.0


class MultiHorizonPredictionResponse(BaseModel):
    """Multi-horizon prediction output matching Section 4 & 8."""
    asset_id: str
    timestamp: datetime
    model_version: str
    horizon_probabilities: Dict[str, float] = Field(
        ...,
        description="Calibrated failure risk for 24h, 72h, 7d, 14d horizons"
    )
    predicted_failure_mode: str
    failure_mode_probabilities: Dict[str, float]
    calibrated_risk_score: float = Field(..., description="Overall calibrated risk score [0-100]")
    severity: str  # NORMAL, WATCHLIST, ELEVATED, CRITICAL


class RULPredictionRequest(BaseModel):
    """Request for Remaining Useful Life estimation."""
    asset_id: str
    sensors: Dict[str, float]
    operating_hours: Optional[float] = 12500.0


class RULPredictionResponse(BaseModel):
    """Probabilistic Remaining Useful Life response matching Section 4 & 5."""
    asset_id: str
    timestamp: datetime
    model_version: str
    rul_days_median: float = Field(..., description="P50 median RUL in days")
    rul_days_p10: float = Field(..., description="P10 pessimistic RUL in days")
    rul_days_p90: float = Field(..., description="P90 optimistic RUL in days")
    rul_hours_median: float
    confidence_interval_width: float
    failure_probability_before_window: float = Field(
        ...,
        description="P(RUL <= Maintenance Lead Time of 7 days)"
    )
    degradation_percentage: float


class AnomalyDetectionRequest(BaseModel):
    """Multivariate anomaly detection request."""
    asset_id: str
    sensors: Dict[str, float]


class AnomalyDetectionResponse(BaseModel):
    """Multivariate anomaly detection output matching Section 4 & 8."""
    asset_id: str
    timestamp: datetime
    is_anomaly: bool
    anomaly_score: float = Field(..., description="Normalized anomaly score [0.0 - 100.0]")
    threshold: float
    contributing_signals: List[Dict[str, Any]] = Field(
        ...,
        description="List of sensors ranked by contribution to anomaly score"
    )


class AssetHealthSummary(BaseModel):
    """Composite asset health response matching Section 17."""
    asset_id: str
    asset_name: str
    asset_family: str
    plant_name: str
    criticality: str
    health_score: float = Field(..., description="Composite health index [0 - 100]")
    calibrated_risk_score: float = Field(..., description="Calibrated overall failure risk [0 - 100]")
    horizon_probabilities: Dict[str, float] = Field(..., description="Failure probabilities by time horizon")
    status: str
    risk_level: str
    rul_days_p50: float
    rul_days_p10: float
    rul_days_p90: float
    failure_probability_before_window: float
    anomaly_score: float
    primary_failure_mode: Optional[str]
    recommended_action: str
    maintenance_window_hours: int
    last_updated: datetime


class ModelExplanationResponse(BaseModel):
    """Root-cause / SHAP attribution explanation matching Section 4 & 17."""
    asset_id: str
    timestamp: datetime
    feature_attributions: List[Dict[str, Any]] = Field(
        ...,
        description="Key features driving risk score with direction and impact"
    )
    evidence_window: List[Dict[str, Any]] = Field(
        ...,
        description="Historical telemetry window evidence showing sensor drift leading up to prediction"
    )
    diagnostic_summary: str


class AlertAckRequest(BaseModel):
    """Alert acknowledgement request matching Section 17."""
    engineer_id: str
    notes: Optional[str] = "Acknowledged by operations team"


class WorkOrderRequest(BaseModel):
    """Maintenance work order generation request matching Section 17."""
    asset_id: str
    alert_id: Optional[str] = None
    failure_mode: str
    priority: Literal["EMERGENCY", "HIGH", "MEDIUM", "LOW"]
    recommended_action: str
    maintenance_window_hours: int
    assigned_work_center: str
    notes: Optional[str] = ""


class MaintenanceFeedbackRequest(BaseModel):
    """Verified inspection outcome submitted against an existing work order."""
    asset_id: str
    actual_outcome: Literal[
        "TRUE_POSITIVE_FAILURE",
        "PREVENTED_DEGRADATION",
        "FALSE_ALERT_NO_DEFECT"
    ]
    confirmed_failure_mode: str
    technician_findings: str
    parts_replaced: List[str] = Field(default_factory=list)


class WorkOrderResponse(BaseModel):
    """Work order creation response."""
    work_order_id: str
    sap_notification_id: str
    asset_id: str
    status: str
    priority: str
    created_at: datetime
    estimated_downtime_hours: float
    estimated_cost_usd: float
