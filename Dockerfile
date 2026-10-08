# HeartGuard — Production Dockerfile
# Multi-stage build for minimal production image
# Python 3.12 slim base (Debian bookworm)
# Application runs as non-root user

# --- Stage 1: Build Python dependencies ---
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Install system dependencies required by numpy/scikit-learn/tensorflow
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libffi-dev \
        && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Build React frontend ---
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --omit=dev 2>/dev/null || npm install --omit=dev

COPY frontend/ ./
RUN npm run build

# --- Stage 3: Production image ---
FROM python:3.12-slim-bookworm AS production

LABEL maintainer="HeartGuard Team"
LABEL description="HeartGuard - Early Heart Disease Risk Prediction with Explainable AI"
LABEL version="2.0.0"

# Security: do not run as root
RUN groupadd --gid 1000 heartguard && \
    useradd --uid 1000 --gid heartguard --create-home heartguard

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY config/ ./config/
COPY src/ ./src/
COPY api/ ./api/
COPY scripts/ ./scripts/

# Copy built frontend from frontend-builder
COPY --from=frontend-builder /app/frontend/dist ./static/

# Copy model artifacts
COPY models/ ./models/

# Copy data files needed at runtime
COPY data/raw/ ./data/raw/

# Create directories for runtime data and logs
RUN mkdir -p /app/data/auth \
    /app/data/security \
    /app/data/assessments \
    /app/data/alerts \
    /app/data/evaluations \
    /app/data/tmp \
    /app/reports/generated \
    /app/logs && \
    chown -R heartguard:heartguard /app

USER heartguard

# Environment defaults (overridable at runtime)
ENV ENVIRONMENT=production \
    DEBUG=false \
    LOG_TO_FILE=true \
    LOG_LEVEL=WARNING \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Health check using the API health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/live')"]

# FastAPI production startup
ENTRYPOINT ["uvicorn", "api.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--workers", "1", \
    "--log-level", "warning"]
