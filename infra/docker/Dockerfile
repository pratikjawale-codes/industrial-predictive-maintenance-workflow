# Multi-stage production container for GE AI Predictive Maintenance Platform
FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY requirements.txt .

# Install dependencies using pip
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Final production stage
FROM python:3.11-slim

WORKDIR /app

# Non-root user for enterprise security (Section 14)
RUN groupadd -g 10001 geops && \
    useradd -u 10001 -g geops -s /bin/bash -m geops

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . /app

RUN chown -R geops:geops /app

USER geops

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live', timeout=3)" || exit 1

ENTRYPOINT ["python", "application.py", "--host", "0.0.0.0", "--port", "8000"]
