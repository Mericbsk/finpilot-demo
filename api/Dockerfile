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

# Ensure headroom-ai and aiolimiter are installed (builder stage may be cached without them)
RUN pip install --no-cache-dir headroom-ai aiolimiter==1.1.0

# Copy application code
COPY api/ ./api/
COPY agents/ ./agents/
COPY core/ ./core/
COPY llm/ ./llm/
COPY scanner/ ./scanner/
COPY auth/ ./auth/
COPY execution/ ./execution/
COPY drl/ ./drl/
COPY models/ ./models/
COPY distribution/ ./distribution/
COPY telegram_alerts.py ./
COPY telegram_bot_runner.py telegram_config.py ./
COPY api/entrypoint.sh ./
# FinSense VS-01 seed artifact; kept outside the mounted /app/data disk.
COPY data/finsense_cases/ ./finsense_cases/

# Non-root user
RUN groupadd -r finpilot && useradd -r -g finpilot finpilot \
 && chown -R finpilot:finpilot /app \
 && chmod +x /app/entrypoint.sh
USER finpilot

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
