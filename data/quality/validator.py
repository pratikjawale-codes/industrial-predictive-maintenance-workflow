"""
Data Quality and Validation Engine for Sensor Telemetry.
Implements Section 9 (Time-Series Data Engineering Design) and Great Expectations-style checks.
"""

from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional
import math


# Engineering ranges and dynamic rate-of-change thresholds by sensor type
SENSOR_BOUNDS: Dict[str, Dict[str, float]] = {
    # Vibration features
    "vib_drive_end_rms": {"min": 0.0, "max": 25.0, "max_rate_change": 5.0, "unit": "mm/s"},
    "vib_non_drive_end_rms": {"min": 0.0, "max": 25.0, "max_rate_change": 5.0, "unit": "mm/s"},
    "vib_peak_to_peak": {"min": 0.0, "max": 200.0, "max_rate_change": 30.0, "unit": "µm"},
    "vib_kurtosis": {"min": 1.5, "max": 15.0, "max_rate_change": 4.0, "unit": "dimensionless"},
    "vib_crest_factor": {"min": 1.0, "max": 10.0, "max_rate_change": 3.0, "unit": "dimensionless"},
    "vib_spectral_1x": {"min": 0.0, "max": 15.0, "max_rate_change": 4.0, "unit": "mm/s"},
    "vib_spectral_2x": {"min": 0.0, "max": 15.0, "max_rate_change": 4.0, "unit": "mm/s"},
    
    # Temperature features
    "temp_bearing_drive_end": {"min": 10.0, "max": 150.0, "max_rate_change": 15.0, "unit": "°C"},
    "temp_bearing_non_drive": {"min": 10.0, "max": 150.0, "max_rate_change": 15.0, "unit": "°C"},
    "temp_lube_oil_supply": {"min": 20.0, "max": 110.0, "max_rate_change": 10.0, "unit": "°C"},
    "temp_lube_oil_return": {"min": 20.0, "max": 120.0, "max_rate_change": 10.0, "unit": "°C"},
    "temp_exhaust_spread": {"min": 0.0, "max": 60.0, "max_rate_change": 12.0, "unit": "°C"},
    "temp_ambient": {"min": -20.0, "max": 55.0, "max_rate_change": 5.0, "unit": "°C"},

    # Pressure & Flow features
    "press_lube_oil_bar": {"min": 0.5, "max": 8.0, "max_rate_change": 1.5, "unit": "bar"},
    "press_discharge_bar": {"min": 1.0, "max": 60.0, "max_rate_change": 10.0, "unit": "bar"},
    "press_diff_filter_mbar": {"min": 0.0, "max": 1200.0, "max_rate_change": 150.0, "unit": "mbar"},
    "flow_rate_m3h": {"min": 0.0, "max": 1200.0, "max_rate_change": 150.0, "unit": "m³/h"},

    # Electrical features
    "motor_current_amps": {"min": 0.0, "max": 450.0, "max_rate_change": 75.0, "unit": "A"},
    "voltage_imbalance_pct": {"min": 0.0, "max": 8.0, "max_rate_change": 2.0, "unit": "%"},
    "acoustic_emission_db": {"min": 20.0, "max": 120.0, "max_rate_change": 25.0, "unit": "dB"}
}


class DataQualityValidator:
    """Validates raw sensor records and maintains Dead-Letter Queue (DLQ)."""

    def __init__(self):
        self.dlq_records: List[Dict[str, Any]] = []
        self.last_seen_values: Dict[str, Dict[str, float]] = {}  # asset_id -> {sensor_id: val}
        self.stale_counters: Dict[str, Dict[str, int]] = {}      # asset_id -> {sensor_id: count}

    def validate_snapshot(
        self,
        asset_id: str,
        sensors: Dict[str, float],
        require_core_sensors: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate incoming snapshot against industrial engineering bounds,
        stale sensor checks, and rate-of-change constraints.
        """
        violations = []
        clean_sensors = {}
        missingness_indicators = {}

        if asset_id not in self.last_seen_values:
            self.last_seen_values[asset_id] = {}
            self.stale_counters[asset_id] = {}

        previous_values = self.last_seen_values[asset_id]
        previous_stale_counters = self.stale_counters[asset_id]
        accepted_values: Dict[str, float] = {}
        accepted_stale_counters: Dict[str, int] = {}

        for sensor_id, bounds in SENSOR_BOUNDS.items():
            if sensor_id not in sensors or sensors[sensor_id] is None:
                missingness_indicators[f"{sensor_id}_missing"] = 1
                # Optional sensors missing are tracked in indicators; mandatory core vibration requires check
                if require_core_sensors and sensor_id in ["vib_drive_end_rms", "temp_bearing_drive_end"]:
                    violations.append({
                        "sensor_id": sensor_id,
                        "type": "MISSING_CRITICAL_SENSOR",
                        "detail": f"Mandatory sensor {sensor_id} is missing in stream"
                    })
                continue
            
            val = float(sensors[sensor_id])
            missingness_indicators[f"{sensor_id}_missing"] = 0

            # 1. Range Check
            if not math.isfinite(val) or val < bounds["min"] or val > bounds["max"]:
                violations.append({
                    "sensor_id": sensor_id,
                    "type": "RANGE_VIOLATION",
                    "detail": f"Value {val} {bounds['unit']} is non-finite or outside valid range [{bounds['min']}, {bounds['max']}]"
                })
                continue

            # 2. Rate-of-Change / Spike Check
            prev_val = previous_values.get(sensor_id)
            if prev_val is not None:
                rate = abs(val - prev_val)
                if rate > bounds["max_rate_change"]:
                    violations.append({
                        "sensor_id": sensor_id,
                        "type": "SPIKE_DETECTED",
                        "detail": f"Instantaneous rate of change {rate:.2f} exceeds threshold {bounds['max_rate_change']}"
                    })

                # 3. Stale Sensor Check (frozen sensor)
                if abs(val - prev_val) < 1e-6:
                    stale_count = previous_stale_counters.get(sensor_id, 0) + 1
                    accepted_stale_counters[sensor_id] = stale_count
                    if stale_count > 20:
                        violations.append({
                            "sensor_id": sensor_id,
                            "type": "STALE_SENSOR",
                            "detail": f"Sensor value unchanged for {stale_count} cycles"
                        })
                else:
                    accepted_stale_counters[sensor_id] = 0
            else:
                accepted_stale_counters[sensor_id] = 0

            clean_sensors[sensor_id] = val
            accepted_values[sensor_id] = val

        is_valid = len(violations) == 0
        if is_valid:
            previous_values.update(accepted_values)
            previous_stale_counters.update(accepted_stale_counters)

        result = {
            "is_valid": is_valid,
            "violations": violations,
            "validated_sensors": clean_sensors,
            "missingness": missingness_indicators,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if not is_valid:
            self.dlq_records.append({
                "asset_id": asset_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "violations": violations,
                "payload": sensors
            })
            # Keep DLQ bounded in memory
            if len(self.dlq_records) > 500:
                self.dlq_records.pop(0)

        return is_valid, result

    def get_dlq_metrics(self) -> Dict[str, Any]:
        """Return DLQ health status and quarantined packet count."""
        return {
            "quarantined_count": len(self.dlq_records),
            "recent_quarantines": self.dlq_records[-10:] if self.dlq_records else []
        }
