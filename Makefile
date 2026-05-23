# ============================================
# 🔧 FinPilot Makefile
# Common development and deployment commands
# ============================================

.PHONY: help install install-dev test test-cov test-fast lint format format-check security clean clean-data run run-legacy scanner scanner-agg docker-check docker-require-env docker-build docker-build-legacy docker-up docker-up-legacy docker-down docker-logs docker-logs-legacy docker-full docker-smoke docker-clean monitoring-up monitoring-down pre-commit pre-run status docs docs-serve

# Default Python
PYTHON := python3
PIP := pip3
COMPOSE ?= docker compose

# Colors for output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

# ============================================
# 📋 Help
# ============================================
help:
	@echo "$(BLUE)FinPilot - Available Commands$(NC)"
	@echo "================================"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make install     - Install dependencies"
	@echo "  make test        - Run all tests"
	@echo "  make test-cov    - Run tests with coverage"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo "  make clean       - Clean cache files"
	@echo ""
	@echo "$(GREEN)Running:$(NC)"
	@echo "  make run         - Start primary local stack (bash start.sh)"
	@echo "  make run-legacy  - Start legacy Streamlit dashboard"
	@echo "  make scanner     - Run stock scanner"
	@echo "  make scanner-agg - Run scanner (aggressive mode)"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-build        - Build API and web images"
	@echo "  make docker-build-legacy - Build legacy Streamlit image"
	@echo "  make docker-up           - Start API and web containers"
	@echo "  make docker-up-legacy    - Start API, web, and legacy Streamlit"
	@echo "  make docker-down         - Stop compose services"
	@echo "  make docker-logs         - View API and web logs"
	@echo "  make docker-logs-legacy  - View legacy Streamlit logs"
	@echo "  make docker-full         - Start API, web, scanner, telegram, cache"
	@echo "  make monitoring-up       - Start Prometheus + Grafana (port 9090 / 3002)"
	@echo "  make monitoring-down     - Stop Prometheus + Grafana"
	@echo "  make docker-smoke        - Build, boot, probe ready/metrics, tear down"
	@echo ""
	@echo "$(GREEN)Documentation:$(NC)"
	@echo "  make docs         - Build documentation site"
	@echo "  make docs-serve   - Serve docs locally (port 8080)"
	@echo ""
	@echo "$(GREEN)Pre-commit:$(NC)"
	@echo "  make pre-commit  - Install pre-commit hooks"
	@echo "  make pre-run     - Run pre-commit on all files"

# ============================================
# 📦 Installation
# ============================================
install:
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov ruff black isort
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-dev: install
	@echo "$(BLUE)Installing dev dependencies...$(NC)"
	$(PIP) install pre-commit bandit safety
	pre-commit install
	@echo "$(GREEN)✓ Dev dependencies installed$(NC)"

# ============================================
# 🧪 Testing
# ============================================
test:
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTHON) -m pytest tests/ -v
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-cov:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest tests/ -v --cov=scanner --cov=drl --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

test-fast:
	@echo "$(BLUE)Running tests (fast mode)...$(NC)"
	$(PYTHON) -m pytest tests/ -x -q
	@echo "$(GREEN)✓ Fast tests completed$(NC)"

# ============================================
# 🔍 Linting & Formatting
# ============================================
lint:
	@echo "$(BLUE)Running linters...$(NC)"
	ruff check scanner/ drl/ --ignore E501,F401
	@echo "$(GREEN)✓ Linting completed$(NC)"

format:
	@echo "$(BLUE)Formatting code...$(NC)"
	black scanner/ drl/ tests/ --line-length 100
	isort scanner/ drl/ tests/ --profile black
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check:
	@echo "$(BLUE)Checking code format...$(NC)"
	black --check scanner/ drl/ --line-length 100
	isort --check-only scanner/ drl/

security:
	@echo "$(BLUE)Running security checks...$(NC)"
	bandit -r scanner/ drl/ -ll -ii --skip B101
	@echo "$(GREEN)✓ Security check completed$(NC)"

security-scan: docker-check
	@echo "$(BLUE)Running Trivy container vulnerability scan...$(NC)"
	docker save borsa-api:latest -o /tmp/trivy-api-scan.tar 2>/dev/null || docker save borsa-api:latest > /tmp/trivy-api-scan.tar
	docker run --rm -v /tmp:/tmp aquasec/trivy:latest image \
	  --input /tmp/trivy-api-scan.tar \
	  --severity CRITICAL,HIGH --ignore-unfixed
	rm -f /tmp/trivy-api-scan.tar
	@echo "$(GREEN)✓ Trivy scan completed$(NC)"

pii-scan:
	@echo "$(BLUE)Running Presidio PII detection test...$(NC)"
	$(PYTHON) -c "from api.middleware.pii_filter import scrub; print(scrub('Test IBAN: TR33 0006 1005 1978 6457 8413 26 and email@test.com'))"
	@echo "$(GREEN)✓ PII scan test completed$(NC)"

# ============================================
# 🧹 Cleanup
# ============================================
clean:
	@echo "$(BLUE)Cleaning cache files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .ruff_cache/
	@echo "$(GREEN)✓ Cache cleaned$(NC)"

