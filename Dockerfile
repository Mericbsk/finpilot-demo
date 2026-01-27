# ============================================
# 🏗️ FinPilot Production Dockerfile
# Multi-stage build for optimized image size
# ============================================

# ---- Stage 1: Builder ----
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ---- Stage 2: Production ----
FROM python:3.11-slim as production

# Security: Run as non-root user
RUN groupadd --gid 1000 finpilot && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home finpilot

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=finpilot:finpilot . .

# Create necessary directories
RUN mkdir -p data/shortlists data/suggestions data/logs && \
    chown -R finpilot:finpilot data/

# Switch to non-root user
USER finpilot

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Start application
ENTRYPOINT ["streamlit", "run", "panel_new.py", "--server.port=8501", "--server.address=0.0.0.0"]
