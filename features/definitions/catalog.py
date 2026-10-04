"""
Feature Catalog and Definitions.
Implements Section 5 & 9: Stateful streaming features, vibration metrics, and physical ratios.
"""

from typing import Dict, List, Any


FEATURE_CATALOG: Dict[str, Dict[str, Any]] = {
    # Vibration & Mechanical Dynamics
    "vib_de_rms_ewma_1h": {
        "description": "Exponentially weighted moving average of Drive-End RMS vibration (alpha=0.1)",
        "unit": "mm/s",
        "category": "Vibration Dynamics"
    },
    "vib_nde_rms_ewma_1h": {
        "description": "Exponentially weighted moving average of Non-Drive-End RMS vibration",
        "unit": "mm/s",
        "category": "Vibration Dynamics"
    },
    "vib_de_trend_slope_24h": {
        "description": "Linear regression slope of DE vibration over 24h window (degradation velocity)",
        "unit": "mm/s per day",
        "category": "Vibration Dynamics"
    },
    "vib_kurtosis": {
        "description": "Statistical 4th standardized moment of vibration acceleration signal (spalling detector)",
        "unit": "dimensionless",
        "category": "Vibration Dynamics"
    },
    "vib_crest_factor": {
        "description": "Ratio of peak vibration to RMS value (early bearing impact detector)",
        "unit": "dimensionless",
        "category": "Vibration Dynamics"
    },
    "vib_harmonic_ratio_2x_1x": {
        "description": "Ratio of 2X shaft rotational harmonic to 1X fundamental (misalignment signature)",
        "unit": "dimensionless",
        "category": "Vibration Dynamics"
    },
    "vib_energy_subsynchronous": {
        "description": "Sub-synchronous spectral band energy below 1X (oil whirl / seal rub)",
        "unit": "mm/s",
        "category": "Vibration Dynamics"
    },

    # Thermal & Heat Dissipation
    "temp_bearing_delta_ambient": {
        "description": "Differential temperature between Drive-End bearing and ambient",
        "unit": "°C",
        "category": "Thermal & Lube"
    },
    "temp_lube_delta_supply_return": {
        "description": "Temperature rise across lube oil cooler (heat generation in bearing cavity)",
        "unit": "°C",
        "category": "Thermal & Lube"
    },
    "temp_exhaust_spread_max": {
        "description": "Combustor exhaust thermocouple spread deviation from mean",
        "unit": "°C",
        "category": "Combustion & Gas Path"
    },

    # Hydraulics, Lube & Aerodynamics
    "press_ratio_discharge_suction": {
        "description": "Compressor/Pump pressure ratio (aerodynamic loading)",
        "unit": "ratio",
        "category": "Hydraulics"
    },
    "press_lube_oil_bar": {
        "description": "Lube oil header pressure (hydrodynamic wedge health)",
        "unit": "bar",
        "category": "Thermal & Lube"
    },
    "press_diff_filter_normalized": {
        "description": "Normalized filter differential pressure relative to baseline flow",
        "unit": "mbar",
        "category": "Hydraulics"
    },

    # Electrical & High-Frequency Acoustic
    "motor_current_unbalance_pct": {
        "description": "Percentage unbalance across motor phase currents (stator/rotor fault indicator)",
        "unit": "%",
        "category": "Electrical"
    },
    "acoustic_high_freq_db": {
        "description": "Ultrasonic acoustic emission energy (sub-surface micro-cracking)",
        "unit": "dB",
        "category": "Acoustic"
    },

    # Composite & Operating Context
    "operating_hours_total": {
        "description": "Cumulative operating hours since last overhaul",
        "unit": "hours",
        "category": "Operating Envelope"
    }
}
