# ── Stage 1: Build dependencies ─────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Production ────────────────────────────────────
FROM python:3.11-slim AS runner
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Ensure headroom-ai is installed (builder stage may be cached without it)
RUN pip install --no-cache-dir headroom-ai

# Copy application code
COPY api/ ./api/
COPY agents/ ./agents/
COPY core/ ./core/
COPY llm/ ./llm/
COPY scanner/ ./scanner/
COPY auth/ ./auth/
COPY drl/ ./drl/
COPY models/ ./models/

# Non-root user
RUN groupadd -r finpilot && useradd -r -g finpilot finpilot \
 && chown -R finpilot:finpilot /app
USER finpilot

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
