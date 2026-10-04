"""
GE AI-Powered Predictive Maintenance Platform — Application Runner.
Enables direct execution: python application.py
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path to ensure seamless module resolution
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn


def print_banner(host: str, port: int):
    banner = f"""
========================================================================================
   ____ _____      _    ___   ____                                    _ 
  / ___| ____|    / \\  |_ _| |  _ \\ _ __ ___  ___  ___ _ __  _ __ ___(_)
 | |  _|  _|     / _ \\  | |  | |_) | '__/ _ \\/ __|/ _ \\ '_ \\| '_ ` _ \\ |
 | |_| | |___   / ___ \\ | |  |  __/| | |  __/\\__ \\  __/ | | | | | | | | |
  \\____|_____| /_/   \\_\\___| |_|   |_|  \\___||___/\\___|_| |_|_| |_| |_|_|
                                                                          
       AI PREDICTIVE MAINTENANCE PLATFORM — LOCAL DEMONSTRATION
                   Sample industrial fleet (5 in-memory assets)
========================================================================================
 Domain:          Manufacturing / Industrial IoT Turbomachinery
 Core Objective:  Predict equipment failure 7-14 days ahead & optimize maintenance
 Fleet Scale:     5 sample assets; production-scale infrastructure is not connected
 Architecture:    Multi-Horizon Risk (24h/72h/7d/14d), Probabilistic RUL, 
                  Multivariate Anomalies, SAP PM Work Orders, GenAI Copilot, MLOps

 [OPERATIONAL INTERFACES]:
   >> Interactive Web Dashboard:     http://{host}:{port}/
   >> OpenAPI / Swagger REST Docs:   http://{host}:{port}/docs
   >> ReDoc API Specification:       http://{host}:{port}/redoc
   >> Liveness Health Probe:         http://{host}:{port}/health/live
   >> Readiness Health Probe:        http://{host}:{port}/health/ready

 [TARGET REST API ENDPOINTS (Section 17)]:
   * POST /v1/predict               - Real-time multi-horizon failure risk
   * POST /v1/rul                   - Probabilistic RUL (P10, P50, P90)
   * POST /v1/anomaly               - Multivariate anomaly detection & attribution
   * GET  /v1/assets/{{id}}/health    - Composite asset health summary
   * GET  /v1/assets/{{id}}/explanation - Feature attribution & 24h sample timeline
   * POST /v1/alerts/{{id}}/ack       - Engineer acknowledgement
   * POST /v1/work-orders           - SAP PM work order dispatch & outcome feedback
   * GET  /v1/models/{{model}}/version - Model registry metadata
   * POST /v1/copilot/chat          - GenAI maintenance copilot (GE manuals RAG)
========================================================================================
"""
    print(banner)


import socket


def find_available_port(host: str, preferred_port: int) -> int:
    """Find preferred port if free, or the next available open TCP port."""
    for port in [preferred_port, 8080, 8001, 8081, 8501, 8888]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    return preferred_port


def main():
    parser = argparse.ArgumentParser(description="Run the GE AI Predictive Maintenance Platform")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    # Determine free port
    actual_port = find_available_port(args.host, args.port)
    if actual_port != args.port:
        print(f"[PORT NOTICE] Port {args.port} is currently in use. Automatically binding to open port {actual_port} instead.")

    print_banner(args.host, actual_port)
    uvicorn.run(
        "apps.inference_api.main:app",
        host=args.host,
        port=actual_port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
