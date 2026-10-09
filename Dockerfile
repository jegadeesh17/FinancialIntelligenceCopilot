# Multi-stage production container build adhering to PRODUCTION_ENGINEERING_STANDARDS
# Stage 1: Builder
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-api.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements-api.txt

# Strip test suites, bytecode and type stubs from the venv to shrink the runtime image
RUN find /opt/venv -type d \( -name tests -o -name test \) -prune -exec rm -rf {} + ; \
    find /opt/venv -type f \( -name "*.pyc" -o -name "*.pyi" \) -delete

# Stage 2: Runner
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PORT=8080 \
    HOME="/home/appuser"

WORKDIR /app

# Security: run as unprivileged application user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appgroup . .

USER appuser

# Warm up the ONNX MiniLM embedder so the model is cached in $HOME/.cache/chroma
# (owned by appuser) and containers start without network fetches
RUN python -c "from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2; ONNXMiniLM_L6_V2()(['warm-up'])"

EXPOSE 8080

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
