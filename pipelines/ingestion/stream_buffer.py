"""
Industrial Fleet Manager and Telemetry Stream Buffer.
Manages the fleet of 15,000 industrial assets across 5 key GE manufacturing/power plants,
handles real-time sensor streams, and supports live fault injection.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
import random


SAMPLE_FLEET = [
    {
        "asset_id": "GE-GT-0104",
        "asset_name": "Gas Turbine Frame 7HA.03 (Unit 1)",
        "plant_id": "PLANT-SC-01",
        "plant_name": "Greenville Gas Turbine Plant, SC",
        "asset_family": "Gas Turbine",
        "criticality": "Tier 1 (Critical)",
        "operating_hours": 18450.0,
        "last_maintenance_date": "2026-04-12",
        "status": "WARNING",
        "latitude": 34.8526,
        "longitude": -82.3940,
        "default_sensors": {
            "vib_drive_end_rms": 4.8,
            "vib_non_drive_end_rms": 2.4,
            "vib_peak_to_peak": 85.0,
            "vib_kurtosis": 6.8,
            "vib_crest_factor": 4.2,
            "vib_spectral_1x": 2.1,
            "vib_spectral_2x": 1.4,
            "temp_bearing_drive_end": 84.0,
            "temp_bearing_non_drive": 68.0,
            "temp_lube_oil_supply": 45.0,
            "temp_lube_oil_return": 68.0,
            "temp_exhaust_spread": 28.0,
            "temp_ambient": 24.0,
            "press_lube_oil_bar": 2.8,
            "press_discharge_bar": 24.5,
            "press_diff_filter_mbar": 340.0,
            "flow_rate_m3h": 720.0,
            "motor_current_amps": 310.0,
            "voltage_imbalance_pct": 1.1,
            "acoustic_emission_db": 68.0
        }
    },
    {
        "asset_id": "GE-CP-0201",
        "asset_name": "Centrifugal Gas Compressor B-4",
        "plant_id": "PLANT-GA-02",
        "plant_name": "Atlanta Power Station, GA",
        "asset_family": "Centrifugal Compressor",
        "criticality": "Tier 1 (Critical)",
        "operating_hours": 14200.0,
        "last_maintenance_date": "2026-06-18",
        "status": "OPERATIONAL",
        "latitude": 33.7490,
        "longitude": -84.3880,
        "default_sensors": {
            "vib_drive_end_rms": 2.1,
            "vib_non_drive_end_rms": 1.9,
            "vib_peak_to_peak": 42.0,
            "vib_kurtosis": 3.1,
            "vib_crest_factor": 2.4,
            "vib_spectral_1x": 1.4,
            "vib_spectral_2x": 0.5,
            "temp_bearing_drive_end": 66.0,
            "temp_bearing_non_drive": 63.0,
            "temp_lube_oil_supply": 42.0,
            "temp_lube_oil_return": 55.0,
            "temp_exhaust_spread": 12.0,
            "temp_ambient": 22.0,
            "press_lube_oil_bar": 3.4,
            "press_discharge_bar": 42.0,
            "press_diff_filter_mbar": 190.0,
            "flow_rate_m3h": 580.0,
            "motor_current_amps": 240.0,
            "voltage_imbalance_pct": 0.6,
            "acoustic_emission_db": 44.0
        }
    },
    {
        "asset_id": "GE-BFP-0302",
        "asset_name": "Boiler Feed Pump Stage 4",
        "plant_id": "PLANT-NY-03",
        "plant_name": "Schenectady Turbine Works, NY",
        "asset_family": "Feed Pump",
        "criticality": "Tier 2 (Essential)",
        "operating_hours": 22100.0,
        "last_maintenance_date": "2026-03-05",
        "status": "OPERATIONAL",
        "latitude": 42.8142,
        "longitude": -73.9396,
        "default_sensors": {
            "vib_drive_end_rms": 2.8,
            "vib_non_drive_end_rms": 2.6,
            "vib_peak_to_peak": 52.0,
            "vib_kurtosis": 3.4,
            "vib_crest_factor": 2.7,
            "vib_spectral_1x": 1.9,
            "vib_spectral_2x": 1.2,
            "temp_bearing_drive_end": 71.0,
            "temp_bearing_non_drive": 69.0,
            "temp_lube_oil_supply": 41.0,
            "temp_lube_oil_return": 52.0,
            "temp_exhaust_spread": 10.0,
            "temp_ambient": 18.0,
            "press_lube_oil_bar": 3.1,
            "press_discharge_bar": 35.0,
            "press_diff_filter_mbar": 210.0,
            "flow_rate_m3h": 410.0,
            "motor_current_amps": 190.0,
            "voltage_imbalance_pct": 0.9,
            "acoustic_emission_db": 49.0
        }
    },
    {
        "asset_id": "GE-WT-0412",
        "asset_name": "Offshore Wind Turbine 2.5MW #12",
        "plant_id": "PLANT-NL-04",
        "plant_name": "Rotterdam Offshore Wind Field, NL",
        "asset_family": "Wind Turbine",
        "criticality": "Tier 2 (Essential)",
        "operating_hours": 9400.0,
        "last_maintenance_date": "2026-07-22",
        "status": "OPERATIONAL",
        "latitude": 51.9244,
        "longitude": 4.4777,
        "default_sensors": {
            "vib_drive_end_rms": 1.8,
            "vib_non_drive_end_rms": 1.5,
            "vib_peak_to_peak": 38.0,
            "vib_kurtosis": 2.9,
            "vib_crest_factor": 2.2,
            "vib_spectral_1x": 1.1,
            "vib_spectral_2x": 0.4,
            "temp_bearing_drive_end": 58.0,
            "temp_bearing_non_drive": 54.0,
            "temp_lube_oil_supply": 38.0,
            "temp_lube_oil_return": 46.0,
            "temp_exhaust_spread": 8.0,
            "temp_ambient": 15.0,
            "press_lube_oil_bar": 3.5,
            "press_discharge_bar": 12.0,
            "press_diff_filter_mbar": 140.0,
            "flow_rate_m3h": 320.0,
            "motor_current_amps": 160.0,
            "voltage_imbalance_pct": 0.5,
            "acoustic_emission_db": 39.0
        }
    },
    {
        "asset_id": "GE-MTR-0508",
        "asset_name": "Induction Motor 6.6kV Test Bench",
        "plant_id": "PLANT-OH-05",
        "plant_name": "Cincinnati Aviation Test Facility, OH",
        "asset_family": "Induction Motor",
        "criticality": "Tier 3 (Balance of Plant)",
        "operating_hours": 8100.0,
        "last_maintenance_date": "2026-05-14",
        "status": "OPERATIONAL",
        "latitude": 39.1031,
        "longitude": -84.5120,
        "default_sensors": {
            "vib_drive_end_rms": 1.9,
            "vib_non_drive_end_rms": 1.7,
            "vib_peak_to_peak": 40.0,
            "vib_kurtosis": 3.0,
            "vib_crest_factor": 2.3,
            "vib_spectral_1x": 1.2,
            "vib_spectral_2x": 0.5,
            "temp_bearing_drive_end": 62.0,
            "temp_bearing_non_drive": 60.0,
            "temp_lube_oil_supply": 40.0,
            "temp_lube_oil_return": 49.0,
            "temp_exhaust_spread": 9.0,
            "temp_ambient": 21.0,
            "press_lube_oil_bar": 3.3,
            "press_discharge_bar": 15.0,
            "press_diff_filter_mbar": 160.0,
            "flow_rate_m3h": 280.0,
            "motor_current_amps": 175.0,
            "voltage_imbalance_pct": 0.7,
            "acoustic_emission_db": 41.0
        }
    }
]


class FleetStreamManager:
    """
    Manages operational telemetry streams and historical evidence windows
    for root-cause SHAP explanations.
    """

    def __init__(self):
        # asset_id -> metadata dictionary
        self.fleet: Dict[str, Dict[str, Any]] = {a["asset_id"]: dict(a) for a in SAMPLE_FLEET}
        # asset_id -> current sensor dict
        self.live_telemetry: Dict[str, Dict[str, float]] = {
            a["asset_id"]: dict(a["default_sensors"]) for a in SAMPLE_FLEET
        }
        # asset_id -> historical 24h timeline window
        self.evidence_windows: Dict[str, List[Dict[str, Any]]] = {}
        self._generate_initial_evidence_windows()

    def _generate_initial_evidence_windows(self):
        """Generate realistic historical time series for each asset."""
        now = datetime.now(timezone.utc)
        for asset_id, data in self.fleet.items():
            window = []
            base_vib = data["default_sensors"]["vib_drive_end_rms"]
            base_temp = data["default_sensors"]["temp_bearing_drive_end"]
            
            # 12 points spaced 2 hours apart
            for i in range(12):
                t = now - timedelta(hours=(12 - i) * 2)
                # Trend upwards if it's the GT-0104 unit (degrading)
                if asset_id == "GE-GT-0104":
                    prog = i / 11.0
                    vib_pt = 2.4 + (base_vib - 2.4) * (prog ** 1.8) + random.uniform(-0.1, 0.1)
                    temp_pt = 66.0 + (base_temp - 66.0) * prog + random.uniform(-0.8, 0.8)
                    kurt_pt = 3.0 + 3.8 * prog
                else:
                    vib_pt = base_vib + random.uniform(-0.15, 0.15)
                    temp_pt = base_temp + random.uniform(-0.5, 0.5)
                    kurt_pt = 3.0 + random.uniform(-0.2, 0.2)

                window.append({
                    "timestamp": t.strftime("%H:%M"),
                    "vib_de_rms": round(vib_pt, 2),
                    "temp_bearing": round(temp_pt, 1),
                    "vib_kurtosis": round(kurt_pt, 2)
                })
            self.evidence_windows[asset_id] = window

    def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        return self.fleet.get(asset_id)

    def get_all_assets(self) -> List[Dict[str, Any]]:
        return list(self.fleet.values())

    def get_current_sensors(self, asset_id: str) -> Dict[str, float]:
        if asset_id in self.live_telemetry:
            return self.live_telemetry[asset_id]
        return SAMPLE_FLEET[0]["default_sensors"]

    def update_sensors(self, asset_id: str, new_sensors: Dict[str, float]):
        """Update live telemetry reading (e.g. from simulator or edge feed)."""
        if asset_id in self.live_telemetry:
            self.live_telemetry[asset_id].update(new_sensors)
        else:
            self.live_telemetry[asset_id] = new_sensors

        # Append to evidence window
        if asset_id in self.evidence_windows:
            self.evidence_windows[asset_id].append({
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M"),
                "vib_de_rms": round(new_sensors.get("vib_drive_end_rms", 2.2), 2),
                "temp_bearing": round(new_sensors.get("temp_bearing_drive_end", 68.0), 1),
                "vib_kurtosis": round(new_sensors.get("vib_kurtosis", 3.0), 2)
            })
            if len(self.evidence_windows[asset_id]) > 20:
                self.evidence_windows[asset_id].pop(0)

    def get_evidence_window(self, asset_id: str) -> List[Dict[str, Any]]:
        return self.evidence_windows.get(asset_id, [])

    def inject_fault(self, asset_id: str, fault_type: str) -> Dict[str, Any]:
        """
        Operational simulation fault injector:
        - BEARING_DAMAGE: Spike vibration, kurtosis, crest factor
        - LUBE_FAILURE: Drop lube pressure to 1.1 bar, increase oil temp
        - MISALIGNMENT: Elevate 2X harmonic and nde vibration
        - FILTER_CLOG: Increase differential pressure across filters
        - RESET_NORMAL: Return to healthy baseline
        """
        if asset_id not in self.live_telemetry:
            return {"status": "error", "message": f"Asset {asset_id} not found"}

        sensors = self.live_telemetry[asset_id]

        if fault_type == "BEARING_DAMAGE":
            sensors["vib_drive_end_rms"] = 6.4
            sensors["vib_peak_to_peak"] = 115.0
            sensors["vib_kurtosis"] = 8.6
            sensors["vib_crest_factor"] = 5.2
            sensors["acoustic_emission_db"] = 85.0
            sensors["temp_bearing_drive_end"] = 89.0
            desc = "Injected outer race spalling fault: Kurtosis=8.6, RMS=6.4 mm/s, Acoustic=85 dB"
        elif fault_type == "LUBE_FAILURE":
            sensors["press_lube_oil_bar"] = 1.3
            sensors["temp_lube_oil_return"] = 86.0
            sensors["temp_bearing_drive_end"] = 92.0
            sensors["acoustic_emission_db"] = 72.0
            desc = "Injected lube starvation: Header pressure=1.3 bar (trip threshold), Temp=92°C"
        elif fault_type == "MISALIGNMENT":
            sensors["vib_spectral_2x"] = 3.8
            sensors["vib_spectral_1x"] = 2.0
            sensors["vib_drive_end_rms"] = 5.1
            sensors["vib_non_drive_end_rms"] = 4.6
            desc = "Injected shaft misalignment: 2X harmonic elevated to 3.8 mm/s, RMS=5.1 mm/s"
        elif fault_type == "FILTER_CLOG":
            sensors["press_diff_filter_mbar"] = 850.0
            desc = "Injected filter clogging: Differential pressure ΔP=850 mbar (>650 mbar limit)"
        elif fault_type == "RESET_NORMAL":
            # Find default
            for asset in SAMPLE_FLEET:
                if asset["asset_id"] == asset_id:
                    self.live_telemetry[asset_id] = dict(asset["default_sensors"])
                    break
            desc = "Reset all sensors to healthy baseline operating envelope"
        else:
            desc = f"Unknown fault type: {fault_type}"

        return {
            "status": "success",
            "asset_id": asset_id,
            "fault_type": fault_type,
            "description": desc,
            "updated_sensors": self.live_telemetry[asset_id]
        }
