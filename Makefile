# ============================================
# 🔧 FinPilot Makefile
# Common development and deployment commands
# ============================================

.PHONY: help install test lint format clean docker run scanner

# Default Python
PYTHON := python3
PIP := pip3

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
	@echo "  make run         - Start Streamlit dashboard"
	@echo "  make scanner     - Run stock scanner"
	@echo "  make scanner-agg - Run scanner (aggressive mode)"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start containers"
	@echo "  make docker-down  - Stop containers"
	@echo "  make docker-logs  - View container logs"
	@echo "  make docker-full  - Start all services"
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
run:
	@echo "$(BLUE)Starting Streamlit dashboard...$(NC)"
	streamlit run panel_new.py --server.port 8501

scanner:
	@echo "$(BLUE)Running stock scanner...$(NC)"
	$(PYTHON) scanner.py

scanner-agg:
	@echo "$(BLUE)Running scanner (aggressive mode)...$(NC)"
	$(PYTHON) scanner.py --aggressive

# ============================================
# 🐳 Docker
# ============================================
docker-build:
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build --target production -t finpilot:latest .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-up:
	@echo "$(BLUE)Starting containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Containers started$(NC)"
	@echo "Dashboard: http://localhost:8501"

docker-down:
	@echo "$(BLUE)Stopping containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

docker-logs:
	docker-compose logs -f finpilot

docker-full:
	@echo "$(BLUE)Starting full stack...$(NC)"
	docker-compose --profile scanner --profile telegram --profile cache up -d
	@echo "$(GREEN)✓ Full stack started$(NC)"

docker-clean:
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	docker-compose down -v --rmi local
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