clean-data:
	@echo "$(YELLOW)Cleaning data files (shortlists, suggestions)...$(NC)"
	rm -rf data/shortlists/*.csv data/suggestions/*.csv
	@echo "$(GREEN)✓ Data files cleaned$(NC)"

# ============================================
# 🚀 Running
# ============================================
up: docker-check
	@echo "$(BLUE)Starting FinPilot stack via docker compose (cross-platform)...$(NC)"
	docker compose up -d --build
	@echo "$(GREEN)✓ Stack started. API: http://localhost:8000  Web: http://localhost:3000$(NC)"
	@echo "$(YELLOW)Run 'make logs' to follow logs, 'make down' to stop.$(NC)"

down:
	@echo "$(YELLOW)Stopping FinPilot stack...$(NC)"
	docker compose down
	@echo "$(GREEN)✓ Stack stopped$(NC)"

logs:
	docker compose logs -f --tail=200

smoke:
	@echo "$(BLUE)Running startup smoke test...$(NC)"
	$(PYTHON) scripts/smoke_test.py

run:
	@echo "$(BLUE)Starting primary local stack (Linux/macOS native)...$(NC)"
	bash start.sh

scanner:
	@echo "$(BLUE)Running stock scanner...$(NC)"
	$(PYTHON) scanner.py

scanner-agg:
	@echo "$(BLUE)Running scanner (aggressive mode)...$(NC)"
	$(PYTHON) scanner.py --aggressive

# ============================================
# 🐳 Docker
# ============================================
docker-check:
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)docker CLI not found$(NC)"; exit 1; }
	@docker compose version >/dev/null 2>&1 || { echo "$(RED)docker compose plugin not available$(NC)"; exit 1; }

docker-require-env:
	@if [ ! -f .env ]; then \
		echo "$(RED).env not found. Copy .env.example to .env before starting compose services.$(NC)"; \
		exit 1; \
	fi

docker-build: docker-check
	@echo "$(BLUE)Building API and web images...$(NC)"
	docker build -f api/Dockerfile -t finpilot-api:latest .
	docker build -f web/Dockerfile -t finpilot-web:latest ./web
	@echo "$(GREEN)✓ API and web images built$(NC)"

docker-build-legacy: docker-check
	@echo "$(BLUE)Building legacy Streamlit image...$(NC)"
	docker build --target production -t finpilot-legacy:latest .
	@echo "$(GREEN)✓ Legacy image built$(NC)"

docker-up: docker-check docker-require-env
	@echo "$(BLUE)Starting API and web containers...$(NC)"
	$(COMPOSE) up -d api web
	@echo "$(GREEN)✓ Primary stack started$(NC)"
	@echo "Frontend: http://localhost:3001"
	@echo "API:      http://localhost:8000/api/v1/ready"

docker-up-legacy: docker-check docker-require-env
	@echo "$(BLUE)Starting API, web, and legacy Streamlit containers...$(NC)"
	$(COMPOSE) --profile legacy up -d api web finpilot
	@echo "$(GREEN)✓ Primary + legacy stack started$(NC)"
	@echo "Frontend:        http://localhost:3001"
	@echo "API:             http://localhost:8000/api/v1/ready"
	@echo "Legacy Streamlit: http://localhost:8501"

docker-down: docker-check
	@echo "$(BLUE)Stopping compose services...$(NC)"
	$(COMPOSE) down --remove-orphans
	@echo "$(GREEN)✓ Containers stopped$(NC)"

docker-logs: docker-check
	$(COMPOSE) logs -f api web

docker-logs-legacy: docker-check
	$(COMPOSE) logs -f finpilot

docker-full: docker-check docker-require-env
	@echo "$(BLUE)Starting API, web, scanner, telegram, and cache services...$(NC)"
	$(COMPOSE) --profile scanner --profile telegram up -d api web scanner telegram_bot redis
	@echo "$(GREEN)✓ Extended stack started$(NC)"

monitoring-up: docker-check docker-require-env
	@echo "$(BLUE)Starting Prometheus + Grafana monitoring stack...$(NC)"
	$(COMPOSE) --profile monitoring up -d prometheus grafana
	@echo "$(GREEN)✓ Prometheus → http://localhost:9090  Grafana → http://localhost:3002$(NC)"

monitoring-down: docker-check
	@echo "$(YELLOW)Stopping monitoring stack...$(NC)"
	$(COMPOSE) --profile monitoring down prometheus grafana
	@echo "$(GREEN)✓ Monitoring stack stopped$(NC)"

docker-smoke: docker-check
	@echo "$(BLUE)Running Docker smoke test for API + web...$(NC)"
	bash scripts/docker_smoke.sh
	@echo "$(GREEN)✓ Docker smoke test passed$(NC)"

docker-clean: docker-check
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	$(COMPOSE) down -v --remove-orphans --rmi local
	@echo "$(GREEN)✓ Docker resources cleaned$(NC)"

# ============================================
# 🔗 Pre-commit
# ============================================
pre-commit:
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	pip install pre-commit
	pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

pre-run:
	@echo "$(BLUE)Running pre-commit on all files...$(NC)"
	pre-commit run --all-files

# ============================================
# 📊 Reporting
# ============================================
status:
	@echo "$(BLUE)Project Status$(NC)"
	@echo "==============="
	@echo ""
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Files:"
	@echo "  - Scanner modules: $$(ls -1 scanner/*.py 2>/dev/null | wc -l)"
	@echo "  - DRL modules: $$(ls -1 drl/*.py 2>/dev/null | wc -l)"
	@echo "  - Tests: $$(ls -1 tests/test_*.py 2>/dev/null | wc -l)"
	@echo ""
	@echo "Data:"
	@echo "  - Shortlists: $$(ls -1 data/shortlists/*.csv 2>/dev/null | wc -l)"
	@echo "  - Suggestions: $$(ls -1 data/suggestions/*.csv 2>/dev/null | wc -l)"

# ============================================
# 📚 Documentation
# ============================================
docs:
	@echo "$(BLUE)Building documentation site...$(NC)"
	mkdocs build --strict 2>&1 || mkdocs build
	@echo "$(GREEN)✓ Documentation built in site/$(NC)"

docs-serve:
	@echo "$(BLUE)Serving documentation at http://localhost:8080$(NC)"
	mkdocs serve -a 0.0.0.0:8080
