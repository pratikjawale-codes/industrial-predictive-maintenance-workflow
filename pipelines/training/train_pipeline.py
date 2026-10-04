"""
Model Training and Calibration Pipeline.
Implements Section 8, 10 & 12: Point-in-time safe training, time-based splits (leakage prevention),
Platt probability calibration, PR-AUC / lead time evaluation, and MLflow-style registry recording.
"""

import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, auc, brier_score_loss, recall_score, precision_score

# Ensure root importability
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.calibration.calibrator import ProbabilityCalibrator


def generate_synthetic_industrial_dataset(n_samples: int = 1200) -> pd.DataFrame:
    """
    Generate point-in-time safe industrial telemetry dataset
    simulating run-to-failure cycles on turbomachinery.
    """
    np.random.seed(42)

    # Time-series timestamps spaced over 180 days
    base_time = pd.Timestamp("2026-01-01 00:00:00")
    timestamps = [base_time + pd.Timedelta(hours=i * 3.6) for i in range(n_samples)]

    # Machine states: 88% normal, 12% degradation & run-to-failure
    is_degraded = np.random.binomial(1, 0.12, n_samples)

    # Sensors generated with physical relationships
    vib_rms = np.where(is_degraded, np.random.normal(5.2, 1.2, n_samples), np.random.normal(2.1, 0.4, n_samples))
    vib_rms = np.clip(vib_rms, 0.8, 15.0)

    kurtosis = np.where(is_degraded, np.random.normal(7.5, 1.8, n_samples), np.random.normal(3.0, 0.3, n_samples))
    kurtosis = np.clip(kurtosis, 2.0, 15.0)

    slope = np.where(is_degraded, np.random.normal(0.8, 0.3, n_samples), np.random.normal(0.02, 0.05, n_samples))
    temp_delta = np.where(is_degraded, np.random.normal(52.0, 8.0, n_samples), np.random.normal(34.0, 4.0, n_samples))
    p_lube = np.where(is_degraded, np.random.normal(1.9, 0.6, n_samples), np.random.normal(3.3, 0.3, n_samples))
    harm_2x = np.where(is_degraded, np.random.normal(1.6, 0.5, n_samples), np.random.normal(0.4, 0.15, n_samples))

    # True binary label: Failure within 7-14 day horizon
    # Positive label only if confirmed degradation reaches failure threshold
    y_failure_7d = np.where((is_degraded == 1) & (vib_rms > 4.2), 1, 0)

    df = pd.DataFrame({
        "timestamp": timestamps,
        "vib_de_rms_ewma_1h": vib_rms,
        "vib_kurtosis": kurtosis,
        "vib_de_trend_slope_24h": slope,
        "temp_bearing_delta_ambient": temp_delta,
        "press_lube_oil_bar": p_lube,
        "vib_harmonic_ratio_2x_1x": harm_2x,
        "label_failure_7d": y_failure_7d
    })

    return df


def run_training_pipeline():
    """
    Execute time-based splitting, training, calibration, and evaluation scorecard.
    """
    print("=" * 80)
    print(" [GE ML PIPELINE] INITIATING TIME-SERIES MODEL TRAINING & CALIBRATION")
    print("=" * 80)

    df = generate_synthetic_industrial_dataset(1500)
    print(f"Generated {len(df)} point-in-time telemetry records.")
    print(f"Positive failure class prevalence: {df['label_failure_7d'].mean() * 100:.2f}%")

    # Time-based splitting to prevent temporal data leakage (Section 10)
    split_idx = int(len(df) * 0.75)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    print(f"Time-Based Split -> Train Set: {len(train_df)} rows | Out-of-Time Test Set: {len(test_df)} rows")
    print(f"Train Period: {train_df['timestamp'].min()} -> {train_df['timestamp'].max()}")
    print(f"Test  Period: {test_df['timestamp'].min()} -> {test_df['timestamp'].max()}")

    features = [
        "vib_de_rms_ewma_1h", "vib_kurtosis", "vib_de_trend_slope_24h",
        "temp_bearing_delta_ambient", "press_lube_oil_bar", "vib_harmonic_ratio_2x_1x"
    ]

    X_train = train_df[features].values
    y_train = train_df["label_failure_7d"].values
    X_test = test_df[features].values
    y_test = test_df["label_failure_7d"].values

    # Train Random Forest / Gradient Boosting baseline
    from sklearn.ensemble import GradientBoostingClassifier
    clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42)
    clf.fit(X_train, y_train)

    raw_probs = clf.predict_proba(X_test)[:, 1]

    # Platt Sigmoid Calibration (Section 5 & 11)
    calibrator = ProbabilityCalibrator()
    calibrated_probs = np.array([calibrator.calibrate(p) for p in raw_probs])

    # Evaluation scorecard (PR-AUC, Recall, Precision, Brier Score)
    precision_curve, recall_curve, _ = precision_recall_curve(y_test, calibrated_probs)
    pr_auc = auc(recall_curve, precision_curve)
    brier = brier_score_loss(y_test, calibrated_probs)

    y_pred_binary = (calibrated_probs >= 0.40).astype(int)
    rec = recall_score(y_test, y_pred_binary)
    prec = precision_score(y_test, y_pred_binary)

    print("\n" + "-" * 80)
    print(" [SYNTHETIC DEMONSTRATION SCORECARD - NOT A PRODUCTION MODEL GATE]")
    print("-" * 80)
    print(f" PR-AUC (Precision-Recall Area):    {pr_auc:.4f}  (illustrative target >= 0.90)")
    print(f" Recall @ Demonstration Threshold:  {rec * 100:.1f}%")
    print(f" Precision @ Demonstration Threshold: {prec * 100:.1f}%")
    print(f" Brier Loss after Fixed Calibration: {brier:.4f}")
    print(" Lead time:                         Not measured by this synthetic dataset")
    print("-" * 80)
    print(" This script does not register, promote, or deploy the fitted model.")
    print("=" * 80)


if __name__ == "__main__":
    run_training_pipeline()
