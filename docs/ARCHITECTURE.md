# Platform Architecture, Operational SLOs & Execution Plan

---

## 1. Technical Framework Blueprint (Section 6)

| Layer | Production Technology | Operational Role |
|:---|:---|:---|
| **Application & APIs** | FastAPI, Pydantic V2, Uvicorn | High-throughput async REST endpoints, data contracts, Swagger UI |
| **Data Ingestion** | Apache Kafka, AWS MSK | High-frequency telemetry ingestion (45M records/day retained) |
| **Stream Processing** | Spark Structured Streaming / Kafka Streams | Stateful rolling windows, EWMA, vibration harmonics |
| **Storage & Lake** | Amazon S3 (KMS Encrypted), PostgreSQL | Raw immutable data layers, feature snapshots, operational state |
| **Feature Store** | Feast / Centralized Catalog | Unified feature definitions across training and online inference |
| **Machine Learning** | XGBoost, LightGBM, Scikit-Learn | Calibrated multi-horizon classifiers, probabilistic RUL, anomaly detection |
| **Calibration** | Platt Sigmoidal Scaling | Empirical probability alignment and Brier score optimization |
| **Orchestration** | Apache Airflow / Step Functions | Scheduled training workflows, backtests, retraining DAGs |
| **Observability** | Prometheus, Grafana, OpenTelemetry | Infrastructure metrics, API p95/p99 latency, trace correlation |
| **ML Observability** | Evidently AI / PSI Drift Monitors | Feature distribution drift, prediction drift, calibration tracking |
| **Infrastructure** | Terraform, Docker, Kubernetes | Multi-stage secure containers, HPA autoscaling, IaC deployment |

---

## 2. Production Service Level Objectives (SLOs) (Section 11)

| Objective / Metric | Production Target | Failure Action / Safeguard |
|:---|:---|:---|
| **API Latency (p95)** | $\le 25\text{ ms}$ | Auto-scale pods via Kubernetes HPA |
| **API Latency (p99)** | $\le 50\text{ ms}$ | Fallback to ISO deterministic rule layer |
| **Service Availability** | $\ge 99.95\%$ | Multi-AZ redundant deployment |
| **Ingestion Freshness** | $\le 10\text{ seconds}$ | Alert on Kafka consumer lag |
| **Prediction Lead Time** | $7\text{ to }14\text{ Days}$ | Flag candidate models that regress lead time |
| **False Alert Burden** | $\le 1.5\text{ / }100\text{ machines / month}$ | Alert hysteresis & minimum duration filters |
| **Recall on Critical Failures** | $\ge 92.0\%$ | Retraining gate blocker |
| **Calibration Brier Score** | $\le 0.05$ | Recalibrate probability scaling layer |

---

## 3. 18-Month Project Plan & Phase Deliverables (Section 20)

| Phase | Duration | Core Deliverables & Milestones |
|:---|:---|:---|
| **Phase 1: Discovery & Architecture** | Months 1–2 | Asset taxonomy, failure mode catalog, data contracts, security model |
| **Phase 2: Data Platform** | Months 3–4 | Kafka cluster, S3 data lake, Great Expectations validation, historical backfills |
| **Phase 3: Feature Engineering** | Months 5–6 | Stateful streaming features, EWMA, FFT spectral bands, point-in-time datasets |
| **Phase 4: Baseline Models** | Months 7–8 | Multi-horizon risk baseline, anomaly baseline, time-based splits |
| **Phase 5: Advanced ML & Calibration** | Months 9–10 | Probabilistic RUL (P10/P50/P90), failure-mode classifier, Platt calibration |
| **Phase 6: Decision System** | Months 11–12 | Cost-sensitive decision engine, hysteresis alert suppression, SHAP explainability |
| **Phase 7: MLOps Control Plane** | Months 13–14 | Model registry, CI/CD automated gates, drift monitors, retraining pipeline |
| **Phase 8: Production Deployment** | Months 15–16 | Kubernetes cluster, canary/shadow deployment, security hardening, load testing |
| **Phase 9: Pilot & Plant Acceptance** | Month 17 | Validation on Greenville & Atlanta plants, engineer acceptance, ROI audit |
| **Phase 10: Scale & Handover** | Month 18 | Global rollout to 15,000 assets, runbooks, disaster recovery drills, handover |

---

## 4. 14-Member Team Structure (Section 21)

```
                    ┌─────────────────────────┐
                    │  Project Lead & Scrum   │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼────────────────────────┐
         │                       │                        │
         ▼                       ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  ML Engineering  │    │ Data Engineering │    │ Platform/DevOps  │
│   (3 Engineers)  │    │   (3 Engineers)  │    │   (4 Engineers)  │
│ - Multi-Horizon  │    │ - Kafka & S3     │    │ - Kubernetes     │
│ - Probabilistic  │    │ - Spark ETL      │    │ - Terraform      │
│   RUL & Anomaly  │    │ - Feature Store  │    │ - MLOps CI/CD    │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│Backend & Services│    │ Analytics & BI   │    │  QA / SDET       │
│  (2 Engineers)   │    │   (1 Engineer)   │    │   (1 Engineer)   │
│ - FastAPI        │    │ - Dashboards     │    │ - Data Contracts │
│ - SAP PM Integ.  │    │ - Executive KPIs │    │ - Model Testing  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```
