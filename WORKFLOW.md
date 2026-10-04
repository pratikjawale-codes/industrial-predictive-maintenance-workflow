# Product and connectivity workflow

## Product

This repository is a local demonstration of how equipment telemetry could inform maintenance decisions. It exposes a FastAPI service and a single-page dashboard for five seeded sample assets. The backend uses in-memory state and deterministic/heuristic model classes; third-party integrations and production-scale assets are not connected.

## Live request path

```text
Dashboard / REST client
        │
        ├─ GET /v1/fleet ───────────────► FleetStreamManager (five seeded assets)
        │                                      └─ feature/model estimates for each asset
        │
        ├─ POST /v1/predict ────────────► DataQualityValidator
        │                                      └─ StreamingFeatureCalculator
        │                                           ├─ MultiHorizonFailureModel
        │                                           ├─ FailureModeClassifier
        │                                           ├─ ProbabilisticRULModel
        │                                           ├─ MultivariateAnomalyDetector
        │                                           └─ MaintenanceDecisionEngine
        │                                                  └─ MaintenanceWorkOrderService alert store
        │
        ├─ GET /v1/assets/{id}/health ───► current sample sensors → feature/model/decision classes
        ├─ GET /v1/assets/{id}/explanation ► attribution rules + generated evidence window
        ├─ POST /v1/simulate/fault ──────► mutate sample sensors → POST /v1/predict
        ├─ GET/POST /v1/alerts... ───────► in-memory alert acknowledgement and work-order store
        ├─ POST /v1/work-orders/{id}/feedback ► validate existing order → append feedback label
        ├─ POST /v1/copilot/chat ────────► keyword retrieval from bundled example manual excerpts
        └─ GET /v1/mlops/drift ──────────► current features → baseline PSI approximation
```

The dashboard refreshes fleet data on load, opens asset details from the fleet table, and loads alert/work-order or drift data when those tabs are selected. Asset detail displays the same horizon probabilities, RUL estimates, and risk score returned by the backend health API; it does not recalculate them in the browser.

Prediction and RUL requests validate the required core telemetry; anomaly requests validate the supplied sensors without requiring unrelated channels. Rejected samples return HTTP 422 and enter the in-memory quarantine list. Dashboard and health reads do not mutate hysteresis or rolling-feature state. Alert hysteresis advances on prediction events only.

## Maintenance feedback loop

1. A prediction can trigger an in-memory alert after the decision engine applies its thresholds and hysteresis.
2. An operator acknowledges an alert or creates a work order from the Alert Center.
3. A technician submits an outcome against an existing work order.
4. The service marks the order completed and appends a feedback record to its in-memory label store.

Feedback is captured but does not automatically launch training. The retraining orchestrator and quality-gate classes are separate examples and are not exposed as an API workflow.

## Related components not connected to the live API

- `features/batch/generator.py`: offline FFT feature extraction.
- `data/labeling/labeler.py`: point-in-time training labels.
- `pipelines/training/train_pipeline.py`: synthetic-data training/evaluation example.
- `pipelines/evaluation/backtester.py`: rolling-origin backtesting example.
- `pipelines/retraining/retrain_orchestrator.py`: retraining/gating example.
- `infra/terraform/`, `infra/kubernetes/`, and `infra/docker/`: deployment templates; they do not provision or connect production systems by themselves.

## State and operational limitations

Fleet telemetry, alerts, work orders, feedback, histories, and feature state are process-local memory. A restart clears them; multiple workers do not share state. Seeded values and bundled technical excerpts are demonstration content, not validated live engineering guidance. Authentication, authorization, persistent storage, external-system credentials, robust observability, and production data governance are not implemented. Do not use this demo to make real maintenance or safety decisions.
