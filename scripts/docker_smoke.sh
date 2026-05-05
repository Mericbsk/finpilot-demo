#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/docker-compose.yml"
TEMP_ENV_CREATED=0

require_command() {
    local command_name="$1"
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "Missing required command: $command_name" >&2
        exit 127
    fi
}

cleanup() {
    local status=$?
    docker compose -f "$COMPOSE_FILE" down --remove-orphans >/dev/null 2>&1 || true
    if [[ "$TEMP_ENV_CREATED" -eq 1 ]]; then
        rm -f "$REPO_ROOT/.env"
    fi
    exit "$status"
}

wait_for_url() {
    local url="$1"
    local label="$2"
    local attempts="${3:-60}"

    for attempt in $(seq 1 "$attempts"); do
        if curl -fsS "$url" >/dev/null 2>&1; then
            echo "OK: $label (${attempt}s)"
            return 0
        fi
        sleep 1
    done

    echo "FAILED: $label -> $url" >&2
    docker compose -f "$COMPOSE_FILE" logs --tail=80 api web >&2 || true
    return 1
}

trap cleanup EXIT INT TERM

require_command docker
require_command curl
docker compose version >/dev/null

if [[ ! -f "$REPO_ROOT/.env" ]]; then
    TEMP_ENV_CREATED=1
    cat > "$REPO_ROOT/.env" <<'EOF'
FINPILOT_SECRET_KEY=docker-smoke-secret-key-not-for-production
EOF
    echo "No .env found. Created temporary smoke configuration."
fi

echo "Building and starting api/web containers..."
docker compose -f "$COMPOSE_FILE" up -d --build api web

wait_for_url "http://localhost:8000/api/v1/ready" "API readiness" 60
wait_for_url "http://localhost:8000/api/v1/health" "API health" 15
wait_for_url "http://localhost:8000/api/v1/metrics" "API metrics" 15
wait_for_url "http://localhost:3001/" "Web frontend" 60

if ! curl -fsS "http://localhost:8000/api/v1/metrics" | grep -qi "finpilot"; then
    echo "FAILED: API metrics endpoint did not expose expected FinPilot payload" >&2
    docker compose -f "$COMPOSE_FILE" logs --tail=80 api web >&2 || true
    exit 1
fi

echo "Docker smoke checks passed."
