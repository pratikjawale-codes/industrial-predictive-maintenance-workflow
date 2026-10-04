"""
Stateful Streaming Feature Calculator.
Maintains asset-level sliding windows, EWMA, vibration harmonics, and rate-of-change.
"""

from typing import Dict, List, Any
import numpy as np


class StreamingFeatureCalculator:
    """Calculates rolling and physical features from live sensor streams."""

    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        # asset_id -> {sensor_name: list of historical values}
        self.history: Dict[str, Dict[str, List[float]]] = {}
        # asset_id -> {sensor_name: current EWMA}
        self.ewma_state: Dict[str, Dict[str, float]] = {}

    def update_and_extract(
        self,
        asset_id: str,
        sensors: Dict[str, float],
        operating_hours: float = 12000.0,
        update_state: bool = True
    ) -> Dict[str, float]:
        """
        Ingest instantaneous sensor reading, update stateful buffers,
        and calculate the complete feature vector required by the ML models.
        """
        if update_state and asset_id not in self.history:
            self.history[asset_id] = {}
            self.ewma_state[asset_id] = {}

        history = self.history.get(asset_id, {})
        ewma_state = self.ewma_state.get(asset_id, {})
        if update_state:
            # Update historical buffers & EWMA (alpha = 0.15)
            alpha = 0.15
            for k, v in sensors.items():
                if k not in history:
                    history[k] = []
                    ewma_state[k] = float(v)

                buf = history[k]
                buf.append(float(v))
                if len(buf) > self.window_size:
                    buf.pop(0)

                ewma_state[k] = alpha * float(v) + (1.0 - alpha) * ewma_state[k]

        # Extract features
        features: Dict[str, float] = {}

        # 1. Base values & EWMAs
        vib_de = sensors.get("vib_drive_end_rms", 2.2)
        vib_nde = sensors.get("vib_non_drive_end_rms", 1.8)
        vib_p2p = sensors.get("vib_peak_to_peak", 45.0)
        kurtosis = sensors.get("vib_kurtosis", 3.0)
        crest = sensors.get("vib_crest_factor", 2.5)
        spec_1x = sensors.get("vib_spectral_1x", 1.5)
        spec_2x = sensors.get("vib_spectral_2x", 0.6)

        t_brg_de = sensors.get("temp_bearing_drive_end", 68.0)
        t_brg_nde = sensors.get("temp_bearing_non_drive", 62.0)
        t_lube_sup = sensors.get("temp_lube_oil_supply", 42.0)
        t_lube_ret = sensors.get("temp_lube_oil_return", 54.0)
        t_amb = sensors.get("temp_ambient", 25.0)
        t_egt_spread = sensors.get("temp_exhaust_spread", 14.0)

        p_lube = sensors.get("press_lube_oil_bar", 3.2)
        p_disch = sensors.get("press_discharge_bar", 18.5)
        p_filter = sensors.get("press_diff_filter_mbar", 180.0)
        flow = sensors.get("flow_rate_m3h", 450.0)

        i_amps = sensors.get("motor_current_amps", 185.0)
        v_imb = sensors.get("voltage_imbalance_pct", 0.8)
        acoustic = sensors.get("acoustic_emission_db", 42.0)

        # 2. Stateful EWMA features
        features["vib_de_rms_ewma_1h"] = float(ewma_state.get("vib_drive_end_rms", vib_de))
        features["vib_nde_rms_ewma_1h"] = float(ewma_state.get("vib_non_drive_end_rms", vib_nde))

        # 3. Trend slope over window (regression slope)
        vib_history = history.get("vib_drive_end_rms", [vib_de])
        if len(vib_history) >= 3:
            x = np.arange(len(vib_history))
            slope, _ = np.polyfit(x, vib_history, 1)
            features["vib_de_trend_slope_24h"] = float(slope * 10.0)  # normalized scale
        else:
            features["vib_de_trend_slope_24h"] = 0.0

        # 4. Statistical moments & harmonic ratios
        features["vib_kurtosis"] = float(kurtosis)
        features["vib_crest_factor"] = float(crest)
        features["vib_harmonic_ratio_2x_1x"] = float(spec_2x / max(spec_1x, 0.01))
        features["vib_energy_subsynchronous"] = float(max(0.0, vib_de - (spec_1x + spec_2x) * 0.5))

        # 5. Thermal differentials & thermodynamic ratios
        features["temp_bearing_delta_ambient"] = float(t_brg_de - t_amb)
        features["temp_lube_delta_supply_return"] = float(t_lube_ret - t_lube_sup)
        features["temp_exhaust_spread_max"] = float(t_egt_spread)

        # 6. Pressure, Hydraulics & Lubrication
        features["press_ratio_discharge_suction"] = float(p_disch / max(p_lube, 0.1))
        features["press_lube_oil_bar"] = float(p_lube)
        features["press_diff_filter_normalized"] = float(p_filter / max(flow, 10.0))

        # 7. Electrical & Acoustic
        features["motor_current_unbalance_pct"] = float(v_imb * 1.5 + (i_amps % 5) * 0.1)
        features["acoustic_high_freq_db"] = float(acoustic)
        features["operating_hours_total"] = float(operating_hours)

        return features
