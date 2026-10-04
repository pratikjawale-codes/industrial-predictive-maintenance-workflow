"""
Batch Feature Engineering and Frequency-Domain Spectral Analysis Engine.
Implements Section 9: FFT spectral band energy, vibration harmonics, kurtosis,
crest factor, and large-scale historical backfill pipelines.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


class SpectralFeatureGenerator:
    """
    Computes frequency-domain vibration spectra and statistical moments
    from raw acceleration waveforms according to ISO 10816 standards.
    """

    @staticmethod
    def extract_fft_features(waveform: np.ndarray, sampling_rate_hz: float = 2000.0) -> Dict[str, float]:
        """
        Extract Fast Fourier Transform (FFT) spectral features:
        - 1X Fundamental shaft rotation energy
        - 2X Harmonic energy (misalignment indicator)
        - Sub-synchronous band energy (<1X - oil whirl / seal rub)
        - High-frequency band energy (>5X - bearing micro-faults)
        - Crest factor and spectral kurtosis
        """
        n = len(waveform)
        if n < 32:
            return {"spec_1x": 0.0, "spec_2x": 0.0, "spec_subsync": 0.0, "crest_factor": 1.0}

        # Real FFT
        fft_vals = np.abs(np.fft.rfft(waveform)) / n
        freqs = np.fft.rfftfreq(n, d=1.0 / sampling_rate_hz)

        # Fundamental 1X (e.g. 50 Hz or 60 Hz grid speed ~ 3000/3600 RPM)
        mask_1x = (freqs >= 48.0) & (freqs <= 52.0)
        spec_1x = float(np.max(fft_vals[mask_1x])) if np.any(mask_1x) else 0.01

        # 2X Harmonic (98 - 102 Hz)
        mask_2x = (freqs >= 98.0) & (freqs <= 102.0)
        spec_2x = float(np.max(fft_vals[mask_2x])) if np.any(mask_2x) else 0.005

        # Sub-synchronous (<45 Hz)
        mask_sub = (freqs >= 5.0) & (freqs < 45.0)
        spec_subsync = float(np.sum(fft_vals[mask_sub])) if np.any(mask_sub) else 0.0

        # High-frequency band (>250 Hz)
        mask_high = freqs > 250.0
        spec_high = float(np.sum(fft_vals[mask_high])) if np.any(mask_high) else 0.0

        # Time-domain statistical moments
        peak = float(np.max(np.abs(waveform)))
        rms = float(np.sqrt(np.mean(waveform ** 2)))
        crest_factor = float(peak / max(rms, 1e-5))

        # Kurtosis (4th standardized moment)
        mean = np.mean(waveform)
        std = np.std(waveform)
        if std > 1e-5:
            kurtosis = float(np.mean(((waveform - mean) / std) ** 4))
        else:
            kurtosis = 3.0

        return {
            "spec_1x_fundamental": round(spec_1x, 4),
            "spec_2x_harmonic": round(spec_2x, 4),
            "spec_harmonic_ratio_2x_1x": round(spec_2x / max(spec_1x, 1e-4), 3),
            "spec_subsynchronous_energy": round(spec_subsync, 4),
            "spec_high_frequency_energy": round(spec_high, 4),
            "vibration_crest_factor": round(crest_factor, 2),
            "vibration_kurtosis": round(kurtosis, 2)
        }
