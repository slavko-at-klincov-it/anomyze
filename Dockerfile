FROM python:3.11-slim AS base

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash anomyze
WORKDIR /home/anomyze/app

# Install Python dependencies
COPY pyproject.toml README.md ./
COPY anomyze/ anomyze/
RUN pip install --no-cache-dir --timeout 300 --retries 5 ".[api,observability,hardening]"

# Switch to non-root user
USER anomyze

# HuggingFace model cache directory (mount as volume for persistence)
ENV HF_HOME=/home/anomyze/.cache/huggingface
ENV TRANSFORMERS_CACHE=/home/anomyze/.cache/huggingface

# Default configuration
ENV ANOMYZE_DEVICE=cpu
ENV ANOMYZE_API_HOST=0.0.0.0
ENV ANOMYZE_API_PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

ENTRYPOINT ["uvicorn", "anomyze.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
