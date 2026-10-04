# How to Present This Project in a Technical Interview
*Grounded directly in Section 24 of the GE Predictive Maintenance Industry-Ready Project Plan.*

---

## 1. The Core Narrative: Lead with the Business Decision System, Not Algorithms
> *"In industrial manufacturing, machine learning is not just a binary classifier—it is an end-to-end operational decision system."*

When presenting this project to Senior Staff Engineers, Directors, or Hiring Managers:
- **Do not start with:** *"I trained an XGBoost model with 96.8% accuracy."* (This is an immediate red flag in industrial ML because accuracy is misleading under severe class imbalance).
- **Lead with:** *"We built an end-to-end industrial IoT decision platform for 15,000 turbomachinery assets across 5 General Electric plants. The platform's objective was to predict catastrophic equipment failure 7 to 14 days in advance, resulting in audited savings of $5.2M annually and a 42% reduction in unplanned downtime."*

---

## 2. Walk Through the End-to-End Operational Path

Be prepared to draw or explain this exact 9-stage pipeline:

```
[1] High-Frequency Telemetry Ingestion (45M retained records/day from SCADA/PLC)
     │
[2] Ingestion Data Quality Contracts & Great Expectations Range/Spike/Stale Checks
     │
[3] Stateful Feature Computation (EWMA, 24h Trend Slopes, FFT Harmonics, ΔT, Kurtosis)
     │
[4] Model Inference Trio (Multi-Horizon Failure Risk, Probabilistic RUL, Multivariate Anomalies)
     │
[5] Bayesian Probability Calibration (Platt Sigmoidal Transformation evaluated by Brier Score)
     │
[6] Cost-Sensitive Decision Engine & Alert Hysteresis (Suppresses transient alarm spikes)
     │
[7] SAP PM Work-Order Integration (Automated notification routing & parts staging)
     │
[8] Human-in-the-Loop Confirmation & Outcome Logging (Technician verifies true/false alarm)
     │
[9] Continuous Closed-Loop Feedback into Retraining Label Store (Leakage-fenced retraining)
```

---

## 3. High-Yield Technical Interview Questions & Battle-Tested Answers

### Q1: "Why is a single 96.8% accuracy metric inappropriate for predictive maintenance?"
**Answer:**
> *"In a healthy fleet of 15,000 industrial machines, catastrophic failure is an extremely rare event—typically under 1% to 2% of asset operating hours. A naive dummy model that always predicts 'Healthy' achieves 98%+ accuracy while failing to detect 100% of real breakdowns.  
> In production, we evaluated the system using PR-AUC (Precision-Recall Area), operational Recall at threshold (ensuring dangerous misses are caught), Precision (preventing technician alert fatigue), calibrated Brier Score, and Advance Lead Time (median 11.2 days before physical failure)."*

---

### Q2: "How did you prevent temporal data leakage during training and feature engineering?"
**Answer:**
> *"We strictly enforced Point-in-Time correctness and temporal splitting rather than random row-level k-fold splits:
> 1. **Time-Based Splitting:** Data was split chronologically (e.g. historical quarters for training, out-of-time future quarters for testing), ensuring the model is evaluated on future data it has never seen.
> 2. **Observation Fences:** For any prediction timestamp $T_{\text{cutoff}}$, feature vectors were calculated using telemetry strictly prior to $T_{\text{cutoff}}$.
> 3. **Maintenance Leakage Prevention:** Work orders and technician logs generated after $T_{\text{cutoff}}$ were completely masked from the feature store. Failure labels were assigned looking forward strictly into $[T_{\text{cutoff}}, T_{\text{cutoff}} + \text{horizon}]$.
> 4. **Right-Censoring:** Assets decommissioned or shut down before horizon completion were flagged as censored to prevent false negative contamination."*

---

### Q3: "How does the system separate predictive risk from maintenance action?"
**Answer:**
> *"We decoupled the statistical probability of failure from physical work order generation:
> - The ML model outputs a calibrated probability $P(\text{failure} \mid \text{horizon}, \text{asset})$.
> - A downstream **Cost-Sensitive Decision Engine** evaluates the financial trade-off:
>   $$\text{Expected Cost of Inaction} = P(\text{fail}) \times \text{Cost}(\text{Unplanned Downtime})$$
>   An alert is only escalated to an emergency work order if the net avoided cost exceeds planned inspection and tooling costs.
> - Furthermore, an **Alert Hysteresis Policy** requires persistent abnormal degradation across multiple consecutive measurement cycles before sounding P1/P2 alarms, keeping our false alert rate down to 1.4 per 100 machines/month."*

---

### Q4: "What happens when telemetry is delayed, Kafka has lag, or the ML inference service fails?"
**Answer:**
> *"Our architecture implements deterministic industrial fail-safes (Section 14 & 26):
> 1. **Event-Time Watermarking:** Streaming pipelines use event timestamps generated at the machine PLC rather than ingestion time, handling out-of-order packets and late arrivals.
> 2. **Dead-Letter Queue (DLQ):** Malformed packets that violate range or rate-of-change contracts are quarantined to S3 DLQ for replay rather than crashing the pipeline.
> 3. **Active Fallback Rules:** If the ML microservice is unreachable or latency breaches our SLO (>50ms), traffic instantly fails over to a deterministic ISO 10816 / API 670 rule layer. Turbine protection always remains fully operational."*

---

### Q5: "How does closed-loop technician feedback update the models without drift?"
**Answer:**
> *"When a work order is completed, field engineers log physical inspection findings (e.g., 'Bearing outer race micro-spalling verified' vs 'False alert due to loose sensor bracket') into SAP PM.  
> This ground-truth outcome is captured by our closed-loop service and written to our versioned Label Store. A retraining orchestrator monitors both feature drift (Population Stability Index - PSI) and new label volume. When retraining triggers, new candidate models must pass automated quality gates (PR-AUC, Recall, Calibration, Lead Time) comparing candidate vs champion before shadow and canary rollout."*
