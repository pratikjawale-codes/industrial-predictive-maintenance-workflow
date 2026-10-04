# Predictive Maintenance Demo

A local FastAPI demonstration of an industrial predictive-maintenance workflow. It combines a five-asset in-memory fleet, telemetry validation, feature extraction, illustrative risk/RUL/anomaly models, alert decisions, simulated SAP PM work orders, technician feedback, and a browser dashboard.

This project is licensed under the [MIT License](./LICENSE).

> **Scope:** This repository is a prototype, not a production GE system. Fleet data, model metrics, manual citations, SAP behavior, and savings figures are illustrative. State is held in process memory and resets on restart. It does not connect to plant equipment, SAP, a model-serving platform, Kafka, or a real generative-AI service.

## Start

Python 3.11 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python application.py
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) for the dashboard, [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive API docs, or [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) for ReDoc. Use `python application.py --host 0.0.0.0 --port 8000` when running in a container.

## What works in the demo

- Fleet overview, asset health, feature attribution, and a generated sample telemetry history.
- Multi-horizon prediction (`24h`, `72h`, `7d`, `14d`), RUL intervals, anomaly scores, and telemetry range/spike checks.
- Fault simulation, alert acknowledgement, work-order creation, and verified-outcome feedback.
- A keyword-retrieval maintenance assistant with citations to bundled example excerpts.
- Model metadata and feature-drift summaries.

The dashboard calls the same API routes documented in the OpenAPI page. [WORKFLOW.md](./WORKFLOW.md) maps those connections and distinguishes active demo paths from standalone or simulated components.

## Tests and training example

```powershell
python -m pytest
python pipelines/training/train_pipeline.py
```

The training command generates synthetic data for an example evaluation; it does not train or deploy the API's live inference classes.

## Dependencies

- `requirements.txt`: runtime dependencies.
- `requirements-dev.txt`: runtime plus pytest and HTTP test-client dependencies.
- `pyproject.toml`: project metadata, dependency constraints, and pytest configuration.

## Deployment examples

Docker and Kubernetes examples are under [infra/](./infra/). They are templates only: configure real images, secrets, persistence, authentication, network policy, telemetry sources, and operational integrations before any non-local use.
